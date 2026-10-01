# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

Karetao is a monorepo for a robotic arm platform:

- `Arm_Sensor_Hub/`: STM32F405RGT6 firmware (CubeMX-generated, CMake + Ninja, FreeRTOS/CMSIS-RTOS2). It reads AS5600 encoders through a TCA9548A I2C mux, drives MKS servo motors over CAN, and acts as the SPI slave to the Pi.
- `RaspberryPi_Sensor_Hub/`: Raspberry Pi host side, written in standard-library Python. Right now it holds the SPI master scaffold plus timing, time-sync, and data-ready analysis tools.
- `Documentation/`: the Karetao system-level documentation authority. Start at `Documentation/00_INDEX.md`.
- `shared/`: placeholder directories (`libs`, `protocols`, `test-vectors`) that are currently empty.

## Working method (ICM Portal)

Requests are run through the ICM Portal: a local app (in the `LentonNeale/Karetao_Consulting` repo) that takes a request from a Client Liaison conversation to a brief, plan, reviewed design, build, verification and delivery. Start it with `.venv/bin/python -m icm_portal --project ~/Git_repos/Karetao` from that repo. Its settings for Karetao are in `portal.toml`, including the Verify commands, which are the same as CI. Karetao's own ICM workspaces, tools, skills and references are in `icm-project/` (see `icm-project/README.md`); generic ones come from the Portal's shared `icm/`. A Portal build works in a separate worktree and never edits this working copy.

## Commands

Run the firmware commands from `Arm_Sensor_Hub/`:

```bash
cmake --preset Debug && cmake --build --preset Debug        # firmware -> build/Debug/Arm_Sensor_Hub.elf
cmake --preset Release && cmake --build --preset Release
cmake --preset HostTests && cmake --build --preset HostTests && ctest --preset HostTests --output-on-failure
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests   # single test executable
```

Run the Pi tests from the repo root:

```bash
python -m unittest discover -s RaspberryPi_Sensor_Hub/tests/spi -p 'test_*.py' -v
python -m unittest RaspberryPi_Sensor_Hub.tests.spi.test_spi_protocol -v   # single module (from root)
```

CI (`.github/workflows/arm-ci.yml` and `raspberry-ci.yml`) runs exactly these commands. It is path-filtered to each component plus `shared/`. The firmware toolchain is `arm-none-eabi-gcc`. Locally, VS Code uses STM32Cube's `cube-cmake`.

The project's definition of done is: a firmware source change is complete when the Debug build passes. Release builds and host tests are required before release approval (`Arm_Sensor_Hub/Documentation/BUILD_CONTRACT.md`).

## Firmware architecture

- Application code lives in `Arm_Sensor_Hub/App/{Inc,Src}` as C11 modules named `<module>.c/.h`. `app_init.c` wires them together and holds the commissioning tables: MKS motor CAN IDs, the sensor mux-channel map (the logical axis N maps to mux channel N+2), and joint mappings. To rewire the arm, edit those tables.
- CubeMX output (`Core/`, `Drivers/`, `.ioc`) must stay regenerable. Put application code in `App/` or in CubeMX `USER CODE` sections only.
- `Middlewares/Third_Party/MksServo` is a C++17 library. It may reach `App/` only through the C-compatible `mks_api.h`. Embedded code uses no exceptions or RTTI.
- The data flow runs like this: sensor/CAN tasks write `*_latest_value` stores, `snapshot_builder` assembles snapshots, `spi_protocol` frames them with CRC32 (`crc32_iso_hdlc`), and `spi_slave_service` serves them to the Pi with a data-ready line (`spi_data_ready`). `lifecycle`, `health_monitor`, `time_service`, and `motion_permission` gate that behaviour.
- Host tests (`tests/host/`) compile selected `App/Src` files natively against the header stubs in `tests/host/stubs/` (FreeRTOS, HAL), with `TIME_SERVICE_HOST_TEST` defined. Their source lists are explicit, so a new App module needs entries in both `Arm_Sensor_Hub/CMakeLists.txt` and `tests/host/CMakeLists.txt`. The `HostTests` preset returns early and never builds the firmware target.

## Cross-component protocol

The SPI frame format is implemented twice and must stay in lockstep:

- C: `Arm_Sensor_Hub/App/Src/spi_protocol.c` and `spi_payload_layout.h`
- Python: `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py`

Clock sync is being redesigned under `Documentation/07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md` (2026-09-24). The system docs describe that target design, where the STM32 does no clock math and the Pi-side ClockSync model does the conversion. The current code still implements the older one-way TIME_SYNC with an STM32-held offset. Documents marked "As-built" describe that current code.

The format uses magic `0xA55A`, an 18-byte little-endian header, a CRC32 trailer, a maximum frame of 512 bytes, and shared message-type IDs. The system-level contract is in `Documentation/02_INTERFACES/SPI/`. When you change one side, change the other side and its tests too.

## Documentation authority rules

These rules are mandatory and come from the README and `Documentation/00_INDEX.md`:

- `Documentation/**` is the only project documentation authority framework. It owns system requirements, architecture, interfaces (CAN/SPI/HOST/TIME), timing and synchronization, safety, configuration, verification status, and decisions.
- `Arm_Sensor_Hub/Documentation/` and `RaspberryPi_Sensor_Hub/Documentation/` own component implementation details only. They may explain how a system requirement is implemented, but they must never redefine it or create competing copies.
- Authority depends on who owns the subject, not on where a file sits. Resolve conflicts against the owning authority and never by guessing. Reference vendor specs as external authority and don't rewrite them.
- Only the Karetao process and `Documentation/05_VERIFICATION/SYSTEM_VERIFICATION_MATRIX.md` can establish `SYSTEM_VERIFIED`. Component test evidence doesn't count.
- Items marked "proposed" or "open" (for example `SYS-MOTION-*` and motion permission) are not normative. Don't treat them as decided. Open decisions are tracked in `Documentation/07_DECISIONS/` and in `For_Lenton`, which is a working review list and not an authority.
- Don't delete docs just because they look old. First check git history, unique content, and inbound links (`Documentation/05_REFACTORING_RULES.md`). No archive is kept in the working tree. Git history is the archive, and the former `Documentation/99_ARCHIVE/` was last present at commit `9c637ba`. References to `99_ARCHIVE/` or `docs/project/**` in the refactoring ledger and plan are historical provenance and don't point to live files.
- Requirement identifiers follow the patterns `SYS-*`, `SD-xx`, and `LIVE-xx`. Keep traceability from the system requirement to the component implementation, then to verification evidence, then to system verification.

## GitHub issues

Follow `.github/ISSUE_CONTRACT.md` and `ISSUE_FRAMEWORK.md`. Issue titles are action-oriented and look like `[SD-xx] Resolve ...` or `[LIVE-xx] Verify ...`. Use only the approved labels and never invent new ones. Issues track work, and technical decisions belong in `Documentation/`.
