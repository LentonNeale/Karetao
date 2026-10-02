# I2C interface (AS5600)

PDF page numbers of the local copy (page 1 is Infineon's notice sheet; the datasheet's own "Page N" is two lower).

| Rule | Value | Citation |
|---|---|---|
| 7-bit slave address | 0x36 (0110110 in binary) | p. 12 |
| Protocol | 2-wire Fast-mode Plus I²C-slave, compliant with UM10204 | p. 12 |
| Role | The AS5600 always operates as a slave on the I²C bus | p. 12 |
| Clock stretching | Clock stretching is not included | p. 12 |
| Bus lines | Connections to the bus are made through the open-drain I/O lines SDA and the input SCL | p. 12 |
| Supported modes | Random/Sequential read; Byte/Page write; Automatic increment (ANGLE register); Standard-mode; Fast-mode; Fast–mode plus | p. 12 |
| Maximum SCL frequency | The maximum SCL frequency is 1 MHz | p. 12 |
| Data sampling | Data is sampled on the rising edge of SCL | p. 12 |
| Word address | The word address selects a register on the AS5600 and is loaded into the address pointer | p. 15 |
| Address pointer | The address pointer is incremented after each byte is transferred, except for certain read transactions to special registers | p. 15 |
| Read from invalid address | The AS5600 returns all zeros in the data bytes | p. 15 |
| Special registers | ANGLE, RAW ANGLE and MAGNITUDE suppress the automatic increment of the address pointer on reads, so a re-read requires no I²C write command to reload the address pointer | p. 15 |
| Special-register condition | This special treatment of the pointer is effective only if the address pointer is set to the high byte of the register | p. 15 |
| Invalid write address | A write to an invalid address is not acknowledged by the AS5600, although the address pointer is incremented | p. 15 |
| Read with pointer reload | S, 0110110, 0, A, Word Address (n), A, Sr, 0110110, 1, A, Data(n), Data(n+1) ... Data(n+X), NA, P; last data byte is followed by NACK | p. 19 |
| Master NACK | The master returns an acknowledge bit after all received bytes other than the last byte; at the end of the last received byte, a NACK is returned | p. 17 |
| Byte order | Data is transferred with the most significant bit (MSB) first | p. 17 |
| Input spike filter | Input filters for SDA and SCL inputs are included to suppress noise spikes of less than 50 ns | p. 19 |
| I²C voltage thresholds (VIL, VIH) | VIL max 0.3 x VDD; VIH min 0.7 x VDD | p. 13 |
| Low output voltage VOL | 0.4 V max, VDD > 2.5V, at 3 mA sink current | p. 13 |
| Total bus capacitance CB | 550 pF max, per bus line | p. 13 |
| I/O capacitance CI/O (SDA, SCL) | 10 pF max | p. 13 |
| Muxes and switches | Special-purpose devices such as multiplexers and switches may exceed this capacitance because they connect multiple paths together | p. 13 |
| Pins SDA, SCL | SDA I²C Data (consider external pull-up); SCL I²C Clock (consider external pull-up) | p. 5 |
