#include "mksservo/protocol_core.hpp"
#include "test_util.hpp"

using namespace mks;

void run_core_tests() {
    // checksum8
    {
        const std::uint8_t d[] = {0x30};
        CHECK(core::checksum8(0x01, d, 1) == static_cast<std::uint8_t>((0x01 + 0x30) & 0xFF));
    }

    // u-range validators
    {
        std::uint8_t b = 0; std::uint16_t w = 0; std::uint32_t d = 0;
        CHECK_STATUS(core::u8(0xFF, b), Status::Ok);
        CHECK_STATUS(core::u8(0x100, b), Status::InvalidArgument);
        CHECK_STATUS(core::u11(0x7FF, w), Status::Ok);
        CHECK_STATUS(core::u11(0x800, w), Status::CanIdOutOfRange);
        CHECK_STATUS(core::u16(0xFFFF, w), Status::Ok);
        CHECK_STATUS(core::u16(0x10000, w), Status::InvalidArgument);
        CHECK_STATUS(core::u24(0xFFFFFF, d), Status::Ok);
        CHECK_STATUS(core::u24(0x1000000, d), Status::InvalidArgument);
        CHECK_STATUS(core::u32(0xFFFFFFFFull, d), Status::Ok);
        CHECK_STATUS(core::u32(0x100000000ull, d), Status::InvalidArgument);
    }

    // s24_to_bytes boundaries
    {
        std::uint8_t o[3];
        CHECK_STATUS(core::s24_to_bytes(8388607, o), Status::Ok);
        CHECK(o[0] == 0x7F && o[1] == 0xFF && o[2] == 0xFF);
        CHECK_STATUS(core::s24_to_bytes(-8388608, o), Status::Ok);
        CHECK(o[0] == 0x80 && o[1] == 0x00 && o[2] == 0x00);
        CHECK_STATUS(core::s24_to_bytes(0, o), Status::Ok);
        CHECK(o[0] == 0 && o[1] == 0 && o[2] == 0);
        CHECK_STATUS(core::s24_to_bytes(8388608, o), Status::InvalidArgument);
        CHECK_STATUS(core::s24_to_bytes(-8388609, o), Status::InvalidArgument);
        CHECK_STATUS(core::s24_to_bytes(-1, o), Status::Ok);
        CHECK(o[0] == 0xFF && o[1] == 0xFF && o[2] == 0xFF);
    }

    // encode_dir_speed
    {
        std::uint8_t o[2];
        CHECK_STATUS(core::encode_dir_speed(true, 0, o), Status::Ok);
        CHECK(o[0] == 0x80 && o[1] == 0x00);
        CHECK_STATUS(core::encode_dir_speed(false, 3000, o), Status::Ok);
        CHECK(o[0] == 0x0B && o[1] == 0xB8);
        CHECK_STATUS(core::encode_dir_speed(true, 3000, o), Status::Ok);
        CHECK(o[0] == 0x8B && o[1] == 0xB8);
        CHECK_STATUS(core::encode_dir_speed(true, 3001, o), Status::SpeedOutOfRange);
    }

    // validate_working_current
    {
        CHECK_STATUS(core::validate_working_current(kServo42, 3000), Status::Ok);
        CHECK_STATUS(core::validate_working_current(kServo42, 3001), Status::WorkingCurrentExceeded);
        CHECK_STATUS(core::validate_working_current(kServo57, 5200), Status::Ok);
        CHECK_STATUS(core::validate_working_current(kServo57, 5201), Status::WorkingCurrentExceeded);
        DeviceConfig noLimit{0x01, 0};
        CHECK_STATUS(core::validate_working_current(noLimit, 0xFFFF), Status::Ok);
    }

    // resolve_can_id
    {
        std::uint16_t id = 0;
        CHECK_STATUS(core::resolve_can_id(kServo42, kUseDefaultCanId, id), Status::Ok);
        CHECK(id == 0x01);
        CHECK_STATUS(core::resolve_can_id(kServo42, 0x7FF, id), Status::Ok);
        CHECK(id == 0x7FF);
        CHECK_STATUS(core::resolve_can_id(kServo42, 0x800, id), Status::CanIdOutOfRange);
    }

    test::report("core");
}
