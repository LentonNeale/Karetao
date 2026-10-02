# CMake presets reference

The CMake presets manual (cmake-presets(7)), only the fields the firmware project's `CMakePresets.json` uses.

## Source

| Field | Value |
|---|---|
| Publisher | Kitware, Inc. (CMake) |
| Title | cmake-presets(7) |
| Version / revision | "latest" documentation page; CMake version unknown (not printed on source). It documents presets schema versions up to 12 |
| Date | page last modified 2026-08-25 (HTTP Last-Modified) |
| Obtained from | https://cmake.org/cmake/help/latest/manual/cmake-presets.7.html |
| Retrieved | 2026-10-01 |
| Licence note | Not stored here; local copy below |
| Local copy | `~/.icm/sources/cmake-presets/cmake-presets.7.html`, 181575 bytes, sha256 `14b5bd46d62d8d29b3d118fada1876ffe7c4d602d6773d2ce43aa98e23d04ba9` (fetched with `fetch_source`; `source.json` beside it) |

## What the project uses

| Item | Project value | Where |
|---|---|---|
| Presets schema `version` | 3 (needs CMake 3.21 per the Versions table) | `Arm_Sensor_Hub/CMakePresets.json` |
| Minimum CMake | `cmake_minimum_required(VERSION 3.22)`; docs say "CMake 3.22 or newer". No `cmakeMinimumRequired` object in the presets file | `Arm_Sensor_Hub/CMakeLists.txt`, `Documentation/development.md` |
| Configure presets | hidden `default` (Ninja, `binaryDir` `${sourceDir}/build/${presetName}`, `toolchainFile` `${sourceDir}/cmake/gcc-arm-none-eabi.cmake`); `Debug` and `Release` inherit it and set `CMAKE_BUILD_TYPE`; `HostTests` does not inherit, sets Ninja and `ARM_SENSOR_HUB_BUILD_HOST_TESTS=ON`, and has no toolchain file | same |
| Build and test presets | `Debug`, `Release`, `HostTests` build presets; `HostTests` test preset; each only sets `configurePreset` | same |
| CI commands | `cmake --preset <name>`, `cmake --build --preset <name>`, `ctest --preset HostTests --output-on-failure` | `.github/workflows/arm-ci.yml` |

The CI runner's CMake version is not pinned (ubuntu-latest image); the version in use is unknown.

## Files

| File | Contains | Read when |
|---|---|---|
| `presets-fields-used.md` | Schema version history for 1-3, and the configure, build and test preset fields and macros the project file uses; from the manual's headings | Editing or reviewing `CMakePresets.json`, or checking the CMake version needed |

## Authority

The manual is authoritative. When a note and the manual disagree, the manual wins; fix the note. Every
value in the note cites a heading of the manual. **Status:** verified on 2026-10-02 with `verify_citations` and `check_reference` (both empty).

## Not covered

Includes, package and workflow presets, conditions, presets versions 4 and later, and the JSON schema.

## Secrets

None.
