# Linux spidev reference

The Linux kernel's spidev userspace API page and the py-spidev Python binding (README and C source), as used by the Raspberry Pi host for `/dev/spidev0.0`.

## Source

| Field | Value |
|---|---|
| Publisher | The kernel development community (kernel page); py-spidev project (doceme/py-spidev, MIT licensed) |
| Title | "SPI userspace API" (docs.kernel.org/spi/spidev.html); "Python Spidev" README and `spidev_module.c` |
| Version / revision | Kernel page: unknown (not printed on source) beyond the site header "7.3.0-rc5" and Sphinx 5.3.0 footer; py-spidev: README unversioned, `spidev_module.c` defines `_VERSION_ "3.8"` (master branch, not a tag) |
| Date | Kernel page: HTTP Last-Modified 2026-09-27 (not printed on the page); py-spidev: unknown (not printed on source) |
| Obtained from | https://docs.kernel.org/spi/spidev.html ; https://raw.githubusercontent.com/doceme/py-spidev/master/README.md ; https://raw.githubusercontent.com/doceme/py-spidev/master/spidev_module.c |
| Retrieved | 2026-10-01 (from `source.json`) |
| Licence note | Not stored here: kernel docs are GPL, so only cited notes are kept; py-spidev is MIT but its files stay in the cache. |
| Local copy | `~/.icm/sources/linux-spidev/spidev.html`, 21,293 bytes, sha256 `bc6d17b3e8743adddf45ec3a0a588501b161f977b0f9b243f914ff10481d6dcd` |
| Local copy | `~/.icm/sources/linux-spidev/README.md`, 7,997 bytes, sha256 `0b878f6e93b62439c2fa47347bfcbba7d723322504f57c6cee78cba1f1d58350` |
| Local copy | `~/.icm/sources/linux-spidev/spidev_module.c`, 38,788 bytes, sha256 `6cfaf4224a6c7560f83df3492d3bd213b70db2baa7c4c687d4b36267c5838e53` (`source.json` there holds only the last fetch; the hashes here are from `sha256sum`) |

Version note: the project installs `python3-spidev` from the Ubuntu 24.04 apt archive (`RASPBERRY_PI_BRINGUP_V1.md`); no py-spidev or kernel version is pinned in the project, so master and the newest kernel page may differ from what runs on the Pi.

## Files

| File | Contains | Read when |
|---|---|---|
| `spidev-kernel-api.md` | Kernel spidev page: device nodes, mode/bits/speed ioctls, half vs full duplex, chip-select behaviour, transfer size limit | Reviewing SPI transfer settings or CS behaviour |
| `py-spidev-api.md` | py-spidev README: settings attributes and the `open`, `xfer`, `xfer2`, `xfer3`, `close` methods | Checking an `import spidev` call |
| `py-spidev-source.md` | `spidev_module.c`: docstrings, list-size limit, how `xfer`/`xfer2` call the kernel | Checking size limits (512-byte transfer) or `xfer2` behaviour |

## Authority

The cached source files are authoritative. When a note and the source disagree, the source wins; fix the note. Every value cites a heading (README, kernel page) or an identifier (C file). **Status:** verified on 2026-10-02 with `verify_citations` and `check_reference`; the only `unchecked` rows are three README bullets (`bits_per_word`, `max_speed_hz`, `cshigh`), read by hand against the README.

## Not covered

`SPI_IOC_MESSAGE` struct fields (`cs_change`, `delay_usecs`) and the exact `bufsiz` module-parameter default: the kernel page says only "one page" and does not print `cs_change`; read `include/uapi/linux/spi/spidev.h` and `drivers/spi/spidev.c` for them. Also not covered: device binding tables, `readbytes`/`writebytes` internals, 3-wire, loopback, udev rules.

## Secrets

None.
