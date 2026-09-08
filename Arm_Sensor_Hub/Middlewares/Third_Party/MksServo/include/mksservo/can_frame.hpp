#pragma once

#include <cstdint>

namespace mks {

/// Maximum classic-CAN data length.
inline constexpr std::uint8_t kMaxDlc = 8;

/// Maximum MKS payload bytes inside a frame (data minus cmd byte minus checksum byte).
inline constexpr std::uint8_t kMaxPayload = kMaxDlc - 2;

/// Generic CAN frame (transport-agnostic). No heap, fixed size.
struct CanFrame {
    std::uint16_t id{0};                    ///< 11-bit CAN identifier (0x000..0x7FF)
    std::uint8_t  dlc{0};                   ///< number of valid bytes in data[]
    std::uint8_t  data[kMaxDlc]{};          ///< frame bytes (only first dlc are valid)
};

} // namespace mks
