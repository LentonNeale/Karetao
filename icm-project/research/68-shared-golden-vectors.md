# Issue #68: Implement shared golden-frame vectors asserted by the C and Python SPI suites

Date: 2026-10-16. Branch: `issue/68-shared-golden-vectors`. Requirement or ruling served: SYS-SPI-001
acceptance ("the C and Python protocol tests exchange the same frames bit-for-bit"); findings SPI-10,
VER-23, PRM-19, PRM-20, VER-34 (NDEBUG guard, moved from #71 by #96).

## Predictions

| Layer | Question | Lenton's prediction | What the source showed | Pointer |
|---|---|---|---|---|
| Requirement | What do the two suites share today to satisfy "exchange the same frames bit-for-bit"? | A shared vector file | Nothing shared. `shared/test-vectors/` holds only `.gitkeep`; each suite builds its own frames and round-trips them. The only values on both sides are the three CRC check values, hand-copied. | `Documentation/01_SYSTEM/SYSTEM_REQUIREMENTS.md:25`; `Arm_Sensor_Hub/tests/host/protocol_test_main.c:613`; `RaspberryPi_Sensor_Hub/tests/spi/test_spi_protocol.py:48` |
| Contract | A 512-byte transaction carries a 26-byte frame: what does the contract say about the rest, and do the sides agree? | Must be zero, both enforce | The contract is silent (only "512 bytes total"). Python rejects non-zero bytes after the CRC; C never reads past the CRC. Ruling R4 closes the gap and is assigned to #88. | `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md:74`; `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py:142`; `Arm_Sensor_Hub/App/Src/spi_protocol.c:137`; `Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md:108` |
| Code | How is the magic 0xA55A spelled where a response is built and where a request is validated? | Two different literals, no macro | Held. Built as `0x5Au, 0xA5u`, checked as `UINT16_C(0xA55A)`; the header names the magic's offset but not its value; the host test repeats the byte literals. Same pattern on the Pi: `512` three times in `spi_bus.py`, correlation offsets as literals in `timing.py`. | `Arm_Sensor_Hub/App/Src/spi_protocol.c:30,137`; `Arm_Sensor_Hub/App/Inc/spi_payload_layout.h:20`; `RaspberryPi_Sensor_Hub/src/spi/spi_bus.py:40,58,77`; `RaspberryPi_Sensor_Hub/src/spi/timing.py:34-40` |
| Hardware | Why does the firmware compute the CRC in a software loop instead of the STM32F405 CRC unit? | Wrong CRC variant | Held. CRC-32/ISO-HDLC is reflected in and out with a final XOR; the firmware loop right-shifts with the reflected polynomial 0xEDB88320 and XORs at the end. The F4 CRC unit is fixed to the unreflected 0x04C11DB7 on 32-bit words with no final XOR (RM0090 §4; the manual is not yet filed in the references, so this is from memory, not a note). | `icm-project/references/crc32-iso-hdlc/parameters.md`; `Arm_Sensor_Hub/App/Src/crc32_iso_hdlc.c:13,27,31` |

## Concepts met

- **Golden vector**: a byte sequence fixed outside both implementations, so each is tested against the contract rather than against itself. Two encoders that only round-trip their own output can each be self-consistent and still disagree.
- **Single point of definition**: a contract constant has one named home per side and every other site refers to it; the golden vectors are the check that the two homes agree.
- **Contract silence**: the 512-byte padding content is not specified, so the two receivers diverged without either being wrong against the text. Ruling R4 fills the gap; the vector for it belongs to the commit that applies it (#88).
- **Reflected CRC**: `refin/refout=true` is implemented in software by right-shifting with the bit-reversed polynomial, which is why the firmware's constant is 0xEDB88320 while the catalogue says 0x04C11DB7.
- **`assert` under `NDEBUG`**: C11 §7.2 makes `assert()` expand to `((void)0)` when `NDEBUG` is defined, and CMake's default Release flags define it; a host test that relies on `assert` must refuse to build in that case (VER-34).
- **Lockstep rule**: C, Python and the shared vectors change in one commit (decision log, 2026-10-14 rulings preamble).

## What the change did and how it was verified

`shared/test-vectors/spi/frames.txt` now holds 13 as-built transactions (boot DIAGNOSTIC, the
four-byte GET requests and their ACK, SNAPSHOT or VERSION reply, TIME_SYNC, and one NACK per status
code 1 to 7),
written by `make_vectors.py` from plain `struct` and `zlib`. The C host test `spi_golden_vector_tests`
puts `spi_protocol.c` in each vector's state and compares all 512 response bytes; the Python test
`test_golden_vectors.py` encodes each request from its fields, decodes each response and checks the
NACK status name, and also asserts the file equals the generator's output. Contract constants now
have one home per side: `SPI_FRAME_MAGIC`, the command-reply layout, `SPI_SNAPSHOT_SCHEMA_VERSION`
and explicit `SpiProtocol_Result` values in the C headers; `HEADER_SIZE`, `MAX_PAYLOAD_BYTES` and the
correlation offsets derived from the structs in `spi_protocol.py`, used by `spi_bus.py` and
`timing.py`. `host_test_assert.h` makes every host test refuse to compile under `NDEBUG` (VER-34).
0x03 is now named DIAGNOSTIC in C as in the contract, and SPI section 14 records the status codes.

Verified: Debug and Release firmware builds with the stack check green; `ctest --preset HostTests`
6 of 6 (13 vectors asserted); 178 Pi tests; `doc_check` clean; `make_vectors.py --check` matches.
Mutation checks: a changed response byte and a changed request byte in a copy of the vector file
each failed the C test with the offending byte named, and the request change failed both Python
assertions; compiling a host test with `-DNDEBUG` stops at the `#error`. The first `/code-review`
pass raised seven findings (generator check not enforced, STATUS versus DIAGNOSTIC naming,
`nack_codes` re-implementing the reply layout, leftover literal header indexes, loader rule
mismatch between C and Python, unguarded optionals in the Python test, and the generator's
transport-validity criterion); all seven were fixed and the checks rerun. A second pass raised six
coverage items (the VERSION reply unpinned, no post-transaction state checks in the C runner, two
loader rules missing on the Python side, `sys.path` pollution in the Python test, the generator's
type set untied from `MessageType`, and `nack_codes` now rejecting unknown schema versions); the
first five were fixed, and the sixth is kept as the contract requires (unsupported `schema_version`
is rejected, `SPI_PAYLOAD_SCHEMA.md` common rules) with the reason in the function's docstring.

## Open questions

- Scope ruling (Lenton, 2026-10-16, plan step): this issue delivers the vector mechanism and the as-built vectors, including the four-byte GET request the firmware already accepts; the R4 ignore-trailing-bytes vector lands with #88, R18 with #63, R19b with the system-activate issue. The issue's acceptance criterion is to be amended by comment.
- The NACK status code numbering is now recorded in `SPI_SYSTEM_INTERFACE.md` §14 (approved in the same plan step).
- `TIME_SYNC` vectors describe the protocol module's reply; the service may still NACK after `time_service` judges the sample. #45 deletes them with TIME_SYNC.
- The local `CLAUDE.md` still says `shared/test-vectors` is empty; it is untracked, so Lenton updates it.
