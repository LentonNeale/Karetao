/**
 * @file tca9548a_mux.c
 * @brief Implements the tca9548a mux module.
 */

#include "tca9548a_mux.h"

#define TCA9548A_DEFAULT_TIMEOUT_MS 10u
#define TCA9548A_MAX_RETRIES 3u

static uint16_t s_mux_addr_7bit = TCA9548A_ADDR_0;
static uint8_t s_selected_mask;
static bool s_has_selected_mask;

/**
 * @brief Executes tca9548 a init.
 */
void TCA9548A_Init(uint16_t mux_address_7bit)
{
    s_mux_addr_7bit = mux_address_7bit;
    s_selected_mask = 0u;
    s_has_selected_mask = false;
}

/**
 * @brief Executes tca9548 a select mask.
 */
I2CManager_Status TCA9548A_SelectMask(uint8_t channel_mask)
{
    uint32_t retry;
    I2CManager_Status status = I2C_MANAGER_STATUS_ERROR;

    if ((channel_mask == 0u) || ((channel_mask & 0xFFu) != channel_mask))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    if (s_has_selected_mask && (s_selected_mask == channel_mask))
    {
        return I2C_MANAGER_STATUS_OK;
    }

    for (retry = 0u; retry < TCA9548A_MAX_RETRIES; retry++)
    {
        status = I2CManager_MasterWrite(s_mux_addr_7bit,
                                        &channel_mask,
                                        1u,
                                        TCA9548A_DEFAULT_TIMEOUT_MS);
        if (status == I2C_MANAGER_STATUS_OK)
        {
            s_selected_mask = channel_mask;
            s_has_selected_mask = true;
            return I2C_MANAGER_STATUS_OK;
        }
    }

    return status;
}

/**
 * @brief Executes tca9548 a probe.
 */
I2CManager_Status TCA9548A_Probe(uint8_t expected_mask, uint8_t *readback_mask)
{
    I2CManager_Status status;
    uint8_t mux_state = 0u;

    if ((expected_mask == 0u) || (readback_mask == NULL))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    status = I2CManager_MasterWrite(s_mux_addr_7bit,
                                    &expected_mask,
                                    1u,
                                    TCA9548A_DEFAULT_TIMEOUT_MS);
    if (status != I2C_MANAGER_STATUS_OK)
    {
        return status;
    }

    status = I2CManager_MasterRead(s_mux_addr_7bit,
                                   &mux_state,
                                   1u,
                                   TCA9548A_DEFAULT_TIMEOUT_MS);
    if (status != I2C_MANAGER_STATUS_OK)
    {
        return status;
    }

    *readback_mask = mux_state;
    s_selected_mask = mux_state;
    s_has_selected_mask = true;

    return I2C_MANAGER_STATUS_OK;
}

/**
 * @brief Executes tca9548 a select channel.
 */
I2CManager_Status TCA9548A_SelectChannel(uint8_t channel)
{
    uint8_t channel_mask;

    if (channel > 7u)
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    channel_mask = (uint8_t)(1u << channel);
    return TCA9548A_SelectMask(channel_mask);
}

/**
 * @brief Executes tca9548 a get selected mask.
 */
uint8_t TCA9548A_GetSelectedMask(void)
{
    return s_selected_mask;
}

/**
 * @brief Executes tca9548 a has selected mask.
 */
bool TCA9548A_HasSelectedMask(void)
{
    return s_has_selected_mask;
}
