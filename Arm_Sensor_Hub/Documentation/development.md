# Development Setup and Workflow

This repository contains two active subtrees:

- `Arm_Sensor_Hub/` for STM32 firmware and host-side native tests.
- `RaspberryPi_Sensor_Hub/` for Raspberry Pi host-side code and SPI integration scaffolding.

## Canonical References

- System architecture: [SYSTEM_ARCHITECTURE.md](../../Documentation/01_SYSTEM/SYSTEM_ARCHITECTURE.md)
- Arm Sensor Hub component definition and hardware baseline: [ARM_SENSOR_HUB.md](../../Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md)
- SPI system interface (transport, DATA_READY, service behaviour): [SPI_SYSTEM_INTERFACE.md](../../Documentation/02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md)
- SPI payload schema: [SPI_PAYLOAD_SCHEMA.md](../../Documentation/02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md)
- Raspberry Pi bring-up and SPI host notes: [RASPBERRY_PI_BRINGUP_V1.md](../../RaspberryPi_Sensor_Hub/Documentation/RASPBERRY_PI_BRINGUP_V1.md)

## Main Tooling

The repository currently uses:

- CMake with Ninja presets for `Arm_Sensor_Hub/`,
- `arm-none-eabi-gcc/g++` for STM32 firmware builds,
- a separate `HostTests` preset for native ARM-side validation,
- Python standard-library modules for the Raspberry Pi SPI scaffold,
- optional VS Code launch/task files for ARM debug workflow.

See [`Arm_Sensor_Hub/CMakePresets.json`](../CMakePresets.json),
[`Arm_Sensor_Hub/CMakeLists.txt`](../CMakeLists.txt), and
[`Arm_Sensor_Hub/cmake/gcc-arm-none-eabi.cmake`](../cmake/gcc-arm-none-eabi.cmake).

## Recommended Local Prerequisites

- CMake 3.22 or newer
- Ninja
- ARM GNU Embedded toolchain with `arm-none-eabi-gcc` and `arm-none-eabi-g++`
- Python 3.12+ for Raspberry Pi-side scaffold tests
- `gdb-multiarch` or equivalent debugger
- ST-Link tools if you will flash or debug hardware

## Standard Build and Test Commands

### ARM firmware and host tests

From the monorepo root:

```bash
cd Arm_Sensor_Hub
cmake --preset Debug
cmake --build --preset Debug
```

Other supported ARM flows:

```bash
cd Arm_Sensor_Hub
cmake --preset Release
cmake --build --preset Release

cmake --preset HostTests
cmake --build --preset HostTests
ctest --preset HostTests
```

Focused ARM protocol validation:

```bash
cd Arm_Sensor_Hub
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
```

### Raspberry Pi SPI scaffold tests

From the monorepo root:

```bash
python -m unittest discover -s RaspberryPi_Sensor_Hub/tests/spi -p 'test_*.py' -v
```

## When To Use Each Validation Path

### Use `HostTests` when:

- changing timestamp logic,
- changing CRC or framing,
- changing snapshot or payload layout code,
- changing other ARM-side logic that is already covered by native tests.

### Use the Raspberry Pi tests when:

- changing packet encode/decode behavior in `RaspberryPi_Sensor_Hub/src/spi/`,
- changing host-side interface contracts or fake backends,
- refining TODO assumptions before hardware-specific SPI backends are introduced.

### Use `Debug` firmware build when:

- changing STM32 runtime code,
- changing HAL-facing integration,
- changing service wiring in `App_Init`, `main.c`, or hardware callbacks.

## Safe Development Habits

- Start by reading the relevant contract before editing an implementation file.
- Make small changes and run the smallest existing validation that covers them.
- Prefer ARM host tests first if your change does not require STM32 hardware.
- Keep Raspberry Pi hardware bindings behind injectable interfaces until the final SPI backend is chosen.
- Do not move ARM application logic into CubeMX-generated files unless there is a protected user section intended for it.
- Keep C application code on the C side of the `mks_api.h` boundary; do not leak C++ interfaces into `App/`.

## Common Mistakes To Avoid

- treating a scaffold as production-complete,
- changing payload layout constants without checking protocol tests and contracts,
- editing generated platform code when the change belongs in `App/`,
- assuming missing hardware validation means the logic is incorrect; sometimes it simply is not yet proven on target,
- hard-coding Raspberry Pi SPI device paths, GPIO numbers, or clock rates before the ARM-side contract gates are closed.
