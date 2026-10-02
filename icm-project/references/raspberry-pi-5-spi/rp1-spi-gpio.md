# RP1 peripherals: SPI controllers and GPIO pads

Page numbers are PDF pages of the cached file (printed page numbers are one lower). Project use: SPI0 master on GPIO8-11, DATA_READY on GPIO25 as an input with rising-edge events, Schmitt trigger enabled, no pull.

| Rule | Value | Citation |
|---|---|---|
| RP1 purpose | RP1 is a peripheral controller, designed by Raspberry Pi for use on Raspberry Pi 5 | p. 5 |
| Link to the AP | It connects to an application processor (AP) via a PCIe 2.0 x4 bus | p. 5 |
| GPIO pin count | Twenty-eight GPIO pins are provided, to implement the standard Raspberry Pi 40-pin GPIO connector | p. 5 |
| GPIO bank | The pins are in a single electrical bank (VDDIO0). The GPIO bank (IO_BANK0) can be powered from 1.8V or 3.3V, but interface timings have been specified at 3.3V | p. 15 |
| SPI controllers | RP1 has nine Synchronous Serial Interface (SSI) controllers, six of which are available on GPIO bank 0 | p. 51 |
| SPI IP | Each SSI controller is based on a configuration of the Synopsys DW_apb_ssi IP (v4.02a) | p. 51 |
| DDR | DDR operation is not supported | p. 51 |
| SPI0 instance | SPI0 M 4 Quad (instance, master/slave, chip-select count, max I/O width) | p. 51 |
| SPI1 instance | SPI1 M 3 Dual | p. 51 |
| SPI4 instance | SPI4 S 1 Single | p. 51 |
| Master clocks | pclk and sclk are driven from clk_sys | p. 52 |
| Core clock | The Core clock (clk_sys) typically runs at 200MHz | p. 13 |
| SPI clocking | SPI master interfaces are clocked from clk_sys, but the SPI slave interface has the TX shift register directly clocked from the GPIO SCLK input pad | p. 14 |
| Rate control | Both SPI and I2C have internal divisors that control the interface data rate | p. 14 |
| SPI0 register base | spi0 APB N 0x40050000 | p. 52 |
| Linux reference driver | For a reference implementation see the Designware SPI/SSI Linux kernel driver | p. 52 |
| GPIO8 function row | 8 SPI0_CSn[0] DPI_D[4] UART3_TX I2C0_SDA SYS_RIO[8] PROC_RIO[8] PIO[8] SPI4_CSn[0] | p. 16 |
| GPIO9 function row | 9 SPI0_SIO[1] DPI_D[5] UART3_RX I2C0_SCL SYS_RIO[9] PROC_RIO[9] PIO[9] SPI4_SIO[0] | p. 16 |
| GPIO10 function row | 10 SPI0_SIO[0] DPI_D[6] UART3_CTS I2C1_SDA SYS_RIO[10] PROC_RIO[10] PIO[10] SPI4_SIO[1] | p. 16 |
| GPIO11 function row | 11 SPI0_SCLK DPI_D[7] UART3_RTS I2C1_SCL SYS_RIO[11] PROC_RIO[11] PIO[11] SPI4_SCLK | p. 16 |
| GPIO25 function row | 25 SDIO0_DAT[1] DPI_D[21] I2S0_SDO[2] AUDIO_IN_CLK I2S1_SDO[2] SYS_RIO[25] PROC_RIO[25] PIO[25] SPI3_CSn[1] | p. 17 |
| Function select | The function allocated to each GPIO is selected by writing to the FUNCSEL field of the GPIO's CTRL register | p. 15 |
| FUNCSEL reset | 4:0 FUNCSEL Function select. 31 == NULL. See GPIO function table for available functions. RW 0x1f | p. 23 |
| Interrupt cases | An interrupt can be generated for every GPIO pin in eight scenarios | p. 18 |
| Edge High | Edge High: the GPIO has transitioned from a logical 0 to a logical 1 | p. 18 |
| Level interrupts | The level interrupts are not latched | p. 18 |
| Edge latching | The edge interrupts are stored in the GPIOn_STATUS register and cleared by writing 1 to the GPIOn_CTRL.IRQRESET register bit | p. 18 |
| Missed level interrupts | Interrupts may be missed by the host processor if this feature is not used | p. 18 |
| Pad type | Each GPIO is connected via a bidirectional CMOS pad | p. 18 |
| Fault tolerance | Fault-tolerant operation - very little current flows into the pin whilst it is below 3.63V and IOVDD is 0V | p. 18 |
| Drive strengths | Output drive strength of 2mA, 4mA, 8mA or 12mA | p. 18 |
| Schmitt trigger | Optional input Schmitt trigger hysteresis | p. 18 |
| Pull options | Integrated pull-up, pull-down, bus-keeper or high-impedance behaviour when the output drive is disabled | p. 18 |
| ESD | ESD rated to 4kV HBM, 500V CDM, 200V MM | p. 18 |
| Input thresholds | By default the pad input thresholds are valid for an VDDIO voltage between 2.5V and 3.3V | p. 19 |
| 1.8V caution | Using VDDIO voltages greater than 1.8V, with the input thresholds set for 1.8V may result in damage to the chip | p. 19 |
| IE reset | 6 IE Input enable RW 0x0 | p. 34 |
| PUE | 3 PUE Pull up enable RW varies | p. 34 |
| PDE | 2 PDE Pull down enable RW varies | p. 35 |
| SCHMITT reset | 1 SCHMITT Enable schmitt trigger RW 0x1 | p. 35 |
| Drive reset | 5:4 DRIVE Drive strength. RW 0x1 | p. 34 |
| Document colophon | build-date: 2023-11-07; build-version: b9b6f74-clean | p. 2 |
| Release history | 1.0 06 Oct 2023 First draft release; 1.1 07 Nov 2023 Final draft | p. 92 |
