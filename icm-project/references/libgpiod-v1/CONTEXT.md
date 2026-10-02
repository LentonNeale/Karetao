# libgpiod v1 reference

The libgpiod 1.6.3 C library header, NEWS and Python binding, which `data_ready.py` uses on the Raspberry Pi 5 for the DATA_READY GPIO, plus a table of v1 versus v2 Python names.

## Source

| Field | Value |
|---|---|
| Publisher | libgpiod project (Bartosz Golaszewski), released on kernel.org |
| Title | libgpiod 1.6.3 source release: `include/gpiod.h`, `NEWS`, `bindings/python/gpiodmodule.c` (docstrings). For the comparison note only: libgpiod 2.3.1 `bindings/python/gpiod/*.py` |
| Version / revision | 1.6.3 (NEWS heading "libgpiod v1.6.3"; `configure.ac` AC_INIT 1.6.3). v2 comparison: tarball named 2.3.1, but its `gpiod/version.py` prints `__version__ = "2.4.0"` |
| Date | 1.6.3 tarball HTTP Last-Modified 2021-03-22 (not printed in the files); 2.3.1 tarball Last-Modified 2026-07-03 |
| Obtained from | https://mirrors.edge.kernel.org/pub/software/libs/libgpiod/libgpiod-1.6.3.tar.xz ; https://mirrors.edge.kernel.org/pub/software/libs/libgpiod/libgpiod-2.3.1.tar.xz (git.kernel.org `/plain/` is disallowed by robots.txt and the GitHub mirror has no v1.6.3 tag, so release tarballs were used) |
| Retrieved | 2026-10-01 (v1.6.3) and 2026-10-02 (v2.3.1), from `source.json` |
| Licence note | LGPL-2.1-or-later; source files are kept in the cache, only notes are stored here |
| Local copy | `~/.icm/sources/libgpiod-v1/libgpiod-1.6.3.tar.xz`, 326,068 bytes, sha256 `841be9d788f00bab08ef22c4be5c39866f0e46cb100a3ae49ed816ac9c5dddc7` (unpacked beside it) |
| Local copy | `~/.icm/sources/libgpiod-v1/libgpiod-2.3.1.tar.xz`, 235,616 bytes, sha256 `e3a358a90a9204ff16f92b6f4028ed91460b1926f10589eb54b3566484650a30` (unpacked beside it) |

Project version: `data_ready.py` says it was confirmed against gpiod 1.6.3, and the bring-up document installs `python3-libgpiod` from Ubuntu apt; no version is pinned in a requirements file. Ubuntu's package version was not checked here.

Reviewer flag: in 1.6.3 `Chip.label` is a method (`label()`), so `chip.label == RP1_CHIP_LABEL` in `find_rp1_chip` compares a bound method with a string. See `gpiod-v1-python-api.md`.

## Files

| File | Contains | Read when |
|---|---|---|
| `gpiod-v1-python-api.md` | The v1.6.3 Python calls the project uses: Chip, ChipIter, Line request, event_wait, event_read, release, constants | Reviewing `data_ready.py` |
| `gpiod-v1-c-semantics.md` | Header and NEWS: request types and flags, event_wait return values, kernel 5.5 needs for bias flags | Checking request flags or kernel needs |
| `gpiod-v1-vs-v2.md` | Row by row: v1 name, v2 name, each cited | Any time v2 documentation (readthedocs) is quoted |

## Authority

The cached source files are authoritative. When a note and the source disagree, the source wins. Citations in the notes are identifiers or phrases in the source files, not page numbers. `gpiod-v1-c-semantics.md` was checked against `gpiod.h` and `NEWS` joined into one text file, and `gpiod-v1-vs-v2.md` against `gpiodmodule.c` plus the v2 `gpiod/*.py` files joined into one, because `verify_citations` takes a single file. **Status:** verified on 2026-10-02 with `verify_citations` and `check_reference`; the only `unchecked` rows are single-name values (constants such as LINE_REQ_EV_RISING_EDGE and v2 names such as Edge.RISING), each read by hand against the cached source.

## Not covered

C++ bindings, command-line tools, LineBulk beyond what Line wraps, Line info properties (name, consumer, direction, bias), set_config, set_value and output requests, the v1 C functions other than those the Python binding calls, and all other v2 behaviour.

## Secrets

None.
