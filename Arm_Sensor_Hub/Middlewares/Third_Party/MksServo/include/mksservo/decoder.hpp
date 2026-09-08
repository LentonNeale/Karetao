#pragma once

#include <cstdint>

#include "can_frame.hpp"
#include "command.hpp"
#include "enums.hpp"
#include "status.hpp"

namespace mks::decode {

/// Parsed frame body excluding CAN transport metadata. Fixed-size, no heap.
struct ParsedResponse {
    std::uint16_t can_id{0};
    std::uint8_t  code{0};
    std::uint8_t  payload[kMaxPayload]{};  ///< up to 6 bytes (data minus cmd minus checksum)
    std::uint8_t  payload_len{0};
    std::uint8_t  checksum{0};
};

/// Fully decoded response: parsed frame plus optional CommandStatus.
struct DecodedResponse {
    ParsedResponse parsed;
    CommandStatus  status{CommandStatus::Failed};
    bool           has_status{false};
};

/// Parse and validate a response frame: length/dlc checks, checksum verify
/// (checksum incorporates can_id), and known-command empty-payload rule from
/// the CommandSpec registry. Never reads past frame.dlc. Rejects dlc > 8.
Status parse(const CanFrame& frame, ParsedResponse& out) noexcept;

/// Parse plus derive an optional CommandStatus from payload byte 0 when it is a
/// known status value. Sets InvalidStatusPayload if payload[0] is present but
/// not a recognized status for status-bearing commands.
Status decode(const CanFrame& frame, DecodedResponse& out) noexcept;

} // namespace mks::decode
