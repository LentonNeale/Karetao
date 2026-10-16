/**
 * @file sensor_latest_value.h
 * @brief Implements the sensor latest value module.
 */

#ifndef SENSOR_LATEST_VALUE_H
#define SENSOR_LATEST_VALUE_H

#include <stdint.h>

#include "time_service.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum
{
    SENSOR_FRESHNESS_INVALID = 0,
    SENSOR_FRESHNESS_FRESH,
    SENSOR_FRESHNESS_STALE
} Sensor_Freshness;

#define SENSOR_VALIDITY_SAMPLE_VALID UINT16_C(0x0001)
#define SENSOR_VALIDITY_COMMUNICATION_ERROR UINT16_C(0x0002)
#define SENSOR_VALIDITY_MAGNET_NOT_DETECTED UINT16_C(0x0004)
#define SENSOR_VALIDITY_MAGNET_TOO_WEAK UINT16_C(0x0008)
#define SENSOR_VALIDITY_MAGNET_TOO_STRONG UINT16_C(0x0010)
#define SENSOR_VALIDITY_TIMESTAMP_SYNCHRONIZED UINT16_C(0x0020)
#define SENSOR_VALIDITY_NOT_FITTED UINT16_C(0x0040)

typedef struct
{
    uint8_t logical_joint_id;
    uint8_t sensor_id;
    uint16_t raw_angle_counts;
    int32_t processed_angle_mdeg;
    uint16_t magnitude;
    uint8_t agc;
    uint8_t status;
    uint16_t validity_flags;
    uint64_t measurement_timestamp_us;
    uint64_t last_update_timestamp_us;
    TimeService_SyncQuality synchronization_quality;
    uint32_t calibration_version;
    Sensor_Freshness freshness;
} Sensor_LatestValue;

void SensorLatestValue_Init(Sensor_LatestValue *record,
                            uint8_t logical_joint_id,
                            uint8_t sensor_id,
                            uint32_t calibration_version);
void SensorLatestValue_SetValid(Sensor_LatestValue *record,
                                uint16_t raw_angle_counts,
                                int32_t processed_angle_mdeg,
                                uint16_t magnitude,
                                uint8_t agc,
                                uint8_t status,
                                uint64_t measurement_timestamp_us,
                                TimeService_SyncQuality synchronization_quality,
                                uint32_t calibration_version);
void SensorLatestValue_SetInvalid(Sensor_LatestValue *record,
                                  uint8_t status,
                                  uint16_t reason_flags,
                                  uint64_t update_timestamp_us);
/**
 * @brief Marks an axis that has no encoder fitted (never a communication error).
 */
void SensorLatestValue_SetNotFitted(Sensor_LatestValue *record, uint64_t update_timestamp_us);
#ifdef __cplusplus
}
#endif

#endif /* SENSOR_LATEST_VALUE_H */