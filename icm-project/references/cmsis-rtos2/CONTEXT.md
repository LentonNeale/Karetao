# CMSIS-RTOS2 reference

The CMSIS-RTOS v2 API (as used by the firmware through the FreeRTOS wrapper `cmsis_os2.c`), limited to the calls the firmware makes.

## Source

| Field | Value |
|---|---|
| Publisher | Arm Limited (CMSIS_5 documentation) |
| Title | CMSIS-RTOS2: Real-Time Operating System: API and RTX Reference Implementation, pages Kernel Control, Thread Management, Generic Wait Functions |
| Version / revision | Version 2.1.3 (shown on the main page). The vendored wrapper declares API 0x20001U (osCMSIS, `cmsis_os.h:132`); the page version and the wrapper's API constant are different numbers, not a matching pair. The project uses CMSIS-RTOS v2 (`cmsis_os.h` includes `cmsis_os2.h`; calls are osThreadNew, not osThreadCreate) |
| Date | unknown (not printed on source) |
| Obtained from | https://arm-software.github.io/CMSIS_5/RTOS2/html/index.html (CMSIS_5 docs; CMSIS_6 not used) |
| Retrieved | 2026-10-02 (each page's `source.json`) |
| Licence note | Not stored here: cached outside the repo. The wrapper is Apache-2.0 per its own header |
| Local copy | `~/.icm/sources/cmsis-rtos2/<page>/`: KernelCtrl 65,301 bytes sha256 `ba05492d9100861383f94147cc90d123379c01e7de8b5ce9e1e73d280308bcb5`; ThreadMgmt 125,137 bytes sha256 `95e3c172f4e488e660b3d246dc83058b539b9ca6fa6bf12457b84dc06c68343a`; Wait 16,385 bytes sha256 `484d7f250a5525f768b87468c1d2a1f827334c10968c8354ad155c839b0e9225`; index 11,565 bytes sha256 `3f2ffd7eb6d301e6f2d091a66e484d9a98179053ea18e91737f9aae905ab91c8`. Notes were verified against `combined/rtos2.txt` (the three group pages, tags stripped; 60,670 bytes sha256 `56aeb440918793c54205e3f30d7b29b25700bd5bc486669ac17d994beac935bf`) |

## Files

| File | Contains | Read when |
|---|---|---|
| `kernel-thread-delay.md` | osKernelInitialize, osKernelStart, osThreadNew, osThreadAttr_t, osPriority_t, osDelay as documented | Reviewing startup order, thread creation, the 1-tick main loop |
| `freertos-wrapper-and-usage.md` | What the vendored FreeRTOS wrapper actually does for those calls, and the firmware's call sites (project lines) | Checking where the wrapper differs from the documentation |

## Authority

The Arm documentation is authoritative for the API; the vendored `cmsis_os2.c` is authoritative for what this firmware gets. They differ in one cited place: the documentation lists osErrorParameter for osDelay with zero ticks, the wrapper returns osOK. **Status:** verified on 2026-10-02 with `verify_citations` and `check_reference`.

## Not covered

All other calls (mutexes, semaphores, queues, flags, timers, memory pools: the firmware calls the FreeRTOS API directly for those, see `freertos-kernel`), RTX-specific text, and the Revision History pages.

## Secrets

None.
