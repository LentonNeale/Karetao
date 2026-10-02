# STM32F4 HAL and CMSIS device reference

STM32CubeF4 V1.28.3 (HAL driver V1.8.5, CMSIS device V2.6.11), the versions vendored under `Arm_Sensor_Hub/Drivers/`; notes cover only the CAN, I2C, SPI, DMA, GPIO and tick APIs the firmware calls.

## Source

| Field | Value |
|---|---|
| Publisher | STMicroelectronics |
| Title | STM32F4xx HAL driver (source, headers, Release_Notes.html), STM32F4xx CMSIS device Release_Notes.html, STM32CubeF4 Release_Notes.html |
| Version / revision | HAL driver V1.8.5 (23-July-2025), CMSIS device V2.6.11 (25-April-2025), STM32CubeF4 package V1.28.3 (23-July-2025). Matches the project: `ProjectManager.FirmwarePackage=STM32Cube FW_F4 V1.28.3` at `Arm_Sensor_Hub/Arm_Sensor_Hub.ioc:150`, HAL macros 0x01/0x08/0x05 at `stm32f4xx_hal.c:55-58`, CMSIS macros 0x02/0x06/0x0B at `stm32f4xx.h:110-113` |
| Date | 23-July-2025 (HAL driver release) |
| Obtained from | https://github.com/STMicroelectronics/stm32f4xx-hal-driver (tag v1.8.5), https://github.com/STMicroelectronics/cmsis-device-f4 (tag v2.6.11), https://github.com/STMicroelectronics/STM32CubeF4 (tag v1.28.3) |
| Retrieved | 2026-10-01 (each file's `source.json`) |
| Licence note | Not stored here: files are cached outside the repo. The vendored copies are BSD-3-Clause per the files' own LICENSE.txt |
| Local copy | `~/.icm/sources/stm32f4-hal-cmsis/`: `files/<name>/` per downloaded file with its `source.json` (sha256, bytes); the six vendored .c files (hal, can, i2c, spi, gpio, dma) are identical to tag v1.8.5 (the I2C file differs only in line endings). Notes were verified against concatenations in `combined/` (can.txt 132,384 bytes sha256 `321ee50941e0c0e843e00b8c45b5717f6840bbb0c92364e959abedee363cb244`; i2c.txt 283,881 bytes sha256 `3134c07e77f36d4ef08e787803f88003becdb16e480cd70756adf31d4ff63a95`; spi-dma-gpio-tick.txt 280,148 bytes sha256 `2eb1c779b704354b4f694e39b387950c420ac6d6fd821fd02e98c8e543ca66e9`; version.txt 438,436 bytes sha256 `2f00e514b7f9f2117218a168d1ba7e25e78984b03358502b9347b99033b9c3ce`) |

## Files

| File | Contains | Read when |
|---|---|---|
| `can.md` | HAL_CAN Init/Start/Stop/ConfigFilter/AddTxMessage/GetRxMessage/GetError behaviour, return codes, error codes, where bus-off is set | Reviewing CAN service, bus-off recovery |
| `i2c.md` | Blocking and interrupt master transfers, timeouts, error handler, error codes | Reviewing the I2C manager |
| `spi-dma-gpio-tick.md` | SPI slave DMA transfer, abort, callbacks, error codes; DMA abort; GPIO write; tick | Reviewing the SPI slave service, data-ready pin |
| `version-and-usage.md` | Project config lines and call sites with project citations | Checking how the firmware configures and calls the HAL |

## Authority

The vendor source at the tagged release is authoritative; citations are function or macro names in quotes. When a note and the source disagree, the source wins. **Status:** verified on 2026-10-02 with `verify_citations` and `check_reference`; three `unchecked` rows in `version-and-usage.md` (module-enabled defines, read by hand against `stm32f4xx_hal_conf.h` lines 42, 65, 86). The tool cannot match three-part version numbers, so those are only in this file.

## Not covered

TIM, RCC, PWR, NVIC, UART and all other HAL modules; CAN interrupt and Tx abort APIs the firmware does not call; reference-manual register detail.

## Secrets

None.
