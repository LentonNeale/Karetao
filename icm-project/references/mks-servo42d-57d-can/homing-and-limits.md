# Homing and limit switches (MKS SERVO42D/57D CAN manual V1.0.9)

Commands 90H, 91H, 92H, 94H, 9AH and 9EH, the worked examples in 7.4-7.7, and the left and right
limit switches (Part 8). Replies for write commands carry the same code and `status (uint8_t)`:
status =1 Set success, status =0 Set fail, unless stated.

## Commands

| Rule | Value | Citation |
|---|---|---|
| Coordinate zeroing | No search process is required; it directly runs to the "coordinate zero point" position | p. 56 |
| Coordinate zeroing precondition | you need to first execute the "Return to Zero" function to determine the "zero point" | p. 56 |
| 9EH port mapping | DLC 3: 9EH, enable (uint8_t), CRC; bus control mode only | p. 56 |
| 9EH enable | enable = 00 Disable port mapping (default); enable = 01 Enable port mapping | p. 56 |
| 9EH on 28/35/42D | since it only has a left limit port, in bus control mode, the limit port remapping can be enabled to add a right limit port | p. 56 |
| 9EH mapped ports | Left limit switch -> En port; Right limit switch -> Dir port; the COM port must be connected to the corresponding high level | p. 56 |
| 90H homing parameters | DLC 8: 90H, homeTrig, homeDir, homeSpeed (Bytes 4-5), EndLimit, hm_mode, CRC | p. 57 |
| 90H homeTrig | 0: Low level when closed; 1: High level when closed | p. 57 |
| 90H homeDir | 0: Clockwise; 1: Counterclockwise | p. 57 |
| 90H homeSpeed | zero-return speed 0~3000 (RPM) | p. 57 |
| 90H EndLimit | 0: Disable limit function; 1: Enable limit function | p. 57 |
| 90H hm_mode | 0: Return to zero using the origin switch; 1: Mechanical limit switch for zeroing; 2: Single lap to zero | p. 57 |
| 90H note | After using the limit function for the first time or changing the limit parameters, you need to perform a limit reset once (Menu -> GoHome or serial command "91H") | p. 57 |
| 94H offset and current | DLC 8: 94H, Hm_offset (Byte2-5), Hm_ma (Bytes 6-7), CRC | p. 58 |
| 94H scope | Hm_ma and Hm_offset are invalid for switch return to zero and single-turn return to zero | p. 58 |
| 94H Hm_offset examples | Hm_offset = 0x4000 (Returns one full rotation, 360 degrees); Hm_offset = 0x2000 (Returns half a circle, 180 degrees) (Default) | p. 58 |
| 94H display | If the value is set to 200mA <= hm_ma < 400mA, the screen will display 200mA | p. 58 |
| 9AH single-turn zero return | DLC 5 in the table, which lays out Byte1-Byte6: 9AH, mode, enable, speed, dir, CRC (see Open questions) | p. 59 |
| 9AH mode | 0: Disable; 1: DirMode; 2: NearMode | p. 59 |
| 9AH enable | 0: Clear 0 points; 1: Set 0 point; 2: Keep 0 points | p. 59 |
| 9AH speed | 0 ~ 4 (The higher the value, the faster the speed) | p. 59 |
| 9AH dir | 0: CW; 1: CCW | p. 59 |
| 92H set zero point | DLC 2: 92H, CRC; This command directly sets the current position to "zero" | p. 59 |
| 91H execute zero return | DLC 3: 91H, goZeroMode, CRC | p. 60 |
| 91H goZeroMode | 00: Execute the "Return to Zero" function; 01: Execute the "Coordinate Zeroing" function | p. 60 |
| 91H default | If the command does not include the "execution mode" parameter, the "origin return to zero" function will be executed by default; `01 91 92` equals `01 91 00 92` | p. 60 |
| 91H status | status = 0 failed to return to zero; status = 1 starting return to zero; status = 2 return to zero complete | p. 60 |

## Worked examples

All examples are for CAN ID 01 and start with `01 82 05 88` (Bus FOC mode).

| Rule | Value | Citation |
|---|---|---|
| Origin switch homing | `01 90 00 00 00 64 00 00 F5`, then `01 91 92`: the motor (100RPM) rotates in the forward direction until the switch is triggered | p. 61 |
| 57D switch supply | When the DIP switches PIN3 and PIN2 of the 57D motor are switched to the ON position, 5V power is supplied to the external switch | p. 61 |
| Mechanical limit homing | `01 90 00 00 00 64 00 01 F6`, `01 94 00 00 20 00 02 58 0F`, then `01 91 92` | p. 62 |
| Mechanical limit current | The zero-return current should not be too large, just enough to drive the load, to avoid damaging the mechanical device | p. 62 |
| Single-lap homing | `01 90 00 00 00 64 00 02 F7`, then `01 9A 02 01 02 00 A0` (Nearest possible zero) | p. 63 |
| Coordinate zeroing | `01 91 01 93`; the motor must be enabled before executing "coordinate return to zero" | p. 64 |
| Coordinate zeroing precondition | For switch-based or mechanical limit switch-based zeroing, "origin zeroing" must be performed first | p. 64 |

## Limit switches (Part 8)

| Rule | Value | Citation |
|---|---|---|
| Limit behaviour | Left limit switch triggered, motor stops moving to the left. Right limit switch triggered, motor stops moving to the right | p. 65 |
| Limit first use | After using the limit function for the first time or changing the limit parameters, you must perform a "return to zero" operation once | p. 65 |
| Pulse mode | The limit function is invalid in pulse control mode | p. 65 |
| Limit settings | Whether the limit port is mapped is set by 9EH; Whether the limit function is enabled is set by 90H | p. 65 |
| Limit configuration example | `01 9E 00 9F` (no mapping), `01 90 00 00 00 64 01 00 F6`, then `01 91 92` | p. 66 |
| Power-on | If the above parameters remain unchanged, there is no need to reconfigure the parameters or execute "origin return to zero" on the next power-on | p. 66 |
| Left limit run | `01 FD 81 2C 02 7F 00 00 2C`; triggering the left limit switch will stop the motor | p. 67 |
| Right limit run | `01 FD 01 2C 02 7F 00 00 AC`; triggering the right limit switch will stop the motor | p. 67 |

## Open questions (manual inconsistencies, not resolved)

- 9AH length (pp. 59-63): the table says DLC 5 but lays out Byte1-Byte6, and the example `01 9A 02 01 02 00 A0` is 6 bytes with a valid checksum. The MksServo library sends DLC 6 (4 payload bytes). Not confirmed on hardware.
- Homing direction: homeDir 0 is Clockwise (p. 57), but the p. 61 example with homeDir 0 "rotates in the forward direction". This adds to the `dir` contradiction recorded in [CONTEXT.md](CONTEXT.md).
