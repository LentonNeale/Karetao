#include "spi_protocol.h"

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