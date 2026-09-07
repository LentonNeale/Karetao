#ifndef CALIBRATION_RECORD_H
#define CALIBRATION_RECORD_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CALIBRATION_SCHEMA_VERSION UINT16_C(1)
#define CALIBRATION_VALIDITY_MARKER UINT32_C(0x43414C56)
#define CALIBRATION_MAX_LOGICAL_ID UINT8_C(5)

typedef struct
{
    uint16_t schema_version;
    uint8_t logical_sensor_id;
    uint8_t logical_joint_id;
    int32_t zero_offset_mdeg;
    int32_t scale_ppm;
    int8_t direction;
    uint8_t reserved[3];
    uint32_t generation;
    uint32_t record_crc32;
    uint32_t validity_marker;
} Calibration_Record;

typedef enum
{
    CALIBRATION_RESULT_OK = 0,
    CALIBRATION_RESULT_INVALID_ARGUMENT,
    CALIBRATION_RESULT_UNSUPPORTED_SCHEMA,
    CALIBRATION_RESULT_INVALID_IDENTITY,
    CALIBRATION_RESULT_INVALID_PARAMETERS,
    CALIBRATION_RESULT_INVALID_GENERATION,
    CALIBRATION_RESULT_INVALID_MARKER,
    CALIBRATION_RESULT_CRC_MISMATCH,
    CALIBRATION_RESULT_DUPLICATE_IDENTITY,
    CALIBRATION_RESULT_IDENTITY_MISMATCH,
    CALIBRATION_RESULT_AMBIGUOUS_GENERATION
} Calibration_Result;

typedef struct
{
    Calibration_Record record;
    uint16_t active_schema_version;
    uint32_t active_generation;
} Calibration_ActiveVersion;

Calibration_Result Calibration_ValidateRecord(const Calibration_Record *record, uint32_t computed_crc32);
Calibration_Result Calibration_ValidateUniqueIdentities(const Calibration_Record *records,
                                                         const uint32_t *computed_crc32,
                                                         size_t record_count);
Calibration_Result Calibration_SelectNewer(const Calibration_Record *first,
                                           uint32_t first_computed_crc32,
                                           const Calibration_Record *second,
                                           uint32_t second_computed_crc32,
                                           Calibration_ActiveVersion *active_version);

#ifdef __cplusplus
}
#endif

#endif /* CALIBRATION_RECORD_H */