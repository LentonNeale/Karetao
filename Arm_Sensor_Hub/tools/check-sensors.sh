#!/usr/bin/env bash
#
# check-sensors.sh - read every commissioned AS5600 axis from the running firmware.
#
# Quick confidence check after changing sensor wiring. It reads the live
# Sensor_LatestValue records out of the STM32 over SWD and reports, per axis,
# which mux channel it is bound to and whether that sensor is producing a valid
# sample. It does NOT build or flash anything, so it only ever reports what the
# firmware already on the board is seeing.
#
# The target is reset first so bring-up re-runs against the current wiring, and
# resumed at the end. The MCU therefore restarts when this script runs.
#
# Usage:
#   tools/check-sensors.sh [path/to/Arm_Sensor_Hub.elf]
#
# Environment:
#   SETTLE_SECONDS   acquisition time before sampling (default 4)
#   AS5600_VDD_5V    1 if the AS5600 supply is 5 V, 0 if 3.3 V (default 1,
#                    since this rig runs the sensors on a 5 V bus). Only
#                    affects the AGC margin hint; the pass/fail verdict does
#                    not depend on it.
#
# Exit status:
#   0  every axis reported a valid sample
#   1  one or more axes did not
#   2  could not run the check at all
#
# Requires: stlink-tools (st-util, st-flash, st-info) and gdb-multiarch.
# The ELF must match the firmware on the board, since symbols come from it.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELF="${1:-$SCRIPT_DIR/../build/Debug/Arm_Sensor_Hub.elf}"
SETTLE_SECONDS="${SETTLE_SECONDS:-4}"
STUTIL_LOG="/tmp/check-sensors-stutil.log"

die() { printf 'ERROR: %s\n' "$1" >&2; exit 2; }

# Use -x (exact name). A -f pattern match would also match this script's own
# command line and kill the shell running it.
stop_server() { pkill -x st-util 2>/dev/null; sleep 1; }
trap stop_server EXIT

for tool in st-util st-flash st-info gdb-multiarch; do
    command -v "$tool" >/dev/null 2>&1 || die "$tool not found in PATH"
done
[ -f "$ELF" ] || die "ELF not found: $ELF (build the Debug preset, or pass the path)"

# A stale gdb server holds the probe and blocks st-flash entirely.
stop_server
st-info --probe >/dev/null 2>&1 || die "no ST-Link probe found (check USB)"

printf 'Resetting target for clean bring-up against current wiring...\n'
st-flash reset >/dev/null 2>&1 || die "could not reset target"
printf 'Acquiring for %ss...\n' "$SETTLE_SECONDS"
sleep "$SETTLE_SECONDS"

setsid st-util -n >"$STUTIL_LOG" 2>&1 &
sleep 2
grep -q 'Listening' "$STUTIL_LOG" 2>/dev/null || die "st-util did not start; see $STUTIL_LOG"

GDB_CMDS="$(mktemp)"
cat > "$GDB_CMDS" <<'EOGDB'
set pagination off
set confirm off
target extended-remote localhost:4242
python
import gdb

VALID, COMM, NO_MAG, WEAK, STRONG = 0x01, 0x02, 0x04, 0x08, 0x10
MD, ML, MH = 0x20, 0x10, 0x08

def verdict(flags):
    if flags & COMM:   return "FAIL", "no I2C response (power or wiring)"
    if flags & NO_MAG: return "FAIL", "magnet not detected"
    if flags & WEAK:   return "FAIL", "magnet too weak"
    if flags & STRONG: return "FAIL", "magnet too strong"
    if flags & VALID:  return "PASS", "valid sample"
    return "FAIL", "no sample yet"

def decode_status(s):
    bits = [n for b, n in ((MD, "MD"), (ML, "ML"), (MH, "MH")) if s & b]
    return "+".join(bits) if bits else "none"

def agc_note(agc, vdd_5v):
    # AS5600 AGC spans 0-128 at 3.3 V or 0-255 at 5 V; lower value means a
    # stronger field. Thresholds are ~90% and ~12% of the applicable span.
    top = 255 if vdd_5v else 128
    if agc >= 0.90 * top: return "  <- weak, little margin"
    if agc <= 0.12 * top: return "  <- strong, little margin"
    return ""

import os
VDD_5V = os.environ.get("AS5600_VDD_5V", "1") not in ("0", "false", "False")
recs = gdb.parse_and_eval("s_latest_values")
encs = gdb.parse_and_eval("s_encoders")
snap = gdb.parse_and_eval("g_sensor_task_snapshot_dbg")

print("")
print("axis  mux  status   raw   degrees   magn  agc  fresh    result")
print("----  ---  ------  ----  --------  -----  ---  -------  ------")
failed = 0
for axis in range(6):
    r = recs[axis]
    flags = int(r["validity_flags"])
    res, why = verdict(flags)
    if res != "PASS":
        failed += 1
    agc = int(r["agc"])
    print("  %d   SD%-2d %-6s  %4d  %8.2f  %5d  %3d  %-7s  %s: %s%s" % (
        axis,
        int(encs[axis]["mux_channel"]),
        decode_status(int(r["status"])),
        int(r["raw_angle_counts"]),
        int(r["processed_angle_mdeg"]) / 1000.0,
        int(r["magnitude"]),
        agc,
        str(r["freshness"]).replace("SENSOR_FRESHNESS_", ""),
        res, why,
        agc_note(agc, VDD_5V) if res == "PASS" else ""))

print("")
print("bring-up: %s   sensor task active: %d" % (
    str(snap["result"]).replace("SENSOR_TASK_BRINGUP_", ""), int(snap["is_active"])))
print("counters: valid=%d  comm_errors=%d  magnet_errors=%d" % (
    int(snap["sample_ok_count"]), int(snap["comm_error_count"]),
    int(snap["magnet_error_count"])))
print("AXES_FAILED=%d" % failed)
end
EOGDB

RAW="$(timeout 90 gdb-multiarch -q -batch -x "$GDB_CMDS" "$ELF" 2>&1)"
rm -f "$GDB_CMDS"

# Release the probe before resetting: gdb leaves the core halted and st-util
# cannot detach, so the reset is what resumes execution.
stop_server
st-flash reset >/dev/null 2>&1

if ! printf '%s\n' "$RAW" | grep -q '^AXES_FAILED='; then
    printf '%s\n' "$RAW" >&2
    die "could not read sensor records (is the matching firmware flashed?)"
fi

printf '%s\n' "$RAW" | sed -n '/^axis/,$p' | grep -v '^AXES_FAILED='
FAILED="$(printf '%s\n' "$RAW" | sed -n 's/^AXES_FAILED=\([0-9]*\)$/\1/p' | tail -1)"

if [ "$FAILED" -eq 0 ]; then
    printf 'RESULT: PASS - all 6 axes reading valid samples\n'
    exit 0
fi
printf 'RESULT: FAIL - %s of 6 axes not reading valid samples\n' "$FAILED"
exit 1
