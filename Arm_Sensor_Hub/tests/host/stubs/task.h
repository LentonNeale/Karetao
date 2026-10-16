#ifndef TASK_H
#define TASK_H

#include "FreeRTOS.h"

typedef void *TaskHandle_t;

UBaseType_t uxTaskGetStackHighWaterMark(TaskHandle_t task);
TaskHandle_t xTaskGetHandle(const char *name);

#endif
