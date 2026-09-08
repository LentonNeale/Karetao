#ifndef SEMPHR_H
#define SEMPHR_H

#include "FreeRTOS.h"

typedef struct
{
    BaseType_t locked;
} StaticSemaphore_t;

typedef StaticSemaphore_t *SemaphoreHandle_t;

SemaphoreHandle_t xSemaphoreCreateMutexStatic(StaticSemaphore_t *storage);
BaseType_t xSemaphoreTake(SemaphoreHandle_t semaphore, TickType_t wait_ticks);
BaseType_t xSemaphoreGive(SemaphoreHandle_t semaphore);
BaseType_t xSemaphoreGiveFromISR(SemaphoreHandle_t semaphore, BaseType_t *higher_priority_task_woken);

#endif
