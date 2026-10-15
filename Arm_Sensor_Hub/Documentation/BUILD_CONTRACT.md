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

The repository now has CI coverage for `HostTests`, Debug firmware, and Release firmware. The ARM CI workflow installs the ARM GNU toolchain on the runner, builds both firmware presets, records ELF size and SHA-256 checksum information, and uploads the Debug/Release ELF files plus the size/checksum report as artifacts. The first successful run on the current baseline is run `35180226459` on commit `1cf0bc7f4d2785f746ca8facac557c776651a2f8`.

## Required Build Rules

- Debug and Release must both configure and link.
- C sources must compile as C11; MksServo sources must compile as C++17.
- C++ must not cross into App except through C-compatible headers.
- Embedded C/C++ code uses no exceptions or RTTI.
- Generated CubeMX files remain regenerable; application code belongs in `App/` or protected user sections.
- Build configuration must be reproducible from a clean build directory.

## Quality and Artifacts

The project should enforce baseline warnings, produce compile commands, report Flash/RAM usage, and retain the ELF/map files needed for debug. CI now builds Debug and Release, runs host protocol and service smoke tests, records firmware size/checksum information, and uploads the firmware artifacts. Documentation-link validation and static analysis remain future CI improvements.

Memory budgets, compiler version range, HAL/FreeRTOS version pins, artifact version metadata, and release signing are open decisions and must be approved before being enforced.

### App source list check

The firmware and the host tests list their `App/Src` sources by hand. At configure time, `cmake/app_source_check.cmake` compares every `App/Src/*.c` file with the sources of the targets each preset builds: the firmware target, or the host-test executables (story B54, finding FW-4). Configure fails when:

- a module is in neither its build nor `cmake/app_source_exemptions.cmake`;
- an exempted module is built anyway;
- an exemption names a module that no longer exists.

Each exemption carries its reason; today the only one is `motion_permission.c`, until WP14. CI configures both presets, so both lists are checked.

### Task stack check

Task stack budgets are enforced (story B53, review findings FW-2 and PRM-9; approved by Lenton Neale, 2026-10-15):

- **Where the sizes live.** The application tasks' stack sizes are set in the CubeMX `.ioc` (`FREERTOS.TasksNN`). The kernel's idle and timer task sizes are set in `FreeRTOSConfig.h` (`configMINIMAL_STACK_SIZE`, `configTIMER_TASK_STACK_DEPTH`), which CubeMX generates from the `.ioc`.
- **How the check works.** Every C and C++ firmware object is compiled with `-fcallgraph-info=su`. After the link, `tools/stack_depth.py` reads the call graphs of the objects actually linked; CMake lists them in `build/<preset>/stack_objects.txt`. For each task it adds the frames along the deepest call path, plus the allowance derived in the tool for an exception and a context switch. The build fails if the total exceeds the stack.
- **Weak functions.** When a weak function and its strong override both exist (HAL callbacks), the deeper of the two is counted.
- **When the depth can't be known, the build fails too:** recursion, an unbounded dynamic frame, an unaccounted function-pointer call or a library function without a size.
  - `tools/stack_depth.cfg` lists the function-pointer calls and the library sizes, each with its source.
  - Each function-pointer entry states the exact number of call sites it covers. A new callback, or a call moved by inlining, changes that number, and the build fails until someone reviews the entry.
- **Turning it off.** The check needs GCC and python3. If either is missing, configure fails, unless the build is configured with `-DARM_SENSOR_HUB_STACK_CHECK=OFF`, which prints a warning.
- **Output.** A passing build writes its report to `build/<preset>/stack_depth.txt`.
- **At run time,** `configCHECK_FOR_STACK_OVERFLOW 2` is on. An overflow masks every interrupt, stops the SPI3 DMA and pending CAN transmissions, and halts in `StackMonitor_OnOverflow`. The least free stack since reset of the default, idle and timer tasks is in `g_stack_monitor_dbg` ([SWD procedure 6](SWD_READOUT_PROCEDURES.md#procedure-6-read-task-stack-headroom)).

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

The `sprint1_protocol_tests` executable is the native test location for CRC framing, explicit serialization/size checks, and monotonic-time helpers. The `service_smoke_tests` executable provides minimal core-functionality and negative-path coverage for the service-layer modules under host stubs. Focused protocol regressions should continue to run with:

```bash
ctest --test-dir build/HostTests --output-on-failure -R sprint1_protocol_tests
```

The current CI evidence establishes that the runner can install the ARM GNU toolchain and successfully build both target presets. It does not by itself provide target-hardware behavior validation or interface acceptance.

## Open Decisions

- supported toolchain/CMake version range;
- warning flags and static-analysis tools;
- CI runner and artifact retention;
- Flash/RAM limits (task stacks are checked, see "Task stack check");
- dependency version pinning;
- CubeMX regeneration review process;
- firmware version and reproducibility metadata.
