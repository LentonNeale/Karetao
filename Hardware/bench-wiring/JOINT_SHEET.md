# Joint and motor sheet

Fill in what you know; write `unknown` where you don't. This sheet is a working record, not a documentation authority. Once it is filled in, the facts move into `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` §2.1 (commissioning table) and the as-found settings into the bring-up session log.

Prefilled cells come from `SYSTEM_CONFIGURATION.md` §2.1 (as built, 2026-10-04). Correct them if they're wrong.

## 1. Joint and mechanics

| Fact | Base (Axis 0) | Shoulder (Axis 1) | Elbow (Axis 2) | Wrist 1  (Axis 3) | Wrist 2 (Axis 4) | Wrist 3  (Axis 5) |
|---|---|---|---|---|---|---|
| Joint name | Joint X | Joint Y | Joint Z | Wrist Joint 1 | Wrist Joint 2 | Wrist Joint 3 |
| Encoder fitted | no | yes | yes | no | yes | yes |
| Gear ratio (motor turns per one joint turn, e.g. `20`) |1:13.5|1:150|1:150|1:48|1:67.82|1:67.82|
| Transmission type (planetary, harmonic, belt, direct, ...) | Belt reduction | Cycloidal | Cycloidal | Compond Planetary | Compond Planetary  | Compond Planetary  |
| Joint travel range (degrees, or mechanical stops) |360 TBC| 200 TBC | 180 TBC |360 TBC | Unknown | Unknown |
| Home or limit switches fitted (none, home, left, right) |1x WSH231 (Home)|2xKY-003 endstop (Left,Right)|2xKY-003 endstop (Left,Right)|1x WSH231 (Home)|2xKY-003 endstop (Left,Right)|1x WSH231 (Home)|
| Drops under gravity when unpowered? (yes, no, brake) | No | Maybe | Maybe | unsure | Maybe | Maybe |
| Worst gravity pose for the phase 9 holding check | Not Sure | Not Sure | Not Sure | Not Sure | Not Sure | Not Sure |

## 2. Motor

| Fact | Axis 0 | Axis 1 | Axis 2 | Axis 3 | Axis 4 | Axis 5 |
|---|---|---|---|---|---|---|
| Make and model | | | | | | |
| Frame size (NEMA 17, 23, ...) | NEMA23-76mm | NEMA23-76mm | NEMA17-60mm  | NEMA17-34mm | NEMA17-23mm | NEMA17-23mm |
| Step angle (degrees) | | | | | | |
| Rated current (A per phase) | 2.8A | 2.8A | 2.1A | 1.3A | 1.2A | 1.2A |
| Holding torque (N·m), if known | 1.8Nm | 1.8Nm | 0.65Nm | Not Given | 0.24Nm | 0.24Nm  |

## 3. MKS drive

| Fact | Axis 0 | Axis 1 | Axis 2 | Axis 3 | Axis 4 | Axis 5 |
|---|---|---|---|---|---|---|
| Model and board version from the label (e.g. SERVO42D_CAN V1.0) | SERVO57D | SERVO57D | SERVO42D | SERVO42D | SERVO42D | SERVO42D |
| Firmware version (boot screen, or 40H) | | | | | | |
| CAN ID as set | 0x001 | 0x002 | 0x003 | 0x004 | 0x005 | 0x006 |
| Ever moved to another motor, or motor rewired? (needs recalibration) | | | | | | |

## 4. Settings as found

Record what each drive is set to now. Don't change anything for this sheet; the project sets these later.

| Setting | Axis 0 | Axis 1 | Axis 2 | Axis 3 | Axis 4 | Axis 5 |
|---|---|---|---|---|---|---|
| CanRate (menu) | | | | | | |
| Work mode (menu Mode, or 82H) | | | | | | |
| Working current Ma (mA) | | | | | | |
| Holding current (Hold Ma, %) | | | | | | |
| Microstep (MStep) | | | | | | |
| Response mode (8CH: respond, active) | | | | | | |
| Power-on auto-run (FFH) | | | | | | |
| En-pin mode (85H: L, H or Hold) | | | | | | |
| Heartbeat time (98H) | | | | | | |

## Set by the project, not on this sheet

| Setting | Where it is decided |
|---|---|
| Work mode: SR_CLOSE (Provisional, phase 9 holding check) | `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md`, "MKS drive work mode" |
| CanRate 1M | Ruling R9a; `PARAMETER_REGISTER.md` PRM-CAN-01 |
| Heartbeat 98H, 500 ms | Ruling R23b; register row to be added |
| Working current, holding percentage | Register rows, added when phase 9 is planned |
| Multi-motor sync (4AH, 4BH) | In development: `ARCHITECTURE_DECISIONS.md`, "MKS multi-motor synchronisation"; needs drive firmware V1.0.8 or later |
| 9EH port mapping on the 42D drives (switches on En and Dir) | Required by the switch wiring; `Hardware/bench-wiring/README.md`, drive switch inputs |
| Response mode | Project requirements, when WP11 needs it |

## Notes

Anything that doesn't fit a cell:
