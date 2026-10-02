# Vendored CMSIS-RTOS2 wrapper for FreeRTOS, and firmware use

The firmware includes `cmsis_os.h` (a CMSIS-RTOS v2 header chain: it includes `cmsis_os2.h`), not the v1 API. Rows cite project lines (`path:start-end`, relative to the Karetao repo root). The wrapper is Arm's `cmsis_os2.c` (Apache-2.0) as vendored by STM32CubeF4.

| Rule | Value | Citation |
|---|---|---|
| Firmware includes the CMSIS-RTOS header | #include "cmsis_os.h" | Arm_Sensor_Hub/Core/Src/main.c:21-21 |
| cmsis_os.h pulls in cmsis_os2.h | #include "cmsis_os2.h" | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os.h:155-155 |
| Wrapper declares the API version it implements | #define osCMSIS               0x20001U  ///< API version (main[31:16].sub[15:0]) | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os.h:132-132 |
| Wrapper reports the kernel as FreeRTOS plus tskKERNEL_VERSION_NUMBER | #define RTOS_ID_s             ("FreeRTOS " tskKERNEL_VERSION_NUMBER) | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os.h:130-130 |
| Application default task attributes: name, stack_size in bytes, priority | .name = "defaultTask", .stack_size = 128 * 4, .priority = (osPriority_t) osPriorityNormal, | Arm_Sensor_Hub/Core/Src/main.c:64-66 |
| Start sequence in main: osKernelInitialize, then App_Init, then osThreadNew, then osKernelStart | osKernelInitialize(); ... App_Init(); ... defaultTaskHandle = osThreadNew(StartDefaultTask, NULL, &defaultTask_attributes); ... osKernelStart(); | Arm_Sensor_Hub/Core/Src/main.c:129-161 |
| The default task loop calls osDelay with 1 tick | osDelay(1); | Arm_Sensor_Hub/Core/Src/main.c:454-454 |
| Wrapper osKernelInitialize: ISR gives osErrorISR; state osKernelInactive becomes osKernelReady and returns osOK; otherwise osError | if (IS_IRQ()) { stat = osErrorISR; } ... if (KernelState == osKernelInactive) { ... KernelState = osKernelReady; stat = osOK; } else { stat = osError; | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os2.c:198-218 |
| Wrapper osKernelStart: only from osKernelReady; sets osKernelRunning then calls vTaskStartScheduler | if (KernelState == osKernelReady) { SVC_Setup(); KernelState = osKernelRunning; vTaskStartScheduler(); stat = osOK; | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os2.c:265-284 |
| Wrapper osThreadNew: default priority osPriorityNormal, default stack configMINIMAL_STACK_SIZE | stack = configMINIMAL_STACK_SIZE; prio  = (UBaseType_t)osPriorityNormal; | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os2.c:454-455 |
| Wrapper osThreadNew rejects priority outside osPriorityIdle to osPriorityISR, and joinable threads, by returning NULL | if ((prio < osPriorityIdle) or (prio > osPriorityISR) or ((attr->attr_bits & osThreadJoinable) == osThreadJoinable)) { return (NULL); | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os2.c:468-470 |
| Wrapper converts stack_size bytes to words | stack = attr->stack_size / sizeof(StackType_t); | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os2.c:475-475 |
| Wrapper osThreadNew with no static memory uses xTaskCreate and the CMSIS priority value directly as the FreeRTOS priority | if (xTaskCreate ((TaskFunction_t)func, name, (uint16_t)stack, argument, prio, &hTask) != pdPASS) { | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os2.c:501-501 |
| Wrapper osDelay: ISR gives osErrorISR; ticks of 0 gives osOK without delay; otherwise vTaskDelay(ticks) and osOK | if (ticks != 0U) { vTaskDelay(ticks); } | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os2.c:881-895 |
| Wrapper SysTick_Handler calls xPortSysTickHandler once the scheduler has started | if (xTaskGetSchedulerState() != taskSCHEDULER_NOT_STARTED) { /* Call tick handler */ xPortSysTickHandler(); | Arm_Sensor_Hub/Middlewares/Third_Party/FreeRTOS/Source/CMSIS_RTOS_V2/cmsis_os2.c:162-166 |
