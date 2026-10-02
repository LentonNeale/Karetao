# Read commands and responses (MKS SERVO42D/57D CAN manual V1.0.9)

Every request is `ID, DLC, code, [data], CRC`; every reply starts with the same code byte.

| Rule | Value | Citation |
|---|---|---|
| 30H read encoder: request | 01, DLC 2, 30H, CRC | p. 26 |
| 30H reply | DLC 8; Byte2-Byte5 carry (int32_t); Byte6-Byte7 value (uint16_t) | p. 26 |
| 30H value range | value: the current vaule of the encoder.(range 0~0x3FFF) | p. 26 |
| 30H carry rule | When value is greater than 0x3FFF, carry +=1. When Value is less than 0, carry -=1. | p. 26 |
| Encoder resolution | Encoder single-turn value range is 0~0x4000 | p. 26 |
| Encoder hardware | Onboard industrial- grade high-precision 16384-line magnetic encoder | p. 8 |
| 31H read cumulative encoder: request | 01, DLC 2, 31H, CRC | p. 27 |
| 31H reply | DLC 8; value (int48_t) | p. 27 |
| 31H direction | After one turn clockwise,the value += 0x4000; After one turn CCW,the value -= 0x4000; | p. 27 |
| 31H use | When moving relative to or absolutely according to coordinate values, use the encoder value as the coordinate. | p. 27 |
| 32H read real-time speed: request | 01, DLC 2, 32H, CRC | p. 27 |
| 32H reply | DLC 4; rpm (int16_t) | p. 27 |
| 32H sign | if it run CCW, the speed > 0 (RPM); if it run CW, the speed < 0 (RPM) | p. 27 |
| 33H read received pulses | Request DLC 2; reply DLC 6, value (int32_t) | p. 28 |
| 35H read raw accumulated encoder | Request DLC 2; reply DLC 8, value (int48_t) | p. 28 |
| 35H direction | After one turn CW, the value += 0x4000; After one turn CCW, the value -= 0x4000; | p. 28 |
| 39H read position angle error | Reply DLC 4, value (int32_t); the unit is 0~ 51200 , which means 0~360° | p. 29 |
| 3AH read enable status | Request: 01, DLC 2, 3AH, CRC( 3B ); reply DLC 3 enable (uint8_t) | p. 29 |
| 3AH enable | enable = 1 The motor is enabled. enable = 0 Motor is not enabled. | p. 29 |
| 3BH read return-to-zero status | Reply DLC 4: status1, status2 | p. 30 |
| 3BH status | statusx =0 going to zero. statusx =1 go back to zero success. statusx =2 go back to zero fail. | p. 30 |
| 3BH status meaning | status1 indicates single-turn zero return state; Status2 indicates non-single-turn zero return state; | p. 30 |
| 01H auto-return read-only parameter: request | 01, DLC 5, Cmd 01H, code, times (Bytes 3-4), CRC | p. 31 |
| 01H times | times: The timeout period, in milliseconds (when times = 0, no data is returned). | p. 31 |
| 01H reply | DLC 4: Cmd 01H, code, status; status=00 Set fail. status=01 Set success. | p. 31 |
| 01H example | Send 01 01 31 03 E8 1E; Return 01 01 31 01 34 | p. 31 |
| 00H read configuration parameter: request | 01, DLC 3, Cmd 00H, code, CRC; to read the "working mode", the corresponding code is 82H | p. 32 |
| 00H reply | DLC n+1: code, param; the data format of param should be consistent with the data format when setting this parameter | p. 32 |
| 00H unsupported parameter | Reply DLC 4: code, FFH, FFH, CRC | p. 32 |
| 40H read version: request | 01, DLC 2, 40H, CRC | p. 33 |
| 40H reply | DLC 5: Byte2 b7-b4 cal, b3-b0 hardVer; Bytes 3-4 firmVer; Byte5 CRC | p. 33 |
| 40H cal | cal = 1 The motor has been calibrated. cal = 0 Motor not calibrated | p. 33 |
| 40H hardVer | S42D_485 1; S42D_CAN 2; S57D_485 3; S57D_CAN 4 | p. 33 |
| 42H write user ID | DLC 6: 42H, ID (Bytes 2-5), CRC; reply DLC 3 status 00 Write failed, 01 Write successed | p. 34 |
| 42H read user ID | Request DLC 2: 42H, CRC; reply DLC 6: 42H, ID (Bytes 2-5), CRC | p. 34 |
| F1H read operating status | Request: 01, DLC 2, F1H, CRC; reply DLC 3 status (uint8_t) | p. 70 |
| F1H status codes | Query failed 0; stop 1; speed up 2; speed down 3; full speed 4; homing 5; Calibration 6 | p. 70 |
| F1H validity | This instruction is only valid in "SR_OPEN/SR_CLOSE/ SR_vFOC " mode. | p. 70 |
| 3EH read stall status | Reply DLC 3: status=00 motor is not stalled; status=01 motor is stalled. | p. 50 |
| 3DH release stall | Request DLC 2; reply DLC 3: status = 0 release failed. status = 1 release sucessed. | p. 50 |
| Firmware check | Note: The firmware version can be viewed on the screen when the driver board is powered on. If there is no screen, you can send a serial port 40H command to read it. | p. 105 |
