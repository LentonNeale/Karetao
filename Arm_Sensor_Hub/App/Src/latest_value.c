/**
 * @file latest_value.c
 * @brief Implements the latest-value store (see latest_value.h).
 */

#include "latest_value.h"

#include <stddef.h>
#include <string.h>

#include "FreeRTOS.h"
#include "task.h"

/** AS5600 counts per revolution (12 bit, PRM-ACQ-06) and millidegrees per revolution. */
#define LATEST_VALUE_AS5600_COUNTS_PER_REV 4096u
#define LATEST_VALUE_MDEG_PER_REV 360000u
#define LATEST_VALUE_MAX_CAN_ID 0x7FFu

static LatestValue_SensorRecord s_sensors[LATEST_VALUE_SENSOR_COUNT];
static LatestValue_MotorRecord s_motors[LATEST_VALUE_MOTOR_COUNT];
static uint64_t s_sensor_window_us;
static uint64_t s_motor_window_us;

/* A sample stamped after the caller read now_us (accepted between that read and the copy) has
 * age zero, not an unsigned wrap to a huge age. */
static LatestValue_Freshness LatestValue_Judge(uint64_t now_us, uint64_t timestamp_us, uint64_t window_us)
{
    uint64_t age_us = (now_us > timestamp_us) ? (now_us - timestamp_us) : 0u;
    return (age_us > window_us) ? LATEST_VALUE_FRESHNESS_STALE : LATEST_VALUE_FRESHNESS_FRESH;
}

LatestValue_Result LatestValue_Configure(const LatestValue_Config *config)
{
    uint8_t index;

    if ((config == NULL) || (config->sensor_window_us == 0u) || (config->motor_window_us == 0u)) {
        return LATEST_VALUE_INVALID_ARGUMENT;
    }
    for (index = 0u; index < LATEST_VALUE_MOTOR_COUNT; ++index) {
        const LatestValue_MotorSlotConfig *slot = &config->motors[index];
        if (slot->registered && ((slot->logical_joint_id > LATEST_VALUE_MAX_LOGICAL_JOINT) ||
                                 (slot->can_id > LATEST_VALUE_MAX_CAN_ID))) {
            return LATEST_VALUE_INVALID_ARGUMENT;
        }
    }

    memset(s_sensors, 0, sizeof(s_sensors));
    memset(s_motors, 0, sizeof(s_motors));
    for (index = 0u; index < LATEST_VALUE_SENSOR_COUNT; ++index) {
        s_sensors[index].logical_id = index;
        s_sensors[index].fitted = config->sensor_fitted[index];
        s_sensors[index].calibration_version = LATEST_VALUE_CALIBRATION_VERSION;
    }
    for (index = 0u; index < LATEST_VALUE_MOTOR_COUNT; ++index) {
        const LatestValue_MotorSlotConfig *slot = &config->motors[index];
        s_motors[index].motor_index = index;
        s_motors[index].registered = slot->registered;
        s_motors[index].logical_joint_id = slot->logical_joint_id;
        s_motors[index].can_id = slot->can_id;
        s_motors[index].configuration_version = slot->configuration_version;
    }
    s_sensor_window_us = config->sensor_window_us;
    s_motor_window_us = config->motor_window_us;
    return LATEST_VALUE_OK;
}

LatestValue_Result LatestValue_AcceptSample(uint8_t axis, const LatestValue_Sample *sample)
{
    LatestValue_SensorRecord record;

    /* A count above 12 bits is no AS5600 reading, and would overflow the uint32 scaling below. */
    if ((axis >= LATEST_VALUE_SENSOR_COUNT) || (sample == NULL) ||
        (sample->raw_angle_counts > LATEST_VALUE_MAX_RAW_ANGLE)) {
        return LATEST_VALUE_INVALID_ARGUMENT;
    }

    /* Built outside the lock; only the store into the slot is guarded. Slot properties are set
     * by Configure alone, so reading them here races with nothing. */
    record = s_sensors[axis];
    if (!record.fitted) {
        return LATEST_VALUE_NOT_FITTED;
    }
    record.has_sample = true;
    record.condition = sample->condition;
    record.status = sample->status;
    if (sample->condition == LATEST_VALUE_SAMPLE_OK) {
        record.raw_angle_counts = sample->raw_angle_counts;
        /* Scale only (ruling R6: RAW ANGLE in millidegrees); calibration version 0. */
        record.processed_angle_mdeg = (int32_t)(((uint32_t)sample->raw_angle_counts * LATEST_VALUE_MDEG_PER_REV) /
                                                LATEST_VALUE_AS5600_COUNTS_PER_REV);
        record.magnitude = sample->magnitude;
        record.agc = sample->agc;
        record.measurement_timestamp_us = sample->timestamp_us;
    } else {
        /* A failed read carries no angle; the record says why and holds no stale value. */
        record.raw_angle_counts = 0u;
        record.processed_angle_mdeg = 0;
        record.magnitude = 0u;
        record.agc = 0u;
        record.measurement_timestamp_us = 0u;
    }

    taskENTER_CRITICAL();
    s_sensors[axis] = record;
    taskEXIT_CRITICAL();
    return LATEST_VALUE_OK;
}

LatestValue_Result LatestValue_AcceptFeedback(uint8_t motor_index, const LatestValue_Feedback *feedback)
{
    if ((motor_index >= LATEST_VALUE_MOTOR_COUNT) || (feedback == NULL) ||
        ((feedback->kind != LATEST_VALUE_FEEDBACK_POSITION) && (feedback->kind != LATEST_VALUE_FEEDBACK_SPEED))) {
        return LATEST_VALUE_INVALID_ARGUMENT;
    }
    if (!s_motors[motor_index].registered) {
        return LATEST_VALUE_NOT_REGISTERED;
    }

    /* A merge reads the record, so the whole read-modify-write is guarded: only the fields of
     * this reply's kind change, each with its own timestamp. */
    taskENTER_CRITICAL();
    if (feedback->kind == LATEST_VALUE_FEEDBACK_POSITION) {
        LatestValue_MotorRecord *record = &s_motors[motor_index];
        record->has_position = true;
        record->position_counts = feedback->position_counts;
        record->position_timestamp_us = feedback->timestamp_us;
        record->position_command_code = feedback->position_command_code;
        memcpy(record->position_reply, feedback->position_reply, sizeof(record->position_reply));
    } else {
        s_motors[motor_index].has_speed = true;
        s_motors[motor_index].speed_rpm = feedback->speed_rpm;
        s_motors[motor_index].speed_timestamp_us = feedback->timestamp_us;
    }
    taskEXIT_CRITICAL();
    return LATEST_VALUE_OK;
}

void LatestValue_CopySnapshot(uint64_t now_us, LatestValue_Snapshot *out)
{
    uint8_t index;

    if (out == NULL) {
        return;
    }

    /* Copy-out under lock: the guarded section is the copy alone, a few microseconds with the
     * kernel-aware interrupts (SPI3 and its DMA among them) held pending; ageing runs on the
     * private copy afterwards. */
    taskENTER_CRITICAL();
    memcpy(out->sensors, s_sensors, sizeof(out->sensors));
    memcpy(out->motors, s_motors, sizeof(out->motors));
    taskEXIT_CRITICAL();

    out->copied_at_us = now_us;
    for (index = 0u; index < LATEST_VALUE_SENSOR_COUNT; ++index) {
        LatestValue_SensorRecord *record = &out->sensors[index];
        if (!record->fitted) {
            /* The schema's not-fitted timestamp is the time the record was last refreshed. */
            record->measurement_timestamp_us = now_us;
            record->freshness = LATEST_VALUE_FRESHNESS_NONE;
        } else if (record->has_sample && (record->condition == LATEST_VALUE_SAMPLE_OK)) {
            record->freshness = LatestValue_Judge(now_us, record->measurement_timestamp_us, s_sensor_window_us);
        } else {
            record->freshness = LATEST_VALUE_FRESHNESS_NONE;
        }
    }
    for (index = 0u; index < LATEST_VALUE_MOTOR_COUNT; ++index) {
        LatestValue_MotorRecord *record = &out->motors[index];
        record->freshness = (record->registered && record->has_position)
                                ? LatestValue_Judge(now_us, record->position_timestamp_us, s_motor_window_us)
                                : LATEST_VALUE_FRESHNESS_NONE;
    }
}
