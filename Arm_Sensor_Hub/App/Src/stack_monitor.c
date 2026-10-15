/**
 * @file stack_monitor.c
 * @brief Implements the stack monitor module.
 */

#include "stack_monitor.h"

#include <stddef.h>

#include "FreeRTOS.h"
#include "task.h"
#include "timers.h"
#include "stm32f4xx_hal.h"

/* The high-water mark scans the unused stack, so it is refreshed at this
 * period rather than on every loop pass. */
#define STACK_MONITOR_REFRESH_MS 1000u

/* The kernel's idle task name (tasks.c, configIDLE_TASK_NAME default). */
#define STACK_MONITOR_IDLE_TASK_NAME "IDLE"

volatile StackMonitor_DebugMirror g_stack_monitor_dbg = {
    .default_task_min_free_bytes = STACK_MONITOR_NOT_READ,
    .idle_task_min_free_bytes = STACK_MONITOR_NOT_READ,
    .timer_task_min_free_bytes = STACK_MONITOR_NOT_READ,
};

static uint32_t s_last_refresh_ms;
static TaskHandle_t s_idle_task;
static TaskHandle_t s_timer_task;

static uint32_t StackMonitor_FreeBytes(TaskHandle_t task)
{
    return (uint32_t)uxTaskGetStackHighWaterMark(task) * (uint32_t)sizeof(StackType_t);
}

void StackMonitor_Process(void)
{
    uint32_t now_ms = HAL_GetTick();

    if ((g_stack_monitor_dbg.sample_count != 0u) &&
        ((now_ms - s_last_refresh_ms) < STACK_MONITOR_REFRESH_MS)) {
        return;
    }
    s_last_refresh_ms = now_ms;

    /* xTaskGetHandle walks every task list, so the handles are looked up once. */
    if (s_idle_task == NULL) {
        s_idle_task = xTaskGetHandle(STACK_MONITOR_IDLE_TASK_NAME);
    }
    if (s_timer_task == NULL) {
        s_timer_task = xTimerGetTimerDaemonTaskHandle();
    }

    g_stack_monitor_dbg.default_task_min_free_bytes = StackMonitor_FreeBytes(NULL);
    if (s_idle_task != NULL) {
        g_stack_monitor_dbg.idle_task_min_free_bytes = StackMonitor_FreeBytes(s_idle_task);
    }
    if (s_timer_task != NULL) {
        g_stack_monitor_dbg.timer_task_min_free_bytes = StackMonitor_FreeBytes(s_timer_task);
    }
    g_stack_monitor_dbg.sample_count++;
}

#ifdef STACK_MONITOR_HOST_TEST
uint32_t g_stack_monitor_host_stop_count;

static void StackMonitor_StopOutputs(void)
{
    g_stack_monitor_host_stop_count++;
}
#else
extern DMA_HandleTypeDef hdma_spi3_rx;
extern DMA_HandleTypeDef hdma_spi3_tx;
extern CAN_HandleTypeDef hcan1;

static void StackMonitor_StopOutputs(void)
{
    /* PRIMASK: no configurable interrupt runs after this, whatever its priority. */
    __disable_irq();
    /* Hardware that keeps working without the CPU: the SPI3 DMA streams and the
     * three CAN transmit mailboxes (TSR.ABRQx: writing 1 aborts a pending frame). */
    __HAL_DMA_DISABLE(&hdma_spi3_rx);
    __HAL_DMA_DISABLE(&hdma_spi3_tx);
    hcan1.Instance->TSR = CAN_TSR_ABRQ0 | CAN_TSR_ABRQ1 | CAN_TSR_ABRQ2;
}
#endif

void StackMonitor_OnOverflow(const char *task_name)
{
    uint32_t i;

    StackMonitor_StopOutputs();
    g_stack_monitor_dbg.overflow_detected = 1u;
    for (i = 0u; i + 1u < STACK_MONITOR_TASK_NAME_BYTES; ++i) {
        char c = (task_name != NULL) ? task_name[i] : '\0';
        g_stack_monitor_dbg.overflow_task[i] = c;
        if (c == '\0') {
            break;
        }
    }
    g_stack_monitor_dbg.overflow_task[STACK_MONITOR_TASK_NAME_BYTES - 1u] = '\0';

#ifndef STACK_MONITOR_HOST_TEST
    /* Stopped here until reset; read g_stack_monitor_dbg over SWD. */
    for (;;) {
    }
#endif
}
