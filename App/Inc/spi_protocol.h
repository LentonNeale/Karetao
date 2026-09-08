/**
 * @file spi_protocol.h
 * @brief Request validation and response construction for SPI transport frames.
 */

#ifndef SPI_PROTOCOL_H
#define SPI_PROTOCOL_H

#include <stdbool.h>
#include <stdint.h>

#include "spi_payload_layout.h"

/** Current transport framing version expected by the STM32 SPI endpoint. */
#define SPI_PROTOCOL_VERSION UINT8_C(1)
#define SPI_MESSAGE_SNAPSHOT UINT8_C(0x01)
#define SPI_MESSAGE_STATUS UINT8_C(0x03)
#define SPI_MESSAGE_GET_SNAPSHOT UINT8_C(0x10)
#define SPI_MESSAGE_GET_STATUS UINT8_C(0x11)
#define SPI_MESSAGE_ACK UINT8_C(0x80)
#define SPI_MESSAGE_NACK UINT8_C(0x81)

/**
 * @brief Result of parsing a host request frame.
 *
 * Successful requests advance protocol state and stage a correlated response.
 * Rejected requests return a NACK and leave the accepted protocol lifecycle
 * state unchanged.
 */
typedef enum { SPI_PROTOCOL_OK = 0, SPI_PROTOCOL_BAD_MAGIC, SPI_PROTOCOL_BAD_VERSION,
    SPI_PROTOCOL_BAD_LENGTH, SPI_PROTOCOL_BAD_CRC, SPI_PROTOCOL_BAD_SEQUENCE, SPI_PROTOCOL_BAD_MESSAGE } SpiProtocol_Result;

/**
 * @brief Persistent protocol state owned by SpiSlaveService.
 *
 * The state is reset at boot, then tracks transmitted frame sequencing,
 * duplicate-request protection, and one queued unsolicited snapshot that may
 * be consumed by the next valid GET_SNAPSHOT request.
 */
typedef struct { uint32_t next_tx_sequence; uint32_t last_request_sequence; bool has_request_sequence;
    uint8_t unsolicited_payload[SPI_PAYLOAD_MAX_BYTES]; uint16_t unsolicited_payload_length; bool unsolicited_pending; } SpiProtocol_State;

/** Reset protocol state to its boot lifecycle with empty sequencing history. */
void SpiProtocol_Init(SpiProtocol_State *state);
/** Queue a snapshot payload for the next correlated GET_SNAPSHOT response. */
bool SpiProtocol_SetUnsolicitedSnapshot(SpiProtocol_State *state, const uint8_t *payload, uint16_t payload_length);
/** Build the defined boot-time status frame served before normal requests. */
SpiProtocol_Result SpiProtocol_BuildBootStatus(SpiProtocol_State *state, uint8_t response[SPI_FRAME_MAX_BYTES]);
/** Validate a host request frame and build the next staged response frame. */
SpiProtocol_Result SpiProtocol_ProcessRequest(SpiProtocol_State *state, const uint8_t request[SPI_FRAME_MAX_BYTES],
                                              uint8_t response[SPI_FRAME_MAX_BYTES]);

#endif /* SPI_PROTOCOL_H */