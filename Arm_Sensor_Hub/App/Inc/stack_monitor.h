/**
 * @file stack_monitor.h
 * @brief Task stack headroom for SWD readout, and the stop on a stack overflow.
 *
 * The task stack sizes come from the CubeMX .ioc and FreeRTOSConfig.h and are
 * checked against each task's worst-case call path after every firmware build
 * (tools/stack_depth.py). This module is the run-time side: it records the least
 * free stack each task has had since reset, and stops the firmware when FreeRTOS
 * detects an overflow (configCHECK_FOR_STACK_OVERFLOW 2).
 *
 * Host tests compile it with STACK_MONITOR_HOST_TEST: the recording logic is the
 * same, the hardware stop is replaced by a counter and the overflow returns.
 */

#ifndef STACK_MONITOR_H
#define STACK_MONITOR_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Longest task name recorded on overflow, terminator included (configMAX_TASK_NAME_LEN). */
#define STACK_MONITOR_TASK_NAME_BYTES 16u

/** A free-stack field not read yet (task handle not found). */
#define STACK_MONITOR_NOT_READ UINT32_MAX

/** Read over SWD: `g_stack_monitor_dbg`. Free-stack figures are bytes, least since reset. */
typedef struct
{
    uint32_t default_task_min_free_bytes;
    uint32_t idle_task_min_free_bytes;
    uint32_t timer_task_min_free_bytes;
    /** Times StackMonitor_Process has refreshed the figures; 0 means never run. */
    uint32_t sample_count;
    /** Non-zero once an overflow was detected; the firmware is then stopped. */
    uint32_t overflow_detected;
    /** Name of the task whose stack overflowed. */
    char overflow_task[STACK_MONITOR_TASK_NAME_BYTES];
} StackMonitor_DebugMirror;

extern volatile StackMonitor_DebugMirror g_stack_monitor_dbg;

/** Call from the default task's loop; refreshes the mirror about once a second. */
void StackMonitor_Process(void);

/**
 * Called by vApplicationStackOverflowHook (freertos.c). Masks every configurable
 * interrupt (PRIMASK, not only those below the FreeRTOS syscall priority), stops
 * the SPI3 DMA streams and aborts pending CAN transmissions, records the task
 * name and stops: the overflow has already corrupted memory, so nothing may keep
 * running on it. Never returns on the target. The MKS drives keep their last
 * command; stopping them when the STM32 goes silent is the drive heartbeat's job
 * (ruling R23).
 */
void StackMonitor_OnOverflow(const char *task_name);

#ifdef __cplusplus
}
#endif

#endif /* STACK_MONITOR_H */
