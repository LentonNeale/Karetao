# Kernel start, threads and delay (CMSIS-RTOS2 API reference, Version 2.1.3)

Only the calls the firmware makes: osKernelInitialize, osKernelStart, osThreadNew (osThreadAttr_t, osPriority_t) and osDelay.

| Rule | Value | Citation |
|---|---|---|
| osKernelInitialize: only osKernelGetInfo and osKernelGetState may be called before it succeeds | Before it is successfully executed, only the functions osKernelGetInfo and osKernelGetState may be called. | "osKernelInitialize" |
| osKernelInitialize return values | osOK in case of success. osError if an unspecific error occurred. osErrorISR if called from an Interrupt Service Routine. osErrorNoMemory if no memory could be reserved for the operation. | "osKernelInitialize" |
| osKernelInitialize cannot be called from an ISR | This function cannot be called from Interrupt Service Routines. | "osKernelInitialize" |
| Before osKernelStart succeeds only osKernelGetInfo, osKernelGetState and object creation functions (osXxxNew) may be called | Before it is successfully executed, only the functions osKernelGetInfo, osKernelGetState, and object creation functions (osXxxNew) may be called. | "osKernelStart" |
| osKernelStart does not return on success | It will not return to its calling function in case of success. | "osKernelStart" |
| At least one initial thread should exist before osKernelStart | At least one initial thread should be created prior osKernelStart, see osThreadNew. | "osKernelStart" |
| Kernel state before and after start | osKernelInactive: osKernelInitialize needs to be executed successfully. osKernelReady: osKernelStart transfers the kernel to the running state. osKernelRunning: The kernel is initialized and running. | "osKernelState_t" |
| osThreadNew parameters and return | func thread function; argument pointer that is passed to the thread function as start argument; attr thread attributes; NULL: default values. Returns thread ID or NULL in case of error. | "osThreadNew" |
| osThreadNew may be called before osKernelStart, not before osKernelInitialize | The function can be safely called before the RTOS is started (call to osKernelStart), but not before it is initialized (call to osKernelInitialize). | "osThreadNew" |
| osThreadNew cannot be called from an ISR | Cannot be called from Interrupt Service Routines. | "osThreadNew" |
| A created thread of higher priority than the running thread starts instantly | When the priority of the created thread function is higher than the current RUNNING thread, the created thread function starts instantly and becomes the new RUNNING thread. | "osThreadNew" |
| CMSIS-RTOS is preemptive | CMSIS-RTOS is preemptive. The active thread with the highest priority becomes the RUNNING thread provided it does not wait for any event. | "Thread Management" |
| osThreadAttr_t stack_size unit | The size (in bytes) of the stack specified by stack_mem. | "osThreadAttr_t" |
| osThreadAttr_t priority default | initial thread priority (default: osPriorityNormal) | "osThreadAttr_t" |
| osThreadAttr_t name default | Default: NULL no name specified | "osThreadAttr_t" |
| osThreadAttr_t attr_bits: detached is the default | osThreadDetached : create thread in a detached mode (default). | "osThreadAttr_t" |
| osThreadJoinable value | #define osThreadJoinable   0x00000001U | "osThreadJoinable" |
| Priority values: None, Idle, Normal, ISR | osPriorityNone = 0, osPriorityIdle = 1, osPriorityNormal = 24, osPriorityISR = 56 | "osPriority_t" |
| osDelay unit and minimum | The function osDelay waits for a time period specified in kernel ticks. For a value of 1 the system waits until the next timer tick occurs. | "osDelay" |
| osDelay(1) can return in less than one tick | The actual time delay may be up to one timer tick less than specified, i.e. calling osDelay(1) right before the next system tick occurs the thread is rescheduled immediately. | "osDelay" |
| osDelay blocks the calling thread | The delayed thread is put into the BLOCKED state and a context switch occurs immediately. | "osDelay" |
| osDelay return values | osOK: the time delay is executed. osErrorParameter: the time cannot be handled (zero value). osErrorISR: osDelay cannot be called from Interrupt Service Routines. osError: osDelay cannot be executed (kernel not running or no READY thread exists). | "osDelay" |
| osDelay cannot be called from an ISR | This function cannot be called from Interrupt Service Routines. | "osDelay" |
