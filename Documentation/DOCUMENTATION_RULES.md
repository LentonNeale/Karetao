# Documentation rules

These rules keep the Karetao documents consistent. They define no system requirement. Map and status vocabulary: [`00_INDEX.md`](00_INDEX.md). Scope and who decides: [`01_SYSTEM/PROJECT_CHARTER.md`](01_SYSTEM/PROJECT_CHARTER.md).

## Authority

- **By subject, not location.** The owner of the subject owns the statement, wherever the file sits. Moving a file does not change what it owns.
- **Component boundary.** Component documents explain how a component implements a system requirement. They refer to `SYS-*` rows by ID and never copy requirement text. Each component documentation folder declares its authority in its README: what it owns, and that it does not redefine system requirements.
- **Vendor material** is external authority. Reference it from `icm-project/references/` and do not rewrite it as a project specification.

## Verification

- A component result marked verified is not `SYSTEM_VERIFIED`. Only `05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` carries that status, set by Lenton Neale.
- Each run is filed as an evidence record in the form of [`05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md`](05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md).
- A dirty build never satisfies a matrix row.
- Evidence never becomes a requirement.

## Numbers

- Every number is either a contract constant in an interface document (magic, header size, CRC, frame size, record sizes, message IDs) or a `PRM-*` entry in `06_CONFIGURATION/PARAMETER_REGISTER.md` with a basis.
- Requirements carry no numbers.
- Write "Provisional" for an engineering estimate not yet confirmed. Do not write "guess" or "assumed".

## Lockstep

The SPI frame format is implemented twice: in C (`Arm_Sensor_Hub/App/Src/spi_protocol.c`, `spi_payload_layout.h`) and in Python (`RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py`). A wire change in a document creates the C, Python and test issues in the same change, and the document says "not yet implemented (issue #n)" until the code matches.

## Conflicts and caveats

- **Conflicts.** The newer statement wins, per statement, unless it is still proposed. Name the subject of the conflict, resolve it against the owning authority, and never guess.
- **Caveats.** A caveat (proposed, open, not yet implemented, as-built) travels verbatim with the text it qualifies. Do not copy the text without it.

## Removing a document

- Before removing a document, check git history, unique content and inbound links. Move any unique content to its owner first and fix the links.
- No archive folder is kept. Git history is the archive.
- Record the removal in the provenance line of `00_INDEX.md`.

## Issues

GitHub issues track work, following `.github/ISSUE_CONTRACT.md`. They are not authority. Decisions are recorded in `07_DECISIONS/`.

## Check tool

Run `icm-project/tools/doc_check` before merging a documentation change. It scans for forbidden terms, resolves relative links across the documentation trees, checks `SYSTEM_REQUIREMENTS.md` for numbers, and checks that every `PRM-*` reference exists in the register.
