#include "spi_slave_service.h"

#include <string.h>

#include "main.h"
#include "time_service.h"

static Lifecycle_Record s_lifecycle;
static SnapshotFrame_Pool s_frame_pool;
static SpiProtocol_State s_protocol;
static uint8_t s_response_frame[SPI_FRAME_MAX_BYTES];
static SpiDataReady_State s_data_ready;
static uint32_t s_poll_period_ms;
static uint32_t s_last_poll_tick;

#define SPI_SERVICE_DEFAULT_POLL_PERIOD_MS 1u
#define SPI_SERVICE_HOST_STALL_MS 100u

static void SpiSlaveService_SetDataReadyPin(bool high)
{
	HAL_GPIO_WritePin(Data_Ready_GPIO_Port, Data_Ready_Pin, high ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

static bool SpiSlaveService_SerializeResponse(uint8_t *frame_buffer,
											  uint16_t frame_capacity,
											  uint16_t *frame_length,
											  void *context)
{
	(void)context;

	if ((frame_capacity < SPI_FRAME_MAX_BYTES) || (frame_length == NULL)) {
		return false;
	}

	memcpy(frame_buffer, s_response_frame, SPI_FRAME_MAX_BYTES);
	*frame_length = SPI_FRAME_MAX_BYTES;
	return true;
}

static bool SpiSlaveService_RequestAllowed(uint8_t request_type)
{
	Lifecycle_State state = Lifecycle_GetState(&s_lifecycle);

	if (request_type == SPI_MESSAGE_TIME_SYNC) {
		return (state == LIFECYCLE_STATE_INACTIVE) || (state == LIFECYCLE_STATE_ACTIVE);
	}

	return state == LIFECYCLE_STATE_ACTIVE;
}

static void SpiSlaveService_StageResponseFrame(void)
{
	if (SnapshotBuilder_Stage(&s_frame_pool, SpiSlaveService_SerializeResponse, NULL) == SNAPSHOT_BUILD_OK &&
		Lifecycle_IsActive(&s_lifecycle) &&
		SpiDataReady_OnFrameStaged(&s_data_ready, HAL_GetTick())) {
		SpiSlaveService_SetDataReadyPin(true);
	}
}

void SpiSlaveService_Init(void)
{
	Lifecycle_Init(&s_lifecycle, "SPI3");
	SnapshotFramePool_Init(&s_frame_pool);
	SpiProtocol_Init(&s_protocol);
	SpiDataReady_Init(&s_data_ready);
	s_poll_period_ms = SPI_SERVICE_DEFAULT_POLL_PERIOD_MS;
	s_last_poll_tick = HAL_GetTick();
	SpiSlaveService_SetDataReadyPin(false);
	(void)SpiProtocol_BuildBootStatus(&s_protocol, s_response_frame);
	(void)Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_CONFIGURE, true, 0u);
}

Lifecycle_Result SpiSlaveService_Activate(void)
{
	return Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_ACTIVATE, true, 0u);
}

Lifecycle_State SpiSlaveService_GetLifecycleState(void)
{
	return Lifecycle_GetState(&s_lifecycle);
}

void SpiSlaveService_Process(void)
{
	if (!Lifecycle_IsActive(&s_lifecycle)) {
		return;
	}
	if ((HAL_GetTick() - s_last_poll_tick) >= s_poll_period_ms) {
		uint16_t frame_length;
		bool staged = SnapshotFramePool_GetStagedFrame(&s_frame_pool, &frame_length) != NULL;
		s_last_poll_tick = HAL_GetTick();
		if (SpiDataReady_Poll(&s_data_ready, staged, s_last_poll_tick, SPI_SERVICE_HOST_STALL_MS)) {
			SpiSlaveService_SetDataReadyPin(true);
		}
	}
}

SnapshotBuild_Result SpiSlaveService_StageSnapshot(SnapshotBuilder_SerializeCallback serialize, void *context)
{
	if (!Lifecycle_IsActive(&s_lifecycle)) {
		return SNAPSHOT_BUILD_NOT_READY;
	}

	SnapshotBuild_Result result = SnapshotBuilder_Stage(&s_frame_pool, serialize, context);
	if ((result == SNAPSHOT_BUILD_OK) && SpiDataReady_OnFrameStaged(&s_data_ready, HAL_GetTick())) {
		SpiSlaveService_SetDataReadyPin(true);
	}
	return result;
}

bool SpiSlaveService_BeginDmaTransfer(const uint8_t **frame_buffer, uint16_t *frame_length)
{
	bool started = Lifecycle_IsActive(&s_lifecycle) && SnapshotFramePool_BeginDma(&s_frame_pool, frame_buffer, frame_length);
	if (started && SpiDataReady_OnFrameConsumed(&s_data_ready)) { SpiSlaveService_SetDataReadyPin(false); }
	return started;
}

bool SpiSlaveService_CompleteDmaTransfer(void)
{
	return SnapshotFramePool_CompleteDma(&s_frame_pool);
}

const SnapshotFrame_Diagnostics *SpiSlaveService_GetSnapshotDiagnostics(void)
{
	return SnapshotFramePool_GetDiagnostics(&s_frame_pool);
}

const SpiDataReady_State *SpiSlaveService_GetDataReadyState(void) { return &s_data_ready; }
void SpiSlaveService_SetPollPeriodMs(uint32_t poll_period_ms) { s_poll_period_ms = poll_period_ms; }

bool SpiSlaveService_SetUnsolicitedSnapshot(const uint8_t *payload, uint16_t payload_length)
{
	return SpiProtocol_SetUnsolicitedSnapshot(&s_protocol, payload, payload_length);
}

SpiProtocol_Result SpiSlaveService_ProcessRequestFrame(const uint8_t request[SPI_FRAME_MAX_BYTES])
{
	SpiProtocol_TimeSyncRequest time_sync;
	SpiProtocol_Result result;
	TimeService_SyncResult sync_result;
	uint8_t request_type;

	if (request == NULL) {
		return SPI_PROTOCOL_BAD_MESSAGE;
	}

	request_type = request[3];
	if (!SpiSlaveService_RequestAllowed(request_type)) {
		return SPI_PROTOCOL_BAD_MESSAGE;
	}

	result = SpiProtocol_ProcessRequest(&s_protocol, request, s_response_frame);
	if ((result == SPI_PROTOCOL_OK) && (request_type == SPI_MESSAGE_TIME_SYNC)) {
		result = SpiProtocol_ParseTimeSyncRequest(request, &time_sync);
		if (result == SPI_PROTOCOL_OK) {
			sync_result = TimeService_AcceptSync(time_sync.pi_time_us, time_sync.sync_sequence);
			if (sync_result != TIME_SERVICE_SYNC_ACCEPTED) {
				SpiProtocol_BuildCommandReply(&s_protocol, SPI_MESSAGE_NACK, request_type,
											  time_sync.request_sequence, SPI_PROTOCOL_BAD_TIME_SYNC,
											  (uint32_t)sync_result, s_response_frame);
				result = SPI_PROTOCOL_BAD_TIME_SYNC;
			}
		}
	}
	SpiSlaveService_StageResponseFrame();
	return result;
}
