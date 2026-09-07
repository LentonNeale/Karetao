#include "mksservo/decoder.hpp"

#include "mksservo/protocol_core.hpp"

namespace mks::decode {

Status parse(const CanFrame& frame, ParsedResponse& out) noexcept {
    if (frame.dlc > kMaxDlc) {
        return Status::InvalidDlc;
    }
    if (frame.dlc < 2) {
        return Status::FrameTooShort;
    }

    out.can_id = frame.id;
    out.code = frame.data[0];
    out.payload_len = static_cast<std::uint8_t>(frame.dlc - 2);
    for (std::uint8_t i = 0; i < out.payload_len; ++i) {
        out.payload[i] = frame.data[1 + i];
    }
    out.checksum = frame.data[frame.dlc - 1];

    const std::uint8_t expected = core::checksum8(frame.id, frame.data, static_cast<std::uint8_t>(frame.dlc - 1));
    if (out.checksum != expected) {
        return Status::ChecksumMismatch;
    }

    // Known commands must include at least one payload byte (unless spec allows empty).
    const CommandSpec* spec = find_command_spec(out.code);
    if (spec != nullptr && out.payload_len == 0 && !spec->empty_response_ok) {
        return Status::EmptyPayloadNotAllowed;
    }

    return Status::Ok;
}

Status decode(const CanFrame& frame, DecodedResponse& out) noexcept {
    Status st = parse(frame, out.parsed);
    if (st != Status::Ok) {
        return st;
    }

    out.has_status = false;
    if (out.parsed.payload_len > 0) {
        const std::uint8_t first = out.parsed.payload[0];
        if (first == static_cast<std::uint8_t>(CommandStatus::Failed) ||
            first == static_cast<std::uint8_t>(CommandStatus::Success)) {
            out.status = static_cast<CommandStatus>(first);
            out.has_status = true;
        }
    }
    return Status::Ok;
}

} // namespace mks::decode
