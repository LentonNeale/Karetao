# API semantics and configuration (FreeRTOS Reference Manual, 10.0.0 issue 1)

Citations are PDF pages of the cached copy (they equal the printed page numbers). The manual is for an earlier version than the vendored kernel; where the kernel source differs, `kernel-source-semantics.md` wins.

| Rule | Value | Citation |
|---|---|---|
| Mutexes carry priority inheritance, binary semaphores do not | Mutexes include a priority inheritance mechanism, binary semaphores do not. | p. 228 |
| A mutex used for mutual exclusion must always be given back | A task that obtains a mutex that is used for mutual exclusion must always give the mutex back | p. 229 |
| Mutex static creation needs static allocation enabled | configSUPPORT_STATIC_ALLOCATION must be set to 1 in FreeRTOSConfig.h for this function to be available. | p. 231 |
| xSemaphoreGive on a mutex by a non-holder fails | The semaphore ‘give’ operation was not successful because the task calling xSemaphoreGive() is not the semaphore holder. | p. 240 |
| xSemaphoreGive: a task must take before it can give | A task must successfully ‘take’ a semaphore before it can successfully ‘give’ it back. | p. 240 |
| xSemaphoreGiveFromISR has no block time and is ISR-safe | Unlike xSemaphoreGive(), xSemaphoreGiveFromISR() does not permit a block time to be specified. | p. 242 |
| pxHigherPriorityTaskWoken may be NULL | pxHigherPriorityTaskWoken is an optional parameter and can be set to NULL. | pp. 242-243 |
| xSemaphoreGiveFromISR on an already-available semaphore | If a semaphore is already available, it cannot be given, and xSemaphoreGiveFromISR() will return errQUEUE_FULL. | p. 243 |
| xSemaphoreGiveFromISR does not switch context itself | Unlike the xSemaphoreGive() API function, xSemaphoreGiveFromISR() will not itself perform a context switch. | p. 243 |
| xSemaphoreGiveFromISR must not run before the scheduler starts | xSemaphoreGiveFromISR() must not be called prior to the scheduler being started. | p. 243 |
| xSemaphoreTake with zero block time returns immediately | If xTicksToWait is zero, then xSemaphoreTake() will return immediately if the semaphore is not available. | p. 248 |
| xSemaphoreTake return values | pdPASS Returned only if the call to xSemaphoreTake() was successful in obtaining the semaphore. | p. 248 |
| xSemaphoreTake must not be called from a critical section | xSemaphoreTake() must not be called from within a critical section or while the scheduler is suspended. | p. 249 |
| xSemaphoreTake only from a running task | xSemaphoreTake() must only be called from an executing task | p. 249 |
| xQueueSend with zero block time on a full queue returns at once | will return immediately if xTicksToWait is zero and the queue is already full. | p. 204 |
| xQueueSend returns errQUEUE_FULL when the queue stays full | errQUEUE_FULL Returned if data could not be written to the queue because the queue was already full. | p. 204 |
| xQueueSend has an ISR-safe counterpart without block time | Unlike xQueueSend(), xQueueSendToFront() and xQueueSendToBack(), the ISR safe versions do not permit a block time to be specified. | p. 206 |
| xTaskNotify value initial state | Each task has a 32-bit notification value that is initialized to zero when the task is created. | p. 100 |
| xTaskNotify with eSetBits ORs the value in | eSetBits – The task’s notification value is bitwise ORed with ulValue. | p. 101 |
| xTaskNotify returns pdPASS except for eSetValueWithoutOverwrite | pdFAIL is returned. In all other cases pdPASS is returned. | p. 101 |
| taskENTER_CRITICAL must not be called from an ISR | taskENTER_CRITICAL() must not be called from an interrupt service routine. | p. 59 |
| Critical section with a max-syscall-priority port leaves higher-priority interrupts enabled | calling taskENTER_CRITICAL() will leave interrupts at and below the interrupt priority set by configMAX_SYSCALL_INTERRUPT_PRIORITY disabled, and all higher priority interrupt enabled. | p. 59 |
| FreeRTOS API must not be called inside a critical section | FreeRTOS API functions must not be called from within a critical section. | p. 60 |
| taskENTER_CRITICAL_FROM_ISR returns the mask to pass back | The return value must be saved so it can be passed into the matching call to taskEXIT_CRITICAL_FROM_ISR(). | p. 63 |
| Interrupts above the max syscall priority cannot call any FreeRTOS API | interrupts that have a priority above configMAX_SYSCALL_INTERRUPT_PRIORITY cannot call any FreeRTOS API functions, even those that end in “FromISR” cannot be used. | p. 342 |
| FromISR functions need an interrupt at or below configMAX_SYSCALL_INTERRUPT_PRIORITY | configMAX_SYSCALL_INTERRUPT_PRIORITY sets the maximum priority of interrupts from which ISR safe FreeRTOS API functions (those that end in “FromISR”) can be called. | p. 341 |
| Task priorities run from zero to configMAX_PRIORITIES minus one | Tasks can be assigned a priority from zero, which is the lowest priority, to (configMAX_PRIORITIES – 1), which is the highest priority. | p. 342 |
| configMINIMAL_STACK_SIZE unit is words | The value is specified in words, not bytes. | p. 343 |
| configTICK_RATE_HZ unit and pdMS_TO_TICKS limit | pdMS_TO_TICKS() can only be used when configTICK_RATE_HZ is less than or equal to 1000. | p. 344 |
| configTOTAL_HEAP_SIZE unit | The size is specified in bytes. | p. 345 |
| configTIMER_TASK_STACK_DEPTH unit | sets the size of the stack (in words, not bytes) allocated to the timer service task. | p. 345 |
| configUSE_16_BIT_TICKS 0 gives a 32-bit tick type | When configUSE_16_BIT_TICKS is set to 0, TickType_t is defined to be an unsigned 32-bit type. | p. 346 |
