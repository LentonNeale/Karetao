# Registers used by the firmware (AS5600)

The firmware reads STATUS 0x0B, RAW ANGLE 0x0C, ANGLE 0x0E, AGC 0x1A and MAGNITUDE 0x1B; it writes none. PDF pages of the local copy.

| Rule | Value | Citation |
|---|---|---|
| STATUS | 0x0B, read-only, bits MD (bit 5), ML (bit 4), MH (bit 3) | p. 20 |
| RAW ANGLE | 0x0C = RAW ANGLE(11:8), 0x0D = RAW ANGLE(7:0), read-only | p. 20 |
| ANGLE | 0x0E = ANGLE(11:8), 0x0F = ANGLE(7:0), read-only | p. 20 |
| AGC | 0x1A, AGC(7:0), read-only | p. 20 |
| MAGNITUDE | 0x1B = MAGNITUDE (11:8), 0x1C = MAGNITUDE(7:0), read-only | p. 20 |
| ZMCO | 0x00, read-only, ZMCO(1:0) | p. 20 |
| ZPOS, MPOS, MANG | 0x01-0x02, 0x03-0x04, 0x05-0x06, R/W/P | p. 20 |
| CONF | 0x07 (WD, FTH(2:0), SF(1:0)) and 0x08 (PWMF(1:0), OUTS(1:0), HYST(1:0), PM(1:0)), R/W/P | p. 20 |
| BURN | 0xFF, write-only; Burn_Angle = 0x80; Burn_Setting = 0x40 | p. 20 |
| Config change rule | To change a configuration, read out the register, modify only the desired bits and write the new configuration | p. 20 |
| Config at power-up | During power-up, configuration registers are reset to the permanently programmed value. Not programmed bits are zero | p. 20 |
| MH bit | AGC minimum gain overflow, magnet too strong | p. 22 |
| ML bit | AGC maximum gain overflow, magnet too weak | p. 22 |
| MD bit | Magnet was detected | p. 22 |
| AGC range 5V | In 5V operation, the AGC range is 0-255 counts | p. 22 |
| AGC range 3.3V | The AGC range is reduced to 0-128 counts in 3.3V mode | p. 22 |
| AGC guidance | For the most robust performance, the gain value should be in the center of its range | p. 22 |
| MAGNITUDE | The MAGNITUDE register indicates the magnitude value of the internal CORDIC | p. 22 |
| RAW ANGLE vs ANGLE | The RAW ANGLE register contains the unscaled and unmodified angle. The scaled output value is available in the ANGLE register | p. 21 |
| ANGLE hysteresis | The ANGLE register has a 10-LSB hysteresis at the limit of the 360 degree range | p. 21 |
| Narrowed range scaling | In case of narrowed angular range, the resolution is not scaled to narrowed range (e.g. 0° to 360°(full-turn) → 4096dec; 0° to180°→2048dec) | p. 21 |
| Minimum angular range | The angular range must be greater than 18 degrees | p. 21 |
| Resolution | 12 bit | p. 10 |
| DIR pin | DIR = GND: values increase clockwise; DIR = VDD: values increase counterclockwise | p. 5 |
| CONF PM(1:0) | 00 = NOM, 01 = LPM1, 10 = LPM2, 11 = LPM3 | p. 21 |
| CONF HYST(1:0) | 00 = OFF, 01 = 1 LSB, 10 = 2 LSBs, 11 = 3 LSBs | p. 21 |
| CONF SF(1:0) | 00 = 16x (1); 01 = 8x; 10 = 4x; 11 = 2x | p. 21 |
| CONF WD | 0 = OFF, 1 = ON | p. 21 |
