/**
 * @file motor_latest_value.h
 * @brief Implements the motor latest value module.
 */

#ifndef MOTOR_LATEST_VALUE_H
#define MOTOR_LATEST_VALUE_H

#include <stdbool.h>
#include <stdint.h>

#include "time_service.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum
{
    MOTOR_FRESHNESS_INVALID = 0,
    MOTOR_FRESHNESS_FRESH,
    MOTOR_FRESHNESS_STALE
} Motor_Freshness;

#define MOTOR_VALIDITY_FEEDBACK_VALID UINT16_C(0x0001)
#define MOTOR_VALIDITY_CONTROLLER_STATUS_VALID UINT16_C(0x0002)
#define MOTOR_VALIDITY_TIMESTAMP_SYNCHRONIZED UINT16_C(0x0004)

typedef struct
{
    uint8_t logical_joint_id;
    uint8_t motor_index;
    uint16_t can_id;
    uint8_t command_code;
    uint8_t controller_status;
    bool controller_status_valid;
    uint8_t payload[6];
    uint8_t payload_length;
    uint16_t validity_flags;
    uint64_t acquisition_timestamp_us;
    uint64_t last_update_timestamp_us;
    TimeService_SyncQuality synchronization_quality;
    uint32_t calibration_version;
    uint32_t configuration_version;
    Motor_Freshness freshness;
    uint32_t rx_ok_count;
    uint32_t rx_decode_error_count;
} Motor_LatestValue;

void MotorLatestValue_Init(Motor_LatestValue *record,
                           uint8_t logical_joint_id,
                           uint8_t motor_index,
                           uint16_t can_id,
                           uint32_t configuration_version);
void MotorLatestValue_SetValid(Motor_LatestValue *record,
                               uint8_t command_code,
                               const uint8_t *payload,
                               uint8_t payload_length,
                               uint8_t controller_status,
                               bool controller_status_valid,
                               uint64_t acquisition_timestamp_us,
                               TimeService_SyncQuality synchronization_quality,
                               uint32_t calibration_version);
/**
 * @brief Executes latest value mark stale.
 */
void MotorLatestValue_MarkStale(Motor_LatestValue *record, uint64_t update_timestamp_us);

#ifdef __cplusplus
}
#endif

#endif /* MOTOR_LATEST_VALUE_H */