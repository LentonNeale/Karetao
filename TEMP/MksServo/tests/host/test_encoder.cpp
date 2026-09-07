// Golden-vector parity tests against the Python reference.
// Expected bytes come from tests/host/tools/gen_golden_vectors.py.
#include "mksservo/encoder.hpp"
#include "test_util.hpp"

using namespace mks;

void run_encoder_tests() {
    const DeviceConfig dev42 = kServo42;   // default id 0x01, max 3000 mA
    const DeviceConfig dev57 = kServo57;   // default id 0x01, max 5200 mA
    CanFrame f{};

    // ---- Motion ----
    CHECK_STATUS(encode::set_motor_enable(dev42, true, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0xF3, 0x01, 0xF5);
    CHECK_STATUS(encode::set_motor_enable(dev42, false, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0xF3, 0x00, 0xF4);

    CHECK_STATUS(encode::power_on_auto_run(dev42, true, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0xFF, 0xC8, 0xC8);
    CHECK_STATUS(encode::power_on_auto_run(dev42, false, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0xFF, 0xCA, 0xCA);

    CHECK_STATUS(encode::speed_mode_run(dev42, true, 3000, 10, false, 0, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 5, 0xF6, 0x8B, 0xB8, 0x0A, 0x44);
    CHECK_STATUS(encode::speed_mode_run(dev42, false, 0, 0, false, 0, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 5, 0xF6, 0x00, 0x00, 0x00, 0xF7);
    CHECK_STATUS(encode::speed_mode_run(dev42, true, 1000, 5, true, 12345, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 8, 0xF6, 0x83, 0xE8, 0x05, 0x00, 0x30, 0x39, 0xD0);
    CHECK_STATUS(encode::speed_mode_run(dev42, true, 3001, 10, false, 0, f), Status::SpeedOutOfRange);

    CHECK_STATUS(encode::emergency_stop(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0xF7, 0xF8);

    CHECK_STATUS(encode::relative_pulse_move(dev42, true, 2000, 8, 100000, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 8, 0xFD, 0x87, 0xD0, 0x08, 0x01, 0x86, 0xA0, 0x84);

    CHECK_STATUS(encode::absolute_pulse_move(dev42, 2000, 8, 8388607, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 8, 0xFE, 0x07, 0xD0, 0x08, 0x7F, 0xFF, 0xFF, 0x5B);
    CHECK_STATUS(encode::absolute_pulse_move(dev42, 2000, 8, -8388607, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 8, 0xFE, 0x07, 0xD0, 0x08, 0x80, 0x00, 0x01, 0x5F);
    CHECK_STATUS(encode::absolute_pulse_move(dev42, 2000, 8, 8388608, f), Status::InvalidArgument);
    CHECK_STATUS(encode::absolute_pulse_move(dev42, 2000, 8, -8388608, f), Status::InvalidArgument);
    CHECK_STATUS(encode::absolute_pulse_move(dev42, 3001, 8, 0, f), Status::SpeedOutOfRange);

    CHECK_STATUS(encode::coordinate_relative_move(dev42, 1500, 4, -500000, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 8, 0xF4, 0x05, 0xDC, 0x04, 0xF8, 0x5E, 0xE0, 0x10);
    CHECK_STATUS(encode::coordinate_absolute_move(dev42, 1500, 4, 123456, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 8, 0xF5, 0x05, 0xDC, 0x04, 0x01, 0xE2, 0x40, 0xFE);

    // ---- Read ----
    CHECK_STATUS(encode::motor_stall_status(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x3E, 0x3F);
    CHECK_STATUS(encode::read_version_information(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x40, 0x41);
    CHECK_STATUS(encode::write_user_id(dev42, 0xDEADBEEF, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 6, 0x42, 0xDE, 0xAD, 0xBE, 0xEF, 0x7B);
    CHECK_STATUS(encode::read_user_id(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x42, 0x43);
    CHECK_STATUS(encode::received_pulses(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x33, 0x34);
    CHECK_STATUS(encode::raw_accumulated_encoder_value(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x35, 0x36);
    CHECK_STATUS(encode::position_angle_error(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x39, 0x3A);
    CHECK_STATUS(encode::motor_enable_status(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x3A, 0x3B);
    CHECK_STATUS(encode::return_to_zero_status(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x3B, 0x3C);
    CHECK_STATUS(encode::motor_operating_status(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0xF1, 0xF2);
    CHECK_STATUS(encode::encoder_value(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x30, 0x31);
    CHECK_STATUS(encode::cumulative_encoder_value(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x31, 0x32);
    CHECK_STATUS(encode::realtime_speed(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x32, 0x33);
    CHECK_STATUS(encode::configuration_parameter(dev42, 0x42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x00, 0x42, 0x43);
    CHECK_STATUS(encode::auto_read_parameter(dev42, 0x30, 500, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 5, 0x01, 0x30, 0x01, 0xF4, 0x27);

    // ---- Homing ----
    CHECK_STATUS(encode::set_zero_point(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x92, 0x93);
    CHECK_STATUS(encode::execute_zero_return(dev42, false, GoZeroMode::Origin, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x91, 0x92);
    CHECK_STATUS(encode::execute_zero_return(dev42, true, GoZeroMode::Origin, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x91, 0x00, 0x92);
    CHECK_STATUS(encode::execute_zero_return(dev42, true, GoZeroMode::Coordinate, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x91, 0x01, 0x93);
    CHECK_STATUS(encode::set_homing_parameters(dev42, 1, 0, 1500, 1, 2, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 8, 0x90, 0x01, 0x00, 0x05, 0xDC, 0x01, 0x02, 0x76);
    CHECK_STATUS(encode::set_homing_offset_and_current(dev42, 0x12345678, 1000, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 8, 0x94, 0x12, 0x34, 0x56, 0x78, 0x03, 0xE8, 0x94);
    CHECK_STATUS(encode::set_single_turn_zero_return_parameters(dev42, 2, 1, 3, 0, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 6, 0x9A, 0x02, 0x01, 0x03, 0x00, 0xA1);

    // ---- Controller ----
    CHECK_STATUS(encode::set_overcurrent_protection(dev42, true, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x88, 0x01, 0x8A);
    CHECK_STATUS(encode::set_position_deviation_protection(dev42, true, 100, 5, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 7, 0x9D, 0x01, 0x00, 0x64, 0x00, 0x05, 0x08);
    CHECK_STATUS(encode::release_stall_state(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x3D, 0x3E);
    CHECK_STATUS(encode::restore_factory_settings(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x3F, 0x40);
    CHECK_STATUS(encode::calibrate_encoder(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x80, 0x00, 0x81);
    CHECK_STATUS(encode::work_mode(dev42, WorkMode::SrVFoc, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x82, 0x05, 0x88);
    CHECK_STATUS(encode::pid_kp_ki_vfoc(dev42, 500, 600, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 7, 0x96, 0x00, 0x01, 0xF4, 0x02, 0x58, 0xE6);
    CHECK_STATUS(encode::pid_kd_kv_vfoc(dev42, 100, 200, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 7, 0x96, 0x01, 0x00, 0x64, 0x00, 0xC8, 0xC4);
    CHECK_STATUS(encode::pid_kp_ki_close(dev42, 700, 800, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 7, 0x97, 0x00, 0x02, 0xBC, 0x03, 0x20, 0x79);
    CHECK_STATUS(encode::pid_kd_kv_close(dev42, 300, 400, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 7, 0x97, 0x01, 0x01, 0x2C, 0x01, 0x90, 0x57);
    CHECK_STATUS(encode::subdivisions(dev42, 16, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x84, 0x10, 0x95);
    CHECK_STATUS(encode::en_pin_active_level(dev42, EnPinActiveLevel::ActiveLow, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x85, 0x00, 0x86);
    CHECK_STATUS(encode::motor_rotation_direction(dev42, MotorRotationDirection::Ccw, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x86, 0x01, 0x88);
    CHECK_STATUS(encode::auto_screen_off(dev42, true, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x87, 0x01, 0x89);
    CHECK_STATUS(encode::subdivision_interpolation(dev42, false, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x89, 0x00, 0x8A);
    CHECK_STATUS(encode::key_lock_function(dev42, true, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x8F, 0x01, 0x91);
    CHECK_STATUS(encode::holding_current_percentage(dev42, 8, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x9B, 0x08, 0xA4);
    CHECK_STATUS(encode::working_current(dev42, 3000, true, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 4, 0x83, 0x0B, 0xB8, 0x47);
    CHECK_STATUS(encode::working_current(dev42, 2000, false, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 5, 0x83, 0x07, 0xD0, 0x00, 0x5B);
    CHECK_STATUS(encode::working_current(dev42, 3001, true, f), Status::WorkingCurrentExceeded);
    CHECK_STATUS(encode::working_current(dev57, 5200, true, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 4, 0x83, 0x14, 0x50, 0xE8);
    CHECK_STATUS(encode::position_reach_threshold(dev42, true, 50, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 5, 0x95, 0x01, 0x00, 0x32, 0xC9);
    CHECK_STATUS(encode::reset_and_restart(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x41, 0x42);

    // ---- CAN settings ----
    CHECK_STATUS(encode::bitrate(dev42, BitrateMode::Mode2, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x8A, 0x02, 0x8D);
    CHECK_STATUS(encode::slave_id(dev42, 0x123, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 4, 0x8B, 0x01, 0x23, 0xB0);
    CHECK_STATUS(encode::group_id(dev42, 0x45, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 4, 0x8D, 0x00, 0x45, 0xD3);
    CHECK_STATUS(encode::response_mode(dev42, true, false, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 4, 0x8C, 0x01, 0x00, 0x8E);
    CHECK_STATUS(encode::heartbeat_protection(dev42, 0x00010000, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 6, 0x98, 0x00, 0x01, 0x00, 0x00, 0x9A);
    CHECK_STATUS(encode::no_verification_mode(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x0F, 0x01, 0x11);
    CHECK_STATUS(encode::sync_mark_enabled(dev42, true, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x4A, 0x01, 0x4C);
    CHECK_STATUS(encode::execute_sync_mark(f), Status::Ok);
    CHECK_FRAME(f, 0x000, 2, 0x4B, 0x4B);

    // ---- IO ----
    CHECK_STATUS(encode::read_status(dev42, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 2, 0x34, 0x35);
    CHECK_STATUS(encode::port_mapping(dev42, true, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x9E, 0x01, 0xA0);
    CHECK_STATUS(encode::configure_in1_port_mode(dev42, true, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x9F, 0x01, 0xA1);
    CHECK_STATUS(encode::write_io_port(dev42, 2, 1, true, false, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 3, 0x36, 0x98, 0xCF);
    CHECK_STATUS(encode::configure_io_pulse_divider_output(dev42, true, 0x0000FFFF, f), Status::Ok);
    CHECK_FRAME(f, 0x001, 7, 0x99, 0x01, 0x00, 0x00, 0xFF, 0xFF, 0x99);

    test::report("encoder");
}
