#ifndef AS5600_H
#define AS5600_H

#include <stdbool.h>
#include <stdint.h>

#include "i2c_manager.h"

typedef enum
{
    AS5600_STATUS_OK = 0,
    AS5600_STATUS_ERROR,
    AS5600_STATUS_BUSY,
    AS5600_STATUS_TIMEOUT,
    AS5600_STATUS_BAD_ARG,
    AS5600_STATUS_NOT_READY
} AS5600_Status;

typedef struct
{
    uint16_t i2c_addr_7bit;
    uint8_t mux_channel;
    uint32_t timeout_ms;
} AS5600_Device;

typedef struct
{
    uint16_t raw_angle;
    uint16_t angle;
    uint16_t magnitude;
    uint8_t agc;
    uint8_t status;
    uint64_t timestamp_us;
} AS5600_Sample;

#define AS5600_I2C_ADDR_7BIT 0x36u
#define AS5600_RAW_ANGLE_MAX 4095u

#define AS5600_STATUS_MD (1u << 5)
#define AS5600_STATUS_ML (1u << 4)
#define AS5600_STATUS_MH (1u << 3)

void AS5600_InitDevice(AS5600_Device *dev, uint8_t mux_channel);

AS5600_Status AS5600_ReadRawAngle(const AS5600_Device *dev, uint16_t *raw_angle, uint64_t *timestamp_us);
AS5600_Status AS5600_ReadAngle(const AS5600_Device *dev, uint16_t *angle, uint64_t *timestamp_us);
AS5600_Status AS5600_ReadMagnitude(const AS5600_Device *dev, uint16_t *magnitude, uint64_t *timestamp_us);
AS5600_Status AS5600_ReadAgc(const AS5600_Device *dev, uint8_t *agc, uint64_t *timestamp_us);
AS5600_Status AS5600_ReadStatus(const AS5600_Device *dev, uint8_t *status, uint64_t *timestamp_us);
AS5600_Status AS5600_ReadSample(const AS5600_Device *dev, AS5600_Sample *sample);

float AS5600_RawToDegrees(uint16_t raw_angle);

#endif /* AS5600_H */
