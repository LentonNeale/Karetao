/**
 * @file le_bytes.h
 * @brief Little-endian byte access shared by the SPI protocol and the SPI slave service.
 *
 * The SPI frame contract is little-endian (Documentation/02_INTERFACES/SPI/). The helpers
 * are written as shifts, not memcpy, so they are correct whatever the host's byte order
 * (the host tests run on the build machine) and match the Python side's '<' struct formats.
 * Header-only, so no source-list entry is needed. In the Debug build (-O0) each helper is a
 * real stack frame in every file that uses it, as the static helpers it replaces were; the
 * stack check sees the same shape.
 */

#ifndef LE_BYTES_H
#define LE_BYTES_H

#include <stdint.h>

static inline uint16_t LeBytes_ReadU16(const uint8_t *data)
{
    return (uint16_t)data[0] | ((uint16_t)data[1] << 8u);
}

static inline uint32_t LeBytes_ReadU32(const uint8_t *data)
{
    return (uint32_t)data[0] | ((uint32_t)data[1] << 8u) | ((uint32_t)data[2] << 16u) | ((uint32_t)data[3] << 24u);
}

static inline uint64_t LeBytes_ReadU64(const uint8_t *data)
{
    return (uint64_t)data[0] | ((uint64_t)data[1] << 8u) | ((uint64_t)data[2] << 16u) | ((uint64_t)data[3] << 24u) |
           ((uint64_t)data[4] << 32u) | ((uint64_t)data[5] << 40u) | ((uint64_t)data[6] << 48u) | ((uint64_t)data[7] << 56u);
}

static inline void LeBytes_WriteU16(uint8_t *data, uint16_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8u);
}

static inline void LeBytes_WriteU32(uint8_t *data, uint32_t value)
{
    data[0] = (uint8_t)value;
    data[1] = (uint8_t)(value >> 8u);
    data[2] = (uint8_t)(value >> 16u);
    data[3] = (uint8_t)(value >> 24u);
}

static inline void LeBytes_WriteU64(uint8_t *data, uint64_t value)
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

#endif /* LE_BYTES_H */
