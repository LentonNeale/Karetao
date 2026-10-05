/**
 * @file sensor_task.c
 * @brief Implements the sensor task module.
 */

#include "sensor_task.h"

#include "as5600.h"
#include "main.h"
#include "sensor_latest_value.h"
#include "tca9548a_mux.h"
#include "time_service.h"

#define SENSOR_TASK_BRINGUP_POLL_PERIOD_MS 20u
#define SENSOR_TASK_RECORD_COUNT SENSOR_TASK_AXIS_COUNT
#define SENSOR_TASK_CALIBRATION_VERSION 0u
#define SENSOR_TASK_MIN_HEALTHY_CHANNELS 1u

static AS5600_Device s_encoders[SENSOR_TASK_RECORD_COUNT];
static SensorTask_BringupSnapshot s_snapshot;
static Sensor_LatestValue s_latest_values[SENSOR_TASK_RECORD_COUNT];
static bool s_axis_fitted[SENSOR_TASK_RECORD_COUNT];
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
	uint8_t mux_readback;
	uint64_t ts;
	uint8_t channel;
	uint32_t healthy_channels = 0u;
	uint32_t fitted_channels = 0u;

	mux_status = TCA9548A_Probe(0x01u, &mux_readback);
	if ((mux_status != I2C_MANAGER_STATUS_OK) || (mux_readback != 0x01u))
	{
		(void)Lifecycle_Fail(&s_lifecycle, (uint32_t)mux_status);
		s_snapshot.result = SENSOR_TASK_BRINGUP_FAIL_COMM;
		s_snapshot.is_active = 0u;
		s_snapshot.comm_error_count++;
		s_diag_word = SensorTask_PackDiagWord();
		SensorTask_UpdateDebugMirrors();
		return;
	}

	s_snapshot.mux_readback_mask = mux_readback;
	s_snapshot.init_stage = SENSOR_TASK_INIT_STAGE_SENSOR;

	for (channel = 0u; channel < SENSOR_TASK_RECORD_COUNT; ++channel)
	{
		uint8_t sensor_status = 0u;
		AS5600_Status sensor_result;

		if (!s_axis_fitted[channel])
		{
			SensorLatestValue_SetNotFitted(&s_latest_values[channel], TimeService_NowUs());
			continue;
		}

		fitted_channels++;
		sensor_result = AS5600_ReadStatus(&s_encoders[channel], &sensor_status, &ts);
		if (sensor_result == AS5600_STATUS_OK)
		{
			healthy_channels++;
			s_snapshot.last_status = sensor_status;
			s_snapshot.last_timestamp_us = ts;
		}
		else
		{
			s_snapshot.comm_error_count++;
			SensorLatestValue_SetInvalid(&s_latest_values[channel],
			                             0u,
			                             SENSOR_VALIDITY_COMMUNICATION_ERROR,
			                             TimeService_NowUs());
		}
	}

	/* The threshold applies to fitted axes; with none fitted there is nothing to require. */
	if ((fitted_channels > 0u) && (healthy_channels < SENSOR_TASK_MIN_HEALTHY_CHANNELS))
	{
		(void)Lifecycle_Fail(&s_lifecycle, (uint32_t)AS5600_STATUS_NOT_READY);
		s_snapshot.result = SENSOR_TASK_BRINGUP_FAIL_COMM;
		s_snapshot.is_active = 0u;
		s_diag_word = SensorTask_PackDiagWord();
		SensorTask_UpdateDebugMirrors();
		return;
	}

	s_snapshot.init_stage = SENSOR_TASK_INIT_STAGE_ACTIVE;
	s_snapshot.is_active = 1u;
	s_snapshot.result = SENSOR_TASK_BRINGUP_PASS;
	s_diag_word = SensorTask_PackDiagWord();
	SensorTask_UpdateDebugMirrors();
}

static void SensorTask_SetChannelInvalid(uint8_t channel, uint8_t status, uint16_t reason_flags)
{
	if (channel >= SENSOR_TASK_RECORD_COUNT)
	{
		return;
	}

	SensorLatestValue_SetInvalid(&s_latest_values[channel],
	                             status,
	                             reason_flags,
	                             TimeService_NowUs());
}

static void SensorTask_ProcessChannel(uint8_t channel, const TimeService_SyncSnapshot *time_sync_snapshot)
{
	AS5600_Sample sample;
	AS5600_Status status;

	status = AS5600_ReadSample(&s_encoders[channel], &sample);
	if (status != AS5600_STATUS_OK)
	{
		s_snapshot.comm_error_count++;
		SensorTask_SetChannelInvalid(channel, 0u, SENSOR_VALIDITY_COMMUNICATION_ERROR);
		return;
	}

	s_snapshot.last_raw_angle = sample.raw_angle;
	s_snapshot.last_status = sample.status;
	s_snapshot.last_timestamp_us = sample.timestamp_us;

	if ((sample.status & AS5600_STATUS_MD) == 0u)
	{
		s_snapshot.magnet_error_count++;
		SensorTask_SetChannelInvalid(channel, sample.status, SENSOR_VALIDITY_MAGNET_NOT_DETECTED);
		return;
	}

	if ((sample.status & AS5600_STATUS_ML) != 0u)
	{
		s_snapshot.magnet_error_count++;
		SensorTask_SetChannelInvalid(channel, sample.status, SENSOR_VALIDITY_MAGNET_TOO_WEAK);
		return;
	}

	if ((sample.status & AS5600_STATUS_MH) != 0u)
	{
		s_snapshot.magnet_error_count++;
		SensorTask_SetChannelInvalid(channel, sample.status, SENSOR_VALIDITY_MAGNET_TOO_STRONG);
		return;
	}

	s_snapshot.result = SENSOR_TASK_BRINGUP_PASS;
	s_snapshot.sample_ok_count++;
	SensorLatestValue_SetValid(&s_latest_values[channel],
	                           sample.raw_angle,
	                           (int32_t)(((uint32_t)sample.angle * 360000u) / 4096u),
	                           sample.magnitude,
	                           sample.agc,
	                           sample.status,
	                           sample.timestamp_us,
	                           time_sync_snapshot->quality,
	                           SENSOR_TASK_CALIBRATION_VERSION);
}

void SensorTask_Init(void)
{
	uint8_t record_index;

	Lifecycle_Init(&s_lifecycle, "AS5600_SENSOR_SERVICE");

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

	/*
	 * Identity axis-to-mux binding is only a safe starting state so the encoder
	 * table is never uninitialized. The commissioned binding is applied by
	 * SensorTask_ConfigureMuxChannels(); App_Init() blocks activation when that
	 * call is missing or rejected.
	 */
	for (record_index = 0u; record_index < SENSOR_TASK_RECORD_COUNT; ++record_index)
	{
		AS5600_InitDevice(&s_encoders[record_index], record_index);
		s_axis_fitted[record_index] = true;
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

bool SensorTask_ConfigureMuxChannels(const uint8_t *mux_channels, size_t count)
{
	size_t axis;
	size_t other;

	if ((mux_channels == NULL) || (count != SENSOR_TASK_RECORD_COUNT))
	{
		return false;
	}

	/* Rebinding a live acquisition path would silently change joint identity. */
	if (Lifecycle_IsActive(&s_lifecycle))
	{
		return false;
	}

	/* Validate the whole map first so a rejected map changes nothing. */
	for (axis = 0u; axis < count; ++axis)
	{
		if (mux_channels[axis] > SENSOR_TASK_MAX_MUX_CHANNEL)
		{
			return false;
		}

		for (other = 0u; other < axis; ++other)
		{
			if (mux_channels[axis] == mux_channels[other])
			{
				return false;
			}
		}
	}

	for (axis = 0u; axis < count; ++axis)
	{
		AS5600_InitDevice(&s_encoders[axis], mux_channels[axis]);
	}

	return true;
}

bool SensorTask_ConfigureFittedAxes(const bool *encoder_fitted, size_t count)
{
	size_t axis;

	if ((encoder_fitted == NULL) || (count != SENSOR_TASK_RECORD_COUNT))
	{
		return false;
	}

	/* Changing which axes are read on a live acquisition path is not allowed. */
	if (Lifecycle_IsActive(&s_lifecycle))
	{
		return false;
	}

	for (axis = 0u; axis < count; ++axis)
	{
		s_axis_fitted[axis] = encoder_fitted[axis];
		if (!s_axis_fitted[axis])
		{
			SensorLatestValue_SetNotFitted(&s_latest_values[axis], TimeService_NowUs());
		}
	}

	return true;
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
	TimeService_SyncSnapshot time_sync_snapshot;
	uint32_t now_tick = HAL_GetTick();
	uint8_t channel;

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

	TimeService_GetSyncSnapshot(&time_sync_snapshot);

	/*
	 * The loop index is the logical axis and record position, not the mux
	 * channel. The mux channel is whatever the bound encoder carries.
	 */
	for (channel = 0u; channel < SENSOR_TASK_RECORD_COUNT; ++channel)
	{
		if (!s_axis_fitted[channel])
		{
			SensorLatestValue_SetNotFitted(&s_latest_values[channel], TimeService_NowUs());
			continue;
		}

		SensorTask_ProcessChannel(channel, &time_sync_snapshot);
	}

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
