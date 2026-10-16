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

void I2CManager_Init(void);
Lifecycle_Result I2CManager_Activate(void);
Lifecycle_State I2CManager_GetLifecycleState(void);

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

uint32_t I2CManager_GetSuccessCount(void);
uint32_t I2CManager_GetErrorCount(void);
uint32_t I2CManager_GetTimeoutCount(void);

#endif /* I2C_MANAGER_H */
