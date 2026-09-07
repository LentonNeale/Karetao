#include <assert.h>
#include <stdint.h>
#include <string.h>

#include "calibration_record.h"
#include "can_tx_policy.h"
#include "crc32_iso_hdlc.h"
#include "joint_mapping.h"
#include "motor_latest_value.h"
#include "sensor_latest_value.h"
#include "snapshot_builder.h"
#include "spi_payload_layout.h"
#include "spi_protocol.h"
#include "spi_data_ready.h"
#include "time_service.h"

static uint32_t ReadCounter(void *context)
{
    return *(uint32_t *)context;
}

static void TestWrapExtension(void)
{
    TimeService_State state;
    uint32_t counter = UINT32_C(0xFFFFFFFE);

    TimeService_StateInit(&state, ReadCounter, &counter);
    assert(TimeService_StateNowUs(&state) == UINT64_C(0xFFFFFFFE));

    counter = UINT32_MAX;
    assert(TimeService_StateNowUs(&state) == UINT64_C(0xFFFFFFFF));

    counter = 0u;
    assert(TimeService_StateNowUs(&state) == (UINT64_C(1) << 32u));

    counter = 42u;
    assert(TimeService_StateNowUs(&state) == ((UINT64_C(1) << 32u) + 42u));
}

static void TestMonotonicAcrossMultipleWraps(void)
{
    TimeService_State state;
    uint32_t counter = UINT32_C(0xFFFFFFF0);
    uint64_t previous;

    TimeService_StateInit(&state, ReadCounter, &counter);
    previous = TimeService_StateNowUs(&state);

    counter = 5u;
    assert(TimeService_StateNowUs(&state) > previous);
    previous = TimeService_StateNowUs(&state);

    counter = UINT32_MAX;
    assert(TimeService_StateNowUs(&state) > previous);
    previous = TimeService_StateNowUs(&state);

    counter = 7u;
    assert(TimeService_StateNowUs(&state) > previous);
}

static TimeService_SyncConfig TestSyncConfig(void)
{
    TimeService_SyncConfig config;

    config.initial_offset_limit_us = INT64_C(10000000);
    config.runtime_offset_step_limit_us = INT64_C(1000000);
    config.validity_timeout_us = UINT64_C(5000000);
    return config;
}

static void TestInitialAcceptanceAndRuntimeRejection(void)
{
    TimeService_SyncState state;
    TimeService_SyncConfig config = TestSyncConfig();
    TimeService_SyncSnapshot snapshot;

    TimeService_SyncStateInit(&state, &config);
    assert(TimeService_SyncStateAccept(&state, UINT64_C(6000000), 10u, UINT64_C(1000000)) ==
           TIME_SERVICE_SYNC_ACCEPTED);
    TimeService_SyncStateGetSnapshot(&state, UINT64_C(1000000), &snapshot);
    assert(snapshot.valid);
    assert(snapshot.quality == TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED);
    assert(snapshot.time_offset_us == INT64_C(5000000));

    assert(TimeService_SyncStateAccept(&state, UINT64_C(8000001), 11u, UINT64_C(2000000)) ==
           TIME_SERVICE_SYNC_REJECTED_OFFSET);
    TimeService_SyncStateGetSnapshot(&state, UINT64_C(2000000), &snapshot);
    assert(snapshot.valid);
    assert(snapshot.time_offset_us == INT64_C(5000000));
    assert(snapshot.last_sync_sequence == 10u);
}

static void TestTimeoutResetAndRecovery(void)
{
    TimeService_SyncState state;
    TimeService_SyncConfig config = TestSyncConfig();
    TimeService_SyncSnapshot snapshot;

    TimeService_SyncStateInit(&state, &config);
    assert(TimeService_SyncStateAccept(&state, UINT64_C(4000000), 1u, UINT64_C(1000000)) ==
           TIME_SERVICE_SYNC_ACCEPTED);
    TimeService_SyncStateGetSnapshot(&state, UINT64_C(5999999), &snapshot);
    assert(snapshot.valid);
    assert(snapshot.age_us == UINT64_C(4999999));

    TimeService_SyncStateGetSnapshot(&state, UINT64_C(6000000), &snapshot);
    assert(!snapshot.valid);
    assert(snapshot.quality == TIME_SERVICE_SYNC_QUALITY_UNSYNCHRONIZED);
    assert(snapshot.time_offset_us == INT64_C(3000000));

    TimeService_SyncStateReset(&state);
    TimeService_SyncStateGetSnapshot(&state, UINT64_C(7000000), &snapshot);
    assert(!snapshot.valid);
    assert(snapshot.time_offset_us == 0);
    assert(snapshot.age_us == UINT64_MAX);

    assert(TimeService_SyncStateAccept(&state, UINT64_C(10000000), 2u, UINT64_C(7000000)) ==
           TIME_SERVICE_SYNC_ACCEPTED);
    TimeService_SyncStateGetSnapshot(&state, UINT64_C(7000000), &snapshot);
    assert(snapshot.valid);
    assert(snapshot.time_offset_us == INT64_C(3000000));
}

static Calibration_Record TestCalibrationRecord(uint8_t sensor_id, uint8_t joint_id, uint32_t generation)
{
    Calibration_Record record = {
        .schema_version = CALIBRATION_SCHEMA_VERSION,
        .logical_sensor_id = sensor_id,
        .logical_joint_id = joint_id,
        .zero_offset_mdeg = -1200,
        .scale_ppm = 1000000,
        .direction = 1,
        .reserved = {0u, 0u, 0u},
        .generation = generation,
        .record_crc32 = UINT32_C(0xA5A55A5A),
        .validity_marker = CALIBRATION_VALIDITY_MARKER
    };

    return record;
}

static void TestCalibrationRecordValidation(void)
{
    Calibration_Record record = TestCalibrationRecord(0u, 0u, 1u);

    assert(Calibration_ValidateRecord(&record, record.record_crc32) == CALIBRATION_RESULT_OK);
    assert(Calibration_ValidateRecord(&record, record.record_crc32 ^ 1u) == CALIBRATION_RESULT_CRC_MISMATCH);

    record.schema_version++;
    assert(Calibration_ValidateRecord(&record, record.record_crc32) == CALIBRATION_RESULT_UNSUPPORTED_SCHEMA);
}

static void TestCalibrationDuplicateIdentity(void)
{
    Calibration_Record records[2] = {
        TestCalibrationRecord(1u, 1u, 1u),
        TestCalibrationRecord(1u, 1u, 2u)
    };
    uint32_t computed_crc32[2] = {records[0].record_crc32, records[1].record_crc32};

    assert(Calibration_ValidateUniqueIdentities(records, computed_crc32, 2u) ==
           CALIBRATION_RESULT_DUPLICATE_IDENTITY);
}

static void TestCalibrationGenerationSelection(void)
{
    Calibration_Record older = TestCalibrationRecord(2u, 2u, 4u);
    Calibration_Record newer = TestCalibrationRecord(2u, 2u, 5u);
    Calibration_ActiveVersion active_version;

    assert(Calibration_SelectNewer(&older,
                                   older.record_crc32,
                                   &newer,
                                   newer.record_crc32,
                                   &active_version) == CALIBRATION_RESULT_OK);
    assert(active_version.active_schema_version == CALIBRATION_SCHEMA_VERSION);
    assert(active_version.active_generation == 5u);
    assert(active_version.record.generation == 5u);
}

static JointMapping_Record TestJointMappingRecord(uint8_t joint_id, uint8_t sensor_id,
                                                   uint8_t motor_index, uint16_t can_id)
{
    JointMapping_Record record = {
        .schema_version = JOINT_MAPPING_SCHEMA_VERSION,
        .logical_joint_id = joint_id,
        .as5600_sensor_id = sensor_id,
        .motor_index = motor_index,
        .can_id = can_id,
        .direction = 1,
        .zero_offset_mdeg = 0,
        .transmission_ratio_numerator = 1u,
        .transmission_ratio_denominator = 1u
    };

    return record;
}

static void TestJointMappingValidation(void)
{
    JointMapping_Record records[2] = {
        TestJointMappingRecord(0u, 0u, 0u, 1u),
        TestJointMappingRecord(1u, 1u, 1u, 2u)
    };

    assert(JointMapping_Validate(records, 2u) == JOINT_MAPPING_RESULT_OK);
    assert(JointMapping_FindByJoint(records, 2u, 1u) == &records[1]);

    records[1].as5600_sensor_id = 0u;
    assert(JointMapping_Validate(records, 2u) == JOINT_MAPPING_RESULT_DUPLICATE_SENSOR_ID);

    records[1] = TestJointMappingRecord(1u, 1u, 1u, 1u);
    assert(JointMapping_Validate(records, 2u) == JOINT_MAPPING_RESULT_DUPLICATE_CAN_ID);
}

static void TestJointMappingInvalidRatioAndRevision(void)
{
    JointMapping_Record record = TestJointMappingRecord(0u, 0u, 0u, 1u);

    record.transmission_ratio_denominator = 0u;
    assert(JointMapping_Validate(&record, 1u) == JOINT_MAPPING_RESULT_INVALID_RATIO);

    record = TestJointMappingRecord(0u, 0u, 0u, 1u);
    record.schema_version++;
    assert(JointMapping_Validate(&record, 1u) == JOINT_MAPPING_RESULT_UNSUPPORTED_SCHEMA);
}

static void TestSensorLatestValue(void)
{
    Sensor_LatestValue record;

    SensorLatestValue_Init(&record, 3u, 4u, 7u);
    assert(record.logical_joint_id == 3u);
    assert(record.sensor_id == 4u);
    assert(record.freshness == SENSOR_FRESHNESS_INVALID);
    assert((record.validity_flags & SENSOR_VALIDITY_SAMPLE_VALID) == 0u);

    SensorLatestValue_SetValid(&record,
                               1234u,
                               108457,
                               UINT8_C(0x20),
                               UINT64_C(1000),
                               TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED,
                               8u);
    assert(record.raw_angle_counts == 1234u);
    assert(record.processed_angle_mdeg == 108457);
    assert(record.measurement_timestamp_us == UINT64_C(1000));
    assert(record.synchronization_quality == TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED);
    assert(record.calibration_version == 8u);
    assert(record.freshness == SENSOR_FRESHNESS_FRESH);
    assert((record.validity_flags & SENSOR_VALIDITY_SAMPLE_VALID) != 0u);
    assert((record.validity_flags & SENSOR_VALIDITY_TIMESTAMP_SYNCHRONIZED) != 0u);

    SensorLatestValue_SetInvalid(&record,
                                 0u,
                                 SENSOR_VALIDITY_COMMUNICATION_ERROR,
                                 UINT64_C(2000));
    assert(record.raw_angle_counts == 0u);
    assert(record.processed_angle_mdeg == 0);
    assert(record.measurement_timestamp_us == 0u);
    assert(record.last_update_timestamp_us == UINT64_C(2000));
    assert(record.freshness == SENSOR_FRESHNESS_INVALID);
    assert((record.validity_flags & SENSOR_VALIDITY_SAMPLE_VALID) == 0u);
    assert((record.validity_flags & SENSOR_VALIDITY_COMMUNICATION_ERROR) != 0u);
}

static void TestMotorLatestValue(void)
{
    Motor_LatestValue record;
    uint8_t payload[2] = {UINT8_C(0x12), UINT8_C(0x34)};

    MotorLatestValue_Init(&record, 2u, 3u, UINT16_C(0x123), 4u);
    assert(record.logical_joint_id == 2u);
    assert(record.motor_index == 3u);
    assert(record.can_id == UINT16_C(0x123));
    assert(record.freshness == MOTOR_FRESHNESS_INVALID);

    MotorLatestValue_SetValid(&record,
                              UINT8_C(0x30),
                              payload,
                              2u,
                              1u,
                              true,
                              UINT64_C(1000),
                              TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED,
                              5u);
    assert(record.command_code == UINT8_C(0x30));
    assert(record.payload[0] == UINT8_C(0x12));
    assert(record.payload_length == 2u);
    assert(record.acquisition_timestamp_us == UINT64_C(1000));
    assert(record.calibration_version == 5u);
    assert(record.freshness == MOTOR_FRESHNESS_FRESH);
    assert(record.rx_ok_count == 1u);
    assert((record.validity_flags & MOTOR_VALIDITY_FEEDBACK_VALID) != 0u);
    assert((record.validity_flags & MOTOR_VALIDITY_TIMESTAMP_SYNCHRONIZED) != 0u);

    MotorLatestValue_MarkStale(&record, UINT64_C(2000));
    assert(record.freshness == MOTOR_FRESHNESS_STALE);
    assert(record.last_update_timestamp_us == UINT64_C(2000));
    assert(record.rx_decode_error_count == 1u);
    assert((record.validity_flags & MOTOR_VALIDITY_FEEDBACK_VALID) == 0u);
}

static void TestSnapshotLayout(void)
{
    assert(SPI_FRAME_MAX_BYTES == 512u);
    assert(SPI_FRAME_HEADER_BYTES == 18u);
    assert(SPI_FRAME_CRC_BYTES == 4u);
    assert(SPI_PAYLOAD_MAX_BYTES == 490u);
    assert(SPI_FRAME_OFFSET_PAYLOAD == 18u);
    assert(SPI_FRAME_CRC_OFFSET(SPI_PAYLOAD_MAX_BYTES) == 508u);
    assert(SPI_SNAPSHOT_PREFIX_BYTES == 12u);
    assert(SPI_SENSOR_RECORD_BYTES == 24u);
    assert(SPI_MOTOR_RECORD_BYTES == 24u);
    assert(SPI_SNAPSHOT_SENSOR_RECORD_COUNT == 6u);
    assert(SPI_SNAPSHOT_MOTOR_RECORD_MAX_COUNT == 8u);
    assert(SPI_SNAPSHOT_PAYLOAD_BYTES(1u) == 180u);
    assert(SPI_SNAPSHOT_MAX_PAYLOAD_BYTES == 348u);
    assert(SPI_SNAPSHOT_MAX_FRAME_BYTES == 370u);
    assert(SPI_SNAPSHOT_MAX_FRAME_BYTES <= SPI_FRAME_MAX_BYTES);
}

static bool SerializeTestFrame(uint8_t *frame_buffer,
                               uint16_t frame_capacity,
                               uint16_t *frame_length,
                               void *context)
{
    const uint8_t *value = context;

    if ((frame_capacity < 2u) || (frame_length == NULL) || (value == NULL))
    {
        return false;
    }

    frame_buffer[0] = *value;
    frame_buffer[1] = 0u;
    *frame_length = 2u;
    return true;
}

static void TestSnapshotFrameOwnership(void)
{
    SnapshotFrame_Pool pool;
    const SnapshotFrame_Diagnostics *diagnostics;
    const uint8_t *dma_frame;
    const uint8_t *staged_frame;
    uint16_t frame_length;
    uint8_t first_value = UINT8_C(0xA1);
    uint8_t replacement_value = UINT8_C(0xB2);
    uint8_t invalid_record_flag = 0u;

    SnapshotFramePool_Init(&pool);
    assert(SnapshotBuilder_Stage(&pool, SerializeTestFrame, &first_value) == SNAPSHOT_BUILD_OK);
    assert(SnapshotFramePool_BeginDma(&pool, &dma_frame, &frame_length));
    assert(frame_length == 2u);
    assert(dma_frame[0] == first_value);

    assert(SnapshotBuilder_Stage(&pool, SerializeTestFrame, &replacement_value) == SNAPSHOT_BUILD_OK);
    assert(dma_frame[0] == first_value);
    assert(!SnapshotFramePool_BeginDma(&pool, &staged_frame, &frame_length));

    assert(SnapshotBuilder_Stage(&pool, SerializeTestFrame, &invalid_record_flag) == SNAPSHOT_BUILD_OK);
    staged_frame = SnapshotFramePool_GetStagedFrame(&pool, &frame_length);
    assert(staged_frame != NULL);
    assert(staged_frame[0] == 0u);

    diagnostics = SnapshotFramePool_GetDiagnostics(&pool);
    assert(diagnostics->replaced_unread_frame_count == 1u);
    assert(diagnostics->dropped_frame_count == 0u);

    assert(SnapshotFramePool_CompleteDma(&pool));
    assert(SnapshotFramePool_BeginDma(&pool, &dma_frame, &frame_length));
    assert(dma_frame[0] == 0u);
    assert(SnapshotFramePool_CompleteDma(&pool));
}

static void TestCrc32IsoHdlc(void)
{
    static const uint8_t known_text[] = "123456789";
    uint8_t frame[] = {
        0x5Au, 0xA5u, 0x01u, 0x01u, 0x03u, 0x00u, 0x34u, 0x12u, 0x00u, 0x00u,
        0x88u, 0x77u, 0x66u, 0x55u, 0x44u, 0x33u, 0x22u, 0x11u, 0xAAu, 0xBBu, 0xCCu
    };
    uint8_t crc_field[4];
    uint32_t crc32;

    assert(Crc32IsoHdlc_Compute(NULL, 0u) == 0u);
    assert(Crc32IsoHdlc_Compute(known_text, sizeof(known_text) - 1u) == UINT32_C(0xCBF43926));

    crc32 = Crc32IsoHdlc_Compute(frame, sizeof(frame));
    assert(crc32 == UINT32_C(0x049705F5));
    Crc32IsoHdlc_WriteLittleEndian(crc32, crc_field);
    assert(Crc32IsoHdlc_ReadLittleEndian(crc_field) == crc32);
    assert(Crc32IsoHdlc_Verify(frame, sizeof(frame), crc_field));

    frame[18] ^= 0x01u;
    assert(!Crc32IsoHdlc_Verify(frame, sizeof(frame), crc_field));
}

static void BuildRequest(uint8_t frame[SPI_FRAME_MAX_BYTES], uint8_t type, uint16_t length, uint32_t sequence)
{
    uint32_t crc32;
    memset(frame, 0, SPI_FRAME_MAX_BYTES);
    frame[0] = 0x5Au; frame[1] = 0xA5u; frame[2] = SPI_PROTOCOL_VERSION; frame[3] = type;
    frame[4] = (uint8_t)length; frame[5] = (uint8_t)(length >> 8u);
    frame[6] = (uint8_t)sequence; frame[7] = (uint8_t)(sequence >> 8u); frame[8] = (uint8_t)(sequence >> 16u); frame[9] = (uint8_t)(sequence >> 24u);
    if ((SPI_FRAME_CRC_OFFSET(length) + SPI_FRAME_CRC_BYTES) <= SPI_FRAME_MAX_BYTES) {
        crc32 = Crc32IsoHdlc_Compute(frame, SPI_FRAME_HEADER_BYTES + length);
        Crc32IsoHdlc_WriteLittleEndian(crc32, &frame[SPI_FRAME_CRC_OFFSET(length)]);
    }
}

static void TestSpiProtocolState(void)
{
    SpiProtocol_State state; uint8_t request[SPI_FRAME_MAX_BYTES]; uint8_t response[SPI_FRAME_MAX_BYTES]; uint8_t snapshot[SPI_SNAPSHOT_PREFIX_BYTES] = {1u};
    SpiProtocol_Init(&state); assert(SpiProtocol_BuildBootStatus(&state, response) == SPI_PROTOCOL_OK); assert(response[3] == SPI_MESSAGE_STATUS);
    assert(SpiProtocol_SetUnsolicitedSnapshot(&state, snapshot, sizeof(snapshot)));
    BuildRequest(request, SPI_MESSAGE_GET_SNAPSHOT, 0u, 10u);
    assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_OK); assert(response[3] == SPI_MESSAGE_SNAPSHOT);
    assert(response[SPI_FRAME_OFFSET_PAYLOAD + SPI_SNAPSHOT_OFFSET_RESPONSE_TO_SEQUENCE] == 10u);
    assert(response[SPI_FRAME_OFFSET_PAYLOAD + SPI_SNAPSHOT_OFFSET_RESPONSE_TO_SEQUENCE + 1u] == 0u);
    request[0] ^= 1u; assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_BAD_MAGIC); assert(response[3] == SPI_MESSAGE_NACK);
    BuildRequest(request, SPI_MESSAGE_GET_STATUS, 0u, 10u); assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_BAD_SEQUENCE);
    BuildRequest(request, SPI_MESSAGE_GET_STATUS, 491u, 11u); assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_BAD_LENGTH);
}

static void TestDataReadyState(void)
{
    SpiDataReady_State state;
    SpiDataReady_Init(&state);
    assert(SpiDataReady_OnFrameStaged(&state, 10u));
    assert(state.high && state.notification_count == 1u);
    assert(SpiDataReady_OnFrameConsumed(&state));
    assert(SpiDataReady_Poll(&state, true, 11u, 100u));
    assert(state.high && state.poll_recovery_count == 1u);
    assert(!SpiDataReady_Poll(&state, true, 111u, 100u));
    assert(state.host_stall_count == 1u);
}

static void TestCanTxAndRecoveryPolicy(void)
{
    CanTx_Queue queue; CanTx_Entry entry; CanBusOff_State bus_off; CanTx_Frame frame = {.id = 1u, .dlc = 0u};
    CanTxQueue_Init(&queue); assert(CanTxQueue_Enqueue(&queue, &frame, CAN_TX_PRIORITY_POLL)); assert(CanTxQueue_Enqueue(&queue, &frame, CAN_TX_PRIORITY_SAFETY));
    assert(CanTxQueue_Dequeue(&queue, &entry)); assert(entry.priority == CAN_TX_PRIORITY_SAFETY);
	entry.retry_count = 1u; assert(CanTxQueue_Requeue(&queue, &entry)); assert(CanTxQueue_Dequeue(&queue, &entry)); assert(entry.retry_count == 1u);
    CanBusOff_Init(&bus_off); assert(!CanBusOff_Record(&bus_off, 1u)); assert(CanBusOff_RecoveryDue(&bus_off, 101u)); CanBusOff_RecoveryResult(&bus_off, false, 101u);
	assert(!CanBusOff_Record(&bus_off, 200u)); assert(CanBusOff_Record(&bus_off, 300u)); assert(bus_off.normal_commands_inhibited); CanBusOff_AllowNormalCommands(&bus_off); assert(!bus_off.normal_commands_inhibited);
}

int main(void)
{
    TestWrapExtension();
    TestMonotonicAcrossMultipleWraps();
    TestInitialAcceptanceAndRuntimeRejection();
    TestTimeoutResetAndRecovery();
    TestCalibrationRecordValidation();
    TestCalibrationDuplicateIdentity();
    TestCalibrationGenerationSelection();
    TestJointMappingValidation();
    TestJointMappingInvalidRatioAndRevision();
    TestSensorLatestValue();
    TestMotorLatestValue();
    TestSnapshotLayout();
    TestSnapshotFrameOwnership();
    TestCrc32IsoHdlc();
    TestSpiProtocolState();
    TestDataReadyState();
    TestCanTxAndRecoveryPolicy();
    return 0;
}