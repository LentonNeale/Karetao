# Reference routing

Which reference note to read for a code area. Paths are from the project root; every note is
under `icm-project/references/` and is one `Rule | Value | Citation` table. Read only the rows
for the part, command, register or call the diff touches, never the whole folder. Each folder's
`CONTEXT.md` gives the source's version and what the notes do not cover. A value not in a note
comes from the source, not from memory; if the note lacks it, say so.

| Code area | Note | Rows to read |
|---|---|---|
| `Arm_Sensor_Hub/App/Src/as5600.c`, `sensor_task.c` | `as5600/register-map.md`, `as5600/i2c-interface.md` | The registers and status bits read; the address and read sequence |
| same, timing or limits | `as5600/electrical-and-timing.md` | Power-up, settling and I2C timing rows |
| `Arm_Sensor_Hub/App/Src/tca9548a_mux.c` | `tca9548a/addressing-and-control.md` | Address, control register, channel select, reset |
| same, timing | `tca9548a/timing-and-electrical.md` | Fast-mode and reset timing rows |
| `Arm_Sensor_Hub/App/Src/i2c_manager.c` | `stm32f4-hal-cmsis/i2c.md`; `freertos-kernel/kernel-source-semantics.md` | The HAL calls used; the mutex and FromISR rows |
| `Arm_Sensor_Hub/App/Src/can_service.c`, `can_tx_policy.c` | `stm32f4-hal-cmsis/can.md`; `can-2-0/error-handling.md` | The HAL calls and error flags used; error counters and bus-off |
| CAN bit rate or timing (`Core/Src/main.c` CAN init, `Arm_Sensor_Hub.ioc`) | `can-2-0/bit-timing.md`; `mks-servo42d-57d-can/frame-and-checksum.md` | Segments and sample point; the bit rates the motors accept |
| `Arm_Sensor_Hub/Middlewares/Third_Party/MksServo/` | `mks-servo42d-57d-can/` the note for the command group: `frame-and-checksum.md`, `read-commands.md`, `config-commands.md`, `motion-commands.md` | Only the command codes the change sends or decodes |
| CAN frame layout or arbitration | `can-2-0/frame-formats.md` | Standard or extended frame rows used |
| `crc32_iso_hdlc.c`, `spi_protocol.c`, `RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py` | `crc32-iso-hdlc/parameters.md`, `crc32-iso-hdlc/project-use.md` | The CRC parameters and check value; the call sites |
| `spi_slave_service.c`, `spi_data_ready.c`, `Core/Src/stm32f4xx_it.c`, DMA or GPIO | `stm32f4-hal-cmsis/spi-dma-gpio-tick.md` | The SPI slave DMA, DMA, GPIO or tick rows used |
| `Core/Src/freertos.c`, `app_init.c`, tasks and delays | `cmsis-rtos2/kernel-thread-delay.md`, `cmsis-rtos2/freertos-wrapper-and-usage.md` | The calls used |
| `FreeRTOSConfig.h`, queues, semaphores, notifications, interrupt priorities | `freertos-kernel/config-in-use.md`, `freertos-kernel/kernel-source-semantics.md`, `freertos-kernel/manual-api.md` | The setting or call the diff touches |
| HAL module enable or version | `stm32f4-hal-cmsis/version-and-usage.md` | Version and module rows |
| `RaspberryPi_Sensor_Hub/src/spi/spi_bus.py`, `spi_device.py` | `linux-spidev/py-spidev-api.md`, `linux-spidev/py-spidev-source.md`, `linux-spidev/spidev-kernel-api.md` | The attributes and methods used; transfer size limits |
| Pi SPI pins, overlays, clock | `raspberry-pi-5-spi/pi-spi-docs.md`, `raspberry-pi-5-spi/rp1-spi-gpio.md` | SPI0 pins, chip selects, clock rows |
| `RaspberryPi_Sensor_Hub/src/spi/data_ready.py` | `libgpiod-v1/gpiod-v1-python-api.md`, `libgpiod-v1/gpiod-v1-vs-v2.md` | The v1 calls used; never use a v2 name |
| `CMakeLists.txt`, `CMakePresets.json`, `cmake/` | `cmake-presets/presets-fields-used.md`; `arm-gnu-toolchain/gcc-arm-flags.md` | The preset fields changed; the `-mcpu`, `-mfpu`, `-mfloat-abi` rows |

Not yet filed (the source could not be fetched): the STM32F405 datasheet, the RM0090 reference
manual, STM32CubeMX UM1718 and the Ninja manual. For those, say the reference is missing.
