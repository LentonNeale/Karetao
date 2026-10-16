/**
 * @file can_service.c
 * @brief Implements the can service module.
 */

#include "can_service.h"
#include "can_tx_policy.h"
#include "latest_value.h"

#include <string.h>

#include "main.h"
#include "time_service.h"

extern CAN_HandleTypeDef hcan1;

typedef struct {
	bool registered;
	MksDevice device;
	bool has_last_response;
	MksParsedResponse last_response;
	uint32_t rx_ok_count;
	uint32_t rx_decode_error_count;
} CanService_MotorSlot;

static CanService_MotorSlot s_motor_slots[CAN_SERVICE_MAX_MKS_MOTORS];
static bool s_can_started;
static Lifecycle_Record s_lifecycle;
static uint32_t s_poll_period_ms;
static uint32_t s_last_poll_tick;
static uint8_t s_poll_motor_index;
static uint8_t s_poll_phase;
static CanTx_Queue s_tx_queue;
static CanBusOff_State s_bus_off;
static uint32_t s_tx_retry_exhausted_count;
static uint32_t s_bus_off_count;

#define CAN_SERVICE_MAX_TX_RETRIES 3u
#define CAN_SERVICE_BUS_OFF_FAULT_CODE 1u
/* MKS read replies (icm-project/references/mks-servo42d-57d-can/read-commands.md), big-endian
 * (manual p. 14). The scheduler polls 30H, which carries an int32 carry and a uint16 value of
 * 0..0x3FFF (one carry per motor turn, p. 26); 32H carries the speed as int16 rpm (p. 27). The
 * move to 31H (int48 cumulative value, the same 0x4000-per-turn unit) is ruling R11, GitHub #61. */
#define CAN_SERVICE_MKS_READ_ENCODER 0x30u
#define CAN_SERVICE_MKS_READ_SPEED 0x32u
#define CAN_SERVICE_ENCODER_REPLY_BYTES 6u
#define CAN_SERVICE_ENCODER_COUNTS_PER_CARRY 0x4000
#define CAN_SERVICE_SPEED_REPLY_BYTES 2u

_Static_assert(CAN_SERVICE_MAX_MKS_MOTORS == LATEST_VALUE_MOTOR_COUNT,
               "Each drive slot is one latest-value motor slot");
_Static_assert(CAN_SERVICE_ENCODER_REPLY_BYTES == LATEST_VALUE_POSITION_REPLY_BYTES,
               "The store keeps the whole encoder reply");

static MksStatus CanService_TransmitFrame(const MksCanFrame *frame);

/**
 * @brief Executes service process bus off.
 */
static void CanService_ProcessBusOff(void)
{
	uint32_t now_ms = HAL_GetTick();

	if ((HAL_CAN_GetError(&hcan1) & HAL_CAN_ERROR_BOF) != 0u) {
		if (s_can_started) {
			s_can_started = false;
			s_bus_off_count++;
			if (CanBusOff_Record(&s_bus_off, now_ms)) {
				(void)Lifecycle_Fail(&s_lifecycle, CAN_SERVICE_BUS_OFF_FAULT_CODE);
			}
			(void)HAL_CAN_Stop(&hcan1);
		}
	}

	if (CanBusOff_RecoveryDue(&s_bus_off, now_ms)) {
		bool recovered = HAL_CAN_Start(&hcan1) == HAL_OK;
		CanBusOff_RecoveryResult(&s_bus_off, recovered, now_ms);
		if (recovered) {
			s_can_started = true;
			if (Lifecycle_GetState(&s_lifecycle) == LIFECYCLE_STATE_ERROR) {
				(void)Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_RECOVER, true, 0u);
			}
		}
	}
}

/**
 * @brief Executes service queue frame.
 */
static MksStatus CanService_QueueFrame(const MksCanFrame *frame, CanTx_Priority priority)
{
	CanTx_Frame queued_frame;

	if ((frame == NULL) || (frame->dlc > MKS_MAX_DLC) || !Lifecycle_IsActive(&s_lifecycle) ||
		(priority != CAN_TX_PRIORITY_SAFETY && s_bus_off.normal_commands_inhibited)) {
		return MKS_INVALID_ARGUMENT;
	}

	queued_frame.id = frame->id;
	queued_frame.dlc = frame->dlc;
	memcpy(queued_frame.data, frame->data, sizeof(queued_frame.data));
	return CanTxQueue_Enqueue(&s_tx_queue, &queued_frame, priority) ? MKS_OK : MKS_INVALID_ARGUMENT;
}

/**
 * @brief Executes service drain tx queue.
 */
static void CanService_DrainTxQueue(void)
{
	CanTx_Entry entry;
	MksCanFrame frame;

	if (!s_can_started || !Lifecycle_IsActive(&s_lifecycle) || s_bus_off.normal_commands_inhibited ||
		!CanTxQueue_Dequeue(&s_tx_queue, &entry)) {
		return;
	}

	frame.id = entry.frame.id;
	frame.dlc = entry.frame.dlc;
	memcpy(frame.data, entry.frame.data, sizeof(frame.data));
	if (CanService_TransmitFrame(&frame) != MKS_OK) {
		entry.retry_count++;
		if ((entry.retry_count <= CAN_SERVICE_MAX_TX_RETRIES) && CanTxQueue_Requeue(&s_tx_queue, &entry)) {
			return;
		}
		s_tx_retry_exhausted_count++;
	}
}

/**
 * @brief Executes service config accept all filter.
 */
static HAL_StatusTypeDef CanService_ConfigAcceptAllFilter(void)
{
	CAN_FilterTypeDef filter;

	memset(&filter, 0, sizeof(filter));
	filter.FilterBank = 0;
	filter.FilterMode = CAN_FILTERMODE_IDMASK;
	filter.FilterScale = CAN_FILTERSCALE_32BIT;
	filter.FilterIdHigh = 0;
	filter.FilterIdLow = 0;
	filter.FilterMaskIdHigh = 0;
	filter.FilterMaskIdLow = 0;
	filter.FilterFIFOAssignment = CAN_RX_FIFO0;
	filter.FilterActivation = ENABLE;
	filter.SlaveStartFilterBank = 14;

	return HAL_CAN_ConfigFilter(&hcan1, &filter);
}

/**
 * @brief Executes service find motor index by can id.
 */
static int32_t CanService_FindMotorIndexByCanId(uint16_t can_id)
{
	uint8_t i;

	for (i = 0U; i < CAN_SERVICE_MAX_MKS_MOTORS; ++i) {
		if (s_motor_slots[i].registered && (s_motor_slots[i].device.default_can_id == can_id)) {
			return (int32_t)i;
		}
	}

	return -1;
}

/**
 * Turns a decoded position or speed reply into typed feedback for the latest-value store.
 * Returns false for every other reply (acknowledgements do not enter the snapshot, ruling R10).
 */
static bool CanService_DecodeFeedback(const MksParsedResponse *parsed, uint64_t timestamp_us,
                                      LatestValue_Feedback *feedback)
{
	memset(feedback, 0, sizeof(*feedback));
	feedback->timestamp_us = timestamp_us;
	/* The decoder's has_status guess (first payload byte 0 or 1) is not used: an encoder reply
	 * has no status byte, so its top data byte would be read as a drive status. */
	if ((parsed->code == CAN_SERVICE_MKS_READ_ENCODER) && (parsed->payload_len == CAN_SERVICE_ENCODER_REPLY_BYTES)) {
		const uint8_t *p = parsed->payload;
		int32_t carry = (int32_t)(((uint32_t)p[0] << 24u) | ((uint32_t)p[1] << 16u) |
		                          ((uint32_t)p[2] << 8u) | (uint32_t)p[3]);
		uint16_t value = (uint16_t)(((uint16_t)p[4] << 8u) | p[5]);

		feedback->kind = LATEST_VALUE_FEEDBACK_POSITION;
		feedback->position_counts = ((int64_t)carry * CAN_SERVICE_ENCODER_COUNTS_PER_CARRY) + (int64_t)value;
		feedback->position_command_code = parsed->code;
		memcpy(feedback->position_reply, parsed->payload, CAN_SERVICE_ENCODER_REPLY_BYTES);
		return true;
	}
	if ((parsed->code == CAN_SERVICE_MKS_READ_SPEED) && (parsed->payload_len == CAN_SERVICE_SPEED_REPLY_BYTES)) {
		feedback->kind = LATEST_VALUE_FEEDBACK_SPEED;
		feedback->speed_rpm = (int16_t)(uint16_t)(((uint16_t)parsed->payload[0] << 8u) | parsed->payload[1]);
		return true;
	}
	return false;
}

/**
 * @brief Executes service process rx frames.
 */
static void CanService_ProcessRxFrames(void)
{
	while (HAL_CAN_GetRxFifoFillLevel(&hcan1, CAN_RX_FIFO0) > 0U) {
		CAN_RxHeaderTypeDef rx_header;
		uint8_t rx_data[MKS_MAX_DLC] = {0};
		MksCanFrame frame;
		MksParsedResponse parsed;
		int32_t motor_index;

		if (HAL_CAN_GetRxMessage(&hcan1, CAN_RX_FIFO0, &rx_header, rx_data) != HAL_OK) {
			break;
		}

		if ((rx_header.IDE != CAN_ID_STD) || (rx_header.DLC > MKS_MAX_DLC)) {
			continue;
		}

		frame.id = (uint16_t)(rx_header.StdId & 0x7FFu);
		frame.dlc = (uint8_t)rx_header.DLC;
		memcpy(frame.data, rx_data, frame.dlc);

		motor_index = CanService_FindMotorIndexByCanId(frame.id);
		if (motor_index < 0) {
			continue;
		}

		if (mks_decode(&frame, &parsed) == MKS_OK) {
			LatestValue_Feedback feedback;

			s_motor_slots[motor_index].has_last_response = true;
			s_motor_slots[motor_index].last_response = parsed;
			s_motor_slots[motor_index].rx_ok_count++;
			if (CanService_DecodeFeedback(&parsed, TimeService_NowUs(), &feedback)) {
				(void)LatestValue_AcceptFeedback((uint8_t)motor_index, &feedback);
			}
		} else {
			/* The record is not touched: it goes stale by age (latest_value.h). */
			s_motor_slots[motor_index].rx_decode_error_count++;
		}
	}
}

/**
 * @brief Executes service run poll scheduler.
 */
static void CanService_RunPollScheduler(void)
{
	uint8_t attempts;
	uint8_t selected_index;
	MksStatus poll_status;

	if (s_poll_period_ms == 0U) {
		return;
	}

	if ((HAL_GetTick() - s_last_poll_tick) < s_poll_period_ms) {
		return;
	}

	s_last_poll_tick = HAL_GetTick();
	selected_index = CAN_SERVICE_MAX_MKS_MOTORS;

	for (attempts = 0U; attempts < CAN_SERVICE_MAX_MKS_MOTORS; ++attempts) {
		uint8_t candidate = (uint8_t)((s_poll_motor_index + attempts) % CAN_SERVICE_MAX_MKS_MOTORS);
		if (s_motor_slots[candidate].registered) {
			selected_index = candidate;
			break;
		}
	}

	if (selected_index == CAN_SERVICE_MAX_MKS_MOTORS) {
		return;
	}

	if (s_poll_phase == 0U) {
		poll_status = CanService_RequestEncoderValue(selected_index);
		s_poll_phase = 1U;
	} else {
		poll_status = CanService_RequestRealtimeSpeed(selected_index);
		s_poll_phase = 0U;
		s_poll_motor_index = (uint8_t)((selected_index + 1U) % CAN_SERVICE_MAX_MKS_MOTORS);
	}

	if (poll_status != MKS_OK) {
		/* Keep scheduler running; failed polls are reflected in response counters. */
	}
}

/**
 * @brief Executes service get motor device.
 */
static MksStatus CanService_GetMotorDevice(uint8_t motor_index, const MksDevice** out_device)
{
	if (out_device == NULL) {
		return MKS_NULL_POINTER;
	}

	if (motor_index >= CAN_SERVICE_MAX_MKS_MOTORS) {
		return MKS_INVALID_ARGUMENT;
	}

	if (!s_motor_slots[motor_index].registered) {
		return MKS_INVALID_ARGUMENT;
	}

	*out_device = &s_motor_slots[motor_index].device;
	return MKS_OK;
}

/**
 * @brief Executes service transmit frame.
 */
static MksStatus CanService_TransmitFrame(const MksCanFrame* frame)
{
	CAN_TxHeaderTypeDef header;
	uint8_t tx_data[MKS_MAX_DLC];
	uint32_t tx_mailbox = 0U;
	HAL_StatusTypeDef hal_status;

	if (frame == NULL) {
		return MKS_NULL_POINTER;
	}

	if (frame->dlc > MKS_MAX_DLC) {
		return MKS_INVALID_DLC;
	}

	if (!s_can_started || !Lifecycle_IsActive(&s_lifecycle)) {
		return MKS_INVALID_ARGUMENT;
	}

	memset(&header, 0, sizeof(header));
	memset(tx_data, 0, sizeof(tx_data));
	memcpy(tx_data, frame->data, frame->dlc);

	header.StdId = frame->id & 0x7FFu;
	header.ExtId = 0U;
	header.IDE = CAN_ID_STD;
	header.RTR = CAN_RTR_DATA;
	header.DLC = frame->dlc;
	header.TransmitGlobalTime = DISABLE;

	hal_status = HAL_CAN_AddTxMessage(&hcan1, &header, tx_data, &tx_mailbox);
	if (hal_status != HAL_OK) {
		return MKS_INVALID_ARGUMENT;
	}

	return MKS_OK;
}

/**
 * @brief Executes service init.
 */
void CanService_Init(void)
{
	uint8_t i;

	Lifecycle_Init(&s_lifecycle, "CAN1");
	s_can_started = false;
	for (i = 0U; i < CAN_SERVICE_MAX_MKS_MOTORS; ++i) {
		s_motor_slots[i].registered = false;
		s_motor_slots[i].device.default_can_id = 0U;
		s_motor_slots[i].device.max_working_current_ma = 0U;
		s_motor_slots[i].has_last_response = false;
		memset(&s_motor_slots[i].last_response, 0, sizeof(s_motor_slots[i].last_response));
		s_motor_slots[i].rx_ok_count = 0U;
		s_motor_slots[i].rx_decode_error_count = 0U;
	}

	s_poll_period_ms = CAN_SERVICE_DEFAULT_POLL_PERIOD_MS;
	s_last_poll_tick = HAL_GetTick();
	s_poll_motor_index = 0U;
	s_poll_phase = 0U;
	CanTxQueue_Init(&s_tx_queue);
	CanBusOff_Init(&s_bus_off);
	s_tx_retry_exhausted_count = 0u;
	s_bus_off_count = 0u;

	if ((CanService_ConfigAcceptAllFilter() == HAL_OK) && (HAL_CAN_Start(&hcan1) == HAL_OK)) {
		s_can_started = true;
		(void)Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_CONFIGURE, true, 0u);
	} else {
		(void)Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_CONFIGURE, false, 1u);
	}
}

/**
 * @brief Executes service activate.
 */
Lifecycle_Result CanService_Activate(void)
{
	Lifecycle_Result result = Lifecycle_Apply(&s_lifecycle,
	                                          LIFECYCLE_TRANSITION_ACTIVATE,
	                                          s_can_started,
	                                          CAN_SERVICE_BUS_OFF_FAULT_CODE);
	if (result == LIFECYCLE_RESULT_OK) {
		CanBusOff_AllowNormalCommands(&s_bus_off);
	}
	return result;
}

/**
 * @brief Executes service get lifecycle state.
 */
Lifecycle_State CanService_GetLifecycleState(void)
{
	return Lifecycle_GetState(&s_lifecycle);
}

/**
 * @brief Executes service process.
 */
void CanService_Process(void)
{
	CanService_ProcessBusOff();
	if (s_can_started && Lifecycle_IsActive(&s_lifecycle)) {
		CanService_ProcessRxFrames();
		CanService_RunPollScheduler();
		CanService_DrainTxQueue();
	}
}

MksStatus CanService_RegisterMotor(uint8_t motor_index,
								   CanService_MksModel model,
								   uint16_t can_id)
{
	MksDevice device;

	if (motor_index >= CAN_SERVICE_MAX_MKS_MOTORS) {
		return MKS_INVALID_ARGUMENT;
	}

	if (can_id > 0x7FFu) {
		return MKS_CAN_ID_OUT_OF_RANGE;
	}

	if (model == CAN_SERVICE_MKS_SERVO42) {
		device = mks_device_servo42(can_id);
	} else if (model == CAN_SERVICE_MKS_SERVO57) {
		device = mks_device_servo57(can_id);
	} else {
		return MKS_INVALID_ARGUMENT;
	}

	s_motor_slots[motor_index].device = device;
	s_motor_slots[motor_index].registered = true;
	s_motor_slots[motor_index].has_last_response = false;
	memset(&s_motor_slots[motor_index].last_response, 0, sizeof(s_motor_slots[motor_index].last_response));
	s_motor_slots[motor_index].rx_ok_count = 0U;
	s_motor_slots[motor_index].rx_decode_error_count = 0U;
	return MKS_OK;
}

/**
 * @brief Executes service send motor enable.
 */
MksStatus CanService_SendMotorEnable(uint8_t motor_index, bool enable)
{
	const MksDevice* device;
	MksCanFrame frame;
	MksStatus status;

	status = CanService_GetMotorDevice(motor_index, &device);
	if (status != MKS_OK) {
		return status;
	}

	status = mks_encode_set_motor_enable(device, enable, &frame, MKS_CAN_ID_DEFAULT);
	if (status != MKS_OK) {
		return status;
	}

	return CanService_QueueFrame(&frame, CAN_TX_PRIORITY_MOTION);
}

/**
 * @brief Executes service set poll period ms.
 */
void CanService_SetPollPeriodMs(uint32_t period_ms)
{
	s_poll_period_ms = period_ms;
}

uint32_t CanService_GetTxQueueDropCount(void) { return s_tx_queue.dropped_count; }
uint32_t CanService_GetTxRetryExhaustedCount(void) { return s_tx_retry_exhausted_count; }
uint32_t CanService_GetBusOffCount(void) { return s_bus_off_count; }

/**
 * @brief Executes service get last response.
 */
bool CanService_GetLastResponse(uint8_t motor_index, MksParsedResponse *out_response)
{
	if ((out_response == NULL) || (motor_index >= CAN_SERVICE_MAX_MKS_MOTORS)) {
		return false;
	}

	if (!s_motor_slots[motor_index].has_last_response) {
		return false;
	}

	*out_response = s_motor_slots[motor_index].last_response;
	return true;
}

/**
 * @brief Executes service get rx ok count.
 */
uint32_t CanService_GetRxOkCount(uint8_t motor_index)
{
	if (motor_index >= CAN_SERVICE_MAX_MKS_MOTORS) {
		return 0U;
	}

	return s_motor_slots[motor_index].rx_ok_count;
}

/**
 * @brief Executes service get rx decode error count.
 */
uint32_t CanService_GetRxDecodeErrorCount(uint8_t motor_index)
{
	if (motor_index >= CAN_SERVICE_MAX_MKS_MOTORS) {
		return 0U;
	}

	return s_motor_slots[motor_index].rx_decode_error_count;
}

/**
 * @brief Executes service send emergency stop.
 */
MksStatus CanService_SendEmergencyStop(uint8_t motor_index)
{
	const MksDevice* device;
	MksCanFrame frame;
	MksStatus status;

	status = CanService_GetMotorDevice(motor_index, &device);
	if (status != MKS_OK) {
		return status;
	}

	status = mks_encode_emergency_stop(device, &frame, MKS_CAN_ID_DEFAULT);
	if (status != MKS_OK) {
		return status;
	}

	return CanService_QueueFrame(&frame, CAN_TX_PRIORITY_SAFETY);
}

/**
 * @brief Executes service send absolute pulse move.
 */
MksStatus CanService_SendAbsolutePulseMove(uint8_t motor_index, uint16_t speed, uint8_t acc, int32_t absolute_pulses)
{
	const MksDevice* device;
	MksCanFrame frame;
	MksStatus status;

	status = CanService_GetMotorDevice(motor_index, &device);
	if (status != MKS_OK) {
		return status;
	}

	status = mks_encode_absolute_pulse_move(device, speed, acc, absolute_pulses, &frame, MKS_CAN_ID_DEFAULT);
	if (status != MKS_OK) {
		return status;
	}

	return CanService_QueueFrame(&frame, CAN_TX_PRIORITY_MOTION);
}

MksStatus CanService_SendRelativePulseMove(uint8_t motor_index, bool dir_cw, uint16_t speed, uint8_t acc,
										   uint32_t relative_pulses)
{
	const MksDevice* device;
	MksCanFrame frame;
	MksStatus status;

	status = CanService_GetMotorDevice(motor_index, &device);
	if (status != MKS_OK) {
		return status;
	}

	status = mks_encode_relative_pulse_move(device, dir_cw, speed, acc, relative_pulses, &frame, MKS_CAN_ID_DEFAULT);
	if (status != MKS_OK) {
		return status;
	}

	return CanService_QueueFrame(&frame, CAN_TX_PRIORITY_MOTION);
}

/**
 * @brief Executes service request encoder value.
 */
MksStatus CanService_RequestEncoderValue(uint8_t motor_index)
{
	const MksDevice* device;
	MksCanFrame frame;
	MksStatus status;

	status = CanService_GetMotorDevice(motor_index, &device);
	if (status != MKS_OK) {
		return status;
	}

	status = mks_encode_encoder_value(device, &frame, MKS_CAN_ID_DEFAULT);
	if (status != MKS_OK) {
		return status;
	}

	return CanService_QueueFrame(&frame, CAN_TX_PRIORITY_POLL);
}

/**
 * @brief Executes service request realtime speed.
 */
MksStatus CanService_RequestRealtimeSpeed(uint8_t motor_index)
{
	const MksDevice* device;
	MksCanFrame frame;
	MksStatus status;

	status = CanService_GetMotorDevice(motor_index, &device);
	if (status != MKS_OK) {
		return status;
	}

	status = mks_encode_realtime_speed(device, &frame, MKS_CAN_ID_DEFAULT);
	if (status != MKS_OK) {
		return status;
	}

	return CanService_QueueFrame(&frame, CAN_TX_PRIORITY_POLL);
}
