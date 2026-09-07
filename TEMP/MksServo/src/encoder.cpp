#include "mksservo/encoder.hpp"

#include "mksservo/command.hpp"
#include "mksservo/protocol_core.hpp"

namespace mks::encode {
namespace {

using core::frame;
using core::resolve_can_id;

/// Build a frame from a command code + payload, resolving can_id against the device.
inline Status build(const DeviceConfig& dev, CommandCode code,
                    const std::uint8_t* payload, std::uint8_t payload_len,
                    std::uint16_t can_id, CanFrame& out) noexcept {
    std::uint16_t id = 0;
    Status st = resolve_can_id(dev, can_id, id);
    if (st != Status::Ok) return st;
    return frame(static_cast<std::uint8_t>(code), payload, payload_len, id, out);
}

inline Status build0(const DeviceConfig& dev, CommandCode code, std::uint16_t can_id, CanFrame& out) noexcept {
    return build(dev, code, nullptr, 0, can_id, out);
}

inline void put_u16_be(std::uint8_t* p, std::uint16_t v) noexcept {
    p[0] = static_cast<std::uint8_t>((v >> 8) & 0xFFu);
    p[1] = static_cast<std::uint8_t>(v & 0xFFu);
}
inline void put_u32_be(std::uint8_t* p, std::uint32_t v) noexcept {
    p[0] = static_cast<std::uint8_t>((v >> 24) & 0xFFu);
    p[1] = static_cast<std::uint8_t>((v >> 16) & 0xFFu);
    p[2] = static_cast<std::uint8_t>((v >> 8) & 0xFFu);
    p[3] = static_cast<std::uint8_t>(v & 0xFFu);
}
inline void put_u24_be(std::uint8_t* p, std::uint32_t v) noexcept {
    p[0] = static_cast<std::uint8_t>((v >> 16) & 0xFFu);
    p[1] = static_cast<std::uint8_t>((v >> 8) & 0xFFu);
    p[2] = static_cast<std::uint8_t>(v & 0xFFu);
}

/// Shared PID pair builder: [selector][u16 be][u16 be], values 0..1024.
Status build_pid_pair(const DeviceConfig& dev, CommandCode code, std::uint8_t selector,
                      std::uint16_t first, std::uint16_t second,
                      std::uint16_t can_id, CanFrame& out) noexcept {
    if (first > 1024u || second > 1024u) return Status::InvalidArgument;
    std::uint8_t p[5];
    p[0] = selector;
    put_u16_be(p + 1, first);
    put_u16_be(p + 3, second);
    return build(dev, code, p, 5, can_id, out);
}

/// Python reference clamps int24 move coordinates to -8388607..8388607 (not the
/// full two's-complement s24 range). Mirror that for byte-for-byte parity.
inline constexpr std::int32_t kMoveAxisMin = -8388607;
inline constexpr std::int32_t kMoveAxisMax = 8388607;

Status encode_move(const DeviceConfig& dev, CommandCode code, std::uint16_t speed,
                   std::uint8_t acceleration, std::int32_t axis,
                   std::uint16_t can_id, CanFrame& out) noexcept {
    if (speed > 3000u) return Status::SpeedOutOfRange;
    if (axis < kMoveAxisMin || axis > kMoveAxisMax) return Status::InvalidArgument;
    std::uint8_t p[6];
    put_u16_be(p, speed);
    p[2] = acceleration;
    Status st = core::s24_to_bytes(axis, p + 3);
    if (st != Status::Ok) return st;
    return build(dev, code, p, 6, can_id, out);
}

} // namespace

// ============================ Motion ============================
Status set_motor_enable(const DeviceConfig& dev, bool enable, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(enable ? 1 : 0)};
    return build(dev, CommandCode::MotorEnableState, p, 1, can_id, out);
}

Status power_on_auto_run(const DeviceConfig& dev, bool enable, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(enable ? 0xC8 : 0xCA)};
    return build(dev, CommandCode::PowerOnAutoRun, p, 1, can_id, out);
}

Status speed_mode_run(const DeviceConfig& dev, bool direction_cw, std::uint16_t speed,
                      std::uint8_t acceleration, bool has_runtime, std::uint32_t runtime_10ms,
                      CanFrame& out, std::uint16_t can_id) noexcept {
    std::uint8_t p[6];
    Status st = core::encode_dir_speed(direction_cw, speed, p);
    if (st != Status::Ok) return st;
    p[2] = acceleration;
    std::uint8_t len = 3;
    if (has_runtime) {
        std::uint32_t v = 0;
        st = core::u24(runtime_10ms, v);
        if (st != Status::Ok) return st;
        put_u24_be(p + 3, v);
        len = 6;
    }
    return build(dev, CommandCode::SpeedModeRun, p, len, can_id, out);
}

Status emergency_stop(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::EmergencyStop, can_id, out);
}

Status relative_pulse_move(const DeviceConfig& dev, bool direction_cw, std::uint16_t speed,
                           std::uint8_t acceleration, std::uint32_t relative_pulses,
                           CanFrame& out, std::uint16_t can_id) noexcept {
    std::uint8_t p[6];
    Status st = core::encode_dir_speed(direction_cw, speed, p);
    if (st != Status::Ok) return st;
    p[2] = acceleration;
    std::uint32_t v = 0;
    st = core::u24(relative_pulses, v);
    if (st != Status::Ok) return st;
    put_u24_be(p + 3, v);
    return build(dev, CommandCode::RelativePulseMove, p, 6, can_id, out);
}

Status absolute_pulse_move(const DeviceConfig& dev, std::uint16_t speed, std::uint8_t acceleration,
                           std::int32_t absolute_pulses, CanFrame& out, std::uint16_t can_id) noexcept {
    return encode_move(dev, CommandCode::AbsolutePulseMove, speed, acceleration, absolute_pulses, can_id, out);
}

Status coordinate_relative_move(const DeviceConfig& dev, std::uint16_t speed, std::uint8_t acceleration,
                                std::int32_t relative_axis, CanFrame& out, std::uint16_t can_id) noexcept {
    return encode_move(dev, CommandCode::CoordinateRelativeMove, speed, acceleration, relative_axis, can_id, out);
}

Status coordinate_absolute_move(const DeviceConfig& dev, std::uint16_t speed, std::uint8_t acceleration,
                                std::int32_t absolute_axis, CanFrame& out, std::uint16_t can_id) noexcept {
    return encode_move(dev, CommandCode::CoordinateAbsoluteMove, speed, acceleration, absolute_axis, can_id, out);
}

// ============================ Read ============================
Status motor_stall_status(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::MotorStallStatus, can_id, out);
}
Status read_version_information(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::VersionInformation, can_id, out);
}
Status write_user_id(const DeviceConfig& dev, std::uint32_t user_id, CanFrame& out, std::uint16_t can_id) noexcept {
    std::uint8_t p[4];
    put_u32_be(p, user_id);
    return build(dev, CommandCode::UserId, p, 4, can_id, out);
}
Status read_user_id(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::UserId, can_id, out);
}
Status received_pulses(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::ReceivedPulses, can_id, out);
}
Status raw_accumulated_encoder_value(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::RawAccumulatedEncoderValue, can_id, out);
}
Status position_angle_error(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::PositionAngleError, can_id, out);
}
Status motor_enable_status(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::MotorEnableStatus, can_id, out);
}
Status return_to_zero_status(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::ReturnToZeroStatus, can_id, out);
}
Status motor_operating_status(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::MotorOperatingStatus, can_id, out);
}
Status encoder_value(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::EncoderValue, can_id, out);
}
Status cumulative_encoder_value(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::CumulativeEncoderValue, can_id, out);
}
Status realtime_speed(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::RealtimeSpeed, can_id, out);
}
Status configuration_parameter(const DeviceConfig& dev, std::uint8_t parameter_code, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {parameter_code};
    return build(dev, CommandCode::ConfigurationParameter, p, 1, can_id, out);
}
Status auto_read_parameter(const DeviceConfig& dev, std::uint8_t parameter_code, std::uint16_t interval_ms, CanFrame& out, std::uint16_t can_id) noexcept {
    std::uint8_t p[3];
    p[0] = parameter_code;
    put_u16_be(p + 1, interval_ms);
    return build(dev, CommandCode::AutoReadParameter, p, 3, can_id, out);
}

// ============================ Homing ============================
Status set_zero_point(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::SetZeroPoint, can_id, out);
}
Status execute_zero_return(const DeviceConfig& dev, bool has_mode, GoZeroMode mode, CanFrame& out, std::uint16_t can_id) noexcept {
    if (!has_mode) {
        return build0(dev, CommandCode::ExecuteZeroReturn, can_id, out);
    }
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(mode)};
    return build(dev, CommandCode::ExecuteZeroReturn, p, 1, can_id, out);
}
Status set_homing_parameters(const DeviceConfig& dev, std::uint8_t home_trigger_level, std::uint8_t home_direction,
                             std::uint16_t home_speed_rpm, std::uint8_t end_limit_enabled, std::uint8_t homing_mode,
                             CanFrame& out, std::uint16_t can_id) noexcept {
    if (home_trigger_level > 1 || home_direction > 1 || end_limit_enabled > 1 || homing_mode > 2) {
        return Status::InvalidArgument;
    }
    if (home_speed_rpm > 3000u) return Status::SpeedOutOfRange;
    std::uint8_t p[6];
    p[0] = home_trigger_level;
    p[1] = home_direction;
    put_u16_be(p + 2, home_speed_rpm);
    p[4] = end_limit_enabled;
    p[5] = homing_mode;
    return build(dev, CommandCode::HomingParameters, p, 6, can_id, out);
}
Status set_homing_offset_and_current(const DeviceConfig& dev, std::uint32_t homing_offset, std::uint16_t homing_current_ma,
                                     CanFrame& out, std::uint16_t can_id) noexcept {
    std::uint8_t p[6];
    put_u32_be(p, homing_offset);
    put_u16_be(p + 4, homing_current_ma);
    return build(dev, CommandCode::HomingOffsetAndCurrent, p, 6, can_id, out);
}
Status set_single_turn_zero_return_parameters(const DeviceConfig& dev, std::uint8_t mode, std::uint8_t zero_point_mode,
                                              std::uint8_t speed, std::uint8_t direction,
                                              CanFrame& out, std::uint16_t can_id) noexcept {
    if (mode > 2 || zero_point_mode > 2 || speed > 4 || direction > 1) {
        return Status::InvalidArgument;
    }
    const std::uint8_t p[4] = {mode, zero_point_mode, speed, direction};
    return build(dev, CommandCode::SingleTurnZeroReturnParams, p, 4, can_id, out);
}

// ============================ Controller ============================
Status set_overcurrent_protection(const DeviceConfig& dev, bool enabled, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(enabled ? 1 : 0)};
    return build(dev, CommandCode::OvercurrentProtection, p, 1, can_id, out);
}
Status set_position_deviation_protection(const DeviceConfig& dev, bool enabled, std::uint16_t time_window,
                                         std::uint16_t error_count, CanFrame& out, std::uint16_t can_id) noexcept {
    std::uint8_t p[5];
    p[0] = static_cast<std::uint8_t>(enabled ? 1 : 0);
    put_u16_be(p + 1, time_window);
    put_u16_be(p + 3, error_count);
    return build(dev, CommandCode::PositionDeviationProtection, p, 5, can_id, out);
}
Status release_stall_state(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::ReleaseStallState, can_id, out);
}
Status restore_factory_settings(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::RestoreFactorySettings, can_id, out);
}
Status calibrate_encoder(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {0x00};
    return build(dev, CommandCode::CalibrateEncoder, p, 1, can_id, out);
}
Status work_mode(const DeviceConfig& dev, WorkMode mode, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(mode)};
    return build(dev, CommandCode::WorkMode, p, 1, can_id, out);
}
Status pid_kp_ki_vfoc(const DeviceConfig& dev, std::uint16_t kp, std::uint16_t ki, CanFrame& out, std::uint16_t can_id) noexcept {
    return build_pid_pair(dev, CommandCode::PidParamsVFoc, 0x00, kp, ki, can_id, out);
}
Status pid_kd_kv_vfoc(const DeviceConfig& dev, std::uint16_t kd, std::uint16_t kv, CanFrame& out, std::uint16_t can_id) noexcept {
    return build_pid_pair(dev, CommandCode::PidParamsVFoc, 0x01, kd, kv, can_id, out);
}
Status pid_kp_ki_close(const DeviceConfig& dev, std::uint16_t kp, std::uint16_t ki, CanFrame& out, std::uint16_t can_id) noexcept {
    return build_pid_pair(dev, CommandCode::PidParamsClose, 0x00, kp, ki, can_id, out);
}
Status pid_kd_kv_close(const DeviceConfig& dev, std::uint16_t kd, std::uint16_t kv, CanFrame& out, std::uint16_t can_id) noexcept {
    return build_pid_pair(dev, CommandCode::PidParamsClose, 0x01, kd, kv, can_id, out);
}
Status subdivisions(const DeviceConfig& dev, std::uint8_t microsteps, CanFrame& out, std::uint16_t can_id) noexcept {
    if (microsteps < 1) return Status::InvalidArgument;
    const std::uint8_t p[1] = {microsteps};
    return build(dev, CommandCode::Subdivisions, p, 1, can_id, out);
}
Status en_pin_active_level(const DeviceConfig& dev, EnPinActiveLevel level, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(level)};
    return build(dev, CommandCode::EnPinActiveLevel, p, 1, can_id, out);
}
Status motor_rotation_direction(const DeviceConfig& dev, MotorRotationDirection direction, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(direction)};
    return build(dev, CommandCode::MotorRotationDirection, p, 1, can_id, out);
}
Status auto_screen_off(const DeviceConfig& dev, bool enabled, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(enabled ? 1 : 0)};
    return build(dev, CommandCode::AutoScreenOff, p, 1, can_id, out);
}
Status subdivision_interpolation(const DeviceConfig& dev, bool enabled, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(enabled ? 1 : 0)};
    return build(dev, CommandCode::SubdivisionInterpolation, p, 1, can_id, out);
}
Status key_lock_function(const DeviceConfig& dev, bool state, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(state ? 1 : 0)};
    return build(dev, CommandCode::KeyLockFunction, p, 1, can_id, out);
}
Status holding_current_percentage(const DeviceConfig& dev, std::uint8_t ratio, CanFrame& out, std::uint16_t can_id) noexcept {
    if (ratio > 8) return Status::InvalidArgument;
    const std::uint8_t p[1] = {ratio};
    return build(dev, CommandCode::HoldingCurrentPercentage, p, 1, can_id, out);
}
Status working_current(const DeviceConfig& dev, std::uint16_t current_ma, bool save_to_flash, CanFrame& out, std::uint16_t can_id) noexcept {
    Status st = core::validate_working_current(dev, current_ma);
    if (st != Status::Ok) return st;
    std::uint8_t p[3];
    put_u16_be(p, current_ma);
    std::uint8_t len = 2;
    if (!save_to_flash) {
        p[2] = 0x00;
        len = 3;
    }
    return build(dev, CommandCode::WorkingCurrent, p, len, can_id, out);
}
Status position_reach_threshold(const DeviceConfig& dev, bool enabled, std::uint16_t threshold, CanFrame& out, std::uint16_t can_id) noexcept {
    std::uint8_t p[3];
    p[0] = static_cast<std::uint8_t>(enabled ? 1 : 0);
    put_u16_be(p + 1, threshold);
    return build(dev, CommandCode::PositionReachThreshold, p, 3, can_id, out);
}
Status reset_and_restart(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::ResetAndRestart, can_id, out);
}

// ============================ CAN settings ============================
Status bitrate(const DeviceConfig& dev, BitrateMode mode, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(mode)};
    return build(dev, CommandCode::Bitrate, p, 1, can_id, out);
}
Status slave_id(const DeviceConfig& dev, std::uint16_t slave_can_id, CanFrame& out, std::uint16_t can_id) noexcept {
    if (slave_can_id > 0x7FFu) return Status::CanIdOutOfRange;
    std::uint8_t p[2];
    put_u16_be(p, slave_can_id);
    return build(dev, CommandCode::SlaveId, p, 2, can_id, out);
}
Status group_id(const DeviceConfig& dev, std::uint16_t group_can_id, CanFrame& out, std::uint16_t can_id) noexcept {
    if (group_can_id < 1 || group_can_id > 0x7FFu) return Status::InvalidArgument;
    std::uint8_t p[2];
    put_u16_be(p, group_can_id);
    return build(dev, CommandCode::GroupId, p, 2, can_id, out);
}
Status response_mode(const DeviceConfig& dev, bool respond_enabled, bool active_enabled, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[2] = {static_cast<std::uint8_t>(respond_enabled ? 1 : 0),
                               static_cast<std::uint8_t>(active_enabled ? 1 : 0)};
    return build(dev, CommandCode::ResponseMode, p, 2, can_id, out);
}
Status heartbeat_protection(const DeviceConfig& dev, std::uint32_t protection_time_ms, CanFrame& out, std::uint16_t can_id) noexcept {
    std::uint8_t p[4];
    put_u32_be(p, protection_time_ms);
    return build(dev, CommandCode::HeartbeatProtection, p, 4, can_id, out);
}
Status no_verification_mode(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {0x01};
    return build(dev, CommandCode::NoVerificationMode, p, 1, can_id, out);
}
Status sync_mark_enabled(const DeviceConfig& dev, bool enabled, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(enabled ? 1 : 0)};
    return build(dev, CommandCode::SyncMarkEnabled, p, 1, can_id, out);
}
Status execute_sync_mark(CanFrame& out) noexcept {
    return frame(static_cast<std::uint8_t>(CommandCode::ExecuteSyncMark), nullptr, 0, 0x00, out);
}

// ============================ IO ============================
Status read_status(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id) noexcept {
    return build0(dev, CommandCode::ReadStatus, can_id, out);
}
Status port_mapping(const DeviceConfig& dev, bool enabled, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(enabled ? 1 : 0)};
    return build(dev, CommandCode::PortMapping, p, 1, can_id, out);
}
Status configure_in1_port_mode(const DeviceConfig& dev, bool output_mode, CanFrame& out, std::uint16_t can_id) noexcept {
    const std::uint8_t p[1] = {static_cast<std::uint8_t>(output_mode ? 1 : 0)};
    return build(dev, CommandCode::IoPortMode, p, 1, can_id, out);
}
Status write_io_port(const DeviceConfig& dev, std::uint8_t out2_mask, std::uint8_t out1_mask,
                     bool out2_value, bool out1_or_in1_value, CanFrame& out, std::uint16_t can_id) noexcept {
    if (out2_mask > 2 || out1_mask > 2) return Status::InvalidArgument;
    const std::uint8_t packed = static_cast<std::uint8_t>(
        ((out2_mask & 0x03u) << 6) |
        ((out1_mask & 0x03u) << 4) |
        ((out2_value ? 1u : 0u) << 3) |
        ((out1_or_in1_value ? 1u : 0u) << 2));
    const std::uint8_t p[1] = {packed};
    return build(dev, CommandCode::WriteIoPort, p, 1, can_id, out);
}
Status configure_io_pulse_divider_output(const DeviceConfig& dev, bool div_level, std::uint32_t div_period,
                                         CanFrame& out, std::uint16_t can_id) noexcept {
    std::uint8_t p[5];
    p[0] = static_cast<std::uint8_t>(div_level ? 1 : 0);
    put_u32_be(p + 1, div_period);
    return build(dev, CommandCode::IoPulseDividerOutput, p, 5, can_id, out);
}

} // namespace mks::encode
