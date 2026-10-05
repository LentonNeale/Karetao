/**
 * @file sensor_task.h
 * @brief Implements the sensor task module.
 */

#ifndef SENSOR_TASK_H
#define SENSOR_TASK_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "lifecycle.h"
#include "sensor_latest_value.h"

#ifdef __cplusplus
extern "C" {
#endif

/** Number of logical sensor axes published in every snapshot (logical IDs 0-5). */
#define SENSOR_TASK_AXIS_COUNT 6u
/** Highest selectable TCA9548A channel index. */
#define SENSOR_TASK_MAX_MUX_CHANNEL 7u

typedef enum
{
	SENSOR_TASK_BRINGUP_UNKNOWN = 0,
	SENSOR_TASK_BRINGUP_PASS,
	SENSOR_TASK_BRINGUP_FAIL_COMM,
	SENSOR_TASK_BRINGUP_FAIL_MAGNET_NOT_DETECTED,
	SENSOR_TASK_BRINGUP_FAIL_MAGNET_TOO_WEAK,
	SENSOR_TASK_BRINGUP_FAIL_MAGNET_TOO_STRONG
} SensorTask_BringupResult;

typedef enum
{
	SENSOR_TASK_INIT_STAGE_MUX = 0,
	SENSOR_TASK_INIT_STAGE_SENSOR,
	SENSOR_TASK_INIT_STAGE_ACTIVE
} SensorTask_InitStage;

typedef struct
{
	SensorTask_BringupResult result;
	SensorTask_InitStage init_stage;
	uint8_t is_active;
	uint8_t mux_readback_mask;
	uint16_t last_raw_angle;
	uint8_t last_status;
	uint64_t last_timestamp_us;
	uint32_t sample_ok_count;
	uint32_t comm_error_count;
	uint32_t magnet_error_count;
} SensorTask_BringupSnapshot;

/**
 * @brief Executes task init.
 */
void SensorTask_Init(void);
/**
 * @brief Bind each logical axis to the TCA9548A channel that carries its AS5600.
 *
 * Realizes the configurable commissioning mapping required by
 * MULTI_SENSOR_CONTRACT: `mux_channels[axis]` is the mux channel read for
 * logical axis `axis`, so the physical wiring may change without touching the
 * acquisition algorithm. Record positions and logical IDs stay 0-5 regardless
 * of which channels are bound.
 *
 * The map is validated before any binding is applied, so a rejected map leaves
 * the previous binding intact. Returns false when the map is NULL, is not
 * exactly SENSOR_TASK_AXIS_COUNT entries, names a channel above
 * SENSOR_TASK_MAX_MUX_CHANNEL, repeats a channel, or when the service is
 * already ACTIVE.
 */
bool SensorTask_ConfigureMuxChannels(const uint8_t *mux_channels, size_t count);
/**
 * @brief Declare which logical axes carry an encoder.
 *
 * `encoder_fitted[axis]` false marks the axis NOT_FITTED: bring-up and polling
 * never address it and its record carries only the NOT_FITTED validity bit, with
 * no fault. The default, until this is called, is every axis fitted. Returns
 * false when the table is NULL, the count is not SENSOR_TASK_AXIS_COUNT, or the
 * service is already ACTIVE.
 */
bool SensorTask_ConfigureFittedAxes(const bool *encoder_fitted, size_t count);
/**
 * @brief Executes task activate.
 */
Lifecycle_Result SensorTask_Activate(void);
/**
 * @brief Executes task get lifecycle state.
 */
Lifecycle_State SensorTask_GetLifecycleState(void);
/**
 * @brief Executes task process.
 */
void SensorTask_Process(void);
/**
 * @brief Executes task get bringup result.
 */
SensorTask_BringupResult SensorTask_GetBringupResult(void);
const SensorTask_BringupSnapshot *SensorTask_GetBringupSnapshot(void);
/**
 * @brief Executes task get bringup diag word.
 */
uint32_t SensorTask_GetBringupDiagWord(void);
/**
 * @brief Executes task is active.
 */
uint8_t SensorTask_IsActive(void);
const Sensor_LatestValue *SensorTask_GetLatestValues(size_t *record_count);

#ifdef __cplusplus
}
#endif

#endif /* SENSOR_TASK_H */
