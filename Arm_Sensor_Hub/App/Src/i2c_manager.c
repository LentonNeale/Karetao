#include "i2c_manager.h"

#include <stddef.h>

#include "FreeRTOS.h"
#include "semphr.h"

typedef enum
{
    I2C_MANAGER_STATE_UNINITIALIZED = 0,
    I2C_MANAGER_STATE_IDLE,
    I2C_MANAGER_STATE_BUSY_TX,
    I2C_MANAGER_STATE_BUSY_RX,
    I2C_MANAGER_STATE_ERROR
} I2CManager_State;

extern I2C_HandleTypeDef hi2c1;

/* All state is written from task context only: every transfer is a blocking HAL call
 * and no I2C interrupt is enabled, so nothing here needs volatile. */
static StaticSemaphore_t s_i2c_mutex_storage;
static SemaphoreHandle_t s_i2c_mutex;
static I2CManager_State s_state = I2C_MANAGER_STATE_UNINITIALIZED;
static Lifecycle_Record s_lifecycle;
static uint32_t s_success_count;
static uint32_t s_error_count;
static uint32_t s_timeout_count;

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

    s_success_count = 0u;
    s_error_count = 0u;
    s_timeout_count = 0u;
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
