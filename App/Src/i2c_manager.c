#include "i2c_manager.h"

#include <stddef.h>

#include "FreeRTOS.h"
#include "queue.h"
#include "semphr.h"
#include "task.h"
#include "time_service.h"

typedef enum
{
    I2C_MANAGER_STATE_UNINITIALIZED = 0,
    I2C_MANAGER_STATE_IDLE,
    I2C_MANAGER_STATE_BUSY_TX,
    I2C_MANAGER_STATE_BUSY_RX,
    I2C_MANAGER_STATE_ERROR
} I2CManager_State;

extern I2C_HandleTypeDef hi2c1;
extern TIM_HandleTypeDef htim2;

static StaticSemaphore_t s_i2c_mutex_storage;
static SemaphoreHandle_t s_i2c_mutex;
static volatile I2CManager_State s_state = I2C_MANAGER_STATE_UNINITIALIZED;
static Lifecycle_Record s_lifecycle;
static volatile uint32_t s_success_count;
static volatile uint32_t s_error_count;
static volatile uint32_t s_timeout_count;
static volatile bool s_fault_pending;
static volatile uint32_t s_pending_fault_code;

static I2CManager_EventHook s_event_hook;
static QueueHandle_t s_event_queue;
static TaskHandle_t s_notify_task;
static uint32_t s_notify_bits;
static I2CManager_Transfer s_active_transfer;
static bool s_has_active_transfer;

typedef struct
{
    I2CManager_EventType event_type;
    uint32_t error_code;
    I2CManager_Status completion_status;
    I2CManager_CompletionCallback completion_cb;
    void *completion_context;
    bool has_completion;
} I2CManager_DispatchItem;

#define I2C_MANAGER_DISPATCH_QUEUE_CAPACITY 4u

static I2CManager_DispatchItem s_dispatch_queue[I2C_MANAGER_DISPATCH_QUEUE_CAPACITY];
static volatile uint8_t s_dispatch_head;
static volatile uint8_t s_dispatch_tail;

static I2CManager_Status I2CManager_MapHalStatus(HAL_StatusTypeDef hal_status);

static bool I2CManager_IsReady(void)
{
    return (s_state != I2C_MANAGER_STATE_UNINITIALIZED) && Lifecycle_IsActive(&s_lifecycle);
}

static I2CManager_Status I2CManager_TakeMutex(uint32_t timeout_ms)
{
    if (xSemaphoreTake(s_i2c_mutex, pdMS_TO_TICKS(timeout_ms)) != pdTRUE)
    {
        s_timeout_count++;
        return I2C_MANAGER_STATUS_TIMEOUT;
    }

    return I2C_MANAGER_STATUS_OK;
}

static I2CManager_Status I2CManager_MasterWriteLocked(uint16_t address_7bit,
                                                      const uint8_t *data,
                                                      uint16_t size,
                                                      uint32_t timeout_ms)
{
    HAL_StatusTypeDef hal_status;
    I2CManager_Status status;

    s_state = I2C_MANAGER_STATE_BUSY_TX;
    hal_status = HAL_I2C_Master_Transmit(&hi2c1, (uint16_t)(address_7bit << 1u), (uint8_t *)data, size, timeout_ms);
    status = I2CManager_MapHalStatus(hal_status);
    s_state = (status == I2C_MANAGER_STATUS_OK) ? I2C_MANAGER_STATE_IDLE : I2C_MANAGER_STATE_ERROR;

    if (status == I2C_MANAGER_STATUS_OK)
    {
        s_success_count++;
    }
    else if (status == I2C_MANAGER_STATUS_TIMEOUT)
    {
        s_timeout_count++;
    }
    else
    {
        s_error_count++;
    }

    return status;
}

static I2CManager_Status I2CManager_MasterReadLocked(uint16_t address_7bit,
                                                     uint8_t *data,
                                                     uint16_t size,
                                                     uint32_t timeout_ms)
{
    HAL_StatusTypeDef hal_status;
    I2CManager_Status status;

    s_state = I2C_MANAGER_STATE_BUSY_RX;
    hal_status = HAL_I2C_Master_Receive(&hi2c1, (uint16_t)(address_7bit << 1u), data, size, timeout_ms);
    status = I2CManager_MapHalStatus(hal_status);
    s_state = (status == I2C_MANAGER_STATUS_OK) ? I2C_MANAGER_STATE_IDLE : I2C_MANAGER_STATE_ERROR;

    if (status == I2C_MANAGER_STATUS_OK)
    {
        s_success_count++;
    }
    else if (status == I2C_MANAGER_STATUS_TIMEOUT)
    {
        s_timeout_count++;
    }
    else
    {
        s_error_count++;
    }

    return status;
}

static void I2CManager_QueueDispatchFromIsr(I2CManager_EventType event_type,
                                            uint32_t error_code,
                                            I2CManager_Status completion_status,
                                            I2CManager_CompletionCallback completion_cb,
                                            void *completion_context,
                                            bool has_completion)
{
    UBaseType_t saved_interrupt_status;
    uint8_t head;
    uint8_t next_head;

    saved_interrupt_status = taskENTER_CRITICAL_FROM_ISR();
    head = s_dispatch_head;
    next_head = (uint8_t)((head + 1u) % I2C_MANAGER_DISPATCH_QUEUE_CAPACITY);
    if (next_head != s_dispatch_tail) {
        s_dispatch_queue[head].event_type = event_type;
        s_dispatch_queue[head].error_code = error_code;
        s_dispatch_queue[head].completion_status = completion_status;
        s_dispatch_queue[head].completion_cb = completion_cb;
        s_dispatch_queue[head].completion_context = completion_context;
        s_dispatch_queue[head].has_completion = has_completion;
        s_dispatch_head = next_head;
    }
    taskEXIT_CRITICAL_FROM_ISR(saved_interrupt_status);
}

static bool I2CManager_PopDispatch(I2CManager_DispatchItem *item)
{
    bool has_item = false;

    if (item == NULL) {
        return false;
    }

    taskENTER_CRITICAL();
    if (s_dispatch_tail != s_dispatch_head) {
        *item = s_dispatch_queue[s_dispatch_tail];
        s_dispatch_tail = (uint8_t)((s_dispatch_tail + 1u) % I2C_MANAGER_DISPATCH_QUEUE_CAPACITY);
        has_item = true;
    }
    taskEXIT_CRITICAL();
    return has_item;
}

static I2CManager_Status I2CManager_MapHalStatus(HAL_StatusTypeDef hal_status)
{
    switch (hal_status)
    {
    case HAL_OK:
        return I2C_MANAGER_STATUS_OK;
    case HAL_TIMEOUT:
        return I2C_MANAGER_STATUS_TIMEOUT;
    case HAL_BUSY:
        return I2C_MANAGER_STATUS_BUSY;
    case HAL_ERROR:
    default:
        return I2C_MANAGER_STATUS_ERROR;
    }
}

static void I2CManager_DispatchEvent(const I2CManager_DispatchItem *item)
{
    I2CManager_Event event;
    uint64_t timestamp_us;

    if (item == NULL) {
        return;
    }

    timestamp_us = TimeService_NowUs();
    event.type = item->event_type;
    event.timestamp_us = timestamp_us;
    event.error_code = item->error_code;

    if (s_event_hook != NULL)
    {
        s_event_hook(&event, false);
    }

    if (s_event_queue != NULL)
    {
        (void)xQueueSend(s_event_queue, &event, 0u);
    }

    if (s_notify_task != NULL)
    {
        (void)xTaskNotify(s_notify_task, s_notify_bits, eSetBits);
    }

    if (item->has_completion && (item->completion_cb != NULL)) {
        item->completion_cb(item->completion_status, item->completion_context, timestamp_us);
    }
}

void I2CManager_Init(void)
{
    if (s_state != I2C_MANAGER_STATE_UNINITIALIZED)
    {
        return;
    }

    Lifecycle_Init(&s_lifecycle, "I2C1");

    s_i2c_mutex = xSemaphoreCreateMutexStatic(&s_i2c_mutex_storage);
    if (s_i2c_mutex == NULL)
    {
        s_state = I2C_MANAGER_STATE_ERROR;
        (void)Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_CONFIGURE, false, 1u);
        return;
    }

    s_has_active_transfer = false;
    s_dispatch_head = 0u;
    s_dispatch_tail = 0u;
    s_success_count = 0u;
    s_error_count = 0u;
    s_timeout_count = 0u;
    s_fault_pending = false;
    s_pending_fault_code = 0u;
    s_state = I2C_MANAGER_STATE_IDLE;
    (void)Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_CONFIGURE, true, 0u);
}

Lifecycle_Result I2CManager_Activate(void)
{
    return Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_ACTIVATE, true, 0u);
}

Lifecycle_State I2CManager_GetLifecycleState(void)
{
    return Lifecycle_GetState(&s_lifecycle);
}

void I2CManager_Process(void)
{
    I2CManager_DispatchItem item;

    if (s_fault_pending)
    {
        s_fault_pending = false;
        (void)Lifecycle_Fail(&s_lifecycle, s_pending_fault_code);
    }

    while (I2CManager_PopDispatch(&item)) {
        I2CManager_DispatchEvent(&item);
    }
}

I2C_HandleTypeDef *I2CManager_GetHandle(void)
{
    return &hi2c1;
}

I2CManager_Status I2CManager_MasterWrite(uint16_t address_7bit, const uint8_t *data, uint16_t size, uint32_t timeout_ms)
{
    HAL_StatusTypeDef hal_status;
    I2CManager_Status status;

    if ((data == NULL) || (size == 0u))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    if (!I2CManager_IsReady())
    {
        return I2C_MANAGER_STATUS_NOT_READY;
    }

    status = I2CManager_TakeMutex(timeout_ms);
    if (status != I2C_MANAGER_STATUS_OK)
    {
        return status;
    }

    status = I2CManager_MasterWriteLocked(address_7bit, data, size, timeout_ms);
    (void)xSemaphoreGive(s_i2c_mutex);
    return status;
}

I2CManager_Status I2CManager_MasterRead(uint16_t address_7bit, uint8_t *data, uint16_t size, uint32_t timeout_ms)
{
    HAL_StatusTypeDef hal_status;
    I2CManager_Status status;

    if ((data == NULL) || (size == 0u))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    if (!I2CManager_IsReady())
    {
        return I2C_MANAGER_STATUS_NOT_READY;
    }

    status = I2CManager_TakeMutex(timeout_ms);
    if (status != I2C_MANAGER_STATUS_OK)
    {
        return status;
    }

    status = I2CManager_MasterReadLocked(address_7bit, data, size, timeout_ms);
    (void)xSemaphoreGive(s_i2c_mutex);
    return status;
}

I2CManager_Status I2CManager_MasterWriteRead(uint16_t address_7bit,
                                              const uint8_t *tx_data,
                                              uint16_t tx_size,
                                              uint8_t *rx_data,
                                              uint16_t rx_size,
                                              uint32_t timeout_ms)
{
    I2CManager_Status write_status;
    I2CManager_Status read_status;

    if ((tx_data == NULL) || (tx_size == 0u) || (rx_data == NULL) || (rx_size == 0u))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    if (!I2CManager_IsReady())
    {
        return I2C_MANAGER_STATUS_NOT_READY;
    }

    write_status = I2CManager_TakeMutex(timeout_ms);
    if (write_status != I2C_MANAGER_STATUS_OK)
    {
        return write_status;
    }

    write_status = I2CManager_MasterWriteLocked(address_7bit, tx_data, tx_size, timeout_ms);
    if (write_status != I2C_MANAGER_STATUS_OK)
    {
        (void)xSemaphoreGive(s_i2c_mutex);
        return write_status;
    }

    read_status = I2CManager_MasterReadLocked(address_7bit, rx_data, rx_size, timeout_ms);
    (void)xSemaphoreGive(s_i2c_mutex);
    return read_status;
}

I2CManager_Status I2CManager_WriteThenWriteRead(uint16_t first_address_7bit,
                                                const uint8_t *first_tx_data,
                                                uint16_t first_tx_size,
                                                uint16_t second_address_7bit,
                                                const uint8_t *second_tx_data,
                                                uint16_t second_tx_size,
                                                uint8_t *rx_data,
                                                uint16_t rx_size,
                                                uint32_t timeout_ms)
{
    I2CManager_Status status;

    if ((first_tx_data == NULL) || (first_tx_size == 0u) ||
        (second_tx_data == NULL) || (second_tx_size == 0u) ||
        (rx_data == NULL) || (rx_size == 0u))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    if (!I2CManager_IsReady())
    {
        return I2C_MANAGER_STATUS_NOT_READY;
    }

    status = I2CManager_TakeMutex(timeout_ms);
    if (status != I2C_MANAGER_STATUS_OK)
    {
        return status;
    }

    status = I2CManager_MasterWriteLocked(first_address_7bit, first_tx_data, first_tx_size, timeout_ms);
    if (status == I2C_MANAGER_STATUS_OK)
    {
        status = I2CManager_MasterWriteLocked(second_address_7bit, second_tx_data, second_tx_size, timeout_ms);
    }
    if (status == I2C_MANAGER_STATUS_OK)
    {
        status = I2CManager_MasterReadLocked(second_address_7bit, rx_data, rx_size, timeout_ms);
    }

    (void)xSemaphoreGive(s_i2c_mutex);
    return status;
}

I2CManager_Status I2CManager_SubmitAsync(const I2CManager_Transfer *transfer)
{
    HAL_StatusTypeDef hal_status;

    if ((transfer == NULL) || (transfer->buffer == NULL) || (transfer->length == 0u))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    if (!I2CManager_IsReady())
    {
        return I2C_MANAGER_STATUS_NOT_READY;
    }

    if (xSemaphoreTake(s_i2c_mutex, 0u) != pdTRUE)
    {
        return I2C_MANAGER_STATUS_BUSY;
    }

    if ((s_state == I2C_MANAGER_STATE_BUSY_TX) || (s_state == I2C_MANAGER_STATE_BUSY_RX))
    {
        (void)xSemaphoreGive(s_i2c_mutex);
        return I2C_MANAGER_STATUS_BUSY;
    }

    s_active_transfer = *transfer;
    s_has_active_transfer = true;

    if (transfer->direction == I2C_MANAGER_DIR_WRITE)
    {
        s_state = I2C_MANAGER_STATE_BUSY_TX;
        hal_status = HAL_I2C_Master_Transmit_IT(&hi2c1,
                                                 (uint16_t)(transfer->address_7bit << 1u),
                                                 transfer->buffer,
                                                 transfer->length);
    }
    else
    {
        s_state = I2C_MANAGER_STATE_BUSY_RX;
        hal_status = HAL_I2C_Master_Receive_IT(&hi2c1,
                                                (uint16_t)(transfer->address_7bit << 1u),
                                                transfer->buffer,
                                                transfer->length);
    }

    if (hal_status != HAL_OK)
    {
        s_state = I2C_MANAGER_STATE_ERROR;
        s_has_active_transfer = false;
        s_error_count++;
        (void)xSemaphoreGive(s_i2c_mutex);
        return I2CManager_MapHalStatus(hal_status);
    }

    return I2C_MANAGER_STATUS_OK;
}

void I2CManager_SetEventHook(I2CManager_EventHook hook)
{
    s_event_hook = hook;
}

void I2CManager_SetEventQueue(void *queue_handle)
{
    s_event_queue = (QueueHandle_t)queue_handle;
}

void I2CManager_SetTaskNotifyTarget(void *task_handle, uint32_t notify_bits)
{
    s_notify_task = (TaskHandle_t)task_handle;
    s_notify_bits = notify_bits;
}

uint32_t I2CManager_GetSuccessCount(void)
{
    return s_success_count;
}

uint32_t I2CManager_GetErrorCount(void)
{
    return s_error_count;
}

uint32_t I2CManager_GetTimeoutCount(void)
{
    return s_timeout_count;
}

void HAL_I2C_MasterTxCpltCallback(I2C_HandleTypeDef *hi2c)
{
    if (hi2c->Instance != I2C1)
    {
        return;
    }

    s_state = I2C_MANAGER_STATE_IDLE;
    s_success_count++;
    I2CManager_QueueDispatchFromIsr(I2C_MANAGER_EVENT_TX_COMPLETE,
                                    0u,
                                    I2C_MANAGER_STATUS_OK,
                                    s_has_active_transfer ? s_active_transfer.completion_cb : NULL,
                                    s_has_active_transfer ? s_active_transfer.context : NULL,
                                    s_has_active_transfer);
    s_has_active_transfer = false;
    (void)xSemaphoreGiveFromISR(s_i2c_mutex, NULL);
}

void HAL_I2C_MasterRxCpltCallback(I2C_HandleTypeDef *hi2c)
{
    if (hi2c->Instance != I2C1)
    {
        return;
    }

    s_state = I2C_MANAGER_STATE_IDLE;
    s_success_count++;
    I2CManager_QueueDispatchFromIsr(I2C_MANAGER_EVENT_RX_COMPLETE,
                                    0u,
                                    I2C_MANAGER_STATUS_OK,
                                    s_has_active_transfer ? s_active_transfer.completion_cb : NULL,
                                    s_has_active_transfer ? s_active_transfer.context : NULL,
                                    s_has_active_transfer);
    s_has_active_transfer = false;
    (void)xSemaphoreGiveFromISR(s_i2c_mutex, NULL);
}

void HAL_I2C_ErrorCallback(I2C_HandleTypeDef *hi2c)
{
    if (hi2c->Instance != I2C1)
    {
        return;
    }

    s_state = I2C_MANAGER_STATE_ERROR;
    s_pending_fault_code = HAL_I2C_GetError(hi2c);
    s_fault_pending = true;
    s_error_count++;
    I2CManager_QueueDispatchFromIsr(I2C_MANAGER_EVENT_ERROR,
                                    s_pending_fault_code,
                                    I2C_MANAGER_STATUS_ERROR,
                                    s_has_active_transfer ? s_active_transfer.completion_cb : NULL,
                                    s_has_active_transfer ? s_active_transfer.context : NULL,
                                    s_has_active_transfer);
    s_has_active_transfer = false;
    (void)xSemaphoreGiveFromISR(s_i2c_mutex, NULL);
}

void HAL_I2C_AbortCpltCallback(I2C_HandleTypeDef *hi2c)
{
    if (hi2c->Instance != I2C1)
    {
        return;
    }

    s_state = I2C_MANAGER_STATE_IDLE;
    I2CManager_QueueDispatchFromIsr(I2C_MANAGER_EVENT_ABORT,
                                    0u,
                                    I2C_MANAGER_STATUS_ERROR,
                                    s_has_active_transfer ? s_active_transfer.completion_cb : NULL,
                                    s_has_active_transfer ? s_active_transfer.context : NULL,
                                    s_has_active_transfer);
    s_has_active_transfer = false;
    (void)xSemaphoreGiveFromISR(s_i2c_mutex, NULL);
}
