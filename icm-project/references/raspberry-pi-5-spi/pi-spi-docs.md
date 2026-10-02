# Raspberry Pi SPI (Pi 5 and header), from the Raspberry Pi documentation

Project use: Pi 5, SPI0 CE0 as `/dev/spidev0.0`, header pins 19/21/23/24, mode 0, 8 bits per word, 5000000 Hz. Citations are headings of the source `.adoc`.

| Rule | Value | Citation |
|---|---|---|
| Pi 5 SPI provider | On the Raspberry Pi 5, SPI functionality is provided by the RP1 I/O controller rather than the main application processor | "Raspberry Pi 5, 500, 500+ and Compute Module 5" |
| RP1 SPI count | RP1 includes nine Synchronous Serial Interface (SSI) controllers. Six of these are routed to GPIO bank 0 | "Raspberry Pi 5, 500, 500+ and Compute Module 5" |
| Not on header | The remaining three - SPI6, SPI7, and SPI8 - are internal to RP1 and are not routed to the standard 40-pin GPIO header | "Raspberry Pi 5, 500, 500+ and Compute Module 5" |
| SPI0 chip selects | SPI0, with four hardware chip selects | "Raspberry Pi 5, 500, 500+ and Compute Module 5" |
| SPI1 chip selects | SPI1, with three hardware chip selects | "Raspberry Pi 5, 500, 500+ and Compute Module 5" |
| DDR | DDR (Double Data Rate) operation is not supported on RP1 SPI controllers | "Raspberry Pi 5, 500, 500+ and Compute Module 5" |
| Device-mode buses | SPI4 and SPI7 buses are device-mode only | "Raspberry Pi 5, 500, 500+ and Compute Module 5" |
| SPI0 MOSI | header pin 19, GPIO10, SPI0_MOSI | "SPI0" |
| SPI0 MISO | header pin 21, GPIO09, SPI0_MISO | "SPI0" |
| SPI0 SCLK | header pin 23, GPIO11, SPI0_SCLK | "SPI0" |
| SPI0 CE0 | header pin 24, GPIO08, SPI0_CE0_N | "SPI0" |
| SPI0 CE1 | header pin 26, GPIO07, SPI0_CE1_N | "SPI0" |
| Header pin 22 / GPIO25 | CE1, header pin 22, GPIO25, SPI4_CE1_N (table titled BCM2711 only) | "SPI4 (BCM2711 only)" |
| Pi 5 Linux driver | On Raspberry Pi 5, the RP1 SPI controllers use the Designware SPI/SSI Linux kernel driver spi_dw | "Linux driver" |
| SPI0 default state | SPI0 is disabled by default | "Linux driver" |
| Enable SPI0 | ensure the line dtparam=spi=on is not commented out in /boot/firmware/config.txt | "Linux driver" |
| SPI0 chip selects via overlay | By default it uses two chip select lines, but this can be reduced to one using dtoverlay=spi0-1cs. There is also dtoverlay=spi0-2cs; without any parameters it is equivalent to dtparam=spi=on | "Linux driver" |
| SPI1 overlays | dtoverlay=spi1-1cs, dtoverlay=spi1-2cs, dtoverlay=spi1-3cs | "Linux driver" |
| Chip selects are GPIOs | The driver does not make use of the hardware chip select lines because of some limitations. Instead, it can use an arbitrary number of GPIOs as software/GPIO chip selects | "Linux driver" |
| Overlay help | run (for example) dtoverlay -h spi0-2cs | "Linux driver" |
| Clock rule | The driver supports all speeds which are even integer divisors of the core clock, although not all of these speeds support data transfer because of limits in the GPIOs and in the devices attached | "Speed" |
| Practical ceiling | As a rule of thumb, anything over 50 MHz is unlikely to work | "Speed" |
| Mode bits | SPI_CPOL: clock polarity; SPI_CPHA: clock phase; SPI_CS_HIGH: chip select active high; SPI_NO_CS: 1 device per bus, no Chip select; SPI_3WIRE: bidirectional mode, data in and out pin shared | "Supported mode bits" |
| Bits per word | 8 - normal; 9 - supported using LoSSI mode | "Supported bits per word" |
| Transfer modes | Interrupt mode is supported on all SPI buses. SPI0, and SPI3-6 also support DMA transfers | "Transfer modes" |
| spidev interface | spidev presents an ioctl-based userspace interface to individual SPI CS lines | "spidev" |
| CS ownership | Device Tree is used to indicate whether a CS line is going to be driven by a kernel driver module or managed by spidev on behalf of the user; it is not possible to do both at the same time | "spidev" |
| Python access | spidev (pip install spidev) and SPI-Py | "Use spidev from Python" |
| Loopback test | Put a wire between MOSI and MISO. It does not test CE0 and CE1 | "Loopback test" |
| Loopback test defaults | spi mode: 0; bits per word: 8; max speed: 500000 Hz (500 KHz) | "Loopback test" |
| DMA-mode CS setup | The CS line will be asserted at least three core clock cycles before the msb of the first byte of the transfer | "Chip selects" |
| DMA-mode CS hold | The CS line will be de-asserted no earlier than one core clock cycle after the trailing edge of the final clock pulse | "Chip selects" |
