# FreeRTOS kernel reference

FreeRTOS Kernel V10.3.1 as vendored under `Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source`, plus the FreeRTOSConfig.h settings and kernel calls the firmware depends on.

## Source

| Field | Value |
|---|---|
| Publisher | Amazon Web Services (FreeRTOS) |
| Title | FreeRTOS Kernel source (queue.c, tasks.c, port.c, heap_4.c, semphr.h, task.h, queue.h) and "The FreeRTOS Reference Manual, API Functions and Configuration Options" |
| Version / revision | Kernel V10.3.1 (`queue.c:2` and `task.h:46` in the project; the GitHub tag is `V10.3.1-kernel-only`, there is no tag named `V10.3.1`; the seven files above equal the vendored copies apart from line endings). Manual: "Reference Manual for FreeRTOS version 10.0.0 issue 1" (PDF page 4). Version gap: the manual predates the kernel by V10.0.0 to V10.3.1; use the source notes first |
| Date | Manual copyright 2017 (page 4); kernel file header copyright 2020; publication date unknown (not printed on source) |
| Obtained from | https://github.com/FreeRTOS/FreeRTOS-Kernel (tag V10.3.1-kernel-only); https://www.freertos.org/media/2018/FreeRTOS_Reference_Manual_V10.0.0.pdf |
| Retrieved | 2026-10-02 (each file's `source.json`) |
| Licence note | Kernel source is MIT (vendored `LICENSE`) and is cached outside the repo; the manual PDF is not copied into the repo |
| Local copy | `~/.icm/sources/freertos-kernel/<file>/` each with `source.json`; manual `refman/FreeRTOS_Reference_Manual_V10.0.0.pdf`, 1,922,103 bytes, sha256 `aa72f74194c486695e8ec6f667833a8a301f2388d6785ad62695c7bfecd8a86b`; source notes were verified against `combined/kernel-src.txt` (the seven source files concatenated, 477,426 bytes, sha256 `a28f036e57f042545577b3a4a0a5f7dd74f6182b9ffa23d8c386ae1ca513b541`) |

## Files

| File | Contains | Read when |
|---|---|---|
| `kernel-source-semantics.md` | V10.3.1 source behaviour: mutex holder, xQueueGiveFromISR assertion, interrupt-priority assertions, notify, tick | Judging an ISR or mutex call against what the kernel really asserts |
| `manual-api.md` | Manual text for xSemaphoreTake/Give/GiveFromISR, xQueueSend, xTaskNotify, critical sections, config constants (PDF pages) | Checking documented return codes and rules |
| `config-in-use.md` | FreeRTOSConfig.h values and the firmware's FreeRTOS call sites and interrupt priorities (project lines) | Checking settings and where each kernel call is made |

## Authority

The V10.3.1 source is authoritative for behaviour; the manual is authoritative only where the source note is silent, and it is for an older version. Rows in `config-in-use.md` cite project lines and are authoritative for the project as at retrieval. **Status:** verified on 2026-10-02 with `verify_citations` and `check_reference`; two `unchecked` rows in `config-in-use.md` (taskENTER_CRITICAL_FROM_ISR at `i2c_manager.c:143` and taskENTER_CRITICAL at `i2c_manager.c:166-172`) read by hand. The tool cannot match three-part version numbers, so the version appears only in this file. The heap scheme in use is `heap_4.c` (`cmake/stm32cubemx/CMakeLists.txt:72`).

## Not covered

Event groups, stream and message buffers, software timers, co-routines, MPU port, other heap schemes, queue sets, the whole manual outside the cited pages, and any FreeRTOS+ product.

## Secrets

None.
