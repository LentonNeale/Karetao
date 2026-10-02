# CAN frame, checksum and bus settings (MKS SERVO42D/57D CAN manual V1.0.9)

| Rule | Value | Citation |
|---|---|---|
| Frame type | The message uses a standard frame, and the maximum length of the data field is Byte8. | p. 25 |
| Downlink layout (host to driver) | ID, DLC(n), Byte1 code, Byte2...Byte(n-1) data, Byte n (n≤8) CRC | p. 25 |
| Uplink layout (driver to host) | ID, DLC(n), Byte1 code, Byte2...Byte(n-1) data, Byte n (n≤8) CRC | p. 25 |
| CAN ID range | The CAN ID range is 00~2047. (default is 01). | p. 25 |
| Broadcast ID | 00 is the broadcast CAN ID | p. 25 |
| Slave IDs settable from the menu | 01~10 can be set in the CanID option of the display menu; greater than 10 need to be set by serial commands. | p. 25 |
| Menu CanID options (differs from p. 25) | 01 ... 16 (Default: 01); CAN IDes greater than 16 need to be set by serial command | p. 22 |
| Slave IDs available | 1 broadcast CAN ID, 2047 slave CAN ID | p. 9 |
| Checksum | The Check code is CHECKSUM 8bit | p. 25 |
| Checksum example (read encoder) | CRC = (0x01 + 0x30) & 0xFF = 0x31 & 0xFF = 0x31 | p. 25 |
| Checksum worked example | the instruction "01 83 0C 80 CRC" ; CRC = (0x 01 + 0x 83 + 0x 0C + 0x 8 0) & 0xFF = 0x1 10 & 0xFF = 0x 10 | p. 14 |
| Checksum definition | after adding each byte, only the last two digits are taken. | p. 14 |
| Byte order | Instruction data and return data are stored in big-endian format. | p. 14 |
| Numeric base | The numerical base in this article is hexadecimal by default. | p. 14 |
| Broadcast and group replies | When sending commands using a broadcast CAN ID, the slave device will not respond. | p. 25 |
| Group-ID replies | When sending commands using a packet CAN ID, the slave device will not respond. | p. 43 |
| Response mode command | Using the 8CH command, you can set whether the slave device should respond, or select the response method | p. 26 |
| Bit rates supported | CAN interface rate 125K/250K/500K/1M | p. 9 |
| Bit rate menu | 125K，250K，500K(default),1M | p. 21 |
| Set bit rate: command | Code 8AH, bitRate (uint8_t), DLC 3 | p. 40 |
| bitRate values | bitRate = 00 125K; bitRate = 01 250K; bitRate = 02 500K (default); bitRate = 03 1M | p. 40 |
| CAN transceiver | TJA1051T | p. 9 |
| Operating voltage | 12V-24V | p. 9 |
| Termination, stand-alone | A 120Ω terminating resistor is not required for stand-alone communication | p. 18 |
| Wiring advice | the host computer and the motor should share a common ground, and the CAN signal should be transmitted using shielded twisted-pair cable. | p. 18 |
| Set slave CAN ID: command | Code 8BH, address (uint16_t), DLC 4 | p. 40 |
| Slave CAN ID note | 00 is the broadcast address | p. 40 |
| Set group CAN ID: command | Code 8DH, ID(01~0x7FF), DLC 4 | p. 43 |
| Group example | send 50 FD 01 2C 64 00 0C 80 6A, motor1-3 will rotate a turn | p. 43 |
| Slave response config: command | Code 8CH, XX, YY, DLC 4 | p. 41 |
| XX | XX = 01 enabled respond (default); XX = 00 disabled respond | p. 41 |
| YY | YY = 01 enabled active (default); YY = 00 disabled active | p. 41 |
| Default response mode (XX=1, YY=1) | Slave immediately returns to position control start 01 or fails 00; After the motor finishes running or stops when it hits the limit switch, return to 02 or 03. | p. 41 |
| Query when responses are off | After setting the slave device to no response, the motor operating status can be queried using the code "F 1 H". | p. 41 |
| Heartbeat protection: command | Code 98H, Bytes 2-5 times in milliseconds, DLC 6 | p. 44 |
| Heartbeat default | times: Protection time, in milliseconds. (Default: 0); When times=0, the heartbeat protection function is turned off. | p. 44 |
| Heartbeat action | if the motor does not receive any instructions from the host computer within the set protection time, it will control the motor to stop urgently | p. 44 |
| No-verification mode | after the motor receives a message, it will execute the message command without checking whether the CRC checksum is correct. | p. 45 |
| No-verification command | Code 0FH, control word 01H, DLC 3; This instruction is for testing purposes only and cannot be saved. | p. 45 |
