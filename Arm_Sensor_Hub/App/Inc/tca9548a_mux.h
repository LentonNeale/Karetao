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

void TCA9548A_Init(uint16_t mux_address_7bit);
I2CManager_Status TCA9548A_SelectChannelWriteRead(uint8_t channel,
                                                  uint16_t target_address_7bit,
                                                  const uint8_t *tx_data,
                                                  uint16_t tx_size,
                                                  uint8_t *rx_data,
                                                  uint16_t rx_size,
                                                  uint32_t timeout_ms);
I2CManager_Status TCA9548A_Probe(uint8_t expected_mask, uint8_t *readback_mask);

#endif /* TCA9548A_MUX_H */
