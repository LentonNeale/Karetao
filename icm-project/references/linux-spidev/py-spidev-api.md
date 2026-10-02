# py-spidev: attributes and methods (README)

Project use (`spi_bus.py`): `spidev.SpiDev()`, `open(bus, cs)`, set `mode`, `bits_per_word`, `max_speed_hz`, `xfer2(list)` of 512 bytes, `close()`. Not used: `xfer`, `xfer3`, `readbytes`, `writebytes`.

| Rule | Value | Citation |
|---|---|---|
| Purpose | a python module for interfacing with SPI devices from user space via the spidev linux kernel driver | "Python Spidev" |
| Licence | All code is MIT licensed unless explicitly stated otherwise | "Python Spidev" |
| Kernel needed | The module uses the SPI_IOC_RD_MODE32 and SPI_IOC_WR_MODE32 ioctls that are available since Linux kernel version 3.15. Older kernels are not supported | "Kernel" |
| Optional features | Some features (e.g. mosi_idle_low) depend on the support being available in the Linux kernel | "Kernel" |
| Settings | spi.max_speed_hz = 5000 and spi.mode = 0b01 (README example values) | "Settings" |
| bits_per_word | * `bits_per_word` | "Settings" |
| mode | SPI mode as two bit pattern of clock polarity and phase [CPOL\|CPHA], min: 0b00 = 0, max: 0b11 = 3 | "Settings" |
| max_speed_hz | * `max_speed_hz` | "Settings" |
| Unsupported setting error | In case of a setting not being supported the error [Errno 22] Invalid argument is thrown | "Settings" |
| Controller support | Not all drivers support all settings | "Settings" |
| cshigh | * `cshigh` | "Settings" |
| no_cs | Set the "SPI_NO_CS" flag to disable use of the chip select (although the driver may still own the CS pin) | "Settings" |
| open(bus, device) | Equivalent to calling open_path("/dev/spidev<bus>.<device>") | "Methods" |
| open vs open_path | Either open_path or open should be used | "Methods" |
| open_path | Connects to the specified SPI device special file, following symbolic links if appropriate | "Methods" |
| readbytes(n) | Read n bytes from SPI device | "Methods" |
| writebytes(list) | Writes a list of values to SPI device | "Methods" |
| writebytes2 | Similar to writebytes but accepts arbitrary large lists. If list size exceeds buffer size (which is read from /sys/module/spidev/parameters/bufsiz), data will be split into smaller chunks and sent in multiple operations | "Methods" |
| xfer | xfer(list of values[, speed_hz, delay_usec, bits_per_word]): Chip-select should be released and reactivated between blocks. Delay specifies the delay in usec between blocks | "Methods" |
| xfer2 | xfer2(list of values[, speed_hz, delay_usec, bits_per_word]): Chip-select should be held active between blocks | "Methods" |
| xfer3 | Similar to xfer2 but accepts arbitrary large lists. If list size exceeds buffer size (which is read from /sys/module/spidev/parameters/bufsiz), data will be split into smaller chunks and sent in multiple operations | "Methods" |
| close | Disconnects from the SPI device | "Methods" |
| Bus numbering | The Linux kernel may assign SPI bus numbers to a system's SPI controllers in a non-deterministic way | "Detailed Information" |
| Bus number stability | Not guaranteed to remain constant between different Linux kernel versions | "Detailed Information" |
| Stable path advice | consider using one or more udev rules to create symlinks to the SPI controller spidev, and then use open_path | "Summary" |
