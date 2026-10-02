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
`Documentation/02_INTERFACES/CAN/MKS_SERVO42D_57D_SYNCHRONISATION.md`: no version mismatch.
Page numbers in notes are PDF pages, equal to the printed page numbers.

## Files

| File | Contains | Read when |
|---|---|---|
| `frame-and-checksum.md` | Frame layout, 8-bit checksum, CAN IDs, bit rates, response method, heartbeat, wiring | Building or checking frames, bxCAN bitrate, ID plan |
| `read-commands.md` | Read commands (30H-42H, 00H, 01H, F1H) and their replies | Decoding replies, polling |
| `config-commands.md` | Write/config commands (80H-9DH, 0FH, 3FH, 41H), limits and statuses | Commissioning, current and protection settings |
| `motion-commands.md` | Speed and acceleration rules, F3H-FFH motion commands, zeroing, 4AH/4BH sync | Motion code and its reviews |

## Authority

The manual is authoritative. When a note and the manual disagree, the manual wins; fix the note.
The manual contradicts itself in places (recorded in the notes, not resolved): menu slave IDs
01~10 on p. 25 against 01..16 on p. 22; the `dir` bit is described as "0/1 (CCW/CW)" on p. 72
while p. 27 says CCW gives positive speed. **Status:** verified on 2026-10-02 with
`verify_citations` and `check_reference`. The phrase check is coarse and does not test every
non-numeric word, so a reviewer should still open the cited page for safety-critical rows.

## Not covered

Menu and OLED description (Part 3, except CanRate and CanID), pulse-interface wiring, I/O ports
and limit switches (Parts 6 and 8, 1.7-1.9), PID parameters (5.3), homing configuration examples
(7.4-7.7), the 8FH key lock, 9EH/94H/90H/9AH homing set-up detail, Cangaroo usage (Part 13), the
`Example Code` folder, and the separate RS485 and Modbus RTU manuals in the same repo.

## Secrets

None.
