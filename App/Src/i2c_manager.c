/**
 * @file i2c_manager.c
 * @brief Implements the i2c manager module.
 */

#include "i2c_manager.h"

#include "FreeRTOS.h"
#include "queue.h"
#include "semphr.h"
#include "task.h"

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

/**
 * @brief Executes i2 cmanager get timestamp us.
 */
static uint32_t I2CManager_GetTimestampUs(void)
{
    return __HAL_TIM_GET_COUNTER(&htim2);
}

/**
 * @brief Executes i2 cmanager map hal status.
 */
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

/**
 * @brief Executes i2 cmanager emit event from isr.
 */
static void I2CManager_EmitEventFromIsr(I2CManager_EventType event_type, uint32_t error_code)
{
    BaseType_t higher_priority_task_woken = pdFALSE;
    I2CManager_Event event;

    event.type = event_type;
    event.timestamp_us = I2CManager_GetTimestampUs();
    event.error_code = error_code;

    if (s_event_hook != NULL)
    {
        s_event_hook(&event, true);
    }

    if (s_event_queue != NULL)
    {
        (void)xQueueSendFromISR(s_event_queue, &event, &higher_priority_task_woken);
    }

    if (s_notify_task != NULL)
    {
        (void)xTaskNotifyFromISR(s_notify_task,
                                 s_notify_bits,
                                 eSetBits,
                                 &higher_priority_task_woken);
    }

    portYIELD_FROM_ISR(higher_priority_task_woken);
}

/**
 * @brief Executes i2 cmanager init.
 */
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
    s_success_count = 0u;
    s_error_count = 0u;
    s_timeout_count = 0u;
    s_fault_pending = false;
    s_pending_fault_code = 0u;
    s_state = I2C_MANAGER_STATE_IDLE;
    (void)Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_CONFIGURE, true, 0u);
}

/**
 * @brief Executes i2 cmanager activate.
 */
Lifecycle_Result I2CManager_Activate(void)
{
    return Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_ACTIVATE, true, 0u);
}

/**
 * @brief Executes i2 cmanager get lifecycle state.
 */
Lifecycle_State I2CManager_GetLifecycleState(void)
{
    return Lifecycle_GetState(&s_lifecycle);
}

/**
 * @brief Executes i2 cmanager process.
 */
void I2CManager_Process(void)
{
    if (s_fault_pending)
    {
        s_fault_pending = false;
        (void)Lifecycle_Fail(&s_lifecycle, s_pending_fault_code);
    }
}

I2C_HandleTypeDef *I2CManager_GetHandle(void)
{
    return &hi2c1;
}

/**
 * @brief Executes i2 cmanager master write.
 */
I2CManager_Status I2CManager_MasterWrite(uint16_t address_7bit, const uint8_t *data, uint16_t size, uint32_t timeout_ms)
{
    HAL_StatusTypeDef hal_status;
    I2CManager_Status status;

    if ((data == NULL) || (size == 0u))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    if ((s_state == I2C_MANAGER_STATE_UNINITIALIZED) || !Lifecycle_IsActive(&s_lifecycle))
    {
        return I2C_MANAGER_STATUS_NOT_READY;
    }

    if (xSemaphoreTake(s_i2c_mutex, pdMS_TO_TICKS(timeout_ms)) != pdTRUE)
    {
        s_timeout_count++;
        return I2C_MANAGER_STATUS_TIMEOUT;
    }

    s_state = I2C_MANAGER_STATE_BUSY_TX;
    hal_status = HAL_I2C_Master_Transmit(&hi2c1, (uint16_t)(address_7bit << 1u), (uint8_t *)data, size, timeout_ms);
    status = I2CManager_MapHalStatus(hal_status);
    s_state = (status == I2C_MANAGER_STATUS_OK) ? I2C_MANAGER_STATE_IDLE : I2C_MANAGER_STATE_ERROR;

    if (status == I2C_MANAGER_STATUS_OK)
    {
        s_success_count++;
    }
/**
 * @brief Executes if.
 */
    else if (status == I2C_MANAGER_STATUS_TIMEOUT)
    {
        s_timeout_count++;
    }
    else
    {
        s_error_count++;
    }

    (void)xSemaphoreGive(s_i2c_mutex);
    return status;
}

/**
 * @brief Executes i2 cmanager master read.
 */
I2CManager_Status I2CManager_MasterRead(uint16_t address_7bit, uint8_t *data, uint16_t size, uint32_t timeout_ms)
{
    HAL_StatusTypeDef hal_status;
    I2CManager_Status status;

    if ((data == NULL) || (size == 0u))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    if ((s_state == I2C_MANAGER_STATE_UNINITIALIZED) || !Lifecycle_IsActive(&s_lifecycle))
    {
        return I2C_MANAGER_STATUS_NOT_READY;
    }

    if (xSemaphoreTake(s_i2c_mutex, pdMS_TO_TICKS(timeout_ms)) != pdTRUE)
    {
        s_timeout_count++;
        return I2C_MANAGER_STATUS_TIMEOUT;
    }

    s_state = I2C_MANAGER_STATE_BUSY_RX;
    hal_status = HAL_I2C_Master_Receive(&hi2c1, (uint16_t)(address_7bit << 1u), data, size, timeout_ms);
    status = I2CManager_MapHalStatus(hal_status);
    s_state = (status == I2C_MANAGER_STATUS_OK) ? I2C_MANAGER_STATE_IDLE : I2C_MANAGER_STATE_ERROR;

    if (status == I2C_MANAGER_STATUS_OK)
    {
        s_success_count++;
    }
/**
 * @brief Executes if.
 */
    else if (status == I2C_MANAGER_STATUS_TIMEOUT)
    {
        s_timeout_count++;
    }
    else
    {
        s_error_count++;
    }

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

    write_status = I2CManager_MasterWrite(address_7bit, tx_data, tx_size, timeout_ms);
    if (write_status != I2C_MANAGER_STATUS_OK)
    {
        return write_status;
    }

    read_status = I2CManager_MasterRead(address_7bit, rx_data, rx_size, timeout_ms);
    return read_status;
}

/**
 * @brief Executes i2 cmanager submit async.
 */
I2CManager_Status I2CManager_SubmitAsync(const I2CManager_Transfer *transfer)
{
    HAL_StatusTypeDef hal_status;

    if ((transfer == NULL) || (transfer->buffer == NULL) || (transfer->length == 0u))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    if ((s_state == I2C_MANAGER_STATE_UNINITIALIZED) || !Lifecycle_IsActive(&s_lifecycle))
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

/**
 * @brief Executes i2 cmanager set event hook.
 */
void I2CManager_SetEventHook(I2CManager_EventHook hook)
{
    s_event_hook = hook;
}

/**
 * @brief Executes i2 cmanager set event queue.
 */
void I2CManager_SetEventQueue(void *queue_handle)
{
    s_event_queue = (QueueHandle_t)queue_handle;
}

/**
 * @brief Executes i2 cmanager set task notify target.
 */
void I2CManager_SetTaskNotifyTarget(void *task_handle, uint32_t notify_bits)
{
    s_notify_task = (TaskHandle_t)task_handle;
    s_notify_bits = notify_bits;
}

/**
 * @brief Executes i2 cmanager get success count.
 */
uint32_t I2CManager_GetSuccessCount(void)
{
    return s_success_count;
}

/**
 * @brief Executes i2 cmanager get error count.
 */
uint32_t I2CManager_GetErrorCount(void)
{
    return s_error_count;
}

/**
 * @brief Executes i2 cmanager get timeout count.
 */
uint32_t I2CManager_GetTimeoutCount(void)
{
    return s_timeout_count;
}

/**
 * @brief Executes hal i2 c master tx cplt callback.
 */
void HAL_I2C_MasterTxCpltCallback(I2C_HandleTypeDef *hi2c)
{
    if (hi2c->Instance != I2C1)
    {
        return;
    }

    s_state = I2C_MANAGER_STATE_IDLE;
    s_success_count++;

    if (s_has_active_transfer && (s_active_transfer.completion_cb != NULL))
    {
        s_active_transfer.completion_cb(I2C_MANAGER_STATUS_OK,
                                        s_active_transfer.context,
                                        I2CManager_GetTimestampUs());
    }

    s_has_active_transfer = false;
    (void)xSemaphoreGiveFromISR(s_i2c_mutex, NULL);
    I2CManager_EmitEventFromIsr(I2C_MANAGER_EVENT_TX_COMPLETE, 0u);
}

/**
 * @brief Executes hal i2 c master rx cplt callback.
 */
void HAL_I2C_MasterRxCpltCallback(I2C_HandleTypeDef *hi2c)
{
    if (hi2c->Instance != I2C1)
    {
        return;
    }

    s_state = I2C_MANAGER_STATE_IDLE;
    s_success_count++;

    if (s_has_active_transfer && (s_active_transfer.completion_cb != NULL))
    {
        s_active_transfer.completion_cb(I2C_MANAGER_STATUS_OK,
                                        s_active_transfer.context,
                                        I2CManager_GetTimestampUs());
    }

    s_has_active_transfer = false;
    (void)xSemaphoreGiveFromISR(s_i2c_mutex, NULL);
    I2CManager_EmitEventFromIsr(I2C_MANAGER_EVENT_RX_COMPLETE, 0u);
}

/**
 * @brief Executes hal i2 c error callback.
 */
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

    if (s_has_active_transfer && (s_active_transfer.completion_cb != NULL))
    {
        s_active_transfer.completion_cb(I2C_MANAGER_STATUS_ERROR,
                                        s_active_transfer.context,
                                        I2CManager_GetTimestampUs());
    }

    s_has_active_transfer = false;
    (void)xSemaphoreGiveFromISR(s_i2c_mutex, NULL);
    I2CManager_EmitEventFromIsr(I2C_MANAGER_EVENT_ERROR, HAL_I2C_GetError(hi2c));
}

/**
 * @brief Executes hal i2 c abort cplt callback.
 */
void HAL_I2C_AbortCpltCallback(I2C_HandleTypeDef *hi2c)
{
    if (hi2c->Instance != I2C1)
    {
        return;
    }

    s_state = I2C_MANAGER_STATE_IDLE;

    if (s_has_active_transfer && (s_active_transfer.completion_cb != NULL))
    {
        s_active_transfer.completion_cb(I2C_MANAGER_STATUS_ERROR,
                                        s_active_transfer.context,
                                        I2CManager_GetTimestampUs());
    }

    s_has_active_transfer = false;
    (void)xSemaphoreGiveFromISR(s_i2c_mutex, NULL);
    I2CManager_EmitEventFromIsr(I2C_MANAGER_EVENT_ABORT, 0u);
}
