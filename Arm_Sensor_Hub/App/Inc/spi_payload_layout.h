/**
 * @file spi_payload_layout.h
 * @brief Wire-format sizes and offsets for SPI frames and snapshot payloads.
 */

#ifndef SPI_PAYLOAD_LAYOUT_H
#define SPI_PAYLOAD_LAYOUT_H

#include <stdint.h>

/** Fixed on-wire frame size for every SPI transaction. */
#define SPI_FRAME_MAX_BYTES UINT16_C(512)
/** Bytes in the fixed transport header before the payload starts. */
#define SPI_FRAME_HEADER_BYTES UINT16_C(18)
/** Bytes reserved for the CRC field at the end of each frame. */
#define SPI_FRAME_CRC_BYTES UINT16_C(4)
/** Maximum payload capacity after accounting for the fixed header and CRC. */
#define SPI_PAYLOAD_MAX_BYTES UINT16_C(490)
/** Synchronization value in the first two bytes of every frame, little-endian on the wire
 *  (SPI_SYSTEM_INTERFACE.md section 3). */
#define SPI_FRAME_MAGIC UINT16_C(0xA55A)

/** Magic field offset used to reject misaligned or malformed frames. */
#define SPI_FRAME_OFFSET_MAGIC UINT16_C(0)
/** Transport protocol version carried in every frame. */
#define SPI_FRAME_OFFSET_PROTOCOL_VERSION UINT16_C(2)
/** Message type selector for request/response routing. */
#define SPI_FRAME_OFFSET_MESSAGE_TYPE UINT16_C(3)
/** Little-endian payload length field. */
#define SPI_FRAME_OFFSET_PAYLOAD_LENGTH UINT16_C(4)
/** Per-frame transport sequence number. */
#define SPI_FRAME_OFFSET_SEQUENCE UINT16_C(6)
/** Frame assembly timestamp in the synchronized hub time domain. */
#define SPI_FRAME_OFFSET_TIME_US UINT16_C(10)
/** Start of the message-specific payload area. */
#define SPI_FRAME_OFFSET_PAYLOAD SPI_FRAME_HEADER_BYTES
/** Start offset of the CRC for a payload of the supplied length. */
#define SPI_FRAME_CRC_OFFSET(payload_length) (SPI_FRAME_HEADER_BYTES + (payload_length))

/** Serialized size of the VERSION (0x04) payload. */
#define SPI_VERSION_PAYLOAD_BYTES UINT16_C(20)
#define SPI_VERSION_OFFSET_SCHEMA_VERSION UINT16_C(0)
#define SPI_VERSION_OFFSET_PROTOCOL_VERSION UINT16_C(1)
#define SPI_VERSION_OFFSET_FW_MAJOR UINT16_C(2)
#define SPI_VERSION_OFFSET_FW_MINOR UINT16_C(3)
#define SPI_VERSION_OFFSET_FW_PATCH UINT16_C(4)
#define SPI_VERSION_OFFSET_BUILD_FLAGS UINT16_C(5)
#define SPI_VERSION_OFFSET_RESERVED UINT16_C(6)
#define SPI_VERSION_OFFSET_RESPONSE_TO_SEQUENCE UINT16_C(8)
#define SPI_VERSION_OFFSET_GIT_HASH_ABBREV UINT16_C(12)
#define SPI_VERSION_OFFSET_COMMIT_EPOCH_SECS UINT16_C(16)

/** Serialized size of the ACK (0x80) and NACK (0x81) payload (SPI_PAYLOAD_SCHEMA.md). */
#define SPI_COMMAND_REPLY_PAYLOAD_BYTES UINT16_C(12)
#define SPI_COMMAND_REPLY_OFFSET_SCHEMA_VERSION UINT16_C(0)
#define SPI_COMMAND_REPLY_OFFSET_REQUEST_TYPE UINT16_C(1)
#define SPI_COMMAND_REPLY_OFFSET_STATUS_CODE UINT16_C(2)
#define SPI_COMMAND_REPLY_OFFSET_REQUEST_SEQUENCE UINT16_C(4)
#define SPI_COMMAND_REPLY_OFFSET_DETAIL_CODE UINT16_C(8)

/** Snapshot prefix shared by all snapshot payload instances. */
#define SPI_SNAPSHOT_PREFIX_BYTES UINT16_C(12)
#define SPI_SNAPSHOT_OFFSET_SCHEMA_VERSION UINT16_C(0)
#define SPI_SNAPSHOT_OFFSET_SENSOR_COUNT UINT16_C(1)
#define SPI_SNAPSHOT_OFFSET_MOTOR_COUNT UINT16_C(2)
#define SPI_SNAPSHOT_OFFSET_RESERVED UINT16_C(3)
#define SPI_SNAPSHOT_OFFSET_FLAGS UINT16_C(4)
#define SPI_SNAPSHOT_OFFSET_DROPPED_SNAPSHOT_COUNT_LOW UINT16_C(6)
#define SPI_SNAPSHOT_OFFSET_RESPONSE_TO_SEQUENCE UINT16_C(8)

/** Serialized size of one fixed-width sensor record within a snapshot. */
#define SPI_SENSOR_RECORD_BYTES UINT16_C(24)
#define SPI_SENSOR_RECORD_OFFSET_SENSOR_ID UINT16_C(0)
#define SPI_SENSOR_RECORD_OFFSET_STATUS UINT16_C(1)
#define SPI_SENSOR_RECORD_OFFSET_VALIDITY_FLAGS UINT16_C(2)
#define SPI_SENSOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US UINT16_C(4)
#define SPI_SENSOR_RECORD_OFFSET_RAW_ANGLE UINT16_C(12)
#define SPI_SENSOR_RECORD_OFFSET_PROCESSED_ANGLE_MDEG UINT16_C(14)
#define SPI_SENSOR_RECORD_OFFSET_MAGNITUDE UINT16_C(18)
#define SPI_SENSOR_RECORD_OFFSET_AGC UINT16_C(20)
#define SPI_SENSOR_RECORD_OFFSET_RESERVED UINT16_C(21)
#define SPI_SENSOR_RECORD_OFFSET_RESERVED_2 UINT16_C(22)
/** Sensor validity bit 6: axis has no encoder in the commissioning table (SPI_PAYLOAD_SCHEMA.md). */
#define SPI_SENSOR_VALIDITY_NOT_FITTED UINT16_C(0x0040)

/** Serialized size of one fixed-width motor record within a snapshot. */
#define SPI_MOTOR_RECORD_BYTES UINT16_C(24)
#define SPI_MOTOR_RECORD_OFFSET_MOTOR_INDEX UINT16_C(0)
#define SPI_MOTOR_RECORD_OFFSET_STATUS UINT16_C(1)
#define SPI_MOTOR_RECORD_OFFSET_VALIDITY_FLAGS UINT16_C(2)
#define SPI_MOTOR_RECORD_OFFSET_CAN_ID UINT16_C(4)
#define SPI_MOTOR_RECORD_OFFSET_COMMAND_CODE UINT16_C(6)
#define SPI_MOTOR_RECORD_OFFSET_PAYLOAD_LENGTH UINT16_C(7)
#define SPI_MOTOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US UINT16_C(8)
#define SPI_MOTOR_RECORD_OFFSET_PAYLOAD UINT16_C(16)

/** Number of logical joint sensor records published in each snapshot. */
#define SPI_SNAPSHOT_SENSOR_RECORD_COUNT UINT16_C(6)
/** Maximum number of motor records that can fit in a snapshot payload. */
#define SPI_SNAPSHOT_MOTOR_RECORD_MAX_COUNT UINT16_C(8)
/** Compute the serialized payload size for a snapshot with the given motor count. */
#define SPI_SNAPSHOT_PAYLOAD_BYTES(motor_count) \
    (SPI_SNAPSHOT_PREFIX_BYTES + (SPI_SNAPSHOT_SENSOR_RECORD_COUNT * SPI_SENSOR_RECORD_BYTES) + \
     ((motor_count) * SPI_MOTOR_RECORD_BYTES))
/** Largest payload this snapshot schema can emit. */
#define SPI_SNAPSHOT_MAX_PAYLOAD_BYTES SPI_SNAPSHOT_PAYLOAD_BYTES(SPI_SNAPSHOT_MOTOR_RECORD_MAX_COUNT)
/** Largest complete frame emitted by the current snapshot schema. */
#define SPI_SNAPSHOT_MAX_FRAME_BYTES \
    (SPI_FRAME_HEADER_BYTES + SPI_SNAPSHOT_MAX_PAYLOAD_BYTES + SPI_FRAME_CRC_BYTES)

_Static_assert(SPI_PAYLOAD_MAX_BYTES == (SPI_FRAME_MAX_BYTES - SPI_FRAME_HEADER_BYTES - SPI_FRAME_CRC_BYTES),
               "SPI payload maximum must match fixed frame overhead");
_Static_assert(SPI_VERSION_PAYLOAD_BYTES == (SPI_VERSION_OFFSET_COMMIT_EPOCH_SECS + 4u),
               "Version payload offsets must consume its fixed size");
_Static_assert(SPI_COMMAND_REPLY_PAYLOAD_BYTES == (SPI_COMMAND_REPLY_OFFSET_DETAIL_CODE + 4u),
               "Command reply offsets must consume its fixed size");
_Static_assert(SPI_SENSOR_RECORD_BYTES == (SPI_SENSOR_RECORD_OFFSET_RESERVED_2 + 2u),
               "Sensor record offsets must consume its fixed size");
_Static_assert(SPI_MOTOR_RECORD_BYTES == (SPI_MOTOR_RECORD_OFFSET_PAYLOAD + 8u),
               "Motor record offsets must consume its fixed size");
_Static_assert(SPI_SNAPSHOT_MAX_PAYLOAD_BYTES == 348u, "Maximum snapshot payload size changed");
_Static_assert(SPI_SNAPSHOT_MAX_PAYLOAD_BYTES <= SPI_PAYLOAD_MAX_BYTES,
               "Maximum snapshot payload exceeds the frame payload limit");
_Static_assert(SPI_SNAPSHOT_MAX_FRAME_BYTES == 370u, "Maximum snapshot frame size changed");
_Static_assert(SPI_SNAPSHOT_MAX_FRAME_BYTES <= SPI_FRAME_MAX_BYTES,
               "Maximum snapshot frame exceeds the fixed frame limit");

#endif /* SPI_PAYLOAD_LAYOUT_H */