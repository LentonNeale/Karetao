/**
 * @file crc32_iso_hdlc.h
 * @brief Implements the crc32 iso hdlc module.
 */

#ifndef CRC32_ISO_HDLC_H
#define CRC32_ISO_HDLC_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Executes iso hdlc compute.
 */
uint32_t Crc32IsoHdlc_Compute(const uint8_t *data, size_t data_length);
/**
 * @brief Executes iso hdlc write little endian.
 */
void Crc32IsoHdlc_WriteLittleEndian(uint32_t crc32, uint8_t output[4]);
/**
 * @brief Executes iso hdlc read little endian.
 */
uint32_t Crc32IsoHdlc_ReadLittleEndian(const uint8_t input[4]);
bool Crc32IsoHdlc_Verify(const uint8_t *header_and_payload,
                          size_t header_and_payload_length,
                          const uint8_t crc_field[4]);

#ifdef __cplusplus
}
#endif

#endif /* CRC32_ISO_HDLC_H */