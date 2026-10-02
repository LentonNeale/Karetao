# Addressing, control register, reset (TCA9548A)

Page numbers are the datasheet's printed pages (the same as the PDF pages of the local copy).

| Rule | Value | Citation |
|---|---|---|
| Channels | Eight bidirectional translating switches; any individual SCn/SDn channel or combination of channels can be selected | p. 1 |
| Address format | Target address 1 1 1 0 A2 A1 A0, then R/W; first four bits fixed, A2-A0 hardware selectable | p. 15 |
| Address A2 A1 A0 = L L L | 112 (decimal), 70 (hexadecimal) | p. 15 |
| Address A2 A1 A0 = L L H | 113 (decimal), 71 (hexadecimal) | p. 15 |
| Address A2 A1 A0 = L H L | 114 (decimal), 72 (hexadecimal) | p. 15 |
| Address A2 A1 A0 = L H H | 115 (decimal), 73 (hexadecimal) | p. 15 |
| Address A2 A1 A0 = H L L | 116 (decimal), 74 (hexadecimal) | p. 15 |
| Address A2 A1 A0 = H L H | 117 (decimal), 75 (hexadecimal) | p. 15 |
| Address A2 A1 A0 = H H L | 118 (decimal), 76 (hexadecimal) | p. 15 |
| Address A2 A1 A0 = H H H | 119 (decimal), 77 (hexadecimal) | p. 15 |
| Address pins | Connect directly to VCC or ground | p. 3 |
| Register model | The TCA9548A is example of a single-register device; the controller merely writes the register data after the target address, skipping the register number | p. 16 |
| Write | Controller sends START, address with R/W = 0, then the control register byte, then STOP | p. 16 |
| Multiple bytes written | There is no limit to the number of bytes sent, but the last byte sent is what is in the register | p. 16 |
| Read | START, address with R/W = 1, the control register byte, NACK from controller, then STOP | p. 17 |
| Control register | Can be written and read via the I2C bus; each bit B7-B0 corresponds to channel 7-0 and a high (or 1) selects this channel | p. 17 |
| Multiple channels | Multiple SCn/SDn channels may be selected at the same time | p. 17 |
| When a channel becomes active | When a channel is selected, the channel becomes active after a stop condition has been placed on the I2C bus | p. 17 |
| STOP placement | A stop condition always must occur immediately after the acknowledge cycle | p. 17 |
| Multiple bytes received | If multiple bytes are received by the TCA9548A, it saves the last byte received | p. 17 |
| Command byte, channel n | Bit n = 1 channel n enabled, 0 channel n disabled (X = don't care for the other bits) | p. 18 |
| Default / reset state | 0 0 0 0 0 0 0 0, no channel selected, power-up/reset default state | p. 18 |
| Power-up state | Power up with all switch channels deselected | p. 1 |
| Power-on reset release | Held in reset until VCC has reached VPORR; registers and I2C state machine then initialized to all zeroes, all channels deselected | p. 14 |
| RESET input | Active-low; asserted low for a minimum of tWL, it resets its registers and I2C state machine and deselects all channels | p. 14 |
| RESET pull-up | The RESET input must be connected to VCC through a pull-up resistor | p. 14 |
| Pull-ups SDA, SCL | Both SDA and SCL lines must be connected to VCC through a pull-up resistor | p. 14 |
| Channel pull-ups | SDn and SCn: connect to VDPUn through a pull-up resistor | p. 3 |
| Bus idle | A bus is considered idle if both SDA and SCL lines are high after a STOP condition | p. 14 |
