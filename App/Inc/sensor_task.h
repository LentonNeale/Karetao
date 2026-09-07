#ifndef SENSOR_TASK_H
#define SENSOR_TASK_H

#include <stddef.h>
#include <stdint.h>

#include "lifecycle.h"
#include "sensor_latest_value.h"

#ifdef __cplusplus
extern "C" {
#endif

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

void SensorTask_Init(void);
Lifecycle_Result SensorTask_Activate(void);
Lifecycle_State SensorTask_GetLifecycleState(void);
void SensorTask_Process(void);
SensorTask_BringupResult SensorTask_GetBringupResult(void);
const SensorTask_BringupSnapshot *SensorTask_GetBringupSnapshot(void);
uint32_t SensorTask_GetBringupDiagWord(void);
uint8_t SensorTask_IsActive(void);
const Sensor_LatestValue *SensorTask_GetLatestValues(size_t *record_count);

#ifdef __cplusplus
}
#endif

#endif /* SENSOR_TASK_H */
