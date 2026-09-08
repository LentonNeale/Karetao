#include "spi_protocol.h"

#include <string.h>

#include "crc32_iso_hdlc.h"
#include "time_service.h"

static uint16_t SpiProtocol_ReadU16(const uint8_t *data) { return (uint16_t)data[0] | ((uint16_t)data[1] << 8u); }
static uint32_t SpiProtocol_ReadU32(const uint8_t *data) { return (uint32_t)data[0] | ((uint32_t)data[1] << 8u) | ((uint32_t)data[2] << 16u) | ((uint32_t)data[3] << 24u); }
static uint64_t SpiProtocol_ReadU64(const uint8_t *data) { return (uint64_t)data[0] | ((uint64_t)data[1] << 8u) | ((uint64_t)data[2] << 16u) | ((uint64_t)data[3] << 24u) | ((uint64_t)data[4] << 32u) | ((uint64_t)data[5] << 40u) | ((uint64_t)data[6] << 48u) | ((uint64_t)data[7] << 56u); }
static void SpiProtocol_WriteU32(uint8_t *data, uint32_t value) { data[0] = (uint8_t)value; data[1] = (uint8_t)(value >> 8u); data[2] = (uint8_t)(value >> 16u); data[3] = (uint8_t)(value >> 24u); }
static void SpiProtocol_WriteU64(uint8_t *data, uint64_t value)
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
static bool SpiProtocol_IsNewer(uint32_t candidate, uint32_t previous) { return candidate != previous && (uint32_t)(candidate - previous) < UINT32_C(0x80000000); }

static void SpiProtocol_BuildFrame(SpiProtocol_State *state, uint8_t type, const uint8_t *payload, uint16_t length, uint8_t *response)
{
    uint32_t crc32;
    memset(response, 0, SPI_FRAME_MAX_BYTES);
    response[0] = 0x5Au; response[1] = 0xA5u; response[2] = SPI_PROTOCOL_VERSION; response[3] = type;
    response[4] = (uint8_t)length; response[5] = (uint8_t)(length >> 8u);
    SpiProtocol_WriteU32(&response[6], state->next_tx_sequence++);
    SpiProtocol_WriteU64(&response[SPI_FRAME_OFFSET_TIME_US], TimeService_NowUs());
    if (length > 0u) { memcpy(&response[SPI_FRAME_OFFSET_PAYLOAD], payload, length); }
    crc32 = Crc32IsoHdlc_Compute(response, SPI_FRAME_HEADER_BYTES + length);
    Crc32IsoHdlc_WriteLittleEndian(crc32, &response[SPI_FRAME_CRC_OFFSET(length)]);
}

static bool SpiProtocol_ValidateTimeSyncPayload(const uint8_t request[SPI_FRAME_MAX_BYTES])
{
    uint16_t length = SpiProtocol_ReadU16(&request[4]);
    const uint8_t *payload = &request[SPI_FRAME_OFFSET_PAYLOAD];

    return (length == SPI_TIME_SYNC_PAYLOAD_BYTES) &&
           (payload[0] == SPI_TIME_SYNC_SCHEMA_VERSION);
}

void SpiProtocol_BuildCommandReply(SpiProtocol_State *state, uint8_t type, uint8_t request_type,
                                   uint32_t request_sequence, uint16_t code, uint32_t detail_code,
                                   uint8_t *response)
{
    uint8_t payload[12] = {1u, request_type, (uint8_t)code, (uint8_t)(code >> 8u), 0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u};
    SpiProtocol_WriteU32(&payload[4], request_sequence);
    SpiProtocol_WriteU32(&payload[8], detail_code);
    SpiProtocol_BuildFrame(state, type, payload, sizeof(payload), response);
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
    SpiProtocol_BuildFrame(state, SPI_MESSAGE_STATUS, NULL, 0u, response); return SPI_PROTOCOL_OK;
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

    if (request[3] != SPI_MESSAGE_TIME_SYNC) {
        return SPI_PROTOCOL_BAD_MESSAGE;
    }

    if (!SpiProtocol_ValidateTimeSyncPayload(request)) {
        return SPI_PROTOCOL_BAD_TIME_SYNC;
    }

    payload = &request[SPI_FRAME_OFFSET_PAYLOAD];
    time_sync->request_sequence = SpiProtocol_ReadU32(&request[6]);
    time_sync->flags = SpiProtocol_ReadU16(&payload[2]);
    time_sync->pi_time_us = SpiProtocol_ReadU64(&payload[4]);
    time_sync->sync_sequence = SpiProtocol_ReadU32(&payload[12]);
    return SPI_PROTOCOL_OK;
}

SpiProtocol_Result SpiProtocol_ValidateRequest(const SpiProtocol_State *state,
                                               const uint8_t request[SPI_FRAME_MAX_BYTES])
{
    uint16_t length;
    uint32_t sequence;
    uint8_t type;

    if ((state == NULL) || (request == NULL)) { return SPI_PROTOCOL_BAD_LENGTH; }

    type = request[3];
    sequence = SpiProtocol_ReadU32(&request[6]);
    length = SpiProtocol_ReadU16(&request[4]);
    if (SpiProtocol_ReadU16(request) != UINT16_C(0xA55A)) { return SPI_PROTOCOL_BAD_MAGIC; }
    if (request[2] != SPI_PROTOCOL_VERSION) { return SPI_PROTOCOL_BAD_VERSION; }
    if ((length > SPI_PAYLOAD_MAX_BYTES) || (SPI_FRAME_CRC_OFFSET(length) + SPI_FRAME_CRC_BYTES > SPI_FRAME_MAX_BYTES)) {
        return SPI_PROTOCOL_BAD_LENGTH;
    }
    if (!Crc32IsoHdlc_Verify(request, SPI_FRAME_HEADER_BYTES + length, &request[SPI_FRAME_CRC_OFFSET(length)])) {
        return SPI_PROTOCOL_BAD_CRC;
    }
    if (state->has_request_sequence && !SpiProtocol_IsNewer(sequence, state->last_request_sequence)) {
        return SPI_PROTOCOL_BAD_SEQUENCE;
    }
    if ((type != SPI_MESSAGE_GET_SNAPSHOT) && (type != SPI_MESSAGE_GET_STATUS) && (type != SPI_MESSAGE_TIME_SYNC)) {
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

    type = request[3];
    sequence = SpiProtocol_ReadU32(&request[6]);
    result = SpiProtocol_ValidateRequest(state, request);
    if (result != SPI_PROTOCOL_OK) { SpiProtocol_BuildCommandReply(state, SPI_MESSAGE_NACK, type, sequence, (uint16_t)result, 0u, response); return result; }
    state->last_request_sequence = sequence; state->has_request_sequence = true;
    if ((type == SPI_MESSAGE_GET_SNAPSHOT) && state->unsolicited_pending) {
        SpiProtocol_WriteU32(&state->unsolicited_payload[SPI_SNAPSHOT_OFFSET_RESPONSE_TO_SEQUENCE], sequence);
        SpiProtocol_BuildFrame(state, SPI_MESSAGE_SNAPSHOT, state->unsolicited_payload, state->unsolicited_payload_length, response);
        state->unsolicited_pending = false;
    } else { SpiProtocol_BuildCommandReply(state, SPI_MESSAGE_ACK, type, sequence, 0u, 0u, response); }
    return SPI_PROTOCOL_OK;
}