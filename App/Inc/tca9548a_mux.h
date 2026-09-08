/**
 * @file tca9548a_mux.h
 * @brief Implements the tca9548a mux module.
 */

#ifndef TCA9548A_MUX_H
#define TCA9548A_MUX_H

#include <stdbool.h>
#include <stdint.h>

#include "i2c_manager.h"

#define TCA9548A_ADDR_0 0x70u
#define TCA9548A_ADDR_1 0x71u
#define TCA9548A_ADDR_2 0x72u
#define TCA9548A_ADDR_3 0x73u
#define TCA9548A_ADDR_4 0x74u
#define TCA9548A_ADDR_5 0x75u
#define TCA9548A_ADDR_6 0x76u
#define TCA9548A_ADDR_7 0x77u

/**
 * @brief Executes tca9548 a init.
 */
void TCA9548A_Init(uint16_t mux_address_7bit);
/**
 * @brief Executes tca9548 a select channel.
 */
I2CManager_Status TCA9548A_SelectChannel(uint8_t channel);
/**
 * @brief Executes tca9548 a select mask.
 */
I2CManager_Status TCA9548A_SelectMask(uint8_t channel_mask);
/**
 * @brief Executes tca9548 a probe.
 */
I2CManager_Status TCA9548A_Probe(uint8_t expected_mask, uint8_t *readback_mask);
/**
 * @brief Executes tca9548 a get selected mask.
 */
uint8_t TCA9548A_GetSelectedMask(void);
/**
 * @brief Executes tca9548 a has selected mask.
 */
bool TCA9548A_HasSelectedMask(void);

#endif /* TCA9548A_MUX_H */
