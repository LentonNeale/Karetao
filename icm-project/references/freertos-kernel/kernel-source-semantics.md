# Queue, mutex, notify and port semantics (FreeRTOS Kernel V10.3.1 source)

Source files: `queue.c`, `tasks.c`, `portable/GCC/ARM_CM4F/port.c`, `portable/MemMang/heap_4.c`, `include/semphr.h`, `include/task.h`, `include/queue.h` at tag V10.3.1-kernel-only (identical to the vendored copies apart from line endings). Citations are function or macro names in quotes.

| Rule | Value | Citation |
|---|---|---|
| A mutex has queue type queueQUEUE_IS_MUTEX | #define queueQUEUE_IS_MUTEX				NULL | "queueQUEUE_IS_MUTEX" |
| A mutex is created with no holder | pxNewQueue->u.xSemaphore.xMutexHolder = NULL; | "xQueueGenericCreateStatic" |
| Taking a mutex records the running task as holder | pxQueue->u.xSemaphore.xMutexHolder = pvTaskIncrementMutexHeldCount(); | "xQueueSemaphoreTake" |
| Giving a mutex (task path) disinherits priority and clears the holder | The mutex is no longer being held. xReturn = xTaskPriorityDisinherit( pxQueue->u.xSemaphore.xMutexHolder ); pxQueue->u.xSemaphore.xMutexHolder = NULL; | "prvCopyDataToQueue" |
| Disinherit asserts the giver is the running task and that it holds a mutex | configASSERT( pxTCB == pxCurrentTCB ); configASSERT( pxTCB->uxMutexesHeld ); | "xTaskPriorityDisinherit" |
| Kernel comment: a mutex held by a task cannot be given from an interrupt | If the mutex is held by a task then it cannot be given from an interrupt | "xTaskPriorityDisinherit" |
| xQueueGiveFromISR asserts that a mutex has no holder | configASSERT( !( ( pxQueue->uxQueueType == queueQUEUE_IS_MUTEX ) && ( pxQueue->u.xSemaphore.xMutexHolder != NULL ) ) ); | "xQueueGiveFromISR" |
| Kernel comment on the same assertion | Normally a mutex would not be given from an interrupt, especially if there is a mutex holder, as priority inheritance makes no sense for an interrupts, only tasks. | "xQueueGiveFromISR" |
| xQueueGiveFromISR also asserts item size 0 and checks interrupt priority | configASSERT( pxQueue->uxItemSize == 0 ); ... portASSERT_IF_INTERRUPT_PRIORITY_INVALID(); | "xQueueGiveFromISR" |
| Only FromISR functions may be called from interrupts at or below the maximum system call priority | Only FreeRTOS functions that end in FromISR can be called from interrupts that have been assigned a priority at or (logically) below the maximum system call interrupt priority. | "xQueueGiveFromISR" |
| xQueueGiveFromISR does not give when the semaphore count is already at its length | if( uxMessagesWaiting < pxQueue->uxLength ) | "xQueueGiveFromISR" |
| Port interrupt-priority check asserts the ISR priority is numerically at or above the maximum system call value | configASSERT( ucCurrentPriority >= ucMaxSysCallPriority ); | "vPortValidateInterruptPriority" |
| Port check requires all priority bits to be pre-emption bits (priority group) | configASSERT( ( portAIRCR_REG & portPRIORITY_GROUP_MASK ) <= ulMaxPRIGROUPValue ); | "vPortValidateInterruptPriority" |
| Port requires configMAX_SYSCALL_INTERRUPT_PRIORITY non-zero | configMAX_SYSCALL_INTERRUPT_PRIORITY must not be set to 0. | "xPortStartScheduler" |
| Task notification eSetBits ORs the value into the notified value | case eSetBits	: pxTCB->ulNotifiedValue gets ulValue ORed in; | "xTaskGenericNotify" |
| xPortSysTickHandler runs at the lowest interrupt priority and increments the RTOS tick | The SysTick runs at the lowest interrupt priority, so when this interrupt executes all interrupts must be unmasked. | "xPortSysTickHandler" |
| Kernel tick count is incremented by xTaskIncrementTick from the tick handler | Increment the RTOS tick. if( xTaskIncrementTick() != pdFALSE ) | "xPortSysTickHandler" |
