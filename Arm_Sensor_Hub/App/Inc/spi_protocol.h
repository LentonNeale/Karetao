/**
 * @file spi_protocol.h
 * @brief Request validation and response construction for SPI transport frames.
 */

#ifndef SPI_PROTOCOL_H
#define SPI_PROTOCOL_H

#include <stdbool.h>
#include <stdint.h>

#include "latest_value.h"
#include "spi_payload_layout.h"

#define SPI_PROTOCOL_VERSION UINT8_C(1)
#define SPI_MESSAGE_SNAPSHOT UINT8_C(0x01)
/* 0x03 is DIAGNOSTIC in SPI_SYSTEM_INTERFACE.md section 5; as built it is sent with an empty
 * payload as the first frame after boot (SpiProtocol_BuildBootStatus). Ruling R14 (B89) adds the v1 content. */
#define SPI_MESSAGE_DIAGNOSTIC UINT8_C(0x03)
#define SPI_MESSAGE_VERSION UINT8_C(0x04)
#define SPI_MESSAGE_GET_SNAPSHOT UINT8_C(0x10)
#define SPI_MESSAGE_GET_STATUS UINT8_C(0x11)
#define SPI_MESSAGE_TIME_SYNC UINT8_C(0x12)
#define SPI_MESSAGE_GET_VERSION UINT8_C(0x14)
#define SPI_MESSAGE_ACK UINT8_C(0x80)
#define SPI_MESSAGE_NACK UINT8_C(0x81)

/**
 * Request validation result. The values are the NACK `status_code` on the wire
 * (SPI_SYSTEM_INTERFACE.md section 14), so they are fixed here and mirrored by
 * NackReason in RaspberryPi_Sensor_Hub/src/spi/spi_protocol.py; the shared golden
 * frames (shared/test-vectors/spi) assert both.
 */
typedef enum {
    SPI_PROTOCOL_OK = 0,
    SPI_PROTOCOL_BAD_MAGIC = 1,
    SPI_PROTOCOL_BAD_VERSION = 2,
    SPI_PROTOCOL_BAD_LENGTH = 3,
    SPI_PROTOCOL_BAD_CRC = 4,
    SPI_PROTOCOL_BAD_SEQUENCE = 5,
    SPI_PROTOCOL_BAD_MESSAGE = 6,
    SPI_PROTOCOL_BAD_TIME_SYNC = 7,
    SPI_PROTOCOL_BAD_STATE = 8
} SpiProtocol_Result;

#define SPI_REQUEST_SCHEMA_VERSION UINT8_C(1)
#define SPI_TIME_SYNC_SCHEMA_VERSION UINT8_C(1)
#define SPI_TIME_SYNC_PAYLOAD_BYTES UINT16_C(16)
#define SPI_VERSION_SCHEMA_VERSION UINT8_C(1)
#define SPI_SNAPSHOT_SCHEMA_VERSION UINT8_C(1)
#define SPI_COMMAND_REPLY_SCHEMA_VERSION UINT8_C(1)

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
SpiProtocol_Result SpiProtocol_BuildSnapshotFrame(SpiProtocol_State *state,
                                                  const uint8_t *payload,
                                                  uint16_t payload_length,
                                                  uint8_t response[SPI_FRAME_MAX_BYTES]);
/**
 * Serialises a latest-value copy as a schema v1 SNAPSHOT payload: the prefix, six sensor records
 * at their logical IDs and the registered motor records in slot order. It reads only the caller's
 * copy (LatestValue_CopySnapshot), so no record changes while it runs. `response_to_seq` is zero;
 * a correlated reply patches it. Returns SPI_PROTOCOL_BAD_LENGTH on a NULL argument.
 */
SpiProtocol_Result SpiProtocol_SerializeSnapshot(const LatestValue_Snapshot *copy,
                                                 uint16_t dropped_snapshot_count_low,
                                                 uint8_t payload[SPI_SNAPSHOT_MAX_PAYLOAD_BYTES],
                                                 uint16_t *payload_length);
void SpiProtocol_BuildCommandReply(SpiProtocol_State *state, uint8_t frame_type, uint8_t request_type,
                                   uint32_t request_sequence, uint16_t status_code, uint32_t detail_code,
                                   uint8_t response[SPI_FRAME_MAX_BYTES]);
SpiProtocol_Result SpiProtocol_ValidateRequest(const SpiProtocol_State *state,
                                               const uint8_t request[SPI_FRAME_MAX_BYTES]);
SpiProtocol_Result SpiProtocol_ParseTimeSyncRequest(const uint8_t request[SPI_FRAME_MAX_BYTES],
                                                    SpiProtocol_TimeSyncRequest *time_sync);
SpiProtocol_Result SpiProtocol_ProcessRequest(SpiProtocol_State *state, const uint8_t request[SPI_FRAME_MAX_BYTES],
                                              uint8_t response[SPI_FRAME_MAX_BYTES]);

#endif /* SPI_PROTOCOL_H */