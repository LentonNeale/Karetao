# TCA9548A reference

Datasheet for the TI TCA9548A low-voltage 8-channel I2C switch with reset, the multiplexer the Arm Sensor Hub firmware uses in front of its AS5600 sensors.

## Source

| Field | Value |
|---|---|
| Publisher | Texas Instruments |
| Title | TCA9548A Low-Voltage 8-Channel I2C Switch with Reset |
| Version / revision | SCPS207H (Revision H), MAY 2012 - REVISED SEPTEMBER 2024 |
| Date | September 2024 (exact day not printed on source) |
| Obtained from | https://www.ti.com/lit/ds/symlink/tca9548a.pdf |
| Retrieved | 2026-10-01 |
| Licence note | Vendor PDF is copyrighted and is not stored here. Local copy below |
| Local copy | `~/.icm/sources/tca9548a/tca9548a.pdf`, 2,772,549 bytes, sha256 `2137822fd7128945ea44e83f4e100a932b30964d763715eeffe217ee6080a2dc` (fetched with `fetch_source`; its `source.json` sits beside it) |

## Files

| File | Contains | Read when |
|---|---|---|
| `addressing-and-control.md` | Address table, control register, channel select behaviour, reset and power-on reset | Reviewing mux address, channel select, probe or recovery code |
| `timing-and-electrical.md` | Fast-mode I2C timing, reset timing, supply, input levels, switch resistance and capacitance | Checking bus speed, timeouts, supply and bus loading |

## Authority

The datasheet PDF is authoritative; page numbers are its printed pages, equal to the PDF pages of the local copy. When a note and the source disagree, the source wins — fix the note. **Status:** verified on 2026-10-02 with `verify_citations` and `check_reference`.

## Not covered

Thermal data, typical characteristics curves, application and layout sections, parameter measurement figures, packaging and orderable information, Standard-mode rows other than fscl. Go to the datasheet.

## Secrets

None.
