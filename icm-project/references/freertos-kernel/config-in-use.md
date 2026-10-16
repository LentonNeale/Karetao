# FreeRTOSConfig.h settings in use, and firmware call sites

Rows cite project lines (`path:start-end`, relative to the Karetao repo root). Kernel version V10.3.1 is stated in `CONTEXT.md` (the version tool cannot match three-part numbers).

| Rule | Value | Citation |
|---|---|---|
| Pre-emptive scheduling | #define configUSE_PREEMPTION                     1 | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:62-62 |
| Static and dynamic allocation both enabled | #define configSUPPORT_STATIC_ALLOCATION          1 | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:63-64 |
| Tick rate | #define configTICK_RATE_HZ                       ((TickType_t)1000) | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:68-68 |
| Number of priorities | #define configMAX_PRIORITIES                     ( 56 ) | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:69-69 |
| Minimal (idle) stack in words | #define configMINIMAL_STACK_SIZE                 ((uint16_t)128) | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:70-70 |
| Heap size in bytes | #define configTOTAL_HEAP_SIZE                    ((size_t)15360) | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:71-71 |
| Tick type is not 16-bit | #define configUSE_16_BIT_TICKS                   0 | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:74-74 |
| Mutexes, recursive mutexes and counting semaphores enabled | #define configUSE_MUTEXES                        1 | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:75-78 |
| Software timers enabled: priority, queue length, stack depth | #define configTIMER_TASK_PRIORITY                ( 2 ) ... #define configTIMER_QUEUE_LENGTH                 10 ... #define configTIMER_TASK_STACK_DEPTH             256 | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:91-94 |
| vTaskDelay and vTaskSuspend included | #define INCLUDE_vTaskSuspend                 1 ... #define INCLUDE_vTaskDelay                   1 | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:110-112 |
| Interrupt priority bits | #define configPRIO_BITS         4 | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:131-131 |
| Lowest interrupt priority | #define configLIBRARY_LOWEST_INTERRUPT_PRIORITY   15 | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:136-136 |
| Highest priority (numerically lowest) from which FromISR calls are allowed | #define configLIBRARY_MAX_SYSCALL_INTERRUPT_PRIORITY 5 | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:142-142 |
| Kernel and max-syscall priority shifted into the top bits | #define configKERNEL_INTERRUPT_PRIORITY 		( configLIBRARY_LOWEST_INTERRUPT_PRIORITY << (8 - configPRIO_BITS) ) | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:146-149 |
| configASSERT disables interrupts and loops forever on failure | #define configASSERT( x ) if ((x) == 0) {taskDISABLE_INTERRUPTS(); for( ;; );} | Arm_Sensor_Hub/Core/Inc/FreeRTOSConfig.h:154-154 |
| SPI3 interrupt priority | HAL_NVIC_SetPriority(SPI3_IRQn, 5, 0); | Arm_Sensor_Hub/Core/Src/stm32f4xx_hal_msp.c:300-300 |
| DMA stream interrupt priorities | HAL_NVIC_SetPriority(DMA1_Stream0_IRQn, 5, 0); ... HAL_NVIC_SetPriority(DMA1_Stream5_IRQn, 6, 0); | Arm_Sensor_Hub/Core/Src/main.c:389-393 |
| NVIC priority grouping set by HAL_Init | HAL_NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_4); | Arm_Sensor_Hub/Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal.c:173-173 |
| I2C mutex created static | s_i2c_mutex = xSemaphoreCreateMutexStatic(&s_i2c_mutex_storage); | Arm_Sensor_Hub/App/Src/i2c_manager.c:235-235 |
| Blocking I2C path takes the mutex with a tick timeout | if (xSemaphoreTake(s_i2c_mutex, pdMS_TO_TICKS(timeout_ms)) != pdTRUE) | Arm_Sensor_Hub/App/Src/i2c_manager.c:65-65 |
| Interrupt I2C path takes the mutex with zero timeout before starting the transfer | if (xSemaphoreTake(s_i2c_mutex, 0u) != pdTRUE) | Arm_Sensor_Hub/App/Src/i2c_manager.c:433-433 |
| I2C completion callbacks give the same mutex from interrupt context | (void)xSemaphoreGiveFromISR(s_i2c_mutex, NULL); | Arm_Sensor_Hub/App/Src/i2c_manager.c:523-523 |
| I2C error callback gives the mutex from interrupt context | (void)xSemaphoreGiveFromISR(s_i2c_mutex, NULL); | Arm_Sensor_Hub/App/Src/i2c_manager.c:563-563 |
| ISR side uses FromISR critical-section macros | saved_interrupt_status = taskENTER_CRITICAL_FROM_ISR(); | Arm_Sensor_Hub/App/Src/i2c_manager.c:143-143 |
| Task side dispatch uses xQueueSend with zero block time and xTaskNotify with eSetBits | (void)xQueueSend(s_event_queue, &event, 0u); ... (void)xTaskNotify(s_notify_task, s_notify_bits, eSetBits); | Arm_Sensor_Hub/App/Src/i2c_manager.c:213-218 |
| Task side critical section | taskENTER_CRITICAL(); ... taskEXIT_CRITICAL(); | Arm_Sensor_Hub/App/Src/i2c_manager.c:166-172 |
