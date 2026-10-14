# MKS SERVO42D/57D CAN reference

Makerbase's CAN user manual for the MKS SERVO42D/57D closed-loop stepper drivers, as used by the
`Arm_Sensor_Hub/Middlewares/Third_Party/MksServo` library and the CAN service.

## Source

| Field | Value |
|---|---|
| Publisher | Makerbase (makerbase-motor on GitHub) |
| Title | MKS SERVO 42/57D Closed-Loop Stepper Motor CAN User Manual V1.0.9 |
| Version / revision | V1.0.9; "This manual corresponds to firmware version V 1.0.9"; version table lists V1.0.9 firmware Nov-2025 (p. 1-2) |
| Date | Nov-2025 (version table, p. 2); PDF creation date 2025-12-18 |
| Obtained from | https://raw.githubusercontent.com/makerbase-motor/MKS-SERVO42D-57D/master/User%20Manual/V1.0.9/MKS%20SERVO42%2657D_CAN%20User%20Manual%20V1.0.9.pdf (repo https://github.com/makerbase-motor/MKS-SERVO42D-57D, folder `User Manual/V1.0.9/`) |
| Retrieved | 2026-10-01 |
| Licence note | The repo has no licence file (GitHub reports none), so the PDF is not copied here. Local copy below |
| Local copy | `~/.icm/sources/mks-servo42d-57d-can/MKS SERVO42&57D_CAN User Manual V1.0.9.pdf`, 3,044,183 bytes, sha256 `2d16ff8e1184ffa50c997280ac05cd5ab47bdf4632ef5397efae233e0107078f` (fetched with `fetch_source`; `source.json` beside it) |

The project cites this same version (V1.0.9) in
`multi-motor-synchronisation.md` (this folder; moved from Documentation/02_INTERFACES/CAN/ on 2026-10-03): no version mismatch.
Page numbers in notes are PDF pages, equal to the printed page numbers.

## Files

| File | Contains | Read when |
|---|---|---|
| `frame-and-checksum.md` | Frame layout, 8-bit checksum, CAN IDs, bit rates, response method, heartbeat, wiring | Building or checking frames, bxCAN bitrate, ID plan |
| `read-commands.md` | Read commands (30H-42H, 00H, 01H, F1H) and their replies | Decoding replies, polling |
| `config-commands.md` | Write/config commands (80H-9DH, 0FH, 3FH, 41H), limits and statuses | Commissioning, current and protection settings |
| `motion-commands.md` | Speed and acceleration rules, F3H-FFH motion commands, zeroing, 4AH/4BH sync | Motion code and its reviews |
| `homing-and-limits.md` | Homing commands (90H, 91H, 92H, 94H, 9AH, 9EH), the worked examples in 7.4-7.7, left and right limit switches (Part 8) | Homing, zeroing or limit-switch code and commissioning |
| `pid-and-misc-config.md` | PID parameters (96H, 97H) with defaults and the factory warning, 87H screen-off, 8FH key lock | Before touching PID, or configuring the drive's screen and keys |
| `firmware-history-and-precautions.md` | Firmware version history, precautions, screen error messages, host software compatibility, schematic links | Checking which firmware has a command, bring-up, fault finding |

## Authority

The manual is authoritative. When a note and the manual disagree, the manual wins; fix the note.
The manual contradicts itself in places (recorded in the notes, not resolved): menu slave IDs
01~10 on p. 25 against 01..16 on p. 22; the `dir` bit is described as "0/1 (CCW/CW)" on p. 72
while p. 27 says CCW gives positive speed. **Status:** verified on 2026-10-02 with
`verify_citations` and `check_reference`. The phrase check is coarse and does not test every
non-numeric word, so a reviewer should still open the cited page for safety-critical rows.

The three notes added on 2026-10-15 (`homing-and-limits.md`, `pid-and-misc-config.md`,
`firmware-history-and-precautions.md`) come from a 2026-10-04 research session and were checked
against the PDF that day: `verify_citations` passes the first two. On the third it flags only
dotted version and section numbers (such as 1.0.9 and 5.2.16), which it cannot match whole, and
the two schematic URLs; those rows were checked by hand against pp. 1-2, 105 and 106. Every
example frame in `homing-and-limits.md` has a correct checksum. Further manual contradictions
are listed under Open questions in those notes: the 9AH length (DLC 5 against a 6-byte example),
the 8FH key lock values, OUT_2 against PEND for 99H, and homeDir 0 (Clockwise) against the
"forward" example on p. 61. Two smaller ones: p. 14 promises four multi-motor control modes and
lists three, and the CAN manual's introduction on p. 7 names the SERVO42D/57D_RS485.

## Checked against the MksServo library

On 2026-10-15, `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/src/encoder.cpp` matched the
manual for 90H (6 payload bytes; homeSpeed up to 3000), 9AH (sent as DLC 6, following the
example rather than the table), 96H/97H (values 0-1024), 9EH and 94H. Two differences: 94H has
no range check on the homing current, and 99H (pulse divider output) is not restricted to the
57D although the manual says it is only for the 57D (p. 54).

## Not covered

Menu and OLED description (Part 3, except CanRate and CanID), pulse-interface wiring, the I/O
port descriptions and wiring (Part 6, 1.7-1.9; the p. 10 pinout is drawings only), Cangaroo
usage (Part 13), the `Example Code` folder, and the separate RS485 and Modbus RTU manuals in the
same repo.

## Secrets

None.
