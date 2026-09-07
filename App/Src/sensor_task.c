#include "sensor_task.h"

#include "as5600.h"
#include "main.h"
#include "sensor_latest_value.h"
#include "tca9548a_mux.h"
#include "time_service.h"

#define SENSOR_TASK_BRINGUP_POLL_PERIOD_MS 20u
#define SENSOR_TASK_MUX_CH0_MASK (1u << 0)
#define SENSOR_TASK_RECORD_COUNT 6u
#define SENSOR_TASK_CALIBRATION_VERSION 0u

static AS5600_Device s_single_encoder;
static SensorTask_BringupSnapshot s_snapshot;
static Sensor_LatestValue s_latest_values[SENSOR_TASK_RECORD_COUNT];
static Lifecycle_Record s_lifecycle;
static uint32_t s_last_poll_tick;
static uint32_t s_diag_word;

volatile SensorTask_BringupSnapshot g_sensor_task_snapshot_dbg;
volatile uint32_t g_sensor_task_diag_word_dbg;

static uint32_t SensorTask_PackDiagWord(void)
{
	uint32_t result_bits = ((uint32_t)s_snapshot.result & 0x0Fu) << 28u;
	uint32_t status_bits = ((uint32_t)s_snapshot.last_status & 0xFFu) << 20u;
	uint32_t angle_bits = ((uint32_t)s_snapshot.last_raw_angle & 0x0FFFu) << 8u;
	uint32_t comm_seen = (s_snapshot.comm_error_count > 0u) ? (1u << 7u) : 0u;
	uint32_t magnet_seen = (s_snapshot.magnet_error_count > 0u) ? (1u << 6u) : 0u;
	uint32_t sample_seen = (s_snapshot.sample_ok_count > 0u) ? (1u << 5u) : 0u;
	uint32_t md_bit = ((s_snapshot.last_status & AS5600_STATUS_MD) != 0u) ? (1u << 4u) : 0u;
	uint32_t ml_bit = ((s_snapshot.last_status & AS5600_STATUS_ML) != 0u) ? (1u << 3u) : 0u;
	uint32_t mh_bit = ((s_snapshot.last_status & AS5600_STATUS_MH) != 0u) ? (1u << 2u) : 0u;
	uint32_t active_bit = (s_snapshot.is_active != 0u) ? (1u << 1u) : 0u;
	uint32_t heartbeat = s_snapshot.sample_ok_count & 0x01u;

	return result_bits | status_bits | angle_bits | comm_seen | magnet_seen | sample_seen | md_bit | ml_bit | mh_bit | active_bit | heartbeat;
}

static void SensorTask_UpdateDebugMirrors(void)
{
	g_sensor_task_snapshot_dbg = s_snapshot;
	g_sensor_task_diag_word_dbg = s_diag_word;
}

static void SensorTask_RunInitChecks(void)
{
	I2CManager_Status mux_status;
	AS5600_Status sensor_status;
	uint8_t mux_readback = 0u;
	uint8_t sensor_status_reg = 0u;
	uint64_t ts = 0u;

	if (s_snapshot.init_stage == SENSOR_TASK_INIT_STAGE_MUX)
	{
		mux_status = TCA9548A_Probe(SENSOR_TASK_MUX_CH0_MASK, &mux_readback);
		s_snapshot.mux_readback_mask = mux_readback;

		if ((mux_status != I2C_MANAGER_STATUS_OK) || (mux_readback != SENSOR_TASK_MUX_CH0_MASK))
		{
			(void)Lifecycle_Fail(&s_lifecycle, (uint32_t)mux_status);
			s_snapshot.result = SENSOR_TASK_BRINGUP_FAIL_COMM;
			s_snapshot.is_active = 0u;
			s_snapshot.comm_error_count++;
			s_diag_word = SensorTask_PackDiagWord();
			SensorTask_UpdateDebugMirrors();
			return;
		}

		s_snapshot.init_stage = SENSOR_TASK_INIT_STAGE_SENSOR;
	}

	if (s_snapshot.init_stage == SENSOR_TASK_INIT_STAGE_SENSOR)
	{
		sensor_status = AS5600_ReadStatus(&s_single_encoder, &sensor_status_reg, &ts);
		if (sensor_status != AS5600_STATUS_OK)
		{
			(void)Lifecycle_Fail(&s_lifecycle, (uint32_t)sensor_status);
			s_snapshot.result = SENSOR_TASK_BRINGUP_FAIL_COMM;
			s_snapshot.is_active = 0u;
			s_snapshot.comm_error_count++;
			s_diag_word = SensorTask_PackDiagWord();
			HAL_GPIO_WritePin(Data_Ready_GPIO_Port, Data_Ready_Pin, GPIO_PIN_RESET);
			return;
		}

		s_snapshot.last_status = sensor_status_reg;
		s_snapshot.last_timestamp_us = ts;
		s_snapshot.init_stage = SENSOR_TASK_INIT_STAGE_ACTIVE;
		s_snapshot.is_active = 1u;
		s_snapshot.result = SENSOR_TASK_BRINGUP_PASS;
		s_diag_word = SensorTask_PackDiagWord();
		SensorTask_UpdateDebugMirrors();
			SensorLatestValue_SetInvalid(&s_latest_values[0],
			                             0u,
			                             SENSOR_VALIDITY_COMMUNICATION_ERROR,
			                             TimeService_NowUs());
	}
}

void SensorTask_Init(void)
{
	uint8_t record_index;

	Lifecycle_Init(&s_lifecycle, "AS5600_SENSOR_SERVICE");
	AS5600_InitDevice(&s_single_encoder, 0u);

	s_snapshot.result = SENSOR_TASK_BRINGUP_UNKNOWN;
	s_snapshot.init_stage = SENSOR_TASK_INIT_STAGE_MUX;
	s_snapshot.is_active = 0u;
	s_snapshot.mux_readback_mask = 0u;
	s_snapshot.last_raw_angle = 0u;
	s_snapshot.last_status = 0u;
	s_snapshot.last_timestamp_us = 0u;
	s_snapshot.sample_ok_count = 0u;
	s_snapshot.comm_error_count = 0u;
	s_snapshot.magnet_error_count = 0u;
	for (record_index = 0u; record_index < SENSOR_TASK_RECORD_COUNT; ++record_index)
	{
		SensorLatestValue_Init(&s_latest_values[record_index],
		                       record_index,
		                       record_index,
		                       SENSOR_TASK_CALIBRATION_VERSION);
	}
	s_diag_word = SensorTask_PackDiagWord();
	SensorTask_UpdateDebugMirrors();

	s_last_poll_tick = HAL_GetTick();
	(void)Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_CONFIGURE, true, 0u);
}

Lifecycle_Result SensorTask_Activate(void)
{
	return Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_ACTIVATE, true, 0u);
}

Lifecycle_State SensorTask_GetLifecycleState(void)
{
	return Lifecycle_GetState(&s_lifecycle);
}

void SensorTask_Process(void)
{
	AS5600_Sample sample;
	AS5600_Status status;
	TimeService_SyncSnapshot time_sync_snapshot;
	uint32_t now_tick = HAL_GetTick();

	if (!Lifecycle_IsActive(&s_lifecycle))
	{
		return;
	}

	if ((now_tick - s_last_poll_tick) < SENSOR_TASK_BRINGUP_POLL_PERIOD_MS)
	{
		return;
	}

	s_last_poll_tick = now_tick;

	if (s_snapshot.init_stage != SENSOR_TASK_INIT_STAGE_ACTIVE)
	{
		SensorTask_RunInitChecks();
		return;
	}

	status = AS5600_ReadSample(&s_single_encoder, &sample);

	if (status != AS5600_STATUS_OK)
	{
		s_snapshot.result = SENSOR_TASK_BRINGUP_FAIL_COMM;
		s_snapshot.comm_error_count++;
		s_diag_word = SensorTask_PackDiagWord();
		SensorTask_UpdateDebugMirrors();
		SensorLatestValue_SetInvalid(&s_latest_values[0],
		                             0u,
		                             SENSOR_VALIDITY_COMMUNICATION_ERROR,
		                             TimeService_NowUs());
		return;
	}

	s_snapshot.last_raw_angle = sample.raw_angle;
	s_snapshot.last_status = sample.status;
	s_snapshot.last_timestamp_us = sample.timestamp_us;
	TimeService_GetSyncSnapshot(&time_sync_snapshot);

	if ((sample.status & AS5600_STATUS_MD) == 0u)
	{
		s_snapshot.result = SENSOR_TASK_BRINGUP_FAIL_MAGNET_NOT_DETECTED;
		s_snapshot.magnet_error_count++;
		s_diag_word = SensorTask_PackDiagWord();
		SensorTask_UpdateDebugMirrors();
		SensorLatestValue_SetInvalid(&s_latest_values[0],
		                             sample.status,
		                             SENSOR_VALIDITY_MAGNET_NOT_DETECTED,
		                             sample.timestamp_us);
		return;
	}

	if ((sample.status & AS5600_STATUS_ML) != 0u)
	{
		s_snapshot.result = SENSOR_TASK_BRINGUP_FAIL_MAGNET_TOO_WEAK;
		s_snapshot.magnet_error_count++;
		s_diag_word = SensorTask_PackDiagWord();
		SensorTask_UpdateDebugMirrors();
		SensorLatestValue_SetInvalid(&s_latest_values[0],
		                             sample.status,
		                             SENSOR_VALIDITY_MAGNET_TOO_WEAK,
		                             sample.timestamp_us);
		return;
	}

	if ((sample.status & AS5600_STATUS_MH) != 0u)
	{
		s_snapshot.result = SENSOR_TASK_BRINGUP_FAIL_MAGNET_TOO_STRONG;
		s_snapshot.magnet_error_count++;
		s_diag_word = SensorTask_PackDiagWord();
		SensorTask_UpdateDebugMirrors();
		SensorLatestValue_SetInvalid(&s_latest_values[0],
		                             sample.status,
		                             SENSOR_VALIDITY_MAGNET_TOO_STRONG,
		                             sample.timestamp_us);
		return;
	}

	s_snapshot.result = SENSOR_TASK_BRINGUP_PASS;
	s_snapshot.sample_ok_count++;
	SensorLatestValue_SetValid(&s_latest_values[0],
	                           sample.raw_angle,
	                           (int32_t)(((uint32_t)sample.angle * 360000u) / 4096u),
	                           sample.status,
	                           sample.timestamp_us,
	                           time_sync_snapshot.quality,
	                           SENSOR_TASK_CALIBRATION_VERSION);
	s_diag_word = SensorTask_PackDiagWord();
	SensorTask_UpdateDebugMirrors();
}

SensorTask_BringupResult SensorTask_GetBringupResult(void)
{
	return s_snapshot.result;
}

const SensorTask_BringupSnapshot *SensorTask_GetBringupSnapshot(void)
{
	return &s_snapshot;
}

uint32_t SensorTask_GetBringupDiagWord(void)
{
	return s_diag_word;
}

uint8_t SensorTask_IsActive(void)
{
	return s_snapshot.is_active;
}

const Sensor_LatestValue *SensorTask_GetLatestValues(size_t *record_count)
{
	if (record_count != NULL)
	{
		*record_count = SENSOR_TASK_RECORD_COUNT;
	}

	return s_latest_values;
}
