#!/bin/sh
# Usage: bash remote.sh <timeout-seconds>
# Executes the one-line remote command staged in /tmp/dgx-remote-cmd.txt
# through the logged-in DGX Terminal tab (see send.sh / dgx-term.py).
set -eu

DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CMD=$(cat /tmp/dgx-remote-cmd.txt)
exec bash "$DIR/send.sh" "$1" "$CMD"
