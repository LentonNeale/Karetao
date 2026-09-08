#!/usr/bin/env bash
set -eu

SERVER="/home/lenton/.local/share/stm32cube/bundles/stlink-gdbserver/7.14.0+st.2/bin/ST-LINK_gdbserver"
PROGRAMMER_CP="/home/lenton/.local/share/stm32cube/bundles/programmer/2.23.0/bin"

exec "$SERVER" -cp "$PROGRAMMER_CP" --swd --halt "$@"
