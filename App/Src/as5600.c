#include "as5600.h"

#include "tca9548a_mux.h"
#include "time_service.h"

#define AS5600_REG_STATUS 0x0Bu
#define AS5600_REG_RAW_ANGLE_MSB 0x0Cu
#define AS5600_REG_ANGLE_MSB 0x0Eu
#define AS5600_REG_AGC 0x1Au
#define AS5600_REG_MAGNITUDE_MSB 0x1Bu

#define AS5600_DEFAULT_TIMEOUT_MS 10u

static AS5600_Status AS5600_MapI2CStatus(I2CManager_Status status)
{
    switch (status)
    {
    case I2C_MANAGER_STATUS_OK:
        return AS5600_STATUS_OK;
    case I2C_MANAGER_STATUS_BUSY:
        return AS5600_STATUS_BUSY;
    case I2C_MANAGER_STATUS_TIMEOUT:
        return AS5600_STATUS_TIMEOUT;
    case I2C_MANAGER_STATUS_BAD_ARG:
        return AS5600_STATUS_BAD_ARG;
    case I2C_MANAGER_STATUS_NOT_READY:
        return AS5600_STATUS_NOT_READY;
    case I2C_MANAGER_STATUS_ERROR:
    default:
        return AS5600_STATUS_ERROR;
    }
}

static AS5600_Status AS5600_SelectDeviceChannel(const AS5600_Device *dev)
{
    return AS5600_MapI2CStatus(TCA9548A_SelectChannel(dev->mux_channel));
}

static AS5600_Status AS5600_ReadRegisterBlock(const AS5600_Device *dev,
                                              uint8_t start_reg,
                                              uint8_t *buffer,
                                              uint16_t size)
{
    I2CManager_Status i2c_status;

    if ((dev == NULL) || (buffer == NULL) || (size == 0u))
    {
        return AS5600_STATUS_BAD_ARG;
    }

    if (AS5600_SelectDeviceChannel(dev) != AS5600_STATUS_OK)
    {
        return AS5600_STATUS_ERROR;
    }

    i2c_status = I2CManager_MasterWriteRead(dev->i2c_addr_7bit,
                                            &start_reg,
                                            1u,
                                            buffer,
                                            size,
                                            dev->timeout_ms);
    if (i2c_status != I2C_MANAGER_STATUS_OK)
    {
        return AS5600_MapI2CStatus(i2c_status);
    }

    return AS5600_STATUS_OK;
}

void AS5600_InitDevice(AS5600_Device *dev, uint8_t mux_channel)
{
    if (dev == NULL)
    {
        return;
    }

    dev->i2c_addr_7bit = AS5600_I2C_ADDR_7BIT;
    dev->mux_channel = mux_channel;
    dev->timeout_ms = AS5600_DEFAULT_TIMEOUT_MS;
}

AS5600_Status AS5600_ReadRawAngle(const AS5600_Device *dev, uint16_t *raw_angle, uint64_t *timestamp_us)
{
    uint8_t data[2];
    AS5600_Status status;

    if (raw_angle == NULL)
    {
        return AS5600_STATUS_BAD_ARG;
    }

    status = AS5600_ReadRegisterBlock(dev, AS5600_REG_RAW_ANGLE_MSB, data, 2u);
    if (status != AS5600_STATUS_OK)
    {
        return status;
    }

    *raw_angle = (uint16_t)(((uint16_t)data[0] << 8u) | data[1]);
    *raw_angle &= AS5600_RAW_ANGLE_MAX;
    if (timestamp_us != NULL)
    {
        *timestamp_us = TimeService_NowUs();
    }

    return AS5600_STATUS_OK;
}

AS5600_Status AS5600_ReadAngle(const AS5600_Device *dev, uint16_t *angle, uint64_t *timestamp_us)
{
    uint8_t data[2];
    AS5600_Status status;

    if (angle == NULL)
    {
        return AS5600_STATUS_BAD_ARG;
    }

    status = AS5600_ReadRegisterBlock(dev, AS5600_REG_ANGLE_MSB, data, 2u);
    if (status != AS5600_STATUS_OK)
    {
        return status;
    }

    *angle = (uint16_t)(((uint16_t)data[0] << 8u) | data[1]);
    *angle &= AS5600_RAW_ANGLE_MAX;
    if (timestamp_us != NULL)
    {
        *timestamp_us = TimeService_NowUs();
    }

    return AS5600_STATUS_OK;
}

AS5600_Status AS5600_ReadMagnitude(const AS5600_Device *dev, uint16_t *magnitude, uint64_t *timestamp_us)
{
    uint8_t data[2];
    AS5600_Status status;

    if (magnitude == NULL)
    {
        return AS5600_STATUS_BAD_ARG;
    }

    status = AS5600_ReadRegisterBlock(dev, AS5600_REG_MAGNITUDE_MSB, data, 2u);
    if (status != AS5600_STATUS_OK)
    {
        return status;
    }

    *magnitude = (uint16_t)(((uint16_t)data[0] << 8u) | data[1]);
    if (timestamp_us != NULL)
    {
        *timestamp_us = TimeService_NowUs();
    }
    return AS5600_STATUS_OK;
}

AS5600_Status AS5600_ReadAgc(const AS5600_Device *dev, uint8_t *agc, uint64_t *timestamp_us)
{
    uint8_t data;
    AS5600_Status status;

    if (agc == NULL)
    {
        return AS5600_STATUS_BAD_ARG;
    }

    status = AS5600_ReadRegisterBlock(dev, AS5600_REG_AGC, &data, 1u);
    if (status != AS5600_STATUS_OK)
    {
        return status;
    }

    *agc = data;
    if (timestamp_us != NULL)
    {
        *timestamp_us = TimeService_NowUs();
    }
    return AS5600_STATUS_OK;
}

AS5600_Status AS5600_ReadStatus(const AS5600_Device *dev, uint8_t *status_out, uint64_t *timestamp_us)
{
    uint8_t data;
    AS5600_Status status;

    if (status_out == NULL)
    {
        return AS5600_STATUS_BAD_ARG;
    }

    status = AS5600_ReadRegisterBlock(dev, AS5600_REG_STATUS, &data, 1u);
    if (status != AS5600_STATUS_OK)
    {
        return status;
    }

    *status_out = data;
    if (timestamp_us != NULL)
    {
        *timestamp_us = TimeService_NowUs();
    }
    return AS5600_STATUS_OK;
}

AS5600_Status AS5600_ReadSample(const AS5600_Device *dev, AS5600_Sample *sample)
{
    AS5600_Status status;
    uint64_t ts = 0u;

    if (sample == NULL)
    {
        return AS5600_STATUS_BAD_ARG;
    }

    status = AS5600_ReadStatus(dev, &sample->status, &ts);
    if (status != AS5600_STATUS_OK)
    {
        return status;
    }

    status = AS5600_ReadRawAngle(dev, &sample->raw_angle, &ts);
    if (status != AS5600_STATUS_OK)
    {
        return status;
    }

    status = AS5600_ReadAngle(dev, &sample->angle, &ts);
    if (status != AS5600_STATUS_OK)
    {
        return status;
    }

    status = AS5600_ReadAgc(dev, &sample->agc, &ts);
    if (status != AS5600_STATUS_OK)
    {
        return status;
    }

    status = AS5600_ReadMagnitude(dev, &sample->magnitude, &ts);
    if (status != AS5600_STATUS_OK)
    {
        return status;
    }

    sample->timestamp_us = TimeService_NowUs();
    return AS5600_STATUS_OK;
}

float AS5600_RawToDegrees(uint16_t raw_angle)
{
    return ((float)(raw_angle & AS5600_RAW_ANGLE_MAX) * 360.0f) / 4096.0f;
}
