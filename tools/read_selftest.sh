#!/bin/sh
# Run a command that starts the in-game self-test (test/selftest.tc), then
# print that run's MECHTEST lines from the Minecraft client log.
#
#   tools/read_selftest.sh [seconds] [command]
#
# Typical use after tc-send.py (which leaves the player in dev mode):
#   tools/read_selftest.sh 30 "$HOME/.claude/skills/terracotta/scripts/tc-mode.py play"
# Waits up to `seconds` (default 30) for a new "MECHTEST DONE" line. With no
# command it waits for the next run started some other way (join, @selftest).
# Exit 0 = run finished with no failures, 1 = failures, 2 = no new run.
# The log is read on the host when inside the VS Code flatpak sandbox.
HOSTRUN=""
[ -f /.flatpak-info ] && HOSTRUN="flatpak-spawn --host"
LOG=$HOME/.var/app/org.prismlauncher.PrismLauncher/data/PrismLauncher/instances/26.3/minecraft/logs/latest.log
lines() { $HOSTRUN sh -c "grep -a 'MECHTEST' '$LOG'" 2>/dev/null | sed 's/.*\[CHAT\] //'; }
done_count() { lines | grep -c 'MECHTEST DONE'; }

before=$(done_count)
[ -n "$2" ] && sh -c "$2" >/dev/null
for i in $(seq 1 "${1:-30}"); do
    [ "$(done_count)" -gt "$before" ] && break
    sleep 1
done
if [ "$(done_count)" -le "$before" ]; then
    echo "no new MECHTEST run"
    exit 2
fi
out=$(lines)
start=$(printf '%s\n' "$out" | grep -n 'MECHTEST BEGIN' | tail -1 | cut -d: -f1)
printf '%s\n' "$out" | tail -n +"$start"
printf '%s\n' "$out" | tail -n +"$start" | grep -q 'MECHTEST FAIL' && exit 1
exit 0
