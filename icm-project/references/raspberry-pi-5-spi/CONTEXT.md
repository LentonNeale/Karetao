# Raspberry Pi 5 SPI reference

The Raspberry Pi documentation page on the SPI bus and the RP1 peripherals datasheet, for the Pi 5 host's SPI0 and its GPIO pads (DATA_READY input).

## Source

| Field | Value |
|---|---|
| Publisher | Raspberry Pi Ltd |
| Title | "Serial peripheral interface (SPI)" (`spi-bus-on-raspberry-pi.adoc`); "Raspberry Pi RP1 Peripherals" (`rp1-peripherals.pdf`) |
| Version / revision | adoc: unknown (not printed on source; `master` branch file). PDF: release 1.1 "Final draft", build-version b9b6f74-clean |
| Date | adoc: unknown (not printed on source). PDF: 07 Nov 2023 (release 1.1; colophon build-date 2023-11-07) |
| Obtained from | https://raw.githubusercontent.com/raspberrypi/documentation/master/documentation/asciidoc/computers/raspberry-pi/spi-bus-on-raspberry-pi.adoc ; https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf |
| Retrieved | adoc 2026-10-01 (`source.json`); PDF 2026-10-02 (`fetch_source` got HTTP 403, so it was downloaded with `curl` and a browser User-Agent; not in `source.json`) |
| Licence note | Not stored here. The PDF colophon says CC BY-ND 4.0; the adoc prints no licence. Only cited notes are kept. |
| Local copy | `~/.icm/sources/raspberry-pi-5-spi/spi-bus-on-raspberry-pi.adoc`, 11,581 bytes, sha256 `14ce8a79356469c6e7640efffa45d0804c04ef8c0334cc867b598c319c5e9448` |
| Local copy | `~/.icm/sources/raspberry-pi-5-spi/rp1-peripherals.pdf`, 3,513,008 bytes, sha256 `87fb7b24e8d9add075b849d095a107827610c0409ea194785af624c1ea986c3d` |

Pi model: the project targets a Pi 5 (RP1). The adoc covers all Pi models; use only its "Raspberry Pi 5, 500, 500+ and Compute Module 5" parts for the project. The RP1 PDF is the 2023 final draft; later releases may differ.

## Files

| File | Contains | Read when |
|---|---|---|
| `pi-spi-docs.md` | Pi docs: Pi 5 SPI controllers, SPI0 header pins, dtparam/dtoverlay settings, clock rule of thumb, mode bits, spidev | Enabling or checking SPI0 and `/dev/spidev0.0` |
| `rp1-spi-gpio.md` | RP1 datasheet: SPI instance table, clocks, GPIO function rows, interrupts, pad features and registers (Schmitt, pull, drive) | Checking SPI0 limits or the DATA_READY GPIO pad setup |

## Authority

The cached source files are authoritative; page numbers in `rp1-spi-gpio.md` are PDF pages (printed page = PDF page minus 1). When a note and the source disagree, the source wins. **Status:** verified on 2026-10-02 with `verify_citations` and `check_reference` (both empty).

## Not covered

Other SPI buses and Pi models, Compute Module alternate mappings, LoSSI and bidirectional modes, GPIO registers other than the pad bits above, electrical timing characteristics (the PDF gives none for SPI clock rates beyond what is quoted), and RP1's other peripherals. The kernel `spi_dw` driver's own limits are not in these sources.

## Secrets

None.
