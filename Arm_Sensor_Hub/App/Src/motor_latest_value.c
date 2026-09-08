/**
 * @file motor_latest_value.c
 * @brief Implements the motor latest value module.
 */

#include "motor_latest_value.h"

#include <stddef.h>
#include <string.h>

void MotorLatestValue_Init(Motor_LatestValue *record,
                           uint8_t logical_joint_id,
                           uint8_t motor_index,
                           uint16_t can_id,
                           uint32_t configuration_version)
{
    if (record == NULL)
    {
        return;
    }

    record->logical_joint_id = logical_joint_id;
    record->motor_index = motor_index;
    record->can_id = can_id;
    record->command_code = 0u;
    record->controller_status = 0u;
    record->controller_status_valid = false;
    memset(record->payload, 0, sizeof(record->payload));
    record->payload_length = 0u;
    record->validity_flags = 0u;
    record->acquisition_timestamp_us = 0u;
    record->last_update_timestamp_us = 0u;
    record->synchronization_quality = TIME_SERVICE_SYNC_QUALITY_UNSYNCHRONIZED;
    record->calibration_version = 0u;
    record->configuration_version = configuration_version;
    record->freshness = MOTOR_FRESHNESS_INVALID;
    record->rx_ok_count = 0u;
    record->rx_decode_error_count = 0u;
}

void MotorLatestValue_SetValid(Motor_LatestValue *record,
                               uint8_t command_code,
                               const uint8_t *payload,
                               uint8_t payload_length,
                               uint8_t controller_status,
                               bool controller_status_valid,
                               uint64_t acquisition_timestamp_us,
                               TimeService_SyncQuality synchronization_quality,
                               uint32_t calibration_version)
{
    if ((record == NULL) || (payload_length > sizeof(record->payload)) ||
        ((payload_length > 0u) && (payload == NULL)))
    {
        return;
    }

    record->command_code = command_code;
    record->controller_status = controller_status;
    record->controller_status_valid = controller_status_valid;
    memset(record->payload, 0, sizeof(record->payload));
    if (payload_length > 0u)
    {
        memcpy(record->payload, payload, payload_length);
    }

    record->payload_length = payload_length;
    record->validity_flags = MOTOR_VALIDITY_FEEDBACK_VALID;
    if (controller_status_valid)
    {
        record->validity_flags |= MOTOR_VALIDITY_CONTROLLER_STATUS_VALID;
    }

    if (synchronization_quality == TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED)
    {
        record->validity_flags |= MOTOR_VALIDITY_TIMESTAMP_SYNCHRONIZED;
    }

    record->acquisition_timestamp_us = acquisition_timestamp_us;
    record->last_update_timestamp_us = acquisition_timestamp_us;
    record->synchronization_quality = synchronization_quality;
    record->calibration_version = calibration_version;
    record->freshness = MOTOR_FRESHNESS_FRESH;
    record->rx_ok_count++;
}

/**
 * @brief Executes latest value mark stale.
 */
void MotorLatestValue_MarkStale(Motor_LatestValue *record, uint64_t update_timestamp_us)
{
    if (record == NULL)
    {
        return;
    }

    record->validity_flags &= ~MOTOR_VALIDITY_FEEDBACK_VALID;
    record->last_update_timestamp_us = update_timestamp_us;
    record->freshness = (record->acquisition_timestamp_us == 0u)
                            ? MOTOR_FRESHNESS_INVALID
                            : MOTOR_FRESHNESS_STALE;
    record->rx_decode_error_count++;
}