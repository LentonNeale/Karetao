#ifndef TASK_H
#define TASK_H

#include "FreeRTOS.h"

typedef void *TaskHandle_t;

UBaseType_t uxTaskGetStackHighWaterMark(TaskHandle_t task);
TaskHandle_t xTaskGetHandle(const char *name);

/* Task critical sections (task_stub.c). The stub counts entries and the nesting depth, so a
 * test can check that a guarded call took the section and always left it. */
void HostStub_EnterCritical(void);
void HostStub_ExitCritical(void);
unsigned HostStub_CriticalDepth(void);
unsigned HostStub_CriticalEntryCount(void);

#define taskENTER_CRITICAL() HostStub_EnterCritical()
#define taskEXIT_CRITICAL() HostStub_ExitCritical()

#endif
