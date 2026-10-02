# Configuration and protection commands (MKS SERVO42D/57D CAN manual V1.0.9)

Replies for write commands carry the same code and `status (uint8_t)` unless stated.

| Rule | Value | Citation |
|---|---|---|
| 80H calibrate encoder | 01, DLC 3, 80H, 00, CRC; status = 0 Calibrating… status = 1 Calibration successful status = 2 Calibration failed | p. 35 |
| 80H precondition | The motor must be unloaded. | p. 35 |
| 82H set working mode | DLC 3, 82H, mode (uint8_t); status = 0 Set fail. status = 1 Set success. | p. 35 |
| 82H modes | 00H CR_OPEN; 01H CR_CLOSE; 02H CR_vFOC (default); 03H SR_OPEN; 04H SR_CLOSE; 05H SR_vFOC | p. 35 |
| Bus-control modes | The instructions in this section are only valid in bus control mode (SR_OPEN/SR_CLOSE/ SR_vFOC ) . | p. 68 |
| 83H set working current | DLC 4: 83H, value (uint16_t) | p. 36 |
| 83H maximum current | SERVO42D/28D/35D: Maximum Current =3000mA; SERVO57D: Maximum Current =5200mA | p. 36 |
| 83H without saving | DLC 5: 83H, value (uint16_t), Cmd 00H | p. 36 |
| 83H reply | status = 0 Set failed. status = 1 Set success with saved. status = 2 Set success without saved. | p. 36 |
| 83H advice | It is not recommended that users directly set the maximum current as the operating current | p. 36 |
| Working current range | 0-3000mA (42D); 0-5200mA (57D) | p. 9 |
| 9BH holding current | DLC 3: 9BH, ratio (uint8_t); ratio = 00 10%; ratio = 01 20%; ratio = 02 30%; ratio = 08 90% | p. 37 |
| 84H subdivisions | DLC 3: 84H, micstep (uint8_t); powers of 2 such as 2, 4, 16, 32, 64 | p. 37 |
| Subdivisions range | 1-256 arbitrary subdivisions | p. 9 |
| 85H En pin level | Level = 00 active low (L); Level = 01 active high (H); Level = 02 active always (Hold) | p. 38 |
| 86H rotation direction | dir = 00 CW; dir = 01 CCW; only valid for pulse interfaces; the direction of the serial interface is determined by the command | p. 38 |
| 89H subdivision interpolation | enable = 00 disables; enable = 01 Enables subdivision interpolation (default value) | p. 39 |
| 8AH bit rate | bitRate = 00 125K; 01 250K; 02 500K (default); 03 1M | p. 40 |
| 8BH slave CAN ID | DLC 4: 8BH, address (uint16_t); status =1 Set success. status =0 Set fail. | p. 40 |
| 8CH response method | DLC 4: 8CH, XX, YY | p. 41 |
| 8DH group CAN ID | DLC 4: 8DH, ID(01~0x7FF) | p. 43 |
| 98H heartbeat | DLC 6: 98H, times in milliseconds; times=0 turns the function off (default 0) | p. 44 |
| 95H position-reach threshold | DLC 5: 95H, enable, values (uint16_t) | p. 44 |
| 95H enable | 00 disables the threshold detection function. 01 Enable the threshold detection function (default) | p. 44 |
| 95H threshold | Location threshold (default value 200); The maximum value is 65535, which is 360 degrees. | p. 44 |
| 95H effect | the "position operation completed" message will only be returned when the actual position of the motor is less than the threshold. | p. 44 |
| 0FH no-verification mode | DLC 3: 0FH, 01H; cannot be saved; testing only | p. 45 |
| 88H overcurrent protection | DLC 3: 88H, enable (uint8_t); enable = 00 disables current overload protection (default). enable = 01 Enables current overload protection | p. 48 |
| Stall release (88H) | The stall protection can be released via CAN command (3D); Press the Enter key; Loosening the motor shaft | p. 48 |
| 9DH position out-of-tolerance | DLC 7: 9DH, Enble, Tim (uint16_t), Errors (uint16_t) | p. 49 |
| 9DH Tim | 1 (Tim) unit is approximately equal to 15 ms. | p. 49 |
| 9DH Errors | When Errrors = 28000 , the motor is misaligned by 360 degrees. | p. 49 |
| 9DH example | send 01 9D 01 00 14 36 B0 99; return 01 9D 01 9F | p. 49 |
| 3FH restore factory settings | DLC 2: 3FH, CRC; status = 0 Recovery failed; status = 1 Recovery successful | p. 51 |
| 3FH side effect | After restoring the default parameters, the driver board will automatically restart, and there is no need to recalibrate the motor. | p. 51 |
| 41H reset and restart | DLC 2: 41H, CRC; This command only resets and restarts the motor; it does not modify configuration parameters. | p. 51 |
| 41H reply | status = 0 Reset failed; status = 1 Reset successful | p. 51 |
| Calibration after install | the driver board is first installed on the motor, or after the motor wiring sequence is changed , the motor needs to be recalibrated. | p. 103 |
