/**
 * @file joint_mapping.h
 * @brief Implements the joint mapping module.
 */

#ifndef JOINT_MAPPING_H
#define JOINT_MAPPING_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define JOINT_MAPPING_SCHEMA_VERSION UINT16_C(1)
#define JOINT_MAPPING_MAX_ENTRIES UINT8_C(6)
#define JOINT_MAPPING_MAX_SENSOR_ID UINT8_C(5)
#define JOINT_MAPPING_MAX_MOTOR_INDEX UINT8_C(7)
#define JOINT_MAPPING_MAX_CAN_ID UINT16_C(0x07FF)

typedef struct
{
    uint16_t schema_version;
    uint8_t logical_joint_id;
    uint8_t as5600_sensor_id;
    uint8_t motor_index;
    uint16_t can_id;
    int8_t direction;
    int32_t zero_offset_mdeg;
    uint32_t transmission_ratio_numerator;
    uint32_t transmission_ratio_denominator;
} JointMapping_Record;

typedef enum
{
    JOINT_MAPPING_RESULT_OK = 0,
    JOINT_MAPPING_RESULT_INVALID_ARGUMENT,
    JOINT_MAPPING_RESULT_UNSUPPORTED_SCHEMA,
    JOINT_MAPPING_RESULT_INVALID_ID,
    JOINT_MAPPING_RESULT_INVALID_DIRECTION,
    JOINT_MAPPING_RESULT_INVALID_RATIO,
    JOINT_MAPPING_RESULT_DUPLICATE_JOINT_ID,
    JOINT_MAPPING_RESULT_DUPLICATE_SENSOR_ID,
    JOINT_MAPPING_RESULT_DUPLICATE_MOTOR_INDEX,
    JOINT_MAPPING_RESULT_DUPLICATE_CAN_ID
} JointMapping_Result;

/**
 * @brief Executes mapping validate.
 */
JointMapping_Result JointMapping_Validate(const JointMapping_Record *records, size_t record_count);
const JointMapping_Record *JointMapping_FindByJoint(const JointMapping_Record *records,
                                                    size_t record_count,
                                                    uint8_t logical_joint_id);

#ifdef __cplusplus
}
#endif

#endif /* JOINT_MAPPING_H */