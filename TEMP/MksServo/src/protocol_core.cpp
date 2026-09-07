#include "mksservo/protocol_core.hpp"

namespace mks::core {

Status s24_to_bytes(std::int32_t value, std::uint8_t out[3]) noexcept {
    if (value < -8388608 || value > 8388607) {
        return Status::InvalidArgument;
    }
    std::uint32_t u = (value < 0) ? (0x1000000u + static_cast<std::uint32_t>(value))
                                  : static_cast<std::uint32_t>(value);
    out[0] = static_cast<std::uint8_t>((u >> 16) & 0xFFu);
    out[1] = static_cast<std::uint8_t>((u >> 8) & 0xFFu);
    out[2] = static_cast<std::uint8_t>(u & 0xFFu);
    return Status::Ok;
}

Status encode_dir_speed(bool direction_cw, std::uint16_t speed, std::uint8_t out[2]) noexcept {
    if (speed > 3000u) {
        return Status::SpeedOutOfRange;
    }
    const std::uint8_t dir = direction_cw ? 0x80u : 0x00u;
    out[0] = static_cast<std::uint8_t>(dir | ((speed >> 8) & 0x0Fu));
    out[1] = static_cast<std::uint8_t>(speed & 0xFFu);
    return Status::Ok;
}

Status validate_working_current(const DeviceConfig& dev, std::uint16_t current_ma) noexcept {
    if (dev.max_working_current_ma != 0 && current_ma > dev.max_working_current_ma) {
        return Status::WorkingCurrentExceeded;
    }
    return Status::Ok;
}

Status resolve_can_id(const DeviceConfig& dev, std::uint16_t can_id, std::uint16_t& out) noexcept {
    std::uint16_t target = (can_id == kUseDefaultCanId) ? dev.default_can_id : can_id;
    if (target > 0x7FFu) {
        return Status::CanIdOutOfRange;
    }
    out = target;
    return Status::Ok;
}

Status frame(std::uint8_t code,
             const std::uint8_t* payload, std::uint8_t payload_len,
             std::uint16_t can_id,
             CanFrame& out) noexcept {
    if (payload_len > kMaxPayload) {
        return Status::PayloadTooLong;
    }
    if (can_id > 0x7FFu) {
        return Status::CanIdOutOfRange;
    }
    out.id = can_id;
    out.data[0] = code;
    for (std::uint8_t i = 0; i < payload_len; ++i) {
        out.data[1 + i] = payload[i];
    }
    const std::uint8_t body_len = static_cast<std::uint8_t>(1 + payload_len);
    out.data[body_len] = checksum8(can_id, out.data, body_len);
    out.dlc = static_cast<std::uint8_t>(body_len + 1);
    return Status::Ok;
}

} // namespace mks::core
