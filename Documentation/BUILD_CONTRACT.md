# Build and Configuration Contract

**Status:** Project policy draft  
**Owner:** Firmware build system  
**Boundary:** Source/configuration/toolchain -> firmware artifacts

## Current Baseline

- C application layer: C11.
- MksServo protocol library: C++17 through `mks_api.h`.
- Target: STM32F405RGT6, Cortex-M4F, hard-float.
- Build system: CMake with Ninja presets.
- Firmware presets: `Debug` and `Release`.
- Native protocol-test preset: `HostTests`; it builds only host-test code and does not compile or link the STM32 firmware target.
- Toolchain: `cmake/gcc-arm-none-eabi.cmake`.
- Outputs: `build/<preset>/Arm_Sensor_Hub.elf` and map/size data.
- Runtime: FreeRTOS with CMSIS-RTOS2.

## Required Build Rules

- Debug and Release must both configure and link.
- C sources must compile as C11; MksServo sources must compile as C++17.
- C++ must not cross into App except through C-compatible headers.
- Embedded C/C++ code uses no exceptions or RTTI.
- Generated CubeMX files remain regenerable; application code belongs in `App/` or protected user sections.
- Build configuration must be reproducible from a clean build directory.

## Quality and Artifacts

The project should enforce baseline warnings, produce compile commands, report Flash/RAM usage, and retain the ELF/map files needed for debug. CI should eventually build Debug and Release, run host protocol tests, validate documentation links, and run static analysis.

Memory budgets, stack budgets, compiler version range, HAL/FreeRTOS version pins, artifact version metadata, and release signing are open decisions and must be approved before being enforced.

## Configuration Ownership

- `CMakeLists.txt`: project targets and source ownership.
- `CMakePresets.json`: supported developer workflows.
- `cmake/gcc-arm-none-eabi.cmake`: target/toolchain flags.
- CubeMX `.ioc` and generated CMake: peripheral generation inputs.
- `Documentation/`: policy and contract documents, not build-generated configuration.

## Verification

A source change is complete when the relevant Debug build passes. Release builds and host tests are required before release approval. Build failures must not be hidden by stale build artifacts.

From the repository root, use these reproducible commands:

```bash
cmake --preset Debug && cmake --build --preset Debug
cmake --preset Release && cmake --build --preset Release
cmake --preset HostTests && cmake --build --preset HostTests
ctest --preset HostTests
```

The `sprint1_protocol_tests` executable is the native test location for CRC framing, explicit serialization/size checks, and monotonic-time helpers. Later tasks should add a focused test there and run it with:

```bash
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
```

## Open Decisions

- supported toolchain/CMake version range;
- warning flags and static-analysis tools;
- CI runner and artifact retention;
- Flash/RAM/stack limits;
- dependency version pinning;
- CubeMX regeneration review process;
- firmware version and reproducibility metadata.
