# Electrical, I2C timing and sensor limits (AS5600)

PDF pages of the local copy. Fast-mode (400 kHz) is the project's bus speed; the AS5600 limits below are its Fast-mode Plus figures.

| Rule | Value | Citation |
|---|---|---|
| Supply VDD5V, 5.0V mode | 4.5 min, 5.0 typ, 5.5 max V | p. 7 |
| Supply VDD3V3, 3.3V mode | 3.0 min, 3.3 typ, 3.6 max V | p. 7 |
| Supply current NOM (PM = 00) | 6.5 mA max, always on | p. 7 |
| Operating temperature TA | -40 to 125 °C | p. 7 |
| Abs max VDD5V | -0.3 to 6.1 V | p. 6 |
| Abs max VDD3V3 | -0.3 to 4.0 V | p. 6 |
| Abs max digital/analog pins VIO | -0.3 to VDD+0.3 V | p. 6 |
| Power-up time T_PU | 10 ms max | p. 9 |
| Sampling rate F_S | 150 μs max | p. 9 |
| Settling time, SF = 00 | 2.2 ms max | p. 9 |
| Settling time, SF = 01 | 1.1 ms max | p. 9 |
| Settling time, SF = 10 | 0.55 ms max | p. 9 |
| Settling time, SF = 11 | 0.286 ms max | p. 9 |
| fSCLK | 1.0 MHz max | p. 14 |
| tBUF, bus free time (STOP to START) | 0.5 μs min | p. 14 |
| tHD;STA, hold time (repeated) START | 0.26 μs min | p. 14 |
| tLOW, SCL low | 0.5 μs min | p. 14 |
| tHIGH, SCL high | 0.26 μs min | p. 14 |
| tSU;STA, setup repeated START | 0.26 μs min | p. 14 |
| tHD;DAT, data hold | 0.45 μs max | p. 14 |
| tSU;DAT, data setup | 50 ns min | p. 14 |
| tR, rise time SDA and SCL | 120 ns max | p. 14 |
| tF, fall time SDA and SCL | 10 ns min, 120 ns max | p. 14 |
| tSU;STO, setup STOP | 0.26 μs min | p. 14 |
| Fast-mode device in standard-mode system | tSU;DAT = 250 ns must be met | p. 14 |
| Digital input VIH / VIL | 0.7 × VDD min / 0.3 × VDD max | p. 8 |
| Digital output VOH / VOL | VDD - 0.5 min / 0.4 max | p. 8 |
| Magnetic field Bz | 30 mT min, 90 mT max (orthogonal, at the die's surface along a circle of 1mm) | p. 10 |
| Magnet detection level Bz_ERROR | 8 mT max | p. 10 |
| System INL | ±1 degree max | p. 10 |
| RMS output noise ON_SLOW | 0.015 degree max, after 2.2 ms, SF = 00 | p. 10 |
| RMS output noise ON_FAST | 0.043 degree max, after 286 μs, SF=11 | p. 10 |
| Step response delay SF = 00 / 01 / 10 / 11 | 2.2 / 1.1 / 0.55 / 0.286 ms | p. 30 |
