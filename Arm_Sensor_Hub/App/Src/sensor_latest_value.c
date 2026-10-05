/**
 * @file sensor_latest_value.c
 * @brief Implements the sensor latest value module.
 */

#include "sensor_latest_value.h"

#include <stddef.h>

void SensorLatestValue_Init(Sensor_LatestValue *record,
                            uint8_t logical_joint_id,
                            uint8_t sensor_id,
                            uint32_t calibration_version)
{
    if (record == NULL)
    {
        return;
    }

    record->logical_joint_id = logical_joint_id;
    record->sensor_id = sensor_id;
    record->raw_angle_counts = 0u;
    record->processed_angle_mdeg = 0;
    record->magnitude = 0u;
    record->agc = 0u;
    record->status = 0u;
    record->validity_flags = 0u;
    record->measurement_timestamp_us = 0u;
    record->last_update_timestamp_us = 0u;
    record->synchronization_quality = TIME_SERVICE_SYNC_QUALITY_UNSYNCHRONIZED;
    record->calibration_version = calibration_version;
    record->freshness = SENSOR_FRESHNESS_INVALID;
}

void SensorLatestValue_SetValid(Sensor_LatestValue *record,
                                uint16_t raw_angle_counts,
                                int32_t processed_angle_mdeg,
                                uint16_t magnitude,
                                uint8_t agc,
                                uint8_t status,
                                uint64_t measurement_timestamp_us,
                                TimeService_SyncQuality synchronization_quality,
                                uint32_t calibration_version)
{
    if (record == NULL)
    {
        return;
    }

    record->raw_angle_counts = raw_angle_counts;
    record->processed_angle_mdeg = processed_angle_mdeg;
    record->magnitude = magnitude;
    record->agc = agc;
    record->status = status;
    record->validity_flags = SENSOR_VALIDITY_SAMPLE_VALID;
    if (synchronization_quality == TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED)
    {
        record->validity_flags |= SENSOR_VALIDITY_TIMESTAMP_SYNCHRONIZED;
    }

    record->measurement_timestamp_us = measurement_timestamp_us;
    record->last_update_timestamp_us = measurement_timestamp_us;
    record->synchronization_quality = synchronization_quality;
    record->calibration_version = calibration_version;
    record->freshness = SENSOR_FRESHNESS_FRESH;
}

void SensorLatestValue_SetInvalid(Sensor_LatestValue *record,
                                  uint8_t status,
                                  uint16_t reason_flags,
                                  uint64_t update_timestamp_us)
{
    if (record == NULL)
    {
        return;
    }

    record->raw_angle_counts = 0u;
    record->processed_angle_mdeg = 0;
    record->magnitude = 0u;
    record->agc = 0u;
    record->status = status;
    record->validity_flags = reason_flags & ~SENSOR_VALIDITY_SAMPLE_VALID;
    record->measurement_timestamp_us = 0u;
    record->last_update_timestamp_us = update_timestamp_us;
    record->synchronization_quality = TIME_SERVICE_SYNC_QUALITY_UNSYNCHRONIZED;
    record->freshness = SENSOR_FRESHNESS_INVALID;
}

void SensorLatestValue_SetNotFitted(Sensor_LatestValue *record, uint64_t update_timestamp_us)
{
    if (record == NULL)
    {
        return;
    }

    record->raw_angle_counts = 0u;
    record->processed_angle_mdeg = 0;
    record->magnitude = 0u;
    record->agc = 0u;
    record->status = 0u;
    record->validity_flags = SENSOR_VALIDITY_NOT_FITTED;
    record->measurement_timestamp_us = update_timestamp_us;
    record->last_update_timestamp_us = update_timestamp_us;
    record->synchronization_quality = TIME_SERVICE_SYNC_QUALITY_UNSYNCHRONIZED;
    record->freshness = SENSOR_FRESHNESS_INVALID;
}

/**
 * @brief Executes latest value mark stale.
 */
void SensorLatestValue_MarkStale(Sensor_LatestValue *record, uint64_t update_timestamp_us)
{
    if ((record == NULL) || (record->freshness != SENSOR_FRESHNESS_FRESH))
    {
        return;
    }

    record->validity_flags &= ~SENSOR_VALIDITY_SAMPLE_VALID;
    record->last_update_timestamp_us = update_timestamp_us;
    record->freshness = SENSOR_FRESHNESS_STALE;
}