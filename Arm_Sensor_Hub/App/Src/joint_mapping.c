/**
 * @file joint_mapping.c
 * @brief Implements the joint mapping module.
 */

#include "joint_mapping.h"

#include <stdbool.h>

/**
 * @brief Executes mapping validate record.
 */
static JointMapping_Result JointMapping_ValidateRecord(const JointMapping_Record *record)
{
    if (record->schema_version != JOINT_MAPPING_SCHEMA_VERSION)
    {
        return JOINT_MAPPING_RESULT_UNSUPPORTED_SCHEMA;
    }

    if ((record->logical_joint_id > JOINT_MAPPING_MAX_SENSOR_ID) ||
        (record->as5600_sensor_id > JOINT_MAPPING_MAX_SENSOR_ID) ||
        (record->motor_index > JOINT_MAPPING_MAX_MOTOR_INDEX) ||
        (record->can_id > JOINT_MAPPING_MAX_CAN_ID))
    {
        return JOINT_MAPPING_RESULT_INVALID_ID;
    }

    if ((record->direction != 1) && (record->direction != -1))
    {
        return JOINT_MAPPING_RESULT_INVALID_DIRECTION;
    }

    if ((record->transmission_ratio_numerator == 0u) ||
        (record->transmission_ratio_denominator == 0u))
    {
        return JOINT_MAPPING_RESULT_INVALID_RATIO;
    }

    return JOINT_MAPPING_RESULT_OK;
}

/**
 * @brief Executes mapping validate.
 */
JointMapping_Result JointMapping_Validate(const JointMapping_Record *records, size_t record_count)
{
    size_t record_index;
    size_t prior_index;

    if ((records == NULL) || (record_count == 0u) || (record_count > JOINT_MAPPING_MAX_ENTRIES))
    {
        return JOINT_MAPPING_RESULT_INVALID_ARGUMENT;
    }

    for (record_index = 0u; record_index < record_count; ++record_index)
    {
        JointMapping_Result result = JointMapping_ValidateRecord(&records[record_index]);
        if (result != JOINT_MAPPING_RESULT_OK)
        {
            return result;
        }

        for (prior_index = 0u; prior_index < record_index; ++prior_index)
        {
            if (records[record_index].logical_joint_id == records[prior_index].logical_joint_id)
            {
                return JOINT_MAPPING_RESULT_DUPLICATE_JOINT_ID;
            }

            if (records[record_index].as5600_sensor_id == records[prior_index].as5600_sensor_id)
            {
                return JOINT_MAPPING_RESULT_DUPLICATE_SENSOR_ID;
            }

            if (records[record_index].motor_index == records[prior_index].motor_index)
            {
                return JOINT_MAPPING_RESULT_DUPLICATE_MOTOR_INDEX;
            }

            if (records[record_index].can_id == records[prior_index].can_id)
            {
                return JOINT_MAPPING_RESULT_DUPLICATE_CAN_ID;
            }
        }
    }

    return JOINT_MAPPING_RESULT_OK;
}

const JointMapping_Record *JointMapping_FindByJoint(const JointMapping_Record *records,
                                                    size_t record_count,
                                                    uint8_t logical_joint_id)
{
    size_t record_index;

    if (records == NULL)
    {
        return NULL;
    }

    for (record_index = 0u; record_index < record_count; ++record_index)
    {
        if (records[record_index].logical_joint_id == logical_joint_id)
        {
            return &records[record_index];
        }
    }

    return NULL;
}