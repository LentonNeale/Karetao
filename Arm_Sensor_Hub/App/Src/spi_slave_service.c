#include "spi_slave_service.h"

#include <string.h>

#include "can_service.h"
#include "main.h"
#include "sensor_task.h"
#include "time_service.h"

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

#define SPI_SERVICE_DEFAULT_POLL_PERIOD_MS 1u
#define SPI_SERVICE_HOST_STALL_MS 100u

static void SpiSlaveService_SetDataReadyPin(bool high)
{
    HAL_GPIO_WritePin(Data_Ready_GPIO_Port, Data_Ready_Pin, high ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

static void SpiSlaveService_WriteU16(uint8_t *data, uint16_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8u);
}

static void SpiSlaveService_WriteU32(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8u);
    data[2] = (uint8_t)(value >> 16u);
    data[3] = (uint8_t)(value >> 24u);
}

static void SpiSlaveService_WriteU64(uint8_t *data, uint64_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8u);
    data[2] = (uint8_t)(value >> 16u);
    data[3] = (uint8_t)(value >> 24u);
    data[4] = (uint8_t)(value >> 32u);
    data[5] = (uint8_t)(value >> 40u);
    data[6] = (uint8_t)(value >> 48u);
    data[7] = (uint8_t)(value >> 56u);
}

static uint32_t SpiSlaveService_ReadU32(const uint8_t *data)
{
    return (uint32_t)data[0] |
           ((uint32_t)data[1] << 8u) |
           ((uint32_t)data[2] << 16u) |
           ((uint32_t)data[3] << 24u);
}

static bool SpiSlaveService_SerializeResponse(uint8_t *frame_buffer,
                                               uint16_t frame_capacity,
                                               uint16_t *frame_length,
                                               void *context)
{
    (void)context;
    if ((frame_buffer == NULL) || (frame_length == NULL) || (frame_capacity < SPI_FRAME_MAX_BYTES)) {
        return false;
    }
    memcpy(frame_buffer, s_response_frame, SPI_FRAME_MAX_BYTES);
    *frame_length = SPI_FRAME_MAX_BYTES;
    return true;
}

static bool SpiSlaveService_ArmDma(void)
{
    const uint8_t *tx_frame;
    uint16_t frame_length;

    if (s_dma_active || s_request_pending || !Lifecycle_IsActive(&s_lifecycle)) {
        return false;
    }

    if (!SpiSlaveService_BeginDmaTransfer(&tx_frame, &frame_length)) {
        return false;
    }

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

    if (!Lifecycle_IsActive(&s_lifecycle)) {
        return false;
    }

    if ((SnapshotFramePool_GetStagedFrame(&s_frame_pool, &frame_length) != NULL) &&
        SpiDataReady_OnFrameStaged(&s_data_ready, HAL_GetTick())) {
        if (SpiSlaveService_ArmDma()) {
            SpiSlaveService_SetDataReadyPin(true);
            return true;
        }
    }

    return false;
}

static uint8_t SpiSlaveService_CountPublishedMotorRecords(const Motor_LatestValue *records, size_t record_count)
{
    uint8_t published_count = 0u;
    size_t record_index;
    if (records == NULL) return 0u;
    for (record_index = 0u; record_index < record_count; ++record_index) {
        if (records[record_index].logical_joint_id <= 5u) published_count++;
    }
    return published_count;
}

static void SpiSlaveService_SerializeSensorRecord(uint8_t *record_buffer,
                                                  const Sensor_LatestValue *record,
                                                  uint8_t fallback_sensor_id)
{
    record_buffer[SPI_SENSOR_RECORD_OFFSET_SENSOR_ID] =
        (record->logical_joint_id <= 5u) ? record->logical_joint_id : fallback_sensor_id;
    record_buffer[SPI_SENSOR_RECORD_OFFSET_STATUS] = record->status;
    SpiSlaveService_WriteU16(&record_buffer[SPI_SENSOR_RECORD_OFFSET_VALIDITY_FLAGS], record->validity_flags);
    SpiSlaveService_WriteU64(&record_buffer[SPI_SENSOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US], record->measurement_timestamp_us);
    SpiSlaveService_WriteU16(&record_buffer[SPI_SENSOR_RECORD_OFFSET_RAW_ANGLE], record->raw_angle_counts);
    SpiSlaveService_WriteU32(&record_buffer[SPI_SENSOR_RECORD_OFFSET_PROCESSED_ANGLE_MDEG], (uint32_t)record->processed_angle_mdeg);
    SpiSlaveService_WriteU16(&record_buffer[SPI_SENSOR_RECORD_OFFSET_MAGNITUDE], record->magnitude);
    record_buffer[SPI_SENSOR_RECORD_OFFSET_AGC] = record->agc;
    record_buffer[SPI_SENSOR_RECORD_OFFSET_RESERVED] = 0u;
    SpiSlaveService_WriteU16(&record_buffer[SPI_SENSOR_RECORD_OFFSET_RESERVED_2], 0u);
}

static void SpiSlaveService_SerializeMotorRecord(uint8_t *record_buffer, const Motor_LatestValue *record)
{
    record_buffer[SPI_MOTOR_RECORD_OFFSET_MOTOR_INDEX] = record->motor_index;
    record_buffer[SPI_MOTOR_RECORD_OFFSET_STATUS] = record->controller_status_valid ? record->controller_status : 0u;
    SpiSlaveService_WriteU16(&record_buffer[SPI_MOTOR_RECORD_OFFSET_VALIDITY_FLAGS], record->validity_flags);
    SpiSlaveService_WriteU16(&record_buffer[SPI_MOTOR_RECORD_OFFSET_CAN_ID], record->can_id);
    record_buffer[SPI_MOTOR_RECORD_OFFSET_COMMAND_CODE] = record->command_code;
    record_buffer[SPI_MOTOR_RECORD_OFFSET_PAYLOAD_LENGTH] = record->payload_length;
    SpiSlaveService_WriteU64(&record_buffer[SPI_MOTOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US], record->acquisition_timestamp_us);
    memset(&record_buffer[SPI_MOTOR_RECORD_OFFSET_PAYLOAD], 0, 8u);
    memcpy(&record_buffer[SPI_MOTOR_RECORD_OFFSET_PAYLOAD], record->payload, record->payload_length);
}

static bool SpiSlaveService_SerializeLatestSnapshot(uint8_t *frame_buffer,
                                                    uint16_t frame_capacity,
                                                    uint16_t *frame_length,
                                                    void *context)
{
    const Sensor_LatestValue *sensor_records;
    const Motor_LatestValue *motor_records;
    const SnapshotFrame_Diagnostics *diagnostics;
    size_t sensor_record_count = 0u;
    size_t motor_record_count = 0u;
    uint8_t payload[SPI_SNAPSHOT_MAX_PAYLOAD_BYTES];
    uint16_t payload_length;
    uint8_t published_motor_count;
    size_t sensor_index;
    size_t motor_index;
    uint8_t published_motor_index = 0u;

    (void)context;
    if ((frame_buffer == NULL) || (frame_length == NULL) || (frame_capacity < SPI_FRAME_MAX_BYTES)) return false;
    sensor_records = SensorTask_GetLatestValues(&sensor_record_count);
    motor_records = CanService_GetLatestMotorValues(&motor_record_count);
    if ((sensor_records == NULL) || (sensor_record_count < SPI_SNAPSHOT_SENSOR_RECORD_COUNT) || (motor_records == NULL)) return false;

    published_motor_count = SpiSlaveService_CountPublishedMotorRecords(motor_records, motor_record_count);
    payload_length = SPI_SNAPSHOT_PAYLOAD_BYTES(published_motor_count);
    if ((payload_length > SPI_SNAPSHOT_MAX_PAYLOAD_BYTES) || (payload_length > SPI_PAYLOAD_MAX_BYTES)) return false;

    memset(payload, 0, sizeof(payload));
    payload[SPI_SNAPSHOT_OFFSET_SCHEMA_VERSION] = 1u;
    payload[SPI_SNAPSHOT_OFFSET_SENSOR_COUNT] = (uint8_t)SPI_SNAPSHOT_SENSOR_RECORD_COUNT;
    payload[SPI_SNAPSHOT_OFFSET_MOTOR_COUNT] = published_motor_count;
    diagnostics = SnapshotFramePool_GetDiagnostics(&s_frame_pool);
    SpiSlaveService_WriteU16(&payload[SPI_SNAPSHOT_OFFSET_FLAGS], 0u);
    SpiSlaveService_WriteU16(&payload[SPI_SNAPSHOT_OFFSET_DROPPED_SNAPSHOT_COUNT_LOW], diagnostics == NULL ? 0u : (uint16_t)diagnostics->dropped_frame_count);
    SpiSlaveService_WriteU32(&payload[SPI_SNAPSHOT_OFFSET_RESPONSE_TO_SEQUENCE], 0u);

    for (sensor_index = 0u; sensor_index < SPI_SNAPSHOT_SENSOR_RECORD_COUNT; ++sensor_index) {
        uint8_t *record_buffer = &payload[SPI_SNAPSHOT_PREFIX_BYTES + (sensor_index * SPI_SENSOR_RECORD_BYTES)];
        SpiSlaveService_SerializeSensorRecord(record_buffer, &sensor_records[sensor_index], (uint8_t)sensor_index);
    }
    for (motor_index = 0u; motor_index < motor_record_count; ++motor_index) {
        uint8_t *record_buffer;
        if (motor_records[motor_index].logical_joint_id > 5u) continue;
        record_buffer = &payload[SPI_SNAPSHOT_PREFIX_BYTES +
                                  (SPI_SNAPSHOT_SENSOR_RECORD_COUNT * SPI_SENSOR_RECORD_BYTES) +
                                  (published_motor_index * SPI_MOTOR_RECORD_BYTES)];
        SpiSlaveService_SerializeMotorRecord(record_buffer, &motor_records[motor_index]);
        published_motor_index++;
    }
    if (SpiProtocol_BuildSnapshotFrame(&s_protocol, payload, payload_length, frame_buffer) != SPI_PROTOCOL_OK) return false;
    *frame_length = (uint16_t)(SPI_FRAME_HEADER_BYTES + payload_length + SPI_FRAME_CRC_BYTES);
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
    if (SnapshotBuilder_Stage(&s_frame_pool, SpiSlaveService_SerializeResponse, NULL) == SNAPSHOT_BUILD_OK) {
        (void)SpiSlaveService_PublishStagedFrame();
    }
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
        taskENTER_CRITICAL();
        memcpy(s_rx_frame, s_pending_request, SPI_FRAME_MAX_BYTES);
        s_request_pending = false;
        taskEXIT_CRITICAL();
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
        (void)SnapshotBuilder_Stage(&s_frame_pool, SpiSlaveService_SerializeResponse, NULL);
        (void)SpiSlaveService_PublishStagedFrame();
    } else if (s_dma_active && ((now - s_dma_start_tick) >= SPI_SERVICE_HOST_STALL_MS)) {
        (void)HAL_SPI_Abort(&hspi3);
        if (s_dma_active) {
            (void)SpiSlaveService_CompleteDmaTransfer();
            s_dma_active = false;
        }
        SpiSlaveService_SetDataReadyPin(false);
        (void)SpiProtocol_BuildBootStatus(&s_protocol, s_response_frame);
        (void)SnapshotBuilder_Stage(&s_frame_pool, SpiSlaveService_SerializeResponse, NULL);
        (void)SpiSlaveService_PublishStagedFrame();
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
    SnapshotBuild_Result result;
    if (!Lifecycle_IsActive(&s_lifecycle)) return SNAPSHOT_BUILD_NOT_READY;
    result = SnapshotBuilder_Stage(&s_frame_pool, serialize, context);
    if (result == SNAPSHOT_BUILD_OK) (void)SpiSlaveService_PublishStagedFrame();
    return result;
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

    if (request == NULL) return SPI_PROTOCOL_BAD_MESSAGE;
    result = SpiProtocol_ValidateRequest(&s_protocol, request);
    request_type = request[3];
    if (result != SPI_PROTOCOL_OK) {
        SpiProtocol_BuildCommandReply(&s_protocol, SPI_MESSAGE_NACK, request_type,
                                      SpiSlaveService_ReadU32(&request[SPI_FRAME_OFFSET_SEQUENCE]),
                                      (uint16_t)result, 0u, s_response_frame);
        SpiSlaveService_StageResponseFrame();
        return result;
    }
    if (!SpiSlaveService_RequestAllowed(request_type)) {
        SpiProtocol_BuildCommandReply(&s_protocol, SPI_MESSAGE_NACK, request_type,
                                      SpiSlaveService_ReadU32(&request[SPI_FRAME_OFFSET_SEQUENCE]),
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

/* HAL invokes these from DMA/SPI interrupt context. Only copy data and signal
 * task context; buffer ownership, parsing, and recovery remain in Process(). */
void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *hspi)
{
    if ((hspi != NULL) && (hspi->Instance == SPI3) && s_dma_active) {
        memcpy(s_pending_request, s_rx_frame, SPI_FRAME_MAX_BYTES);
        s_request_pending = true;
    }
}

void HAL_SPI_ErrorCallback(SPI_HandleTypeDef *hspi)
{
    if ((hspi != NULL) && (hspi->Instance == SPI3)) s_dma_error = true;
}
