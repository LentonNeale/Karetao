/**
 * @file i2c_manager.h
 * @brief Implements the i2c manager module.
 */

#ifndef I2C_MANAGER_H
#define I2C_MANAGER_H

#include <stdbool.h>
#include <stdint.h>

#include "stm32f4xx_hal.h"
#include "lifecycle.h"

typedef enum
{
    I2C_MANAGER_STATUS_OK = 0,
    I2C_MANAGER_STATUS_ERROR,
    I2C_MANAGER_STATUS_BUSY,
    I2C_MANAGER_STATUS_TIMEOUT,
    I2C_MANAGER_STATUS_BAD_ARG,
    I2C_MANAGER_STATUS_NOT_READY
} I2CManager_Status;

typedef enum
{
    I2C_MANAGER_DIR_WRITE = 0,
    I2C_MANAGER_DIR_READ = 1
} I2CManager_Direction;

typedef enum
{
    I2C_MANAGER_EVENT_TX_COMPLETE = 0,
    I2C_MANAGER_EVENT_RX_COMPLETE,
    I2C_MANAGER_EVENT_ERROR,
    I2C_MANAGER_EVENT_ABORT
} I2CManager_EventType;

typedef struct
{
    I2CManager_EventType type;
    uint64_t timestamp_us;
    uint32_t error_code;
} I2CManager_Event;

typedef void (*I2CManager_CompletionCallback)(I2CManager_Status status, void *context, uint64_t timestamp_us);

typedef void (*I2CManager_EventHook)(const I2CManager_Event *event, bool from_isr);

typedef struct
{
    uint16_t address_7bit;
    uint8_t *buffer;
    uint16_t length;
    I2CManager_Direction direction;
    I2CManager_CompletionCallback completion_cb;
    void *context;
} I2CManager_Transfer;

void I2CManager_Init(void);
Lifecycle_Result I2CManager_Activate(void);
Lifecycle_State I2CManager_GetLifecycleState(void);
void I2CManager_Process(void);
I2C_HandleTypeDef *I2CManager_GetHandle(void);

I2CManager_Status I2CManager_MasterWrite(uint16_t address_7bit, const uint8_t *data, uint16_t size, uint32_t timeout_ms);
I2CManager_Status I2CManager_MasterRead(uint16_t address_7bit, uint8_t *data, uint16_t size, uint32_t timeout_ms);
I2CManager_Status I2CManager_MasterWriteRead(uint16_t address_7bit,
                                              const uint8_t *tx_data,
                                              uint16_t tx_size,
                                              uint8_t *rx_data,
                                              uint16_t rx_size,
                                              uint32_t timeout_ms);
I2CManager_Status I2CManager_WriteThenWriteRead(uint16_t first_address_7bit,
                                                 const uint8_t *first_tx_data,
                                                 uint16_t first_tx_size,
                                                 uint16_t second_address_7bit,
                                                 const uint8_t *second_tx_data,
                                                 uint16_t second_tx_size,
                                                 uint8_t *rx_data,
                                                 uint16_t rx_size,
                                                 uint32_t timeout_ms);
I2CManager_Status I2CManager_SubmitAsync(const I2CManager_Transfer *transfer);

void I2CManager_SetEventHook(I2CManager_EventHook hook);
void I2CManager_SetEventQueue(void *queue_handle);
void I2CManager_SetTaskNotifyTarget(void *task_handle, uint32_t notify_bits);

uint32_t I2CManager_GetSuccessCount(void);
uint32_t I2CManager_GetErrorCount(void);
uint32_t I2CManager_GetTimeoutCount(void);

#endif /* I2C_MANAGER_H */
