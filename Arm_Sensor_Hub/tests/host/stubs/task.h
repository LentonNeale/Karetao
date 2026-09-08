#ifndef TASK_H
#define TASK_H

#include "FreeRTOS.h"

typedef void *TaskHandle_t;

typedef enum
{
    eSetBits = 0
} eNotifyAction;

BaseType_t xTaskNotify(TaskHandle_t task, uint32_t value, eNotifyAction action);
BaseType_t xTaskNotifyFromISR(TaskHandle_t task,
                              uint32_t value,
                              eNotifyAction action,
                              BaseType_t *higher_priority_task_woken);

#endif
