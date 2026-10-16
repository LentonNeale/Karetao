#include <stdint.h>
#include <string.h>

#include "host_test_assert.h"

#include "calibration_record.h"
#include "can_tx_policy.h"
#include "crc32_iso_hdlc.h"
#include "firmware_version.h"
#include "health_monitor.h"
#include "joint_mapping.h"
#include "lifecycle.h"
#include "latest_value.h"
#include "sensor_task.h"
#include "snapshot_builder.h"
#include "spi_payload_layout.h"
#include "spi_protocol.h"
#include "spi_data_ready.h"
#include "task.h"
#include "time_service.h"

static uint64_t s_test_now_us;
static TimeService_SyncSnapshot s_test_sync_snapshot;
static Lifecycle_State s_test_i2c_state;
static Lifecycle_State s_test_sensor_state;
static Lifecycle_State s_test_can_state;
static Lifecycle_State s_test_spi_state;
static SensorTask_BringupSnapshot s_test_sensor_snapshot;
static SnapshotFrame_Diagnostics s_test_spi_diagnostics;
static uint32_t s_test_i2c_success_count;
static uint32_t s_test_i2c_error_count;
static uint32_t s_test_i2c_timeout_count;
static uint32_t s_test_can_tx_queue_drop_count;
static uint32_t s_test_can_tx_retry_exhausted_count;
static uint32_t s_test_can_bus_off_count;
static uint32_t s_test_app_mks_register_failures;
static uint32_t s_test_app_lifecycle_activation_failures;

uint64_t TimeService_NowUs(void)
{
    return s_test_now_us;
}

void TimeService_GetSyncSnapshot(TimeService_SyncSnapshot *snapshot)
{
    if (snapshot != NULL) {
        *snapshot = s_test_sync_snapshot;
    }
}

Lifecycle_State I2CManager_GetLifecycleState(void)
{
    return s_test_i2c_state;
}

uint32_t I2CManager_GetSuccessCount(void)
{
    return s_test_i2c_success_count;
}

uint32_t I2CManager_GetErrorCount(void)
{
    return s_test_i2c_error_count;
}

uint32_t I2CManager_GetTimeoutCount(void)
{
    return s_test_i2c_timeout_count;
}

Lifecycle_State SensorTask_GetLifecycleState(void)
{
    return s_test_sensor_state;
}

const SensorTask_BringupSnapshot *SensorTask_GetBringupSnapshot(void)
{
    return &s_test_sensor_snapshot;
}

Lifecycle_State CanService_GetLifecycleState(void)
{
    return s_test_can_state;
}

uint32_t CanService_GetTxQueueDropCount(void)
{
    return s_test_can_tx_queue_drop_count;
}

uint32_t CanService_GetTxRetryExhaustedCount(void)
{
    return s_test_can_tx_retry_exhausted_count;
}

uint32_t CanService_GetBusOffCount(void)
{
    return s_test_can_bus_off_count;
}

Lifecycle_State SpiSlaveService_GetLifecycleState(void)
{
    return s_test_spi_state;
}

const SnapshotFrame_Diagnostics *SpiSlaveService_GetSnapshotDiagnostics(void)
{
    return &s_test_spi_diagnostics;
}

uint32_t App_GetMksRegisterFailureCount(void)
{
    return s_test_app_mks_register_failures;
}

uint32_t App_GetLifecycleActivationFailureCount(void)
{
    return s_test_app_lifecycle_activation_failures;
}

static uint32_t ReadCounter(void *context)
{
    return *(uint32_t *)context;
}

static void ResetHealthMonitorInputs(void)
{
    s_test_now_us = 0u;
    s_test_sync_snapshot = (TimeService_SyncSnapshot){0};
    s_test_i2c_state = LIFECYCLE_STATE_UNCONFIGURED;
    s_test_sensor_state = LIFECYCLE_STATE_UNCONFIGURED;
    s_test_can_state = LIFECYCLE_STATE_UNCONFIGURED;
    s_test_spi_state = LIFECYCLE_STATE_UNCONFIGURED;
    s_test_sensor_snapshot = (SensorTask_BringupSnapshot){0};
    s_test_sensor_snapshot.result = SENSOR_TASK_BRINGUP_UNKNOWN;
    s_test_spi_diagnostics = (SnapshotFrame_Diagnostics){0};
    s_test_i2c_success_count = 0u;
    s_test_i2c_error_count = 0u;
    s_test_i2c_timeout_count = 0u;
    s_test_can_tx_queue_drop_count = 0u;
    s_test_can_tx_retry_exhausted_count = 0u;
    s_test_can_bus_off_count = 0u;
    s_test_app_mks_register_failures = 0u;
    s_test_app_lifecycle_activation_failures = 0u;
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
    uint32_t initial_accept_count;
    uint32_t initial_reject_count;

    TimeService_SyncStateInit(&state, &config);

    /* Test ACCEPTED path */
    g_time_sync_dbg = (TimeService_SyncDebugMirror){0};
    assert(TimeService_SyncStateAccept(&state, UINT64_C(6000000), 10u, UINT64_C(1000000)) ==
           TIME_SERVICE_SYNC_ACCEPTED);
    initial_accept_count = g_time_sync_dbg.accept_count;
    assert(g_time_sync_dbg.pi_time_us == UINT64_C(6000000));
    assert(g_time_sync_dbg.local_capture_us == UINT64_C(1000000));
    assert(g_time_sync_dbg.candidate_offset_us == INT64_C(5000000));
    assert(g_time_sync_dbg.result == TIME_SERVICE_SYNC_ACCEPTED);
    assert(initial_accept_count == 1u);
    assert(g_time_sync_dbg.reject_count == 0u);

    TimeService_SyncStateGetSnapshot(&state, UINT64_C(1000000), &snapshot);
    assert(snapshot.valid);
    assert(snapshot.quality == TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED);
    assert(snapshot.time_offset_us == INT64_C(5000000));

    /* Test REJECTED_OFFSET path */
    initial_reject_count = g_time_sync_dbg.reject_count;
    assert(TimeService_SyncStateAccept(&state, UINT64_C(8000001), 11u, UINT64_C(2000000)) ==
           TIME_SERVICE_SYNC_REJECTED_OFFSET);
    assert(g_time_sync_dbg.pi_time_us == UINT64_C(8000001));
    assert(g_time_sync_dbg.local_capture_us == UINT64_C(2000000));
    assert(g_time_sync_dbg.candidate_offset_us == INT64_C(6000001));
    assert(g_time_sync_dbg.result == TIME_SERVICE_SYNC_REJECTED_OFFSET);
    assert(g_time_sync_dbg.accept_count == initial_accept_count);
    assert(g_time_sync_dbg.reject_count == (initial_reject_count + 1u));

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
    uint32_t accept_count;

    TimeService_SyncStateInit(&state, &config);
    g_time_sync_dbg = (TimeService_SyncDebugMirror){0};

    assert(TimeService_SyncStateAccept(&state, UINT64_C(4000000), 1u, UINT64_C(1000000)) ==
           TIME_SERVICE_SYNC_ACCEPTED);
    assert(g_time_sync_dbg.result == TIME_SERVICE_SYNC_ACCEPTED);
    accept_count = g_time_sync_dbg.accept_count;
    assert(accept_count == 1u);

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
    assert(g_time_sync_dbg.result == TIME_SERVICE_SYNC_ACCEPTED);
    assert(g_time_sync_dbg.accept_count == (accept_count + 1u));

    TimeService_SyncStateGetSnapshot(&state, UINT64_C(7000000), &snapshot);
    assert(snapshot.valid);
    assert(snapshot.time_offset_us == INT64_C(3000000));
}

static void TestSyncDebugMirrorRejectionCodes(void)
{
    TimeService_SyncState state;
    TimeService_SyncConfig config = TestSyncConfig();
    uint32_t reject_count;

    TimeService_SyncStateInit(&state, &config);
    g_time_sync_dbg = (TimeService_SyncDebugMirror){0};

    /* Test REJECTED_ARGUMENT path (NULL state) */
    assert(TimeService_SyncStateAccept(NULL, UINT64_C(1000000), 1u, UINT64_C(500000)) ==
           TIME_SERVICE_SYNC_REJECTED_ARGUMENT);
    assert(g_time_sync_dbg.result == TIME_SERVICE_SYNC_REJECTED_ARGUMENT);
    reject_count = g_time_sync_dbg.reject_count;
    assert(reject_count == 1u);

    /* Establish initial state for REJECTED_SEQUENCE test */
    TimeService_SyncStateInit(&state, &config);
    g_time_sync_dbg = (TimeService_SyncDebugMirror){0};
    assert(TimeService_SyncStateAccept(&state, UINT64_C(1000000), 5u, UINT64_C(500000)) ==
           TIME_SERVICE_SYNC_ACCEPTED);
    reject_count = g_time_sync_dbg.reject_count;

    /* Test REJECTED_SEQUENCE path (old sequence) */
    assert(TimeService_SyncStateAccept(&state, UINT64_C(2000000), 3u, UINT64_C(600000)) ==
           TIME_SERVICE_SYNC_REJECTED_SEQUENCE);
    assert(g_time_sync_dbg.result == TIME_SERVICE_SYNC_REJECTED_SEQUENCE);
    assert(g_time_sync_dbg.reject_count == (reject_count + 1u));
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

#define TEST_SENSOR_WINDOW_US UINT64_C(100000)
#define TEST_MOTOR_WINDOW_US UINT64_C(200000)

static LatestValue_Config TestStoreConfig(void)
{
    LatestValue_Config config;
    size_t axis;

    memset(&config, 0, sizeof(config));
    for (axis = 0u; axis < LATEST_VALUE_SENSOR_COUNT; ++axis) {
        config.sensor_fitted[axis] = (axis != 3u);
    }
    config.motors[2].registered = true;
    config.motors[2].logical_joint_id = 1u;
    config.motors[2].can_id = UINT16_C(0x002);
    config.motors[2].configuration_version = 4u;
    config.sensor_window_us = TEST_SENSOR_WINDOW_US;
    config.motor_window_us = TEST_MOTOR_WINDOW_US;
    return config;
}

static LatestValue_Sample TestSample(LatestValue_SampleCondition condition, uint16_t raw, uint64_t timestamp_us)
{
    LatestValue_Sample sample;

    memset(&sample, 0, sizeof(sample));
    sample.condition = condition;
    sample.status = UINT8_C(0x20);
    sample.raw_angle_counts = raw;
    sample.magnitude = 1500u;
    sample.agc = 90u;
    sample.timestamp_us = timestamp_us;
    return sample;
}

static const uint8_t *TestSensorRecordBytes(const uint8_t *payload, size_t axis)
{
    return &payload[SPI_SNAPSHOT_PREFIX_BYTES + (axis * SPI_SENSOR_RECORD_BYTES)];
}

static uint16_t TestSensorFlags(const LatestValue_Snapshot *copy, size_t axis)
{
    static uint8_t payload[SPI_SNAPSHOT_MAX_PAYLOAD_BYTES];
    uint16_t length = 0u;
    const uint8_t *record;

    assert(SpiProtocol_SerializeSnapshot(copy, 0u, payload, &length) == SPI_PROTOCOL_OK);
    record = TestSensorRecordBytes(payload, axis);
    return (uint16_t)(record[SPI_SENSOR_RECORD_OFFSET_VALIDITY_FLAGS] |
                      (record[SPI_SENSOR_RECORD_OFFSET_VALIDITY_FLAGS + 1u] << 8u));
}

static void TestLatestValueConfigure(void)
{
    static LatestValue_Snapshot copy;
    LatestValue_Config config = TestStoreConfig();
    LatestValue_Sample sample = TestSample(LATEST_VALUE_SAMPLE_OK, 0x800u, 1000u);

    assert(LatestValue_Configure(NULL) == LATEST_VALUE_INVALID_ARGUMENT);
    assert(LatestValue_Configure(&config) == LATEST_VALUE_OK);
    assert(LatestValue_AcceptSample(1u, &sample) == LATEST_VALUE_OK);

    /* A rejected config changes nothing: the accepted sample survives each refusal. */
    config.sensor_window_us = 0u;
    assert(LatestValue_Configure(&config) == LATEST_VALUE_INVALID_ARGUMENT);
    config = TestStoreConfig();
    config.motor_window_us = 0u;
    assert(LatestValue_Configure(&config) == LATEST_VALUE_INVALID_ARGUMENT);
    config = TestStoreConfig();
    config.motors[2].logical_joint_id = 6u;
    assert(LatestValue_Configure(&config) == LATEST_VALUE_INVALID_ARGUMENT);
    config = TestStoreConfig();
    config.motors[2].can_id = UINT16_C(0x800);
    assert(LatestValue_Configure(&config) == LATEST_VALUE_INVALID_ARGUMENT);
    LatestValue_CopySnapshot(1000u, &copy);
    assert(copy.sensors[1].has_sample);
    assert(copy.sensors[1].raw_angle_counts == 0x800u);

    /* An accepted config clears every record and sets the slot properties. */
    config = TestStoreConfig();
    assert(LatestValue_Configure(&config) == LATEST_VALUE_OK);
    LatestValue_CopySnapshot(1000u, &copy);
    assert(!copy.sensors[1].has_sample);
    assert(copy.sensors[1].logical_id == 1u);
    assert(!copy.sensors[3].fitted);
    assert(copy.motors[2].registered);
    assert(copy.motors[2].motor_index == 2u);
    assert(copy.motors[2].logical_joint_id == 1u);
    assert(copy.motors[2].can_id == UINT16_C(0x002));
    assert(copy.motors[2].configuration_version == 4u);
    assert(!copy.motors[0].registered);
}

static void TestLatestValueSampleAgeing(void)
{
    static LatestValue_Snapshot copy;
    static uint8_t payload[SPI_SNAPSHOT_MAX_PAYLOAD_BYTES];
    LatestValue_Config config = TestStoreConfig();
    LatestValue_Sample sample = TestSample(LATEST_VALUE_SAMPLE_OK, 0x800u, 1000u);
    uint16_t length = 0u;
    const uint8_t *record;

    assert(LatestValue_Configure(&config) == LATEST_VALUE_OK);
    assert(LatestValue_AcceptSample(1u, &sample) == LATEST_VALUE_OK);

    /* Raw counts become millidegrees by scale only (R6), calibration version 0. */
    LatestValue_CopySnapshot(1000u, &copy);
    assert(copy.sensors[1].processed_angle_mdeg == 180000);
    assert(copy.sensors[1].calibration_version == LATEST_VALUE_CALIBRATION_VERSION);

    /* Fresh up to and including the window; stale one microsecond past it. */
    LatestValue_CopySnapshot(1000u + TEST_SENSOR_WINDOW_US, &copy);
    assert(copy.sensors[1].freshness == LATEST_VALUE_FRESHNESS_FRESH);
    assert(TestSensorFlags(&copy, 1u) == SPI_SENSOR_VALIDITY_SAMPLE_VALID);
    LatestValue_CopySnapshot(1001u + TEST_SENSOR_WINDOW_US, &copy);
    assert(copy.copied_at_us == 1001u + TEST_SENSOR_WINDOW_US);
    assert(copy.sensors[1].freshness == LATEST_VALUE_FRESHNESS_STALE);

    /* Stale on the wire: bit 0 clear, the last values and their timestamp kept. */
    assert(SpiProtocol_SerializeSnapshot(&copy, 0u, payload, &length) == SPI_PROTOCOL_OK);
    record = TestSensorRecordBytes(payload, 1u);
    assert(TestSensorFlags(&copy, 1u) == 0u);
    assert(record[SPI_SENSOR_RECORD_OFFSET_RAW_ANGLE] == 0x00u);
    assert(record[SPI_SENSOR_RECORD_OFFSET_RAW_ANGLE + 1u] == 0x08u);
    assert(record[SPI_SENSOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US] == (uint8_t)1000u);
    assert(record[SPI_SENSOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US + 1u] == (uint8_t)(1000u >> 8u));

    /* A sample stamped after the caller read `now` is age zero, not a wrapped huge age. */
    sample = TestSample(LATEST_VALUE_SAMPLE_OK, 0x400u, 5000u);
    assert(LatestValue_AcceptSample(1u, &sample) == LATEST_VALUE_OK);
    LatestValue_CopySnapshot(4000u, &copy);
    assert(copy.sensors[1].freshness == LATEST_VALUE_FRESHNESS_FRESH);

    /* A fitted axis never sampled, and the not-fitted axis, carry no usable value. */
    assert(copy.sensors[2].freshness == LATEST_VALUE_FRESHNESS_NONE);
    assert(TestSensorFlags(&copy, 2u) == 0u);
    assert(copy.sensors[3].freshness == LATEST_VALUE_FRESHNESS_NONE);
    assert(copy.sensors[3].measurement_timestamp_us == 4000u);
    assert(TestSensorFlags(&copy, 3u) == SPI_SENSOR_VALIDITY_NOT_FITTED);
}

static void TestLatestValueSampleConditions(void)
{
    static const struct {
        LatestValue_SampleCondition condition;
        uint16_t flags;
    } cases[] = {
        {LATEST_VALUE_SAMPLE_COMM_ERROR, SPI_SENSOR_VALIDITY_COMMUNICATION_ERROR},
        {LATEST_VALUE_SAMPLE_MAGNET_MISSING, SPI_SENSOR_VALIDITY_MAGNET_NOT_DETECTED},
        {LATEST_VALUE_SAMPLE_MAGNET_WEAK, SPI_SENSOR_VALIDITY_MAGNET_TOO_WEAK},
        {LATEST_VALUE_SAMPLE_MAGNET_STRONG, SPI_SENSOR_VALIDITY_MAGNET_TOO_STRONG},
    };
    static LatestValue_Snapshot copy;
    LatestValue_Config config = TestStoreConfig();
    size_t index;

    assert(LatestValue_Configure(&config) == LATEST_VALUE_OK);
    for (index = 0u; index < sizeof(cases) / sizeof(cases[0]); ++index) {
        LatestValue_Sample sample = TestSample(cases[index].condition, 0x123u, 2000u);
        assert(LatestValue_AcceptSample(0u, &sample) == LATEST_VALUE_OK);
        LatestValue_CopySnapshot(2000u, &copy);
        /* A failed read keeps its status byte but no angle and no timestamp. */
        assert(copy.sensors[0].status == UINT8_C(0x20));
        assert(copy.sensors[0].raw_angle_counts == 0u);
        assert(copy.sensors[0].processed_angle_mdeg == 0);
        assert(copy.sensors[0].magnitude == 0u);
        assert(copy.sensors[0].measurement_timestamp_us == 0u);
        assert(copy.sensors[0].freshness == LATEST_VALUE_FRESHNESS_NONE);
        assert(TestSensorFlags(&copy, 0u) == cases[index].flags);
    }
}

static void TestLatestValueRefusedWrites(void)
{
    static LatestValue_Snapshot copy;
    LatestValue_Config config = TestStoreConfig();
    LatestValue_Sample sample = TestSample(LATEST_VALUE_SAMPLE_OK, 0x123u, 1000u);
    LatestValue_Feedback feedback;
    unsigned entries;

    memset(&feedback, 0, sizeof(feedback));
    feedback.kind = LATEST_VALUE_FEEDBACK_POSITION;
    feedback.timestamp_us = 1000u;
    assert(LatestValue_Configure(&config) == LATEST_VALUE_OK);

    entries = HostStub_CriticalEntryCount();
    assert(LatestValue_AcceptSample(3u, &sample) == LATEST_VALUE_NOT_FITTED);
    assert(LatestValue_AcceptSample(LATEST_VALUE_SENSOR_COUNT, &sample) == LATEST_VALUE_INVALID_ARGUMENT);
    assert(LatestValue_AcceptSample(0u, NULL) == LATEST_VALUE_INVALID_ARGUMENT);
    /* A count above 12 bits is no AS5600 reading (and would overflow the mdeg scaling). */
    sample.raw_angle_counts = LATEST_VALUE_MAX_RAW_ANGLE + 1u;
    assert(LatestValue_AcceptSample(0u, &sample) == LATEST_VALUE_INVALID_ARGUMENT);
    sample.raw_angle_counts = 0x123u;
    assert(LatestValue_AcceptFeedback(0u, &feedback) == LATEST_VALUE_NOT_REGISTERED);
    assert(LatestValue_AcceptFeedback(LATEST_VALUE_MOTOR_COUNT, &feedback) == LATEST_VALUE_INVALID_ARGUMENT);
    assert(LatestValue_AcceptFeedback(2u, NULL) == LATEST_VALUE_INVALID_ARGUMENT);
    feedback.kind = (LatestValue_FeedbackKind)7;
    assert(LatestValue_AcceptFeedback(2u, &feedback) == LATEST_VALUE_INVALID_ARGUMENT);
    /* A refused write takes no lock and changes no record. */
    assert(HostStub_CriticalEntryCount() == entries);
    LatestValue_CopySnapshot(1000u, &copy);
    assert(!copy.sensors[3].has_sample);
    assert(!copy.motors[0].has_position && !copy.motors[2].has_position);
    LatestValue_CopySnapshot(1000u, NULL);
}

static void TestLatestValueFeedbackMerge(void)
{
    static LatestValue_Snapshot copy;
    static uint8_t payload[SPI_SNAPSHOT_MAX_PAYLOAD_BYTES];
    static const uint8_t reply[LATEST_VALUE_POSITION_REPLY_BYTES] = {0x00u, 0x00u, 0x00u, 0x48u, 0x34u, 0x56u};
    LatestValue_Config config = TestStoreConfig();
    LatestValue_Feedback feedback;
    uint16_t length = 0u;
    const uint8_t *motor = &payload[SPI_SNAPSHOT_PAYLOAD_BYTES(0u)];
    unsigned entries;

    assert(LatestValue_Configure(&config) == LATEST_VALUE_OK);

    /* Speed first: merged, but the record is not valid until a position has arrived. */
    memset(&feedback, 0, sizeof(feedback));
    feedback.kind = LATEST_VALUE_FEEDBACK_SPEED;
    feedback.timestamp_us = 900u;
    feedback.speed_rpm = 120;
    entries = HostStub_CriticalEntryCount();
    assert(LatestValue_AcceptFeedback(2u, &feedback) == LATEST_VALUE_OK);
    LatestValue_CopySnapshot(1000u, &copy);
    assert(HostStub_CriticalEntryCount() == entries + 2u);
    assert(HostStub_CriticalDepth() == 0u);
    assert(copy.motors[2].has_speed && !copy.motors[2].has_position);
    assert(copy.motors[2].freshness == LATEST_VALUE_FRESHNESS_NONE);
    assert(SpiProtocol_SerializeSnapshot(&copy, 0u, payload, &length) == SPI_PROTOCOL_OK);
    assert(length == SPI_SNAPSHOT_PAYLOAD_BYTES(1u));
    assert(payload[SPI_SNAPSHOT_OFFSET_MOTOR_COUNT] == 1u);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_MOTOR_INDEX] == 2u);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_VALIDITY_FLAGS] == 0u);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_COMMAND_CODE] == 0u);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_PAYLOAD_LENGTH] == 0u);

    /* Position: valid and fresh, the v1 record carrying the raw position reply. */
    memset(&feedback, 0, sizeof(feedback));
    feedback.kind = LATEST_VALUE_FEEDBACK_POSITION;
    feedback.timestamp_us = 1000u;
    feedback.position_counts = (INT64_C(0x48) * 0x4000) + 0x3456;
    feedback.position_command_code = 0x30u;
    memcpy(feedback.position_reply, reply, sizeof(reply));
    assert(LatestValue_AcceptFeedback(2u, &feedback) == LATEST_VALUE_OK);
    LatestValue_CopySnapshot(1000u + TEST_MOTOR_WINDOW_US, &copy);
    assert(copy.motors[2].freshness == LATEST_VALUE_FRESHNESS_FRESH);
    assert(copy.motors[2].speed_rpm == 120 && copy.motors[2].speed_timestamp_us == 900u);
    assert(copy.motors[2].position_counts == (INT64_C(0x48) * 0x4000) + 0x3456);
    assert(SpiProtocol_SerializeSnapshot(&copy, 0u, payload, &length) == SPI_PROTOCOL_OK);
    /* No polled reply carries a drive status: status 0, bit 1 never set. */
    assert(motor[SPI_MOTOR_RECORD_OFFSET_STATUS] == 0u);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_VALIDITY_FLAGS] == SPI_MOTOR_VALIDITY_FEEDBACK_VALID);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_CAN_ID] == 0x02u);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_COMMAND_CODE] == 0x30u);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_PAYLOAD_LENGTH] == LATEST_VALUE_POSITION_REPLY_BYTES);
    assert(memcmp(&motor[SPI_MOTOR_RECORD_OFFSET_PAYLOAD], reply, sizeof(reply)) == 0);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_PAYLOAD + 6u] == 0u && motor[SPI_MOTOR_RECORD_OFFSET_PAYLOAD + 7u] == 0u);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US] == (uint8_t)1000u);

    /* Stale past PRM-MOT-01's window: FEEDBACK_VALID clear, the reply kept. */
    LatestValue_CopySnapshot(1001u + TEST_MOTOR_WINDOW_US, &copy);
    assert(copy.motors[2].freshness == LATEST_VALUE_FRESHNESS_STALE);
    assert(SpiProtocol_SerializeSnapshot(&copy, 0u, payload, &length) == SPI_PROTOCOL_OK);
    assert(motor[SPI_MOTOR_RECORD_OFFSET_VALIDITY_FLAGS] == 0u);
    assert(memcmp(&motor[SPI_MOTOR_RECORD_OFFSET_PAYLOAD], reply, sizeof(reply)) == 0);
    assert(SpiProtocol_SerializeSnapshot(NULL, 0u, payload, &length) == SPI_PROTOCOL_BAD_LENGTH);
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
    /* Validity bits as SPI_PAYLOAD_SCHEMA.md numbers them; bit 5 is reserved (R16). */
    assert(SPI_SENSOR_VALIDITY_SAMPLE_VALID == 0x0001u);
    assert(SPI_SENSOR_VALIDITY_COMMUNICATION_ERROR == 0x0002u);
    assert(SPI_SENSOR_VALIDITY_MAGNET_NOT_DETECTED == 0x0004u);
    assert(SPI_SENSOR_VALIDITY_MAGNET_TOO_WEAK == 0x0008u);
    assert(SPI_SENSOR_VALIDITY_MAGNET_TOO_STRONG == 0x0010u);
    assert(SPI_SENSOR_VALIDITY_NOT_FITTED == 0x0040u);
    assert(SPI_MOTOR_VALIDITY_FEEDBACK_VALID == 0x0001u);
    assert(SPI_MOTOR_VALIDITY_CONTROLLER_STATUS_VALID == 0x0002u);
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
    frame[SPI_FRAME_OFFSET_MAGIC] = (uint8_t)SPI_FRAME_MAGIC;
    frame[SPI_FRAME_OFFSET_MAGIC + 1u] = (uint8_t)(SPI_FRAME_MAGIC >> 8u);
    frame[SPI_FRAME_OFFSET_PROTOCOL_VERSION] = SPI_PROTOCOL_VERSION;
    frame[SPI_FRAME_OFFSET_MESSAGE_TYPE] = type;
    frame[SPI_FRAME_OFFSET_PAYLOAD_LENGTH] = (uint8_t)length;
    frame[SPI_FRAME_OFFSET_PAYLOAD_LENGTH + 1u] = (uint8_t)(length >> 8u);
    frame[SPI_FRAME_OFFSET_SEQUENCE] = (uint8_t)sequence;
    frame[SPI_FRAME_OFFSET_SEQUENCE + 1u] = (uint8_t)(sequence >> 8u);
    frame[SPI_FRAME_OFFSET_SEQUENCE + 2u] = (uint8_t)(sequence >> 16u);
    frame[SPI_FRAME_OFFSET_SEQUENCE + 3u] = (uint8_t)(sequence >> 24u);
    if ((SPI_FRAME_CRC_OFFSET(length) + SPI_FRAME_CRC_BYTES) <= SPI_FRAME_MAX_BYTES) {
        crc32 = Crc32IsoHdlc_Compute(frame, SPI_FRAME_HEADER_BYTES + length);
        Crc32IsoHdlc_WriteLittleEndian(crc32, &frame[SPI_FRAME_CRC_OFFSET(length)]);
    }
}

static void BuildTimeSyncRequest(uint8_t frame[SPI_FRAME_MAX_BYTES],
                                 uint32_t request_sequence,
                                 uint64_t pi_time_us,
                                 uint32_t sync_sequence)
{
    uint32_t crc32;

    BuildRequest(frame, SPI_MESSAGE_TIME_SYNC, SPI_TIME_SYNC_PAYLOAD_BYTES, request_sequence);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 0u] = SPI_TIME_SYNC_SCHEMA_VERSION;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 1u] = 0u;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 2u] = 0u;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 3u] = 0u;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 4u] = (uint8_t)pi_time_us;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 5u] = (uint8_t)(pi_time_us >> 8u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 6u] = (uint8_t)(pi_time_us >> 16u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 7u] = (uint8_t)(pi_time_us >> 24u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 8u] = (uint8_t)(pi_time_us >> 32u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 9u] = (uint8_t)(pi_time_us >> 40u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 10u] = (uint8_t)(pi_time_us >> 48u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 11u] = (uint8_t)(pi_time_us >> 56u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 12u] = (uint8_t)sync_sequence;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 13u] = (uint8_t)(sync_sequence >> 8u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 14u] = (uint8_t)(sync_sequence >> 16u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 15u] = (uint8_t)(sync_sequence >> 24u);
    crc32 = Crc32IsoHdlc_Compute(frame, SPI_FRAME_HEADER_BYTES + SPI_TIME_SYNC_PAYLOAD_BYTES);
    Crc32IsoHdlc_WriteLittleEndian(crc32, &frame[SPI_FRAME_CRC_OFFSET(SPI_TIME_SYNC_PAYLOAD_BYTES)]);
}

static void TestSpiProtocolState(void)
{
    uint32_t crc32;
    SpiProtocol_State state; uint8_t request[SPI_FRAME_MAX_BYTES]; uint8_t response[SPI_FRAME_MAX_BYTES]; uint8_t snapshot[SPI_SNAPSHOT_PREFIX_BYTES] = {1u};
    SpiProtocol_TimeSyncRequest time_sync;
    SpiProtocol_Init(&state); assert(SpiProtocol_BuildBootStatus(&state, response) == SPI_PROTOCOL_OK); assert(response[SPI_FRAME_OFFSET_MESSAGE_TYPE] == SPI_MESSAGE_DIAGNOSTIC);
    assert(SpiProtocol_SetUnsolicitedSnapshot(&state, snapshot, sizeof(snapshot)));
    BuildRequest(request, SPI_MESSAGE_GET_SNAPSHOT, 0u, 10u);
    assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_OK); assert(response[SPI_FRAME_OFFSET_MESSAGE_TYPE] == SPI_MESSAGE_SNAPSHOT);
    assert(response[SPI_FRAME_OFFSET_PAYLOAD + SPI_SNAPSHOT_OFFSET_RESPONSE_TO_SEQUENCE] == 10u);
    assert(response[SPI_FRAME_OFFSET_PAYLOAD + SPI_SNAPSHOT_OFFSET_RESPONSE_TO_SEQUENCE + 1u] == 0u);
    BuildTimeSyncRequest(request, 11u, UINT64_C(123456789), 3u);
    assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_OK);
    assert(response[SPI_FRAME_OFFSET_MESSAGE_TYPE] == SPI_MESSAGE_ACK);
    assert(SpiProtocol_ParseTimeSyncRequest(request, &time_sync) == SPI_PROTOCOL_OK);
    assert(time_sync.request_sequence == 11u);
    assert(time_sync.pi_time_us == UINT64_C(123456789));
    assert(time_sync.sync_sequence == 3u);
    request[0] ^= 1u; assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_BAD_MAGIC); assert(response[SPI_FRAME_OFFSET_MESSAGE_TYPE] == SPI_MESSAGE_NACK);
    BuildRequest(request, SPI_MESSAGE_GET_STATUS, 0u, 11u); assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_BAD_SEQUENCE);
    BuildRequest(request, SPI_MESSAGE_GET_STATUS, (uint16_t)(SPI_PAYLOAD_MAX_BYTES + 1u), 12u); assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_BAD_LENGTH);
    BuildRequest(request, SPI_MESSAGE_TIME_SYNC, 15u, 13u); assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_BAD_TIME_SYNC);
    BuildTimeSyncRequest(request, 13u, UINT64_C(123456789), 4u);
    request[SPI_FRAME_OFFSET_PAYLOAD] = 2u;
    crc32 = Crc32IsoHdlc_Compute(request, SPI_FRAME_HEADER_BYTES + SPI_TIME_SYNC_PAYLOAD_BYTES);
    Crc32IsoHdlc_WriteLittleEndian(crc32, &request[SPI_FRAME_CRC_OFFSET(SPI_TIME_SYNC_PAYLOAD_BYTES)]);
    assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_BAD_TIME_SYNC);
}

static uint32_t TestReadU32(const uint8_t *data)
{
    return (uint32_t)data[0] | ((uint32_t)data[1] << 8u) | ((uint32_t)data[2] << 16u) | ((uint32_t)data[3] << 24u);
}

static void TestSpiVersionReply(void)
{
    SpiProtocol_State state;
    uint8_t request[SPI_FRAME_MAX_BYTES];
    uint8_t response[SPI_FRAME_MAX_BYTES];
    const uint8_t *payload = &response[SPI_FRAME_OFFSET_PAYLOAD];

    SpiProtocol_Init(&state);

    BuildRequest(request, SPI_MESSAGE_GET_VERSION, 1u, 20u);
    request[SPI_FRAME_OFFSET_PAYLOAD] = SPI_REQUEST_SCHEMA_VERSION;
    Crc32IsoHdlc_WriteLittleEndian(Crc32IsoHdlc_Compute(request, SPI_FRAME_HEADER_BYTES + 1u),
                                   &request[SPI_FRAME_CRC_OFFSET(1u)]);

    assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_OK);
    assert(response[SPI_FRAME_OFFSET_MESSAGE_TYPE] == SPI_MESSAGE_VERSION);
    assert(response[SPI_FRAME_OFFSET_PAYLOAD_LENGTH] == (uint8_t)SPI_VERSION_PAYLOAD_BYTES);
    assert(response[SPI_FRAME_OFFSET_PAYLOAD_LENGTH + 1u] == 0u);

    assert(payload[SPI_VERSION_OFFSET_SCHEMA_VERSION] == SPI_VERSION_SCHEMA_VERSION);
    assert(payload[SPI_VERSION_OFFSET_PROTOCOL_VERSION] == SPI_PROTOCOL_VERSION);
    assert(payload[SPI_VERSION_OFFSET_FW_MAJOR] == FIRMWARE_VERSION_MAJOR);
    assert(payload[SPI_VERSION_OFFSET_FW_MINOR] == FIRMWARE_VERSION_MINOR);
    assert(payload[SPI_VERSION_OFFSET_FW_PATCH] == FIRMWARE_VERSION_PATCH);
    assert(payload[SPI_VERSION_OFFSET_BUILD_FLAGS] == FIRMWARE_BUILD_FLAGS);
    assert(payload[SPI_VERSION_OFFSET_RESERVED] == 0u);
    assert(payload[SPI_VERSION_OFFSET_RESERVED + 1u] == 0u);
    assert(TestReadU32(&payload[SPI_VERSION_OFFSET_RESPONSE_TO_SEQUENCE]) == 20u);
    assert(TestReadU32(&payload[SPI_VERSION_OFFSET_GIT_HASH_ABBREV]) == FIRMWARE_GIT_HASH_ABBREV);
    assert(TestReadU32(&payload[SPI_VERSION_OFFSET_COMMIT_EPOCH_SECS]) == FIRMWARE_COMMIT_EPOCH_SECS);

    assert(Crc32IsoHdlc_Verify(response, SPI_FRAME_HEADER_BYTES + SPI_VERSION_PAYLOAD_BYTES,
                               &response[SPI_FRAME_CRC_OFFSET(SPI_VERSION_PAYLOAD_BYTES)]));

    /* An unassigned request type must still be rejected. */
    BuildRequest(request, UINT8_C(0x15), 0u, 21u);
    assert(SpiProtocol_ProcessRequest(&state, request, response) == SPI_PROTOCOL_BAD_MESSAGE);
    assert(response[SPI_FRAME_OFFSET_MESSAGE_TYPE] == SPI_MESSAGE_NACK);
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

static void TestLifecycleTransitions(void)
{
    Lifecycle_Record record;

    Lifecycle_Init(&record, "test");
    assert(record.state == LIFECYCLE_STATE_UNCONFIGURED);
    assert(Lifecycle_Apply(&record, LIFECYCLE_TRANSITION_CONFIGURE, true, 0u) == LIFECYCLE_RESULT_OK);
    assert(record.state == LIFECYCLE_STATE_INACTIVE);
    assert(Lifecycle_Apply(&record, LIFECYCLE_TRANSITION_ACTIVATE, true, 0u) == LIFECYCLE_RESULT_OK);
    assert(record.state == LIFECYCLE_STATE_ACTIVE);
    assert(Lifecycle_Apply(&record, LIFECYCLE_TRANSITION_DEACTIVATE, true, 0u) == LIFECYCLE_RESULT_OK);
    assert(record.state == LIFECYCLE_STATE_INACTIVE);
    assert(Lifecycle_Apply(&record, LIFECYCLE_TRANSITION_ACTIVATE, false, 7u) == LIFECYCLE_RESULT_OPERATION_FAILED);
    assert(record.state == LIFECYCLE_STATE_ERROR);
    assert(record.fault_code == 7u);
    assert(Lifecycle_Apply(&record, LIFECYCLE_TRANSITION_RECOVER, true, 0u) == LIFECYCLE_RESULT_OK);
    assert(record.state == LIFECYCLE_STATE_INACTIVE);
    assert(Lifecycle_Apply(&record, LIFECYCLE_TRANSITION_CLEANUP, true, 0u) == LIFECYCLE_RESULT_OK);
    assert(record.state == LIFECYCLE_STATE_UNCONFIGURED);
    assert(Lifecycle_Apply(&record, LIFECYCLE_TRANSITION_DEACTIVATE, true, 0u) == LIFECYCLE_RESULT_INVALID_TRANSITION);
}

static void TestHealthMonitorSnapshotLevels(void)
{
    const HealthMonitor_Snapshot *snapshot;

    ResetHealthMonitorInputs();
    s_test_now_us = 100u;
    HealthMonitor_Init();
    snapshot = HealthMonitor_GetSnapshot();
    assert(snapshot->level == HEALTH_MONITOR_LEVEL_UNKNOWN);
    assert(snapshot->timestamp_us == 100u);

    s_test_now_us = 200u;
    s_test_sync_snapshot.valid = true;
    s_test_sync_snapshot.quality = TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED;
    s_test_i2c_state = LIFECYCLE_STATE_ACTIVE;
    s_test_sensor_state = LIFECYCLE_STATE_ACTIVE;
    s_test_can_state = LIFECYCLE_STATE_ACTIVE;
    s_test_spi_state = LIFECYCLE_STATE_ACTIVE;
    s_test_sensor_snapshot.result = SENSOR_TASK_BRINGUP_PASS;
    s_test_sensor_snapshot.sample_ok_count = 5u;
    s_test_i2c_success_count = 4u;
    s_test_spi_diagnostics.staged_frame_count = 2u;
    HealthMonitor_Process();
    snapshot = HealthMonitor_GetSnapshot();
    assert(snapshot->level == HEALTH_MONITOR_LEVEL_GREEN);
    assert(snapshot->sensor_sample_ok_count == 5u);
    assert(snapshot->i2c_success_count == 4u);
    assert(snapshot->spi_staged_frame_count == 2u);
    assert(snapshot->timestamp_us == 200u);

    s_test_now_us = 300u;
    s_test_sync_snapshot.valid = false;
    HealthMonitor_Process();
    assert(HealthMonitor_GetLevel() == HEALTH_MONITOR_LEVEL_YELLOW);

    s_test_now_us = 400u;
    s_test_app_mks_register_failures = 1u;
    HealthMonitor_Process();
    snapshot = HealthMonitor_GetSnapshot();
    assert(snapshot->level == HEALTH_MONITOR_LEVEL_RED);
    assert(snapshot->app_mks_register_failures == 1u);
}

int main(void)
{
    TestWrapExtension();
    TestMonotonicAcrossMultipleWraps();
    TestInitialAcceptanceAndRuntimeRejection();
    TestTimeoutResetAndRecovery();
    TestSyncDebugMirrorRejectionCodes();
    TestCalibrationRecordValidation();
    TestCalibrationDuplicateIdentity();
    TestCalibrationGenerationSelection();
    TestJointMappingValidation();
    TestJointMappingInvalidRatioAndRevision();
    TestLatestValueConfigure();
    TestLatestValueSampleAgeing();
    TestLatestValueSampleConditions();
    TestLatestValueRefusedWrites();
    TestLatestValueFeedbackMerge();
    TestSnapshotLayout();
    TestSnapshotFrameOwnership();
    TestCrc32IsoHdlc();
    TestSpiProtocolState();
    TestSpiVersionReply();
    TestDataReadyState();
    TestCanTxAndRecoveryPolicy();
    TestLifecycleTransitions();
    TestHealthMonitorSnapshotLevels();
    return 0;
}