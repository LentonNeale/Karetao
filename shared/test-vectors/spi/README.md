# Shared SPI golden frames

`frames.txt` holds the frames that the two SPI protocol implementations must agree on byte for
byte: `Arm_Sensor_Hub/App/Src/spi_protocol.c` (C) and `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py`
(Python). Both test suites read this one file, which is how the acceptance clause of SYS-SPI-001
("the C and Python protocol tests exchange the same frames bit-for-bit") is met. The frame format
itself is defined in `Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md`; this directory
never redefines it.

## Authority and upkeep

- `frames.txt` is the authority. `make_vectors.py` is the tool that writes it from plain `struct`
  and `zlib`, without importing either implementation, and `make_vectors.py --check` fails when the
  committed file no longer equals what the tool would write. Edit the tool, regenerate, commit both.
- Lockstep rule (`ARCHITECTURE_DECISIONS.md`, code-review rulings): a change to the wire changes C,
  Python and this file in one commit. A ruling that is not yet applied in code has no vector here;
  its vector arrives with the commit that applies it (R1 rejection rules and R4 padding with #88,
  R18 reason codes with #63, R19 system-activate with its own issue).
- The vectors describe the protocol module's as-built behaviour. The VERSION reply's identity
  fields (version, build flags, git hash, commit epoch) are build facts, not contract; the vector
  carries the fallback identity the host tests build with (`firmware_version.h`, mirrored as
  `HOST_TEST_IDENTITY` in `make_vectors.py`), so a change to `FIRMWARE_VERSION_*` regenerates it.

## Who asserts what

| Suite | Command | Asserts |
|---|---|---|
| C, `spi_golden_vector_tests` (`Arm_Sensor_Hub/tests/host/spi_golden_vector_tests.c`) | `cmake --preset HostTests && cmake --build --preset HostTests && ctest --preset HostTests` | Puts `spi_protocol.c` in the vector's state, feeds it the request, checks the reported result and compares all 512 response bytes. For a transport-valid request it also reads the header through the `SPI_FRAME_OFFSET_*` macros and checks the CRC. After the transaction it checks the state the result implies: a rejected request changed nothing, an accepted one became the sequence high-water mark, a sent snapshot stopped pending, one transmit sequence number was used. For `get_snapshot_staged` it also feeds the latest-value store (`latest_value.c`) the inputs `make_vectors.py` builds the staged payload from, copies at `SNAPSHOT_COPY_US`, serialises the copy with `SpiProtocol_SerializeSnapshot` and compares it with `stm32.staged_snapshot` byte for byte. |
| Python, `test_golden_vectors.py` (`RaspberryPi_Sensor_Hub/tests/spi/`) | `python -m unittest discover -s RaspberryPi_Sensor_Hub/tests/spi -p 'test_*.py'` | Encodes the request fields and compares with the request bytes; decodes the response bytes and compares with the response fields; decodes ACK/NACK, SNAPSHOT and VERSION payloads and checks status names and correlation, and for SNAPSHOT sensor records the exact validity flags and the RAW ANGLE scaling; rejects every request that carries no fields; checks that `frames.txt` equals the generator's output and that the generator's type set is `MessageType`. |

## File format

Plain text, one vector per section, so C can read it without a parser library.

```text
[name]                              one vector; names are unique
description = free text             ignored by the tests
stm32.next_tx_seq = N               state before the transaction: next response seq
stm32.last_request_seq = N | none   last accepted request seq, or none since boot
stm32.now_us = N                    the STM32 clock when the response is built
stm32.staged_snapshot = HEX         optional: a snapshot payload staged before the request
request = HEX                       optional: the Pi's frame; absent for the boot STATUS frame
request.type = 0xNN                 the decoded request, present only for a transport-valid frame
request.seq = N
request.frame_time_us = N
request.payload = HEX               may be empty
expect = NAME                       OK or a NACK status name (SPI_SYSTEM_INTERFACE.md section 14)
response = HEX                      optional: the frame the firmware stages
response.type = 0xNN                the decoded response
response.seq = N
response.frame_time_us = N
response.payload = HEX
```

Rules:

- `#` starts a comment; blank lines are ignored; numbers are decimal or `0x` hex.
- A hex value is a byte sequence in wire order: the first two characters are byte 0.
- A request or response shorter than 512 bytes is followed by zero bytes up to the 512-byte
  transaction. When a malformed request has no CRC position inside 512 bytes, the request is the
  whole transaction.
- `request.*` fields are present only when the frame is a valid transport frame (good magic,
  version, length, CRC and a message type the Pi knows). A request without them must be rejected
  by the Pi decoder, whatever the firmware's reason code is.
