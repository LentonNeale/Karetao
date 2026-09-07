#include "tca9548a_mux.h"

#include <stddef.h>

#define TCA9548A_DEFAULT_TIMEOUT_MS 10u
#define TCA9548A_MAX_RETRIES 3u

static uint16_t s_mux_addr_7bit = TCA9548A_ADDR_0;
static uint8_t s_selected_mask;
static bool s_has_selected_mask;

void TCA9548A_Init(uint16_t mux_address_7bit)
{
    s_mux_addr_7bit = mux_address_7bit;
    s_selected_mask = 0u;
    s_has_selected_mask = false;
}

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

I2CManager_Status TCA9548A_Probe(uint8_t expected_mask, uint8_t *readback_mask)
{
    I2CManager_Status status;
    uint8_t mux_state = 0u;

    if ((expected_mask == 0u) || (readback_mask == NULL))
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    status = I2CManager_MasterWriteRead(s_mux_addr_7bit,
                                        &expected_mask,
                                        1u,
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

I2CManager_Status TCA9548A_SelectChannelWriteRead(uint8_t channel,
                                                  uint16_t target_address_7bit,
                                                  const uint8_t *tx_data,
                                                  uint16_t tx_size,
                                                  uint8_t *rx_data,
                                                  uint16_t rx_size,
                                                  uint32_t timeout_ms)
{
    uint8_t channel_mask;
    I2CManager_Status status;

    if (channel > 7u)
    {
        return I2C_MANAGER_STATUS_BAD_ARG;
    }

    channel_mask = (uint8_t)(1u << channel);
    status = I2CManager_WriteThenWriteRead(s_mux_addr_7bit,
                                           &channel_mask,
                                           1u,
                                           target_address_7bit,
                                           tx_data,
                                           tx_size,
                                           rx_data,
                                           rx_size,
                                           timeout_ms);
    if (status == I2C_MANAGER_STATUS_OK)
    {
        s_selected_mask = channel_mask;
        s_has_selected_mask = true;
    }

    return status;
}

uint8_t TCA9548A_GetSelectedMask(void)
{
    return s_selected_mask;
}

bool TCA9548A_HasSelectedMask(void)
{
    return s_has_selected_mask;
}
