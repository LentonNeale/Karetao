#pragma once

#include <cstdint>

#include "can_frame.hpp"
#include "device_config.hpp"
#include "status.hpp"

namespace mks::core {

/// MKS checksum: (can_id & 0xFF) + sum(bytes), truncated to 8 bits.
constexpr std::uint8_t checksum8(std::uint16_t can_id, const std::uint8_t* data, std::uint8_t len) noexcept {
    std::uint32_t sum = (can_id & 0xFFu);
    for (std::uint8_t i = 0; i < len; ++i) {
        sum += data[i];
    }
    return static_cast<std::uint8_t>(sum & 0xFFu);
}

// ---- Range-checked integer helpers (return Status, no exceptions) ----

inline Status u8(std::uint32_t v, std::uint8_t& out) noexcept {
    if (v > 0xFFu) return Status::InvalidArgument;
    out = static_cast<std::uint8_t>(v);
    return Status::Ok;
}

inline Status u11(std::uint32_t v, std::uint16_t& out) noexcept {
    if (v > 0x7FFu) return Status::CanIdOutOfRange;
    out = static_cast<std::uint16_t>(v);
    return Status::Ok;
}

inline Status u16(std::uint32_t v, std::uint16_t& out) noexcept {
    if (v > 0xFFFFu) return Status::InvalidArgument;
    out = static_cast<std::uint16_t>(v);
    return Status::Ok;
}

inline Status u32(std::uint64_t v, std::uint32_t& out) noexcept {
    if (v > 0xFFFFFFFFull) return Status::InvalidArgument;
    out = static_cast<std::uint32_t>(v);
    return Status::Ok;
}

inline Status u24(std::uint32_t v, std::uint32_t& out) noexcept {
    if (v > 0xFFFFFFu) return Status::InvalidArgument;
    out = v;
    return Status::Ok;
}

/// Encode signed 24-bit (two's complement) as 3 big-endian bytes.
/// Range -8388608..8388607.
Status s24_to_bytes(std::int32_t value, std::uint8_t out[3]) noexcept;

/// Encode direction bit + 12-bit speed (max 3000) into 2 bytes:
/// byte0 = (0x80 if cw else 0x00) | ((speed >> 8) & 0x0F); byte1 = speed & 0xFF.
Status encode_dir_speed(bool direction_cw, std::uint16_t speed, std::uint8_t out[2]) noexcept;

/// Validate working current against the device's configured maximum.
Status validate_working_current(const DeviceConfig& dev, std::uint16_t current_ma) noexcept;

/// Resolve target CAN id: explicit can_id or device default; validates 11-bit range.
Status resolve_can_id(const DeviceConfig& dev, std::uint16_t can_id, std::uint16_t& out) noexcept;

/// Assemble a full frame: [code][payload(0..6)][checksum8]. Fills `out` (dlc set to actual length).
Status frame(std::uint8_t code,
             const std::uint8_t* payload, std::uint8_t payload_len,
             std::uint16_t can_id,
             CanFrame& out) noexcept;

} // namespace mks::core
