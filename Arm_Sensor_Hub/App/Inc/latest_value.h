/**
 * @file latest_value.h
 * @brief The latest-value store: one owner for the newest encoder sample of each axis and the
 *        newest drive feedback of each motor, their ageing, and the coherent snapshot copy.
 *
 * Producers (the sensor task, the CAN service) only accept. The SPI service takes a copy and
 * serialises that copy (SpiProtocol_SerializeSnapshot), never the live records. This is the
 * implementation of snapshot coherency (SPI_SYSTEM_INTERFACE.md section 8): every record is
 * copied whole, keeps its own acquisition timestamp, and cannot change while it is serialised
 * or sent by DMA.
 *
 * Freshness is decided when the copy is taken: a record is stale when now minus its
 * acquisition timestamp exceeds its kind's window. The caller passes `now`, so the store
 * depends on no clock (TimeService) and no HAL.
 *
 * Every accept and the copy run inside a FreeRTOS task critical section (ruling R15: the
 * stores are protected once acquisition has its own task). None may be called from an
 * interrupt. LatestValue_Configure takes no lock and runs before any producer (App_Init,
 * before the scheduler starts, when a critical section would leave interrupts masked).
 */

#ifndef LATEST_VALUE_H
#define LATEST_VALUE_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Sensor slots: the logical axes 0-5 that every snapshot carries. */
#define LATEST_VALUE_SENSOR_COUNT 6u
/** Motor slots: the drive table size of the CAN service. */
#define LATEST_VALUE_MOTOR_COUNT 8u
/** Highest logical joint a motor slot may carry (joints 0-5). */
#define LATEST_VALUE_MAX_LOGICAL_JOINT 5u
/** Highest AS5600 RAW ANGLE count (12 bit, PRM-ACQ-06); a larger sample is refused. */
#define LATEST_VALUE_MAX_RAW_ANGLE 4095u
/** Calibration version the processed angle is computed with: scale only, no calibration yet. */
#define LATEST_VALUE_CALIBRATION_VERSION 0u
/**
 * Bytes of a position reply after its command code: 30H carries int32 carry + uint16 value, 31H
 * an int48 cumulative value, both big-endian and both six bytes (MKS manual pp. 26-27).
 */
#define LATEST_VALUE_POSITION_REPLY_BYTES 6u

typedef enum {
    LATEST_VALUE_OK = 0,
    LATEST_VALUE_INVALID_ARGUMENT,
    /** The axis has no encoder in the commissioning table. */
    LATEST_VALUE_NOT_FITTED,
    /** No drive is registered in the motor slot. */
    LATEST_VALUE_NOT_REGISTERED
} LatestValue_Result;

/** Outcome of one encoder read, mapped to the validity flags when serialised. */
typedef enum {
    LATEST_VALUE_SAMPLE_OK = 0,
    LATEST_VALUE_SAMPLE_COMM_ERROR,
    LATEST_VALUE_SAMPLE_MAGNET_MISSING,
    LATEST_VALUE_SAMPLE_MAGNET_WEAK,
    LATEST_VALUE_SAMPLE_MAGNET_STRONG
} LatestValue_SampleCondition;

/** Freshness of a record in a copy, judged at copy time. */
typedef enum {
    /** No usable value: never written, a failed sample, not fitted or not registered. */
    LATEST_VALUE_FRESHNESS_NONE = 0,
    LATEST_VALUE_FRESHNESS_FRESH,
    LATEST_VALUE_FRESHNESS_STALE
} LatestValue_Freshness;

typedef enum {
    /** An encoder reply (30H as polled today; 31H once ruling R11 lands): position. */
    LATEST_VALUE_FEEDBACK_POSITION = 0,
    /** A 32H reply: real-time speed. */
    LATEST_VALUE_FEEDBACK_SPEED
} LatestValue_FeedbackKind;

typedef struct {
    bool registered;
    uint8_t logical_joint_id;
    uint16_t can_id;
    uint32_t configuration_version;
} LatestValue_MotorSlotConfig;

typedef struct {
    bool sensor_fitted[LATEST_VALUE_SENSOR_COUNT];
    LatestValue_MotorSlotConfig motors[LATEST_VALUE_MOTOR_COUNT];
    /** Sensor freshness window (PRM-ACQ-07); must be non-zero. */
    uint64_t sensor_window_us;
    /** Motor feedback window (PRM-MOT-01); must be non-zero. */
    uint64_t motor_window_us;
} LatestValue_Config;

/** One encoder read as the sensor task took it. */
typedef struct {
    LatestValue_SampleCondition condition;
    /** The AS5600 STATUS register of the read; 0 on a bus error. */
    uint8_t status;
    uint16_t raw_angle_counts;
    uint16_t magnitude;
    uint8_t agc;
    uint64_t timestamp_us;
} LatestValue_Sample;

/** One decoded drive reply as the CAN service received it. */
typedef struct {
    LatestValue_FeedbackKind kind;
    uint64_t timestamp_us;
    /** POSITION: encoder counts, 16384 per motor turn (0x4000, manual pp. 26-27). */
    int64_t position_counts;
    /** POSITION: the reply's command code (0x30 or 0x31), kept for the schema v1 motor record. */
    uint8_t position_command_code;
    /** POSITION: the reply bytes after the command code, kept for the schema v1 motor record. */
    uint8_t position_reply[LATEST_VALUE_POSITION_REPLY_BYTES];
    /** SPEED: the 32H value. */
    int16_t speed_rpm;
} LatestValue_Feedback;

typedef struct {
    uint8_t logical_id;
    bool fitted;
    /** A sample has been accepted since Configure. */
    bool has_sample;
    LatestValue_SampleCondition condition;
    LatestValue_Freshness freshness;
    uint8_t status;
    uint16_t raw_angle_counts;
    int32_t processed_angle_mdeg;
    uint16_t magnitude;
    uint8_t agc;
    /** Acquisition time of the sample; for a not-fitted axis, the copy time. */
    uint64_t measurement_timestamp_us;
    uint32_t calibration_version;
} LatestValue_SensorRecord;

typedef struct {
    uint8_t motor_index;
    bool registered;
    uint8_t logical_joint_id;
    uint16_t can_id;
    uint32_t configuration_version;
    /** Valid once a position has arrived; freshness follows the position's age. */
    bool has_position;
    LatestValue_Freshness freshness;
    int64_t position_counts;
    uint64_t position_timestamp_us;
    bool has_speed;
    int16_t speed_rpm;
    uint64_t speed_timestamp_us;
    /** The last position reply, kept only so the schema v1 motor record stays as it was (R10a). */
    uint8_t position_command_code;
    uint8_t position_reply[LATEST_VALUE_POSITION_REPLY_BYTES];
} LatestValue_MotorRecord;

typedef struct {
    /** The `now` the copy was judged at. */
    uint64_t copied_at_us;
    LatestValue_SensorRecord sensors[LATEST_VALUE_SENSOR_COUNT];
    LatestValue_MotorRecord motors[LATEST_VALUE_MOTOR_COUNT];
} LatestValue_Snapshot;

/**
 * Sets the slot properties and windows and clears every record. A rejected config (a joint
 * above 5, a CAN ID above 0x7FF, a zero window) changes nothing.
 */
LatestValue_Result LatestValue_Configure(const LatestValue_Config *config);
/** Accepts one sample for a fitted axis; a not-fitted axis or a raw count above 4095 is refused. */
LatestValue_Result LatestValue_AcceptSample(uint8_t axis, const LatestValue_Sample *sample);
/** Merges one reply into a registered motor's record; an unregistered slot is refused. */
LatestValue_Result LatestValue_AcceptFeedback(uint8_t motor_index, const LatestValue_Feedback *feedback);
/** Copies every record coherently and judges freshness at now_us. */
void LatestValue_CopySnapshot(uint64_t now_us, LatestValue_Snapshot *out);

#ifdef __cplusplus
}
#endif

#endif /* LATEST_VALUE_H */
