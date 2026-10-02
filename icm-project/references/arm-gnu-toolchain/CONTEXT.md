# Arm GNU toolchain reference

The Arm GNU Toolchain (arm-none-eabi GCC) install guide and the GCC ARM options the Cortex-M4F firmware build uses.

## Source

| Field | Value |
|---|---|
| Publisher | Arm (install guide, learn.arm.com); GNU Project (GCC manual) |
| Title | "Arm GNU Toolchain" install guide; "3.20.5 ARM Options" in Using the GNU Compiler Collection (GCC) |
| Version / revision | Install guide: last updated 11 Jun 2026, example toolchain 15.2.Rel1. GCC manual: online "current" page, GCC version unknown (not printed on source) |
| Date | install guide Last-Modified 2026-09-28; GCC page Last-Modified 2026-09-15 |
| Obtained from | https://learn.arm.com/install-guides/gcc/arm-gnu/ ; https://gcc.gnu.org/onlinedocs/gcc/ARM-Options.html |
| Retrieved | 2026-10-01 |
| Licence note | Not stored here; local copies below |
| Local copy | `~/.icm/sources/arm-gnu-install/source.html`, 29,589 bytes, sha256 `a9ca7637f691ec1aee4d69c2dc13b159bee54c2720650edfd75a1dd91944a009` |
| Local copy | `~/.icm/sources/gcc-arm-options/ARM-Options.html`, 76,042 bytes, sha256 `9b3e322acf52db33766da260252e2fece24bea38803115d2ff58deb14ec7d576` |
| Downloads page | https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads fetched (`~/.icm/sources/arm-gnu-downloads/source.html`, 45,370 bytes, sha256 `50f0f99d6198419ce0c5a756cd2c24857954bc63505e6189e66498908bae2a26`) but its HTML holds no release list (script-rendered), so nothing is extracted from it |

## What the project uses

| Item | Project value | Where |
|---|---|---|
| Compiler | `arm-none-eabi-gcc`, `g++`, `objcopy`, `size` from PATH | `Arm_Sensor_Hub/cmake/gcc-arm-none-eabi.cmake` |
| Target flags | `-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard` for compile and link | same |
| Other flags | `-Wall -fdata-sections -ffunction-sections -fstack-usage`; Debug `-O0 -g3`, Release `-Os -g0`; C++ adds `-fno-rtti -fno-exceptions -fno-threadsafe-statics`; link `--specs=nano.specs -Wl,--gc-sections -Wl,--print-memory-usage`, script `STM32F405xx_FLASH.ld` | same |
| Version pinned by CI | None: `arm-ci.yml` runs `apt-get install gcc-arm-none-eabi binutils-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib` on ubuntu-latest, so the version is whatever the image's apt provides (unknown) | `.github/workflows/arm-ci.yml` |
| Version used locally | VS Code query-driver paths name `gnu-tools-for-stm32/14.3.1+st.2` (ST's bundle, not an Arm release) | `Arm_Sensor_Hub/.vscode/settings.json` |
| Documented requirement | "ARM GNU Embedded toolchain" with no version | `Arm_Sensor_Hub/Documentation/development.md` |

Mismatch to note: the project pins no toolchain version; CI (apt) and local (ST bundle 14.3.1) can differ, and the install guide's example is 15.2.Rel1.

## Files

| File | Contains | Read when |
|---|---|---|
| `gcc-arm-flags.md` | `-mcpu`, `-mfpu`, `-mfloat-abi` rules from the GCC manual's ARM Options | Reviewing the toolchain file's target flags |
| `install-guide.md` | Arm's install steps, PATH, verify command, versions named, licence | Setting up or checking a toolchain install |

## Authority

The sources are authoritative; when a note disagrees, the source wins. Every value cites a section heading.
**Status:** verified on 2026-10-02 with `verify_citations` and `check_reference` (both empty).

## Not covered

`--specs=nano.specs`, `-ffunction-sections`, `-Wl,--gc-sections`, `-O` levels and `-fstack-usage` (other GCC and newlib documents, not fetched), the downloads page, the other host and target install steps, and other `-mcpu` extensions.

## Secrets

None.
