#include "spi_slave_service.h"

#include <stdatomic.h>
#include <string.h>

#include "latest_value.h"
#include "le_bytes.h"
#include "main.h"
#include "time_service.h"

extern SPI_HandleTypeDef hspi3;

static Lifecycle_Record s_lifecycle;
static SnapshotFrame_Pool s_frame_pool;
static SpiProtocol_State s_protocol;
static uint8_t s_response_frame[SPI_FRAME_MAX_BYTES];
static uint8_t s_rx_frame[SPI_FRAME_MAX_BYTES];
static uint8_t s_pending_request[SPI_FRAME_MAX_BYTES];
static volatile bool s_dma_active;
static volatile bool s_request_pending;
static volatile bool s_dma_error;
static uint32_t s_dma_start_tick;
static SpiDataReady_State s_data_ready;
static uint32_t s_poll_period_ms;
static uint32_t s_last_poll_tick;

/**
 * @brief Debug mirror for SPI transaction timing (SWD readout).
 *
 * Tracks timestamps at four critical points: DMA complete (ISR), process entry,
 * response staged, and DATA_READY assertion.
 */
volatile SpiSlaveService_TimingMirror g_spi_timing_dbg = {0};

/**
 * @brief Capture of last request type and sequence for timing mirror.
 */
static uint8_t s_last_request_type;
static uint32_t s_last_request_seq;

#define SPI_SERVICE_DEFAULT_POLL_PERIOD_MS 1u
#define SPI_SERVICE_HOST_STALL_MS 100u

static void SpiSlaveService_SetDataReadyPin(bool high)
{
    HAL_GPIO_WritePin(Data_Ready_GPIO_Port, Data_Ready_Pin, high ? GPIO_PIN_SET : GPIO_PIN_RESET);
    /* Capture DATA_READY assertion time and update mirror with request metadata. */
    if (high) {
        g_spi_timing_dbg.data_ready_set_us = TimeService_NowUs();
        g_spi_timing_dbg.request_type = s_last_request_type;
        g_spi_timing_dbg.request_seq = s_last_request_seq;
    }
}

static bool SpiSlaveService_SerializeResponse(uint8_t *frame_buffer,
                                               uint16_t frame_capacity,
                                               uint16_t *frame_length,
                                               void *context)
{
    (void)context;
    if ((frame_buffer == NULL) || (frame_length == NULL) || (frame_capacity < SPI_FRAME_MAX_BYTES)) return false;
    memcpy(frame_buffer, s_response_frame, SPI_FRAME_MAX_BYTES);
    *frame_length = SPI_FRAME_MAX_BYTES;
    return true;
}

static bool SpiSlaveService_ArmDma(void)
{
    const uint8_t *tx_frame;
    uint16_t frame_length;

    if (s_dma_active || s_request_pending || !Lifecycle_IsActive(&s_lifecycle)) return false;
    if (!SpiSlaveService_BeginDmaTransfer(&tx_frame, &frame_length)) return false;
    (void)frame_length;

    memset(s_rx_frame, 0, sizeof(s_rx_frame));
    if (HAL_SPI_TransmitReceive_DMA(&hspi3, tx_frame, s_rx_frame, SPI_FRAME_MAX_BYTES) != HAL_OK) {
        (void)SpiSlaveService_CompleteDmaTransfer();
        return false;
    }

    s_dma_active = true;
    s_dma_start_tick = HAL_GetTick();
    return true;
}

static bool SpiSlaveService_PublishStagedFrame(void)
{
    uint16_t frame_length;

    if (!Lifecycle_IsActive(&s_lifecycle)) return false;
    if ((SnapshotFramePool_GetStagedFrame(&s_frame_pool, &frame_length) != NULL) &&
        SpiDataReady_OnFrameStaged(&s_data_ready, HAL_GetTick())) {
        if (SpiSlaveService_ArmDma()) {
            SpiSlaveService_SetDataReadyPin(true);
            return true;
        }
    }
    return false;
}

/* The latest-value copy and the snapshot payload live here, not on the calling task's stack:
 * together they are larger than the rest of the deepest call path (PRM-9). They are used only
 * inside SpiSlaveService_StageAndPublish, whose guard also covers the frame pool. */
static LatestValue_Snapshot s_snapshot_copy;
static uint8_t s_snapshot_payload[SPI_SNAPSHOT_MAX_PAYLOAD_BYTES];

/* Staging writes the frame pool, and for a snapshot the shared copy and payload buffers, so
 * one stage-and-publish runs at a time. SpiSlaveService_StageSnapshot is public;
 * a caller that arrives while another is staging gets SNAPSHOT_BUILD_BUSY, never a
 * frame mixing two snapshots under a valid CRC. */
static atomic_flag s_staging_busy = ATOMIC_FLAG_INIT;

/* Every snapshot is built from a fresh coherent copy of the latest-value store, serialised by
 * the protocol module (SPI_SYSTEM_INTERFACE.md section 8). */
static bool SpiSlaveService_BuildLatestSnapshot(LatestValue_Snapshot *copy,
                                                uint8_t *payload,
                                                uint8_t *frame_buffer,
                                                uint16_t frame_capacity,
                                                uint16_t *frame_length)
{
    const SnapshotFrame_Diagnostics *diagnostics;
    uint16_t payload_length;

    if ((frame_buffer == NULL) || (frame_length == NULL) || (frame_capacity < SPI_FRAME_MAX_BYTES)) return false;
    LatestValue_CopySnapshot(TimeService_NowUs(), copy);
    diagnostics = SnapshotFramePool_GetDiagnostics(&s_frame_pool);
    if (SpiProtocol_SerializeSnapshot(copy,
                                      diagnostics == NULL ? 0u : (uint16_t)diagnostics->dropped_frame_count,
                                      payload, &payload_length) != SPI_PROTOCOL_OK) return false;
    if (SpiProtocol_BuildSnapshotFrame(&s_protocol, payload, payload_length, frame_buffer) != SPI_PROTOCOL_OK) return false;
    *frame_length = (uint16_t)(SPI_FRAME_HEADER_BYTES + payload_length + SPI_FRAME_CRC_BYTES);
    return true;
}

static bool SpiSlaveService_SerializeLatestSnapshot(uint8_t *frame_buffer,
                                                    uint16_t frame_capacity,
                                                    uint16_t *frame_length,
                                                    void *context)
{
    (void)context;
    return SpiSlaveService_BuildLatestSnapshot(&s_snapshot_copy, s_snapshot_payload, frame_buffer, frame_capacity, frame_length);
}

static bool SpiSlaveService_RequestAllowed(uint8_t request_type)
{
    Lifecycle_State state = Lifecycle_GetState(&s_lifecycle);
    if (request_type == SPI_MESSAGE_TIME_SYNC) return (state == LIFECYCLE_STATE_INACTIVE) || (state == LIFECYCLE_STATE_ACTIVE);
    return state == LIFECYCLE_STATE_ACTIVE;
}

/* Every stage-and-publish in this service runs through here (see s_staging_busy).
 * SpiSlaveService_Init stages its boot frame directly: no other caller exists yet. */
static SnapshotBuild_Result SpiSlaveService_StageAndPublish(SnapshotBuilder_SerializeCallback serialize,
                                                            void *context,
                                                            bool record_staged_time)
{
    SnapshotBuild_Result result;

    if (atomic_flag_test_and_set(&s_staging_busy)) return SNAPSHOT_BUILD_BUSY;
    result = SnapshotBuilder_Stage(&s_frame_pool, serialize, context);
    if (result == SNAPSHOT_BUILD_OK) {
        if (record_staged_time) {
            /* Capture response staged time when frame is staged. */
            g_spi_timing_dbg.response_staged_us = TimeService_NowUs();
        }
        (void)SpiSlaveService_PublishStagedFrame();
    }
    atomic_flag_clear(&s_staging_busy);
    return result;
}

static void SpiSlaveService_StageResponseFrame(void)
{
    (void)SpiSlaveService_StageAndPublish(SpiSlaveService_SerializeResponse, NULL, true);
}

void SpiSlaveService_Init(void)
{
    Lifecycle_Init(&s_lifecycle, "SPI3");
    SnapshotFramePool_Init(&s_frame_pool);
    SpiProtocol_Init(&s_protocol);
    SpiDataReady_Init(&s_data_ready);
    s_dma_active = false;
    s_request_pending = false;
    s_dma_error = false;
    s_poll_period_ms = SPI_SERVICE_DEFAULT_POLL_PERIOD_MS;
    s_last_poll_tick = HAL_GetTick();
    SpiSlaveService_SetDataReadyPin(false);
    (void)SpiProtocol_BuildBootStatus(&s_protocol, s_response_frame);
    (void)SnapshotBuilder_Stage(&s_frame_pool, SpiSlaveService_SerializeResponse, NULL);
    (void)Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_CONFIGURE, true, 0u);
}

Lifecycle_Result SpiSlaveService_Activate(void)
{
    Lifecycle_Result result = Lifecycle_Apply(&s_lifecycle, LIFECYCLE_TRANSITION_ACTIVATE, true, 0u);
    if (result == LIFECYCLE_RESULT_OK) (void)SpiSlaveService_PublishStagedFrame();
    return result;
}

Lifecycle_State SpiSlaveService_GetLifecycleState(void) { return Lifecycle_GetState(&s_lifecycle); }

void SpiSlaveService_Process(void)
{
    uint32_t now = HAL_GetTick();
    if (!Lifecycle_IsActive(&s_lifecycle)) return;

    if (s_request_pending) {
        /* Capture process start time at entry when request is pending. */
        g_spi_timing_dbg.process_start_us = TimeService_NowUs();
        memcpy(s_rx_frame, s_pending_request, SPI_FRAME_MAX_BYTES);
        s_request_pending = false;
        (void)SpiSlaveService_CompleteDmaTransfer();
        s_dma_active = false;
        (void)SpiSlaveService_ProcessRequestFrame(s_rx_frame);
    } else if (s_dma_error) {
        s_dma_error = false;
        (void)HAL_SPI_Abort(&hspi3);
        if (s_dma_active) {
            (void)SpiSlaveService_CompleteDmaTransfer();
            s_dma_active = false;
        }
        SpiSlaveService_SetDataReadyPin(false);
        (void)SpiProtocol_BuildBootStatus(&s_protocol, s_response_frame);
        (void)SpiSlaveService_StageAndPublish(SpiSlaveService_SerializeResponse, NULL, false);
    } else if (s_dma_active && ((now - s_dma_start_tick) >= SPI_SERVICE_HOST_STALL_MS)) {
        (void)HAL_SPI_Abort(&hspi3);
        if (s_dma_active) {
            (void)SpiSlaveService_CompleteDmaTransfer();
            s_dma_active = false;
        }
        SpiSlaveService_SetDataReadyPin(false);
        (void)SpiProtocol_BuildBootStatus(&s_protocol, s_response_frame);
        (void)SpiSlaveService_StageAndPublish(SpiSlaveService_SerializeResponse, NULL, false);
    }

    if ((now - s_last_poll_tick) >= s_poll_period_ms) {
        uint16_t frame_length;
        bool staged = SnapshotFramePool_GetStagedFrame(&s_frame_pool, &frame_length) != NULL;
        s_last_poll_tick = now;
        if (!s_dma_active && SpiDataReady_Poll(&s_data_ready, staged, now, SPI_SERVICE_HOST_STALL_MS)) {
            (void)SpiSlaveService_PublishStagedFrame();
        }
    }
}

SnapshotBuild_Result SpiSlaveService_StageSnapshot(SnapshotBuilder_SerializeCallback serialize, void *context)
{
    if (!Lifecycle_IsActive(&s_lifecycle)) return SNAPSHOT_BUILD_NOT_READY;
    return SpiSlaveService_StageAndPublish(serialize, context, false);
}

SnapshotBuild_Result SpiSlaveService_StageLatestSnapshot(void)
{
    return SpiSlaveService_StageSnapshot(SpiSlaveService_SerializeLatestSnapshot, NULL);
}

bool SpiSlaveService_BeginDmaTransfer(const uint8_t **frame_buffer, uint16_t *frame_length)
{
    bool started = Lifecycle_IsActive(&s_lifecycle) && SnapshotFramePool_BeginDma(&s_frame_pool, frame_buffer, frame_length);
    if (started && SpiDataReady_OnFrameConsumed(&s_data_ready)) SpiSlaveService_SetDataReadyPin(false);
    return started;
}

bool SpiSlaveService_CompleteDmaTransfer(void) { return SnapshotFramePool_CompleteDma(&s_frame_pool); }
const SnapshotFrame_Diagnostics *SpiSlaveService_GetSnapshotDiagnostics(void) { return SnapshotFramePool_GetDiagnostics(&s_frame_pool); }
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
    uint32_t request_seq;

    if (request == NULL) return SPI_PROTOCOL_BAD_MESSAGE;
    result = SpiProtocol_ValidateRequest(&s_protocol, request);
    request_type = request[SPI_FRAME_OFFSET_MESSAGE_TYPE];
    request_seq = LeBytes_ReadU32(&request[SPI_FRAME_OFFSET_SEQUENCE]);
    /* Capture request type and sequence for timing mirror. */
    s_last_request_type = request_type;
    s_last_request_seq = request_seq;
    if (result != SPI_PROTOCOL_OK) {
        SpiProtocol_BuildCommandReply(&s_protocol, SPI_MESSAGE_NACK, request_type,
                                      request_seq,
                                      (uint16_t)result, 0u, s_response_frame);
        SpiSlaveService_StageResponseFrame();
        return result;
    }
    if (!SpiSlaveService_RequestAllowed(request_type)) {
        SpiProtocol_BuildCommandReply(&s_protocol, SPI_MESSAGE_NACK, request_type,
                                      request_seq,
                                      SPI_PROTOCOL_BAD_STATE, 0u, s_response_frame);
        SpiSlaveService_StageResponseFrame();
        return SPI_PROTOCOL_BAD_STATE;
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

void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *hspi)
{
    if ((hspi != NULL) && (hspi->Instance == SPI3) && s_dma_active) {
        memcpy(s_pending_request, s_rx_frame, SPI_FRAME_MAX_BYTES);
        s_request_pending = true;
        /* Capture raw TIM2 counter at DMA completion (ISR context). */
        g_spi_timing_dbg.dma_complete_raw = TimeService_RawCounter();
    }
}

void HAL_SPI_ErrorCallback(SPI_HandleTypeDef *hspi)
{
    if ((hspi != NULL) && (hspi->Instance == SPI3)) s_dma_error = true;
}
