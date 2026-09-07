#include "mksservo/decoder.hpp"
#include "mksservo/protocol_core.hpp"
#include "test_util.hpp"

#include <initializer_list>

using namespace mks;

namespace {
CanFrame make_frame(std::uint16_t id, std::initializer_list<std::uint8_t> bytes) {
    CanFrame f{};
    f.id = id;
    f.dlc = static_cast<std::uint8_t>(bytes.size());
    std::uint8_t i = 0;
    for (std::uint8_t b : bytes) f.data[i++] = b;
    return f;
}
// Build a well-formed response: [code][payload...][checksum]
CanFrame make_response(std::uint16_t id, std::uint8_t code, std::initializer_list<std::uint8_t> payload) {
    CanFrame f{};
    f.id = id;
    f.data[0] = code;
    std::uint8_t i = 1;
    for (std::uint8_t b : payload) f.data[i++] = b;
    f.dlc = i;  // body length so far
    f.data[f.dlc] = core::checksum8(id, f.data, f.dlc);
    f.dlc = static_cast<std::uint8_t>(f.dlc + 1);
    return f;
}
} // namespace

void run_decoder_tests() {
    // Valid frame with success status (e.g. set_motor_enable response F3 01 cks)
    {
        CanFrame f = make_response(0x01, 0xF3, {0x01});
        decode::DecodedResponse d{};
        CHECK_STATUS(decode::decode(f, d), Status::Ok);
        CHECK(d.parsed.code == 0xF3);
        CHECK(d.parsed.payload_len == 1);
        CHECK(d.has_status && d.status == CommandStatus::Success);
    }

    // Valid frame with failed status
    {
        CanFrame f = make_response(0x01, 0xF3, {0x00});
        decode::DecodedResponse d{};
        CHECK_STATUS(decode::decode(f, d), Status::Ok);
        CHECK(d.has_status && d.status == CommandStatus::Failed);
    }

    // Payload byte that is not a known status => has_status false, still Ok
    {
        CanFrame f = make_response(0x01, 0x32, {0x05, 0xDC}); // realtime speed data
        decode::DecodedResponse d{};
        CHECK_STATUS(decode::decode(f, d), Status::Ok);
        CHECK(d.parsed.payload_len == 2);
        CHECK(!d.has_status);
    }

    // Invalid checksum
    {
        CanFrame f = make_response(0x01, 0xF3, {0x01});
        f.data[f.dlc - 1] ^= 0xFF; // corrupt checksum
        decode::DecodedResponse d{};
        CHECK_STATUS(decode::decode(f, d), Status::ChecksumMismatch);
    }

    // Truncated frame (< 2 bytes)
    {
        CanFrame f = make_frame(0x01, {0xF3});
        decode::DecodedResponse d{};
        CHECK_STATUS(decode::decode(f, d), Status::FrameTooShort);
    }

    // Invalid DLC (> 8)
    {
        CanFrame f = make_response(0x01, 0xF3, {0x01});
        f.dlc = 9;
        decode::DecodedResponse d{};
        CHECK_STATUS(decode::decode(f, d), Status::InvalidDlc);
    }

    // Known command with empty payload (where empty not allowed)
    {
        CanFrame f = make_response(0x01, 0x30, {}); // EncoderValue, expects payload
        decode::DecodedResponse d{};
        CHECK_STATUS(decode::decode(f, d), Status::EmptyPayloadNotAllowed);
    }

    // Unknown command code: parses fine (no registry rule violated) if checksum ok
    {
        CanFrame f = make_response(0x01, 0x02, {0x01}); // 0x02 not in registry
        decode::DecodedResponse d{};
        CHECK_STATUS(decode::decode(f, d), Status::Ok);
        CHECK(d.parsed.code == 0x02);
    }

    // parse() only (no status interpretation)
    {
        CanFrame f = make_response(0x01, 0xF3, {0x01});
        decode::ParsedResponse p{};
        CHECK_STATUS(decode::parse(f, p), Status::Ok);
        CHECK(p.code == 0xF3 && p.payload_len == 1);
    }

    test::report("decoder");
}
