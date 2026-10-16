#include "spi_protocol.h"

#include <stddef.h>
#include <string.h>

#include "crc32_iso_hdlc.h"
#include "firmware_version.h"
#include "le_bytes.h"
#include "time_service.h"

static bool SpiProtocol_IsNewer(uint32_t candidate, uint32_t previous) { return candidate != previous && (uint32_t)(candidate - previous) < UINT32_C(0x80000000); }

static void SpiProtocol_BuildFrame(SpiProtocol_State *state, uint8_t type, const uint8_t *payload, uint16_t length, uint8_t *response)
{
    uint32_t crc32;
    memset(response, 0, SPI_FRAME_MAX_BYTES);
    LeBytes_WriteU16(&response[SPI_FRAME_OFFSET_MAGIC], SPI_FRAME_MAGIC);
    response[SPI_FRAME_OFFSET_PROTOCOL_VERSION] = SPI_PROTOCOL_VERSION;
    response[SPI_FRAME_OFFSET_MESSAGE_TYPE] = type;
    LeBytes_WriteU16(&response[SPI_FRAME_OFFSET_PAYLOAD_LENGTH], length);
    LeBytes_WriteU32(&response[SPI_FRAME_OFFSET_SEQUENCE], state->next_tx_sequence++);
    LeBytes_WriteU64(&response[SPI_FRAME_OFFSET_TIME_US], TimeService_NowUs());
    if (length > 0u) { memcpy(&response[SPI_FRAME_OFFSET_PAYLOAD], payload, length); }
    crc32 = Crc32IsoHdlc_Compute(response, SPI_FRAME_HEADER_BYTES + length);
    Crc32IsoHdlc_WriteLittleEndian(crc32, &response[SPI_FRAME_CRC_OFFSET(length)]);
}

static bool SpiProtocol_ValidateTimeSyncPayload(const uint8_t request[SPI_FRAME_MAX_BYTES])
{
    uint16_t length = LeBytes_ReadU16(&request[SPI_FRAME_OFFSET_PAYLOAD_LENGTH]);
    const uint8_t *payload = &request[SPI_FRAME_OFFSET_PAYLOAD];

    return (length == SPI_TIME_SYNC_PAYLOAD_BYTES) &&
           (payload[0] == SPI_TIME_SYNC_SCHEMA_VERSION);
}

void SpiProtocol_BuildCommandReply(SpiProtocol_State *state, uint8_t type, uint8_t request_type,
                                   uint32_t request_sequence, uint16_t code, uint32_t detail_code,
                                   uint8_t response[SPI_FRAME_MAX_BYTES])
{
    uint8_t payload[SPI_COMMAND_REPLY_PAYLOAD_BYTES] = {0};
    payload[SPI_COMMAND_REPLY_OFFSET_SCHEMA_VERSION] = SPI_COMMAND_REPLY_SCHEMA_VERSION;
    payload[SPI_COMMAND_REPLY_OFFSET_REQUEST_TYPE] = request_type;
    LeBytes_WriteU16(&payload[SPI_COMMAND_REPLY_OFFSET_STATUS_CODE], code);
    LeBytes_WriteU32(&payload[SPI_COMMAND_REPLY_OFFSET_REQUEST_SEQUENCE], request_sequence);
    LeBytes_WriteU32(&payload[SPI_COMMAND_REPLY_OFFSET_DETAIL_CODE], detail_code);
    SpiProtocol_BuildFrame(state, type, payload, sizeof(payload), response);
}

static void SpiProtocol_BuildVersionReply(SpiProtocol_State *state, uint32_t request_sequence, uint8_t *response)
{
    uint8_t payload[SPI_VERSION_PAYLOAD_BYTES] = {0};

    payload[SPI_VERSION_OFFSET_SCHEMA_VERSION] = SPI_VERSION_SCHEMA_VERSION;
    payload[SPI_VERSION_OFFSET_PROTOCOL_VERSION] = SPI_PROTOCOL_VERSION;
    payload[SPI_VERSION_OFFSET_FW_MAJOR] = FIRMWARE_VERSION_MAJOR;
    payload[SPI_VERSION_OFFSET_FW_MINOR] = FIRMWARE_VERSION_MINOR;
    payload[SPI_VERSION_OFFSET_FW_PATCH] = FIRMWARE_VERSION_PATCH;
    payload[SPI_VERSION_OFFSET_BUILD_FLAGS] = FIRMWARE_BUILD_FLAGS;
    LeBytes_WriteU32(&payload[SPI_VERSION_OFFSET_RESPONSE_TO_SEQUENCE], request_sequence);
    LeBytes_WriteU32(&payload[SPI_VERSION_OFFSET_GIT_HASH_ABBREV], FIRMWARE_GIT_HASH_ABBREV);
    LeBytes_WriteU32(&payload[SPI_VERSION_OFFSET_COMMIT_EPOCH_SECS], FIRMWARE_COMMIT_EPOCH_SECS);
    SpiProtocol_BuildFrame(state, SPI_MESSAGE_VERSION, payload, sizeof(payload), response);
}

void SpiProtocol_Init(SpiProtocol_State *state) { if (state != NULL) { memset(state, 0, sizeof(*state)); } }
bool SpiProtocol_SetUnsolicitedSnapshot(SpiProtocol_State *state, const uint8_t *payload, uint16_t length)
{
    if ((state == NULL) || (payload == NULL) || (length < SPI_SNAPSHOT_PREFIX_BYTES) || (length > SPI_PAYLOAD_MAX_BYTES)) { return false; }
    memcpy(state->unsolicited_payload, payload, length); state->unsolicited_payload_length = length; state->unsolicited_pending = true; return true;
}
SpiProtocol_Result SpiProtocol_BuildBootStatus(SpiProtocol_State *state, uint8_t response[SPI_FRAME_MAX_BYTES])
{
    if ((state == NULL) || (response == NULL)) { return SPI_PROTOCOL_BAD_LENGTH; }
    SpiProtocol_BuildFrame(state, SPI_MESSAGE_DIAGNOSTIC, NULL, 0u, response); return SPI_PROTOCOL_OK;
}

SpiProtocol_Result SpiProtocol_BuildSnapshotFrame(SpiProtocol_State *state,
                                                  const uint8_t *payload,
                                                  uint16_t payload_length,
                                                  uint8_t response[SPI_FRAME_MAX_BYTES])
{
    if ((state == NULL) || (payload == NULL) || (response == NULL) ||
        (payload_length < SPI_SNAPSHOT_PREFIX_BYTES) || (payload_length > SPI_PAYLOAD_MAX_BYTES)) {
        return SPI_PROTOCOL_BAD_LENGTH;
    }

    SpiProtocol_BuildFrame(state, SPI_MESSAGE_SNAPSHOT, payload, payload_length, response);
    return SPI_PROTOCOL_OK;
}

_Static_assert(LATEST_VALUE_SENSOR_COUNT == SPI_SNAPSHOT_SENSOR_RECORD_COUNT,
               "Every sensor slot is one fixed snapshot record");
_Static_assert(LATEST_VALUE_MOTOR_COUNT <= SPI_SNAPSHOT_MOTOR_RECORD_MAX_COUNT,
               "Every motor slot must fit in the snapshot");
_Static_assert(LATEST_VALUE_POSITION_REPLY_BYTES <= 8u, "The position reply fits the motor record payload");

static uint16_t SpiProtocol_SensorValidity(const LatestValue_SensorRecord *record)
{
    if (!record->fitted) { return SPI_SENSOR_VALIDITY_NOT_FITTED; }
    if (!record->has_sample) { return 0u; }
    switch (record->condition) {
    case LATEST_VALUE_SAMPLE_OK:
        /* Stale: bit 0 clear, the last values and timestamp kept (SPI_PAYLOAD_SCHEMA.md). */
        return (record->freshness == LATEST_VALUE_FRESHNESS_FRESH) ? SPI_SENSOR_VALIDITY_SAMPLE_VALID : 0u;
    case LATEST_VALUE_SAMPLE_COMM_ERROR: return SPI_SENSOR_VALIDITY_COMMUNICATION_ERROR;
    case LATEST_VALUE_SAMPLE_MAGNET_MISSING: return SPI_SENSOR_VALIDITY_MAGNET_NOT_DETECTED;
    case LATEST_VALUE_SAMPLE_MAGNET_WEAK: return SPI_SENSOR_VALIDITY_MAGNET_TOO_WEAK;
    case LATEST_VALUE_SAMPLE_MAGNET_STRONG: return SPI_SENSOR_VALIDITY_MAGNET_TOO_STRONG;
    default: return 0u;
    }
}

static void SpiProtocol_SerializeSensorRecord(uint8_t *out, const LatestValue_SensorRecord *record)
{
    out[SPI_SENSOR_RECORD_OFFSET_SENSOR_ID] = record->logical_id;
    out[SPI_SENSOR_RECORD_OFFSET_STATUS] = record->status;
    LeBytes_WriteU16(&out[SPI_SENSOR_RECORD_OFFSET_VALIDITY_FLAGS], SpiProtocol_SensorValidity(record));
    LeBytes_WriteU64(&out[SPI_SENSOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US], record->measurement_timestamp_us);
    LeBytes_WriteU16(&out[SPI_SENSOR_RECORD_OFFSET_RAW_ANGLE], record->raw_angle_counts);
    LeBytes_WriteU32(&out[SPI_SENSOR_RECORD_OFFSET_PROCESSED_ANGLE_MDEG], (uint32_t)record->processed_angle_mdeg);
    LeBytes_WriteU16(&out[SPI_SENSOR_RECORD_OFFSET_MAGNITUDE], record->magnitude);
    out[SPI_SENSOR_RECORD_OFFSET_AGC] = record->agc;
}

/* The v1 motor record carries the last position reply only (ruling R10); speed stays in the copy.
 * Neither polled reply (30H position, 32H speed) has a status byte, so `status` is 0 and
 * CONTROLLER_STATUS_VALID is never set. */
static void SpiProtocol_SerializeMotorRecord(uint8_t *out, const LatestValue_MotorRecord *record)
{
    out[SPI_MOTOR_RECORD_OFFSET_MOTOR_INDEX] = record->motor_index;
    LeBytes_WriteU16(&out[SPI_MOTOR_RECORD_OFFSET_VALIDITY_FLAGS],
                     (record->freshness == LATEST_VALUE_FRESHNESS_FRESH) ? SPI_MOTOR_VALIDITY_FEEDBACK_VALID : 0u);
    LeBytes_WriteU16(&out[SPI_MOTOR_RECORD_OFFSET_CAN_ID], record->can_id);
    out[SPI_MOTOR_RECORD_OFFSET_COMMAND_CODE] = record->position_command_code;
    LeBytes_WriteU64(&out[SPI_MOTOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US], record->position_timestamp_us);
    if (record->has_position) {
        out[SPI_MOTOR_RECORD_OFFSET_PAYLOAD_LENGTH] = LATEST_VALUE_POSITION_REPLY_BYTES;
        memcpy(&out[SPI_MOTOR_RECORD_OFFSET_PAYLOAD], record->position_reply, LATEST_VALUE_POSITION_REPLY_BYTES);
    }
}

SpiProtocol_Result SpiProtocol_SerializeSnapshot(const LatestValue_Snapshot *copy,
                                                 uint16_t dropped_snapshot_count_low,
                                                 uint8_t payload[SPI_SNAPSHOT_MAX_PAYLOAD_BYTES],
                                                 uint16_t *payload_length)
{
    uint8_t motor_count = 0u;
    size_t index;

    if ((copy == NULL) || (payload == NULL) || (payload_length == NULL)) { return SPI_PROTOCOL_BAD_LENGTH; }

    /* Zero first: every reserved byte and unused payload byte must be zero on the wire. */
    memset(payload, 0, SPI_SNAPSHOT_MAX_PAYLOAD_BYTES);
    for (index = 0u; index < LATEST_VALUE_SENSOR_COUNT; ++index) {
        SpiProtocol_SerializeSensorRecord(&payload[SPI_SNAPSHOT_PREFIX_BYTES + (index * SPI_SENSOR_RECORD_BYTES)],
                                          &copy->sensors[index]);
    }
    for (index = 0u; index < LATEST_VALUE_MOTOR_COUNT; ++index) {
        if (!copy->motors[index].registered) { continue; }
        SpiProtocol_SerializeMotorRecord(&payload[SPI_SNAPSHOT_PAYLOAD_BYTES(motor_count)], &copy->motors[index]);
        motor_count++;
    }
    payload[SPI_SNAPSHOT_OFFSET_SCHEMA_VERSION] = SPI_SNAPSHOT_SCHEMA_VERSION;
    payload[SPI_SNAPSHOT_OFFSET_SENSOR_COUNT] = (uint8_t)SPI_SNAPSHOT_SENSOR_RECORD_COUNT;
    payload[SPI_SNAPSHOT_OFFSET_MOTOR_COUNT] = motor_count;
    LeBytes_WriteU16(&payload[SPI_SNAPSHOT_OFFSET_DROPPED_SNAPSHOT_COUNT_LOW], dropped_snapshot_count_low);
    *payload_length = (uint16_t)SPI_SNAPSHOT_PAYLOAD_BYTES(motor_count);
    return SPI_PROTOCOL_OK;
}

SpiProtocol_Result SpiProtocol_ParseTimeSyncRequest(const uint8_t request[SPI_FRAME_MAX_BYTES],
                                                    SpiProtocol_TimeSyncRequest *time_sync)
{
    const uint8_t *payload;

    if ((request == NULL) || (time_sync == NULL)) {
        return SPI_PROTOCOL_BAD_LENGTH;
    }

    if (request[SPI_FRAME_OFFSET_MESSAGE_TYPE] != SPI_MESSAGE_TIME_SYNC) {
        return SPI_PROTOCOL_BAD_MESSAGE;
    }

    if (!SpiProtocol_ValidateTimeSyncPayload(request)) {
        return SPI_PROTOCOL_BAD_TIME_SYNC;
    }

    payload = &request[SPI_FRAME_OFFSET_PAYLOAD];
    time_sync->request_sequence = LeBytes_ReadU32(&request[SPI_FRAME_OFFSET_SEQUENCE]);
    time_sync->flags = LeBytes_ReadU16(&payload[2]);
    time_sync->pi_time_us = LeBytes_ReadU64(&payload[4]);
    time_sync->sync_sequence = LeBytes_ReadU32(&payload[12]);
    return SPI_PROTOCOL_OK;
}

SpiProtocol_Result SpiProtocol_ValidateRequest(const SpiProtocol_State *state,
                                               const uint8_t request[SPI_FRAME_MAX_BYTES])
{
    uint16_t length;
    uint32_t sequence;
    uint8_t type;

    if ((state == NULL) || (request == NULL)) { return SPI_PROTOCOL_BAD_LENGTH; }

    type = request[SPI_FRAME_OFFSET_MESSAGE_TYPE];
    sequence = LeBytes_ReadU32(&request[SPI_FRAME_OFFSET_SEQUENCE]);
    length = LeBytes_ReadU16(&request[SPI_FRAME_OFFSET_PAYLOAD_LENGTH]);
    if (LeBytes_ReadU16(&request[SPI_FRAME_OFFSET_MAGIC]) != SPI_FRAME_MAGIC) { return SPI_PROTOCOL_BAD_MAGIC; }
    if (request[SPI_FRAME_OFFSET_PROTOCOL_VERSION] != SPI_PROTOCOL_VERSION) { return SPI_PROTOCOL_BAD_VERSION; }
    if ((length > SPI_PAYLOAD_MAX_BYTES) || (SPI_FRAME_CRC_OFFSET(length) + SPI_FRAME_CRC_BYTES > SPI_FRAME_MAX_BYTES)) {
        return SPI_PROTOCOL_BAD_LENGTH;
    }
    if (!Crc32IsoHdlc_Verify(request, SPI_FRAME_HEADER_BYTES + length, &request[SPI_FRAME_CRC_OFFSET(length)])) {
        return SPI_PROTOCOL_BAD_CRC;
    }
    if (state->has_request_sequence && !SpiProtocol_IsNewer(sequence, state->last_request_sequence)) {
        return SPI_PROTOCOL_BAD_SEQUENCE;
    }
    if ((type != SPI_MESSAGE_GET_SNAPSHOT) && (type != SPI_MESSAGE_GET_STATUS) &&
        (type != SPI_MESSAGE_TIME_SYNC) && (type != SPI_MESSAGE_GET_VERSION)) {
        return SPI_PROTOCOL_BAD_MESSAGE;
    }
    if ((type == SPI_MESSAGE_TIME_SYNC) && !SpiProtocol_ValidateTimeSyncPayload(request)) {
        return SPI_PROTOCOL_BAD_TIME_SYNC;
    }

    return SPI_PROTOCOL_OK;
}

SpiProtocol_Result SpiProtocol_ProcessRequest(SpiProtocol_State *state, const uint8_t request[SPI_FRAME_MAX_BYTES], uint8_t response[SPI_FRAME_MAX_BYTES])
{
    uint32_t sequence;
    uint8_t type;
    SpiProtocol_Result result;

    if ((state == NULL) || (request == NULL) || (response == NULL)) { return SPI_PROTOCOL_BAD_LENGTH; }

    type = request[SPI_FRAME_OFFSET_MESSAGE_TYPE];
    sequence = LeBytes_ReadU32(&request[SPI_FRAME_OFFSET_SEQUENCE]);
    result = SpiProtocol_ValidateRequest(state, request);
    if (result != SPI_PROTOCOL_OK) { SpiProtocol_BuildCommandReply(state, SPI_MESSAGE_NACK, type, sequence, (uint16_t)result, 0u, response); return result; }
    state->last_request_sequence = sequence; state->has_request_sequence = true;
    if ((type == SPI_MESSAGE_GET_SNAPSHOT) && state->unsolicited_pending) {
        LeBytes_WriteU32(&state->unsolicited_payload[SPI_SNAPSHOT_OFFSET_RESPONSE_TO_SEQUENCE], sequence);
        SpiProtocol_BuildFrame(state, SPI_MESSAGE_SNAPSHOT, state->unsolicited_payload, state->unsolicited_payload_length, response);
        state->unsolicited_pending = false;
    } else if (type == SPI_MESSAGE_GET_VERSION) {
        SpiProtocol_BuildVersionReply(state, sequence, response);
    } else { SpiProtocol_BuildCommandReply(state, SPI_MESSAGE_ACK, type, sequence, 0u, 0u, response); }
    return SPI_PROTOCOL_OK;
}