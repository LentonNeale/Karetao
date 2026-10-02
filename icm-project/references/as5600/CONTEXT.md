# AS5600 reference

Datasheet for the AS5600 12-bit magnetic rotary position sensor (I²C, address 0x36), read by the Arm Sensor Hub firmware behind a TCA9548A multiplexer.

## Source

| Field | Value |
|---|---|
| Publisher | ams OSRAM Group (legacy document); owner and provider since 1 July 2026 is Infineon Technologies AG, which now hosts it (non-optical sensor portfolio sold to Infineon) |
| Title | AS5600 12-Bit Programmable Contactless Potentiometer (datasheet) |
| Version / revision | v1-06, 2018-Jun-20 (revision 1-06, changed from 1-05 of 2018-May-18). Document number DS000365: unknown (not printed on source); named in the request |
| Date | 2018-Jun-20 |
| Obtained from | https://www.infineon.com/assets/row/public/documents/24/49/infineon-as5600-datasheet-en.pdf (Infineon's successor page for the part is https://www.infineon.com/part/AS5600). The ams-osram.com product page, https://ams-osram.com/products/sensor-solutions/position-sensors/ams-as5600-position-sensor, redirects to a press release and no longer lists the PDF |
| Retrieved | 2026-10-01 |
| Licence note | Vendor PDF is copyrighted and is not stored here. Local copy below |
| Local copy | `~/.icm/sources/as5600/infineon-as5600-datasheet-en.pdf`, 1,464,781 bytes, sha256 `548490c8a9a6bac0137d360062f98fcba9d7edbf4ee552c99c3e713aea773d7a` (fetched with `fetch_source`; its `source.json` sits beside it) |

## Files

| File | Contains | Read when |
|---|---|---|
| `i2c-interface.md` | Address 0x36, protocol, modes, address-pointer rules, bus electrical limits | Reviewing the driver's I²C transactions or bus design |
| `register-map.md` | Registers the firmware reads (STATUS, RAW ANGLE, ANGLE, AGC, MAGNITUDE), MD/ML/MH bits, CONF fields, resolution | Reviewing register reads, status handling, angle conversion |
| `electrical-and-timing.md` | Supply, power-up, sampling, settling, I²C timing, magnetic and accuracy limits | Checking timeouts, bus speed, sampling rates, supply |

## Authority

The datasheet PDF is authoritative. Page numbers in the notes are PDF pages of the local copy: page 1 is Infineon's notice sheet, so the datasheet's own "Page N" is two lower. When a note and the source disagree, the source wins — fix the note. Note: this copy is the legacy ams-OSRAM document republished by Infineon; no newer revision was found. **Status:** verified on 2026-10-02 with `verify_citations` and `check_reference`.

## Not covered

Analog and PWM output modes, OTP programming and Burn commands, angle programming options A/B/C, low power mode behaviour, watchdog, hysteresis detail, mechanical data, package drawings, ordering. Go to the datasheet.

## Secrets

None.
