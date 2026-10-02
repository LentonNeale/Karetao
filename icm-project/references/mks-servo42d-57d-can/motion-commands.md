# Motion, zeroing and multi-motor sync commands (MKS SERVO42D/57D CAN manual V1.0.9)

| Rule | Value | Citation |
|---|---|---|
| Speed range | The speed parameter ranges from 0 to 3000. When speed = 0, the motor stops rotating. | p. 68 |
| Max speed, open modes | CR_OPEN / SR_OPEN 400(RPM) | p. 68 |
| Max speed, close modes | CR_CLOSE / SR_CLSOE 1500(RPM) | p. 68 |
| Max speed, FOC modes | CR_vFOC / SR_vFOC 3000(RPM) | p. 68 |
| Speed above mode maximum | If the set speed is greater than the maximum speed of the control mode, the motor runs at the maximum speed of the control mode. | p. 68 |
| Speed vs subdivision | The speed value is calibrated based on 16/32/64 subdivisions; setting speed=1200: At 8 subdivisions, the speed is 2400 (RPM); At 128 subdivisions, the speed is 150 (RPM) | p. 68 |
| Acceleration range | The value of the acceleration(acc) ranges from 0 to 255. If acc=0, the motor runs without acceleration or deceleration | p. 69 |
| Acceleration step time | t2 – t1 = （256-acc）* 50 (uS); Vt2 = Vt1 + 1 (Vt2 <= speed) | p. 69 |
| Speed and direction bytes | Byte 2: The highest bit indicates the direction, the lower 4 bits and Byte 3 together indicate the speed | p. 72 |
| dir value | dir: the value range is 0/1 (CCW/CW) | p. 72 |
| F3H motor enable | DLC 3: F3H, enable (uint8_t); enable = 00 Motor is disabled (loose shaft). enable = 01 Motor enable (shaft lock) | p. 71 |
| F3H validity | In bus control mode, the motor's enable state is no longer controlled by the level of the En pin | p. 71 |
| F7H emergency stop | DLC 2: F7H, CRC; status = 0 Emergency stop failed; status = 1 Emergency stop successful | p. 71 |
| F7H caution | Emergency stop commands are not recommended when the motor speed exceeds 1000 RPM ! | p. 71 |
| F6H speed mode | DLC 5: F6H, dir/speed (Byte2-3), acc (Byte4), CRC | p. 72 |
| F6H example | Send 01 F6 01 40 02 3A , the motor rotates forward at an acc= 2 , speed= 320 (RPM). | p. 72 |
| F6H with run time | DLC 8: F6H, dir/speed, acc, runTime (Bytes 5-7), CRC; runTime unit: 10ms , range (0 ~ 0xFFFFFF) | p. 73 |
| F6H reply | status = 0 Running failed; status = 1 Start running; status = 2 Running completed; status = 5 Data has received for Synchronous mode. | p. 73 |
| F6H stop | When setting acc ≠ 0, the motor decelerates and stops slowly; When setting acc = 0, the motor stops immediately | p. 74 |
| F6H stop caution | It is not recommended to use the immediate stop command when the motor speed exceeds 1000 RPM ! | p. 74 |
| FFH power-on auto run | DLC 3: FFH, enable; enable = C8 Enable automatic operation upon power-on; enable = CA Turn off | p. 75 |
| FDH relative pulses | DLC 8: FDH, dir/speed (Bytes 2-3), acc (Byte4), relpulses (Bytes5-7), CRC | p. 78 |
| FDH relpulses range | relpulses: the motor run steps, the range is 0 – 0xFFFFFF | p. 78 |
| FDH example | send 01 FD 01 40 02 00 FA 00 3B, the motor rotates 20 revolutions in the forward direction ( 16 microsteps ) | p. 78 |
| FDH reply | status = 0 run fail. status = 1 run starting…. status = 2 run complete. status = 3 end limit stoped. status = 5 Data has received for Synchronous mode. | p. 79 |
| FDH reply control | The 8CH instruction can be set to whether to return data. | p. 79 |
| FDH stop | Send 01 FD 00 00 04 00 00 00 02 (decelerate, acc = 4); Send 01 FD 00 00 00 00 00 00 FE (immediate) | p. 80 |
| FDH stop reply | status = 0 stop the motor fail. status = 1 stop the motor starting…. status = 2 stop the motor complete. status = 3 stop by endstop. | p. 80 |
| FEH absolute pulses | DLC 8: FEH, speed (Bytes 2-3), acc (Byte4), absPulses (Bytes 5-7), CRC | p. 82 |
| FEH absPulses range | absPulses the absolute pulse count, with a value range of int24_t ( -8388607 , +8388607 ) . | p. 82 |
| FEH precondition | Before using absolute motion, a zeroing process must be performed once (instruction 0x9 1 or 0x9 2 ) to mark the "zero point". | p. 82 |
| FEH example | Send 01 FE 02 58 02 00 0C 80 E7 | p. 82 |
| FEH reply | status = 0 run fail. status = 1 run starting…. status = 2 run complete. status = 3 end limit stoped. status = 5 Data has received for Synchronous mode. | p. 83 |
| F4H relative coordinates | DLC 8: F4H, speed, acc, relAxis (Bytes 5-7), range int24_t ( -8388607 , +8388607 ) | p. 86 |
| F4H example | Send 01 F4 02 58 02 00 40 00 91 | p. 86 |
| F5H absolute coordinates | DLC 8: F5H, speed, acc, absAxis (Bytes 5-7), range int24_t ( -8388607 , +8388607 ) | p. 90 |
| F5H real-time update | Supports real-time updates of speed and coordinates, meaning that a new command can be issued to change the speed and coordinates while the previous command is running. | p. 90 |
| Coordinate unit | The coordinate values are the cumulative multi-turn encoder values ( 16384/ turn), read using the command "3 1 ". | p. 90 |
| Pulses per turn | the decimal pulse count under 16 subdivisions is 3200, and the corresponding hexadecimal value is 0xC80. | p. 14 |
| 91H execute zero return | DLC 3: 91H, goZeroMode; 00: Execute the "Return to Zero" function; 01: Execute the "Coordinate Zeroing" function | p. 60 |
| 91H equivalence | The following two instructions are equivalent 01 91 92; 01 91 00 92 | p. 60 |
| 91H reply | status = 0 failed to return to zero; status = 1 starting return to zero; status = 2 return to zero complete | p. 60 |
| 92H set zero point | DLC 2: 92H, CRC; This command directly sets the current position to "zero". status =1 Set success. status =0 Set fail. | p. 59 |
| 4AH sync enable | DLC 3: 4AH, enable; enable = 00 disables the multi-motor synchronization flag function (default). enable = 01 Enables | p. 96 |
| 4AH reply | status =1 Set success. status =0 Set fail. | p. 96 |
| 4BH sync execute | CAN ID 00, DLC 2: 4BH, CRC; Returned data: None. | p. 97 |
| 4BH repeat | consider sending the synchronization execution command repeatedly at intervals of about 1ms. | p. 97 |
| Sync example | 00 4A 01 4B; 01 F6 02 80 02 7B; 02 FD 80 64 02 04 E2 00 CB; 00 4B 4B | p. 98 |
| Sync scope | This method allows for the control of an unlimited number of motors. | p. 95 |
| Broadcast example | 00 FD 01 2C 02 00 0C 80 B8 | p. 95 |
