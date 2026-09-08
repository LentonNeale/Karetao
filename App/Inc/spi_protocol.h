/**
 * @file spi_protocol.h
 * @brief Request validation and response construction for SPI transport frames.
 */

#ifndef SPI_PROTOCOL_H
#define SPI_PROTOCOL_H

#include <stdbool.h>
#include <stdint.h>

#include "spi_payload_layout.h"

#define SPI_PROTOCOL_VERSION UINT8_C(1)
#define SPI_MESSAGE_SNAPSHOT UINT8_C(0x01)
#define SPI_MESSAGE_STATUS UINT8_C(0x03)
#define SPI_MESSAGE_GET_SNAPSHOT UINT8_C(0x10)
#define SPI_MESSAGE_GET_STATUS UINT8_C(0x11)
#define SPI_MESSAGE_TIME_SYNC UINT8_C(0x12)
#define SPI_MESSAGE_ACK UINT8_C(0x80)
#define SPI_MESSAGE_NACK UINT8_C(0x81)

typedef enum { SPI_PROTOCOL_OK = 0, SPI_PROTOCOL_BAD_MAGIC, SPI_PROTOCOL_BAD_VERSION,
    SPI_PROTOCOL_BAD_LENGTH, SPI_PROTOCOL_BAD_CRC, SPI_PROTOCOL_BAD_SEQUENCE,
    SPI_PROTOCOL_BAD_MESSAGE, SPI_PROTOCOL_BAD_TIME_SYNC } SpiProtocol_Result;

#define SPI_REQUEST_SCHEMA_VERSION UINT8_C(1)
#define SPI_TIME_SYNC_SCHEMA_VERSION UINT8_C(1)
#define SPI_TIME_SYNC_PAYLOAD_BYTES UINT16_C(16)

typedef struct {
    uint32_t request_sequence;
    uint16_t flags;
    uint64_t pi_time_us;
    uint32_t sync_sequence;
} SpiProtocol_TimeSyncRequest;

typedef struct { uint32_t next_tx_sequence; uint32_t last_request_sequence; bool has_request_sequence;
    uint8_t unsolicited_payload[SPI_PAYLOAD_MAX_BYTES]; uint16_t unsolicited_payload_length; bool unsolicited_pending; } SpiProtocol_State;

void SpiProtocol_Init(SpiProtocol_State *state);
bool SpiProtocol_SetUnsolicitedSnapshot(SpiProtocol_State *state, const uint8_t *payload, uint16_t payload_length);
SpiProtocol_Result SpiProtocol_BuildBootStatus(SpiProtocol_State *state, uint8_t response[SPI_FRAME_MAX_BYTES]);
void SpiProtocol_BuildCommandReply(SpiProtocol_State *state, uint8_t frame_type, uint8_t request_type,
                                   uint32_t request_sequence, uint16_t status_code, uint32_t detail_code,
                                   uint8_t response[SPI_FRAME_MAX_BYTES]);
SpiProtocol_Result SpiProtocol_ParseTimeSyncRequest(const uint8_t request[SPI_FRAME_MAX_BYTES],
                                                    SpiProtocol_TimeSyncRequest *time_sync);
SpiProtocol_Result SpiProtocol_ProcessRequest(SpiProtocol_State *state, const uint8_t request[SPI_FRAME_MAX_BYTES],
                                              uint8_t response[SPI_FRAME_MAX_BYTES]);

#endif /* SPI_PROTOCOL_H */