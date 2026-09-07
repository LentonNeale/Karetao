#include "calibration_record.h"

#include <stdbool.h>

static bool Calibration_HasSameIdentity(const Calibration_Record *first, const Calibration_Record *second)
{
    return (first->logical_sensor_id == second->logical_sensor_id) &&
           (first->logical_joint_id == second->logical_joint_id);
}

static bool Calibration_IsGenerationNewer(uint32_t candidate, uint32_t previous)
{
    return (candidate != previous) &&
           ((uint32_t)(candidate - previous) < UINT32_C(0x80000000));
}

Calibration_Result Calibration_ValidateRecord(const Calibration_Record *record, uint32_t computed_crc32)
{
    if (record == NULL)
    {
        return CALIBRATION_RESULT_INVALID_ARGUMENT;
    }

    if (record->schema_version != CALIBRATION_SCHEMA_VERSION)
    {
        return CALIBRATION_RESULT_UNSUPPORTED_SCHEMA;
    }

    if ((record->logical_sensor_id > CALIBRATION_MAX_LOGICAL_ID) ||
        (record->logical_joint_id > CALIBRATION_MAX_LOGICAL_ID))
    {
        return CALIBRATION_RESULT_INVALID_IDENTITY;
    }

    if ((record->scale_ppm == 0) || ((record->direction != 1) && (record->direction != -1)))
    {
        return CALIBRATION_RESULT_INVALID_PARAMETERS;
    }

    if (record->generation == 0u)
    {
        return CALIBRATION_RESULT_INVALID_GENERATION;
    }

    if (record->validity_marker != CALIBRATION_VALIDITY_MARKER)
    {
        return CALIBRATION_RESULT_INVALID_MARKER;
    }

    if (record->record_crc32 != computed_crc32)
    {
        return CALIBRATION_RESULT_CRC_MISMATCH;
    }

    return CALIBRATION_RESULT_OK;
}

Calibration_Result Calibration_ValidateUniqueIdentities(const Calibration_Record *records,
                                                         const uint32_t *computed_crc32,
                                                         size_t record_count)
{
    size_t record_index;
    size_t prior_index;

    if ((records == NULL) || (computed_crc32 == NULL) || (record_count == 0u))
    {
        return CALIBRATION_RESULT_INVALID_ARGUMENT;
    }

    for (record_index = 0u; record_index < record_count; ++record_index)
    {
        Calibration_Result result = Calibration_ValidateRecord(&records[record_index], computed_crc32[record_index]);
        if (result != CALIBRATION_RESULT_OK)
        {
            return result;
        }

        for (prior_index = 0u; prior_index < record_index; ++prior_index)
        {
            if (Calibration_HasSameIdentity(&records[record_index], &records[prior_index]))
            {
                return CALIBRATION_RESULT_DUPLICATE_IDENTITY;
            }
        }
    }

    return CALIBRATION_RESULT_OK;
}

Calibration_Result Calibration_SelectNewer(const Calibration_Record *first,
                                           uint32_t first_computed_crc32,
                                           const Calibration_Record *second,
                                           uint32_t second_computed_crc32,
                                           Calibration_ActiveVersion *active_version)
{
    Calibration_Result result;
    const Calibration_Record *selected;

    if ((first == NULL) || (second == NULL) || (active_version == NULL))
    {
        return CALIBRATION_RESULT_INVALID_ARGUMENT;
    }

    result = Calibration_ValidateRecord(first, first_computed_crc32);
    if (result != CALIBRATION_RESULT_OK)
    {
        return result;
    }

    result = Calibration_ValidateRecord(second, second_computed_crc32);
    if (result != CALIBRATION_RESULT_OK)
    {
        return result;
    }

    if (!Calibration_HasSameIdentity(first, second))
    {
        return CALIBRATION_RESULT_IDENTITY_MISMATCH;
    }

    if (first->generation == second->generation)
    {
        return CALIBRATION_RESULT_AMBIGUOUS_GENERATION;
    }

    selected = Calibration_IsGenerationNewer(second->generation, first->generation) ? second : first;
    active_version->record = *selected;
    active_version->active_schema_version = selected->schema_version;
    active_version->active_generation = selected->generation;
    return CALIBRATION_RESULT_OK;
}