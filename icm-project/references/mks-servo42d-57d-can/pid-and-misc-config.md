# PID parameters and miscellaneous configuration (MKS SERVO42D/57D CAN manual V1.0.9)

Commands 96H and 97H (PID, 5.3), 87H (screen off) and 8FH (key lock). Replies carry the same code
and `status (uint8_t)`: status =1 Set success, status =0 Set fail.

| Rule | Value | Citation |
|---|---|---|
| PID warning | MKS motors have their PID parameters pre-adjusted at the factory. Unless otherwise required, users are advised against adjusting the PID parameters themselves | p. 46 |
| PID caution | If such adjustment is necessary, proceed with extreme caution to avoid damaging the motor | p. 46 |
| 96H vFOC Kp, Ki | DLC 7: 96H, CMD 00H, Kp (Bytes 3-4), Ki (Bytes 5-6), CRC | p. 46 |
| 96H vFOC Kp, Ki defaults | Kp: Range 0-1024 (Default: 0xDC); Ki: Range 0-1024 (Default: 0x64) | p. 46 |
| 96H vFOC Kd, Kv | DLC 7: 96H, CMD 01H, Kd (Bytes 3-4), Kv (Bytes 5-6), CRC | p. 46 |
| 96H vFOC Kd, Kv defaults | Kd: Range 0-1024 (Default: 0x10E); Kv: Range 0-1024 (Default: 0x140) | p. 46 |
| 96H read back | `01 00 96 00 CRC` (Kp, Ki); `01 00 96 01 CRC` (Kd, Kv) | p. 46 |
| 97H CLOSE Kp, Ki | DLC 7: 97H, CMD 00, Kp, Ki, CRC; Kp: Range 0-1024 (Default: 0xC8); Ki: Range 0-1024 (Default: 0x50) | p. 47 |
| 97H CLOSE Kd, Kv | DLC 7: 97H, CMD 01, Kd, Kv, CRC; Kd: Range 0-1024 (Default: 0xFA); Kv: Range 0-1024 (Default: 0x12C) | p. 47 |
| 97H read back | `01 00 97 00 CRC` (Kp, Ki); `01 00 97 01 CRC` (Kd, Kv) | p. 47 |
| 87H auto screen-off | DLC 3: 87H, enable (uint8_t), CRC; enable = 01 enabled; enable = 00 disabled | p. 39 |
| 87H behaviour | the screen will automatically turn off after about 15 seconds, and any button can wake up the screen again | p. 39 |
| 8FH key lock | DLC 3: 8FH, enable (uint8_t), CRC; enable = 00 Key lock; enable = 01 Key lock (see Open questions) | p. 42 |

## Open questions (manual inconsistencies, not resolved)

- 8FH: both 00 and 01 are labelled "Key lock" (p. 42), so which value locks the keys is unknown.
- 99H (pulse divider output, p. 54): the output is first called OUT_2 and then the "PEND port". The manual does not say whether they are the same pin.
