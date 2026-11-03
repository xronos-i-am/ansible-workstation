#!/usr/bin/env python3
"""Индикатор Яндекс.Диска в трее: статус демона и статус синхронизации."""

import os
import subprocess

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")

from gi.repository import AyatanaAppIndicator3, GLib, Gtk  # noqa: E402

REFRESH_SECONDS = 5
DISK_DIR = os.path.expanduser("~/.yandex-disk")

# Ключ — статус ядра из первой строки `yandex-disk status`.
SYNC_STATES = {
    "idle": ("emblem-ok-symbolic", "синхронизировано"),
    "busy": ("emblem-synchronizing-symbolic", "идёт обмен"),
    "index": ("emblem-synchronizing-symbolic", "индексация"),
    "paused": ("media-playback-pause-symbolic", "пауза"),
    "no internet access": ("network-wired-disconnected-symbolic", "нет соединения"),
    "error": ("emblem-important-symbolic", "ошибка"),
}
UNKNOWN_ICON = "dialog-question-symbolic"


def run_status():
    """Вывод `yandex-disk status`. LC_ALL=C — иначе ответ приходит на языке сессии и не парсится."""
    env = dict(os.environ, LC_ALL="C")
    try:
        done = subprocess.run(
            ["yandex-disk", "status"],
            capture_output=True, text=True, timeout=10, env=env,
        )
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return ""
    return (done.stdout or done.stderr).strip()


def read_state():
    """→ (иконка, строка про демон, строка про синхронизацию)."""
    out = run_status()
    if out is None:
        return UNKNOWN_ICON, "yandex-disk не установлен", "—"
    if not out:
        return "dialog-error-symbolic", "не отвечает", "—"
    if "daemon not started" in out:
        return "action-unavailable-symbolic", "остановлен", "—"

    head = out.splitlines()[0]
    core = head.split(":", 1)[1].strip().lower() if ":" in head else ""
    icon, text = SYNC_STATES.get(core, (UNKNOWN_ICON, core or "неизвестно"))
    return icon, "запущен", text


class Indicator:
    def __init__(self):
        self.indicator = AyatanaAppIndicator3.Indicator.new(
            "yandex-disk-indicator",
            UNKNOWN_ICON,
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_title("Яндекс.Диск")

        self.daemon_item = Gtk.MenuItem(label="Демон: …")
        self.sync_item = Gtk.MenuItem(label="Синхронизация: …")
        self.daemon_item.set_sensitive(False)
        self.sync_item.set_sensitive(False)

        open_item = Gtk.MenuItem(label="Открыть папку")
        open_item.connect("activate", self.on_open)
        refresh_item = Gtk.MenuItem(label="Обновить")
        refresh_item.connect("activate", lambda _: self.refresh())
        quit_item = Gtk.MenuItem(label="Выйти")
        quit_item.connect("activate", lambda _: Gtk.main_quit())

        menu = Gtk.Menu()
        for item in (
            self.daemon_item, self.sync_item, Gtk.SeparatorMenuItem(),
            open_item, refresh_item, Gtk.SeparatorMenuItem(), quit_item,
        ):
            menu.append(item)
        menu.show_all()
        self.indicator.set_menu(menu)

        self.refresh()
        GLib.timeout_add_seconds(REFRESH_SECONDS, self.refresh)

    def on_open(self, _item):
        subprocess.Popen(["xdg-open", DISK_DIR])

    def refresh(self):
        icon, daemon, sync = read_state()
        self.indicator.set_icon_full(icon, f"Яндекс.Диск: {sync}")
        self.daemon_item.set_label(f"Демон: {daemon}")
        self.sync_item.set_label(f"Синхронизация: {sync}")
        return True  # таймер продолжает тикать


if __name__ == "__main__":
    Indicator()
    Gtk.main()
