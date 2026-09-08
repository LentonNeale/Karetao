# Development Setup and Workflow

## Main Tooling

The repository uses:

- CMake with Ninja presets,
- `arm-none-eabi-gcc/g++` for STM32 firmware builds,
- a separate `HostTests` preset for native validation,
- optional VS Code launch/task files for debug workflow.

See [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/CMakePresets.json`](../../CMakePresets.json), [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/CMakeLists.txt`](../../CMakeLists.txt), and [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/cmake/gcc-arm-none-eabi.cmake`](../../cmake/gcc-arm-none-eabi.cmake).

## Recommended Local Prerequisites

- CMake 3.22 or newer
- Ninja
- ARM GNU Embedded toolchain with `arm-none-eabi-gcc` and `arm-none-eabi-g++`
- `gdb-multiarch` or equivalent debugger
- ST-Link tools if you will flash or debug hardware

## Standard Build Commands

From the repository root:

```bash
cmake --preset Debug
cmake --build --preset Debug
```

Other supported flows:

```bash
cmake --preset Release
cmake --build --preset Release

cmake --preset HostTests
cmake --build --preset HostTests
ctest --preset HostTests
```

Focused Sprint 1 protocol validation:

```bash
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
```

## When To Use Each Build Path

### Use `HostTests` when:

- changing timestamp logic,
- changing CRC or framing,
- changing snapshot or payload layout code,
- changing other logic that is already covered by native tests.

### Use `Debug` firmware build when:

- changing STM32 runtime code,
- changing HAL-facing integration,
- changing service wiring in `App_Init`, `main.c`, or hardware callbacks.

### Use `Release` when:

- preparing a more complete validation pass,
- confirming no configuration drift between debug and optimized builds.

## Debug Workflow

The repository includes VS Code configuration for Cortex-Debug with ST-Link and a build task named `CMake: Build Debug`. If you are using VS Code, inspect:

- [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/.vscode/tasks.json`](../../.vscode/tasks.json)
- [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/.vscode/launch.json`](../../.vscode/launch.json)

If you are not using VS Code, the preset-based CLI flow is still the source of truth.

## Safe Development Habits For Interns

- Start by reading the relevant contract before editing an implementation file.
- Make small changes and run the smallest existing validation that covers them.
- Prefer host tests first if your change does not require STM32 hardware.
- Do not move application logic into CubeMX-generated files unless there is a protected user section intended for it.
- Keep C application code on the C side of the `mks_api.h` boundary; do not leak C++ interfaces into `App/`.

## Common Mistakes To Avoid

- treating a scaffold as production-complete,
- changing payload layout constants without checking protocol tests and contracts,
- editing generated platform code when the change belongs in `App/`,
- assuming missing hardware validation means the logic is incorrect; sometimes it simply is not yet proven on target.

