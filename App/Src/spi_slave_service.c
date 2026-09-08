/**
 * @file spi_slave_service.c
 * @brief Lifecycle-gated coordinator for SPI protocol state, frame buffers, and DATA_READY.
 */

#include "spi_slave_service.h"

#include <string.h>

#include "main.h"

/** Service lifecycle gate that controls whether frames may be advertised. */
static Lifecycle_Record s_lifecycle;
/** Double-buffered frame pool for staged and DMA-owned SPI responses. */
static SnapshotFrame_Pool s_frame_pool;
/** Persistent protocol parser and sequence tracker for host requests. */
static SpiProtocol_State s_protocol;
/** Scratch response image used to build the next staged frame content. */
static uint8_t s_response_frame[SPI_FRAME_MAX_BYTES];
/** DATA_READY logical state and diagnostics owned by this service. */
static SpiDataReady_State s_data_ready;
/** Fallback poll interval used to recover missed DATA_READY assertions. */
static uint32_t s_poll_period_ms;
/** Tick count of the last poll used for DATA_READY recovery and stall detection. */
static uint32_t s_last_poll_tick;

#define SPI_SERVICE_DEFAULT_POLL_PERIOD_MS 1u
#define SPI_SERVICE_HOST_STALL_MS 100u

/** Drive the physical DATA_READY GPIO according to the service-owned logical state. */
static void SpiSlaveService_SetDataReadyPin(bool high)
{
	HAL_GPIO_WritePin(Data_Ready_GPIO_Port, Data_Ready_Pin, high ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

/**
 * Serialize the currently prepared response frame into the shared snapshot
 * buffer pool so the host can retrieve it on the next transaction.
 */
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

/**
 * Initialize every SPI component to its boot lifecycle: configure the service,
 * reset protocol and DATA_READY state, and preload the boot-status response.
 */
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

/** Move the SPI service into ACTIVE so staged responses can be published. */
Lifecycle_Result SpiSlaveService_Activate(void)
{
	return Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_ACTIVATE, true, 0u);
}

/** Report the lifecycle state that currently gates SPI traffic. */
Lifecycle_State SpiSlaveService_GetLifecycleState(void)
{
	return Lifecycle_GetState(&s_lifecycle);
}

/**
 * Run periodic task-context housekeeping for DATA_READY recovery while the
 * service remains active.
 */
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

/** Stage a newly serialized frame and assert DATA_READY when publication succeeds. */
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

/** Hand the staged frame to the DMA path and deassert DATA_READY on success. */
bool SpiSlaveService_BeginDmaTransfer(const uint8_t **frame_buffer, uint16_t *frame_length)
{
	bool started = Lifecycle_IsActive(&s_lifecycle) && SnapshotFramePool_BeginDma(&s_frame_pool, frame_buffer, frame_length);
	if (started && SpiDataReady_OnFrameConsumed(&s_data_ready)) { SpiSlaveService_SetDataReadyPin(false); }
	return started;
}

/** Release the DMA-owned frame once completion has been deferred to task context. */
bool SpiSlaveService_CompleteDmaTransfer(void)
{
	return SnapshotFramePool_CompleteDma(&s_frame_pool);
}

/** Expose snapshot-buffer diagnostics gathered by the frame pool. */
const SnapshotFrame_Diagnostics *SpiSlaveService_GetSnapshotDiagnostics(void)
{
	return SnapshotFramePool_GetDiagnostics(&s_frame_pool);
}

/** Expose the current DATA_READY tracking state and diagnostics. */
const SpiDataReady_State *SpiSlaveService_GetDataReadyState(void) { return &s_data_ready; }
/** Update the task-context polling cadence used for DATA_READY recovery. */
void SpiSlaveService_SetPollPeriodMs(uint32_t poll_period_ms) { s_poll_period_ms = poll_period_ms; }

/** Queue an unsolicited snapshot payload for the next eligible host request. */
bool SpiSlaveService_SetUnsolicitedSnapshot(const uint8_t *payload, uint16_t payload_length)
{
	return SpiProtocol_SetUnsolicitedSnapshot(&s_protocol, payload, payload_length);
}

/**
 * Validate a host request frame, prepare the next response, and stage it for
 * the following SPI transaction.
 */
SpiProtocol_Result SpiSlaveService_ProcessRequestFrame(const uint8_t request[SPI_FRAME_MAX_BYTES])
{
	SpiProtocol_Result result;

	if (!Lifecycle_IsActive(&s_lifecycle)) {
		return SPI_PROTOCOL_BAD_MESSAGE;
	}

	result = SpiProtocol_ProcessRequest(&s_protocol, request, s_response_frame);
	(void)SpiSlaveService_StageSnapshot(SpiSlaveService_SerializeResponse, NULL);
	return result;
}
