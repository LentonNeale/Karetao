# CAN 2.0 reference

The Bosch CAN Version 2.0 protocol (frame formats, error handling, fault confinement, bit timing)
as printed in the Motorola/Freescale/NXP "CAN Protocol" manual, for the bxCAN configuration and the
CAN interface documents.

## Source

| Field | Value |
|---|---|
| Publisher | Motorola Ltd (document `BCANPSV2.0/D`), cover branded Freescale Semiconductor; hosted by NXP |
| Title | CAN: Bosch Controller Area Network (CAN) Version 2.0 Protocol Standard (cover: "Bosch Controller Area Network (CAN) Version 2.0 PROTOCOL STANDARD") |
| Version / revision | Rev. 3 (printed on the cover and page footers); the text refers to "the BOSCH specification dated September 1991" |
| Date | 1998 ("MOTOROLA LTD., 1998", p. 3); PDF modified 2005-12-08; NXP copy `Last-Modified` 2019-08-12 |
| Obtained from | https://www.nxp.com/docs/en/reference-manual/BCANPSV2.pdf |
| Retrieved | 2026-10-01 |
| Licence note | Copyrighted Motorola/NXP document, not copied here. Local copy below. Bosch's own specification PDF was not found on bosch-semiconductors.com (searched 2026-10-02), so this NXP-hosted copy is used |
| Local copy | `~/.icm/sources/can-2-0/BCANPSV2.pdf`, 2,714,645 bytes, sha256 `4cdadf8a70719f30b9c4bb34866424593d5b123e3c1cb27ad4015f0a5031975f` (fetched with `fetch_source`; `source.json` beside it) |

This is Motorola's reproduction of the Bosch protocol text plus its own controller chapters, not
Bosch's own PDF. Its section pages are numbered per section (e.g. "10-3"); notes cite PDF pages
instead. Part A (PDF pp. 29-72, sections 1-7) is the 11-bit Standard Format only; Part B (pp. 75-111,
sections 8-13) adds the 29-bit Extended Format. The notes use Part B.

## Files

| File | Contains | Read when |
|---|---|---|
| `frame-formats.md` | Standard and Extended frame fields, DLC, CRC polynomial, bit stuffing, arbitration, intermission | Checking frame layout, ID width, bus-load maths |
| `error-handling.md` | The five error types, error and overload flags, error counters, error-passive and bus-off rules | Bus-off policy and bxCAN error handling |
| `bit-timing.md` | Nominal bit time, segment lengths, sample point, resynchronization jump width, sync rules | Checking prescaler, BS1, BS2 and SJW choices |

## Authority

The cached PDF is authoritative; when a note and the PDF disagree, the PDF wins. The PDF contains
typos (p. 83 says Extended frames have "12 bit" identifiers; p. 85 gives 29 bits). The project
documents also cite **ISO 11898-1** (for example the CAN1 pin notes in
`Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md`). ISO 11898-1 is a paid standard: it is not stored
or quoted here, and no value in these notes comes from it. **Status:** verified on 2026-10-02 with
`verify_citations` and `check_reference`.

## Not covered

Section 7 (increasing oscillator tolerance, Part A, from PDF p. 59), the physical layer and the Motorola
MCAN, TouCAN and MSCAN module chapters (everything after PDF p. 111), Part A text (duplicated by
Part B), message filtering detail, sleep mode, and ISO 11898 physical-layer and CAN FD material.

## Secrets

None.
