#!/bin/sh

if [[ -e ${HOME}/.wine ]]; then
  source "${HOME}/.wine/winetricks.bash-completion"
fi