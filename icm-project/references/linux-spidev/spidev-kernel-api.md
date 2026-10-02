# Linux spidev userspace API (kernel docs)

Values are the page's own wording, shortened. Project use: `/dev/spidev0.0`, mode 0, 8 bits per word, 5000000 Hz, one 512-byte full-duplex transfer (`spi_bus.py`).

| Rule | Value | Citation |
|---|---|---|
| Device node name | /dev/spidevB.C ... character special device, major number 153 with a dynamically chosen minor device number | "DEVICE CREATION, DRIVER BINDING" |
| Node naming | For a SPI device with chipselect C on bus B | "DEVICE CREATION, DRIVER BINDING" |
| Open and close | Normal open() and close() operations on /dev/spidevB.D files work as you would expect | "BASIC CHARACTER DEVICE API" |
| read()/write() are half-duplex | Standard read() and write() operations are obviously only half-duplex, and the chipselect is deactivated between those operations | "BASIC CHARACTER DEVICE API" |
| Full duplex and no CS release | Full-duplex access, and composite operation without chipselect de-activation, is available using the SPI_IOC_MESSAGE(N) request | "BASIC CHARACTER DEVICE API" |
| Mode ioctl | SPI_IOC_RD_MODE, SPI_IOC_WR_MODE: pass a pointer to a byte which will return (RD) or assign (WR) the SPI transfer mode | "BASIC CHARACTER DEVICE API" |
| Mode constants | Use the constants SPI_MODE_0..SPI_MODE_3 | "BASIC CHARACTER DEVICE API" |
| CPOL | SPI_CPOL (clock polarity, idle high iff this is set) | "BASIC CHARACTER DEVICE API" |
| CPHA | SPI_CPHA (clock phase, sample on trailing edge iff this is set) | "BASIC CHARACTER DEVICE API" |
| Mode byte limit | this request is limited to SPI mode flags that fit in a single byte | "BASIC CHARACTER DEVICE API" |
| 32-bit mode | SPI_IOC_RD_MODE32, SPI_IOC_WR_MODE32: pass a pointer to a uin32_t which will return (RD) or assign (WR) the full SPI transfer mode | "BASIC CHARACTER DEVICE API" |
| Bit order | Zero indicates MSB-first; other values indicate the less common LSB-first encoding | "BASIC CHARACTER DEVICE API" |
| Bits per word | SPI_IOC_RD_BITS_PER_WORD, SPI_IOC_WR_BITS_PER_WORD: the number of bits in each SPI transfer word. The value zero signifies eight bits | "BASIC CHARACTER DEVICE API" |
| Max speed | SPI_IOC_RD_MAX_SPEED_HZ, SPI_IOC_WR_MAX_SPEED_HZ: pass a pointer to a u32 which will return (RD) or assign (WR) the maximum SPI transfer speed, in Hz | "BASIC CHARACTER DEVICE API" |
| Speed not exact | The controller can't necessarily assign that specific clock speed | "BASIC CHARACTER DEVICE API" |
| No async I/O | At this time there is no async I/O support; everything is purely synchronous | "BASIC CHARACTER DEVICE API" |
| Actual bit rate | There's currently no way to report the actual bit rate used to shift data to/from a given device | "BASIC CHARACTER DEVICE API" |
| CS polarity | From userspace, you can't currently change the chip select polarity | "BASIC CHARACTER DEVICE API" |
| CS between uses | Each SPI device is deselected when it's not in active use, allowing other drivers to talk to other devices | "BASIC CHARACTER DEVICE API" |
| Transfer size limit | There's a limit on the number of bytes each I/O request can transfer to the SPI device. It defaults to one page, but that can be changed using a module parameter | "BASIC CHARACTER DEVICE API" |
| No ACK | Because SPI has no low-level transfer acknowledgement, you usually won't see any I/O errors when talking to a non-existent device | "BASIC CHARACTER DEVICE API" |
| Full-duplex transfer | To make a full duplex request, provide both rx_buf and tx_buf for the same transfer. It's even OK if those are the same buffer | "FULL DUPLEX CHARACTER DEVICE API" |
| Chip not deselected between request and response | These requests commonly require that the chip not be deselected between the request and response | "FULL DUPLEX CHARACTER DEVICE API" |
| Chaining messages | Several such requests could be chained into a single kernel request, even allowing the chip to be deselected after each response | "FULL DUPLEX CHARACTER DEVICE API" |
| Per-transfer overrides | Other protocol options include changing the word size and bitrate for each transfer segment | "FULL DUPLEX CHARACTER DEVICE API" |
| Binding | Sysfs also supports userspace driven binding/unbinding of drivers to devices that do not bind automatically using one of the tables above | "DEVICE CREATION, DRIVER BINDING" |
| Do not hand-manage nodes | Do not try to manage the /dev character device special file nodes by hand | "DEVICE CREATION, DRIVER BINDING" |
| Plain "spidev" name | It used to be supported to define an SPI device using the "spidev" name ... this is no longer supported by the Linux kernel | "DEVICE CREATION, DRIVER BINDING" |

Not on this page: the name of the module parameter (`bufsiz`) and the field name `cs_change`; the page does not print them. The py-spidev README names `/sys/module/spidev/parameters/bufsiz` (see `py-spidev-api.md`).
