#!/usr/bin/env python3
"""Run a command on the DGX Spark via the owner's logged-in Mac Terminal tab.

The command file /tmp/dgx-term-cmd.txt must already contain the framing:
  P=__DGX; T=<tag>; printf "\\n${P}${T}B\\n"; <cmd>; printf "\\n${P}${T}E\\n"
Shell-variable assembly keeps the echoed command line free of the literal
markers, so the unique end marker can only come from real output.

Safety: refuses to type unless the front Terminal window is the DGX session
(sparker@spark-5c72) and the selected tab looks idle at a shell prompt.
No file writes; every subprocess call uses constant arguments only.

Usage: dgx-term.py <tag> [--timeout N]
Prints only the output between this run's BEGIN/END markers.
"""
import subprocess
import sys
import time

HOST_MARK = 'sparker@spark-5c72'


def run_const(script):
    return subprocess.run(
        ['osascript', '-e', script], capture_output=True, text=True, shell=False
    )


def resolve_tab_ref():
    """Return an AppleScript tab reference for the DGX session tab.

    Prefers the front window; otherwise scans all windows by title so an
    unrelated local window being frontmost does not block the channel.
    """
    r = run_const(
        'tell application "Terminal" to get name of front window'
    )
    if HOST_MARK in r.stdout:
        return 'selected tab of front window'
    r = run_const(
        'tell application "Terminal" to repeat with w in windows\n'
        'if name of w contains "' + HOST_MARK + '" then return id of w\n'
        'end repeat\n'
        'return 0'
    )
    window_id = r.stdout.strip()
    if not window_id or window_id == '0':
        sys.exit(f'WRONG_WINDOW: no Terminal window title contains {HOST_MARK!r}')
    return f'tab 1 of window id {window_id}'


def tab_contents(tab_ref):
    r = run_const(f'tell application "Terminal" to get contents of {tab_ref}')
    if r.returncode != 0:
        sys.exit(f'OSA_ERR: {r.stderr.strip()}')
    return r.stdout


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit('usage: dgx-term.py <tag> [--timeout N]')
    tag = args[0]
    timeout = 60
    if len(args) > 2 and args[1] == '--timeout':
        timeout = int(args[2])
    begin = f'__DGX{tag}B__'
    end = f'__DGX{tag}E__'

    tab_ref = resolve_tab_ref()
    before = tab_contents(tab_ref)
    lines = [ln for ln in before.splitlines() if ln.strip()]
    if not lines or not lines[-1].rstrip().endswith('$'):
        sys.exit(f'BUSY_OR_NOT_PROMPT: last line is {lines[-1] if lines else "<empty>"!r}')

    r = run_const(
        'set cmdText to do shell script "cat /tmp/dgx-term-cmd.txt"\n'
        f'tell application "Terminal" to do script cmdText in {tab_ref}'
    )
    if r.returncode != 0:
        sys.exit(f'OSA_ERR: {r.stderr.strip()}')

    def extract(contents):
        stop = contents.rfind(end)
        if stop == -1:
            return None
        start = contents.rfind(begin, 0, stop)
        if start == -1:
            return None
        return contents[start + len(begin):stop].strip()

    # --timeout bounds the total wait. Terminal's AppleScript contents reads
    # can lag behind real execution, so long-budget commands (>= 20s) also get
    # a bounded grace window after the deadline; short budgets stay strict.
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2.5)
        block = extract(tab_contents(tab_ref))
        if block is not None:
            print(block)
            return
    if timeout >= 20:
        grace_end = deadline + 15
        while time.time() < grace_end:
            time.sleep(5.0)
            block = extract(tab_contents(tab_ref))
            if block is not None:
                print(block)
                return
    sys.exit('TIMEOUT waiting for remote command to finish')


if __name__ == '__main__':
    main()
