# CRC-32/ISO-HDLC reference

The parameter set of CRC-32/ISO-HDLC from the RevEng CRC catalogue, plus where the Karetao project
uses it (the SPI frame trailer between the STM32 firmware and the Raspberry Pi).

## Source

| Field | Value |
|---|---|
| Publisher | Gregory Cook's RevEng project (reveng.sourceforge.io), "Catalogue of parametrised CRC algorithms" |
| Title | Catalogue of parametrised CRC algorithms with 17 or more bits |
| Version / revision | unknown (not printed on source); the page footer says "Last updated 11 December 2024" and the CRC-32/ISO-HDLC entry says "Updated: 11 December 2024" |
| Date | 2024-12-11 (page footer; matches `Last-Modified` 2024-12-11) |
| Obtained from | https://reveng.sourceforge.io/crc-catalogue/17plus.htm |
| Retrieved | 2026-10-01 |
| Licence note | No licence stated on the page; the HTML is not copied here. Local copy below |
| Local copy | `~/.icm/sources/crc32-iso-hdlc/17plus.htm`, 71,925 bytes, sha256 `dee3b75edd21185ba276450f8ae29f213d8f740207b74652967f6b44e55aefbb` (fetched with `fetch_source`; `source.json` beside it) |

## Files

| File | Contains | Read when |
|---|---|---|
| `parameters.md` | width, poly, init, refin, refout, xorout, check, residue, aliases of CRC-32/ISO-HDLC, and two same-poly neighbours | Implementing or reviewing a CRC-32 routine or a test vector |
| `project-use.md` | Where Arm_Sensor_Hub and RaspberryPi_Sensor_Hub compute and check it, cited as `path:lines` | Changing either side of the SPI frame, or the CRC code |

## Authority

The catalogue page is authoritative for `parameters.md`; the project files named in
`project-use.md` are authoritative for what the project does. The firmware loop uses the reflected
polynomial `0xEDB88320`, which the catalogue page does not print (it prints `poly=0x04c11db7` with
`refin=true`); that equivalence is not asserted here. HDLC itself is defined in ISO/IEC 13239 and
ITU-T V.42 is among the catalogue's references; neither is stored or quoted. **Status:** verified on
2026-10-02 with `verify_citations` and `check_reference`; three `unchecked` rows in `parameters.md`
(refin, refout, Class: one-word values) were read by hand against the cached page and match.

## Not covered

Every other CRC in the catalogue, the 16-bit and smaller pages, the catalogue's definitions of the
parameters, the codeword lists and the implementations it cites (AUTOSAR, RFC 1662, xz).

## Secrets

None.
