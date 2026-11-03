#!/bin/sh
# Usage: send.sh <timeout-seconds> [remote-command]
#        send.sh <timeout-seconds>            (remote command on stdin)
# Wraps the remote command in unique BEGIN/END framing, stages it in the
# fixed command file, and drives the logged-in DGX Terminal tab.
set -eu

DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TIMEOUT="${1:?usage: send.sh <timeout-seconds> [remote-command]}"
TAG=$(uuidgen | tr -d '-' | cut -c1-8)
if [ "$#" -ge 2 ]; then
  CMD="$2"
else
  CMD=$(cat)
fi

printf 'P=__DGX; T=%s; printf "\\n${P}${T}B__\\n"; %s; printf "\\n${P}${T}E__\\n"' \
  "$TAG" "$CMD" > /tmp/dgx-term-cmd.txt
exec python3 "$DIR/dgx-term.py" "$TAG" --timeout "$TIMEOUT"
