# Where the Karetao project uses CRC-32/ISO-HDLC (project citations, not source citations)

These rows are facts about the project, cited as `path:lines` in this repository.
Parameters come from `parameters.md`; this note records what the code and docs state.

| Rule | Value | Citation |
|---|---|---|
| Project CLAUDE.md | spi_protocol frames them with CRC32 (crc32_iso_hdlc) | CLAUDE.md:45 |
| Project CLAUDE.md, frame format | The format uses magic 0xA55A, an 18-byte little-endian header, a CRC32 trailer, a maximum frame of 512 bytes | CLAUDE.md:57 |
| System contract parameters | CRC-32/ISO-HDLC: polynomial 0x04C11DB7, initial 0xFFFFFFFF, reflected input/output, final XOR 0xFFFFFFFF, little-endian wire field | Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md:43 |
| Firmware init value | uint32_t crc32 = UINT32_C(0xFFFFFFFF); | Arm_Sensor_Hub/App/Src/crc32_iso_hdlc.c:13 |
| Firmware polynomial (reflected form) | UINT32_C(0xEDB88320) in a bit-by-bit right-shift loop | Arm_Sensor_Hub/App/Src/crc32_iso_hdlc.c:27 |
| Firmware final XOR | return crc32 ^ UINT32_C(0xFFFFFFFF); | Arm_Sensor_Hub/App/Src/crc32_iso_hdlc.c:31 |
| Firmware frame build | Crc32IsoHdlc_Compute(response, SPI_FRAME_HEADER_BYTES + length); written little-endian | Arm_Sensor_Hub/App/Src/spi_protocol.c:35 |
| Firmware frame check | Crc32IsoHdlc_Verify(request, SPI_FRAME_HEADER_BYTES + length, ...) else SPI_PROTOCOL_BAD_CRC | Arm_Sensor_Hub/App/Src/spi_protocol.c:142 |
| Pi implementation | return zlib.crc32(data) & 0xFFFFFFFF | RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py:308 |
| Pi frame build | crc = crc32_iso_hdlc(header + payload); struct.pack('<I', crc) | RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py:123 |
| Pi frame check | actual_crc = crc32_iso_hdlc(raw[:expected_length - CRC_SIZE]) | RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py:153 |
| Reference vector, check value | ASCII 123456789 gives 0xCBF43926, wire bytes 26 39 F4 CB (equals the catalogue check value) | Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md:51 |
| Firmware test | Crc32IsoHdlc_Compute(known_text, sizeof(known_text) - 1u) == UINT32_C(0xCBF43926) | Arm_Sensor_Hub/tests/host/protocol_test_main.c:580 |
