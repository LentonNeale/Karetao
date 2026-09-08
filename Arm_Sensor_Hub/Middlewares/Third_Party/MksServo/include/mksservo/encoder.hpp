#pragma once

#include <cstdint>

#include "can_frame.hpp"
#include "device_config.hpp"
#include "enums.hpp"
#include "status.hpp"

/// Protocol-oriented command encoders. Flat functions, no object hierarchy.
/// Every function validates arguments (Status), builds [code][payload][checksum],
/// and fills `out` with the actual DLC. `can_id == kUseDefaultCanId` uses the
/// device default. Implemented in src/encoder.cpp.
namespace mks::encode {

// ---- Motion (groups/motion.py) ----
Status set_motor_enable(const DeviceConfig& dev, bool enable, CanFrame& out,
                        std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status power_on_auto_run(const DeviceConfig& dev, bool enable, CanFrame& out,
                         std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status speed_mode_run(const DeviceConfig& dev, bool direction_cw, std::uint16_t speed,
                      std::uint8_t acceleration, bool has_runtime, std::uint32_t runtime_10ms,
                      CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status emergency_stop(const DeviceConfig& dev, CanFrame& out,
                      std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status relative_pulse_move(const DeviceConfig& dev, bool direction_cw, std::uint16_t speed,
                           std::uint8_t acceleration, std::uint32_t relative_pulses,
                           CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status absolute_pulse_move(const DeviceConfig& dev, std::uint16_t speed, std::uint8_t acceleration,
                           std::int32_t absolute_pulses, CanFrame& out,
                           std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status coordinate_relative_move(const DeviceConfig& dev, std::uint16_t speed, std::uint8_t acceleration,
                                std::int32_t relative_axis, CanFrame& out,
                                std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status coordinate_absolute_move(const DeviceConfig& dev, std::uint16_t speed, std::uint8_t acceleration,
                                std::int32_t absolute_axis, CanFrame& out,
                                std::uint16_t can_id = kUseDefaultCanId) noexcept;

// ---- Read (groups/read.py) ----
Status motor_stall_status(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status read_version_information(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status write_user_id(const DeviceConfig& dev, std::uint32_t user_id, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status read_user_id(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status received_pulses(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status raw_accumulated_encoder_value(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status position_angle_error(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status motor_enable_status(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status return_to_zero_status(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status motor_operating_status(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status encoder_value(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status cumulative_encoder_value(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status realtime_speed(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status configuration_parameter(const DeviceConfig& dev, std::uint8_t parameter_code, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status auto_read_parameter(const DeviceConfig& dev, std::uint8_t parameter_code, std::uint16_t interval_ms, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;

// ---- Homing (groups/homing.py) ----
Status set_zero_point(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status execute_zero_return(const DeviceConfig& dev, bool has_mode, GoZeroMode mode, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status set_homing_parameters(const DeviceConfig& dev, std::uint8_t home_trigger_level, std::uint8_t home_direction,
                             std::uint16_t home_speed_rpm, std::uint8_t end_limit_enabled, std::uint8_t homing_mode,
                             CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status set_homing_offset_and_current(const DeviceConfig& dev, std::uint32_t homing_offset, std::uint16_t homing_current_ma,
                                     CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status set_single_turn_zero_return_parameters(const DeviceConfig& dev, std::uint8_t mode, std::uint8_t zero_point_mode,
                                              std::uint8_t speed, std::uint8_t direction,
                                              CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;

// ---- Controller (groups/controller.py) ----
Status set_overcurrent_protection(const DeviceConfig& dev, bool enabled, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status set_position_deviation_protection(const DeviceConfig& dev, bool enabled, std::uint16_t time_window,
                                         std::uint16_t error_count, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status release_stall_state(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status restore_factory_settings(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status calibrate_encoder(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status work_mode(const DeviceConfig& dev, WorkMode mode, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status pid_kp_ki_vfoc(const DeviceConfig& dev, std::uint16_t kp, std::uint16_t ki, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status pid_kd_kv_vfoc(const DeviceConfig& dev, std::uint16_t kd, std::uint16_t kv, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status pid_kp_ki_close(const DeviceConfig& dev, std::uint16_t kp, std::uint16_t ki, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status pid_kd_kv_close(const DeviceConfig& dev, std::uint16_t kd, std::uint16_t kv, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status subdivisions(const DeviceConfig& dev, std::uint8_t microsteps, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status en_pin_active_level(const DeviceConfig& dev, EnPinActiveLevel level, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status motor_rotation_direction(const DeviceConfig& dev, MotorRotationDirection direction, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status auto_screen_off(const DeviceConfig& dev, bool enabled, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status subdivision_interpolation(const DeviceConfig& dev, bool enabled, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status key_lock_function(const DeviceConfig& dev, bool state, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status holding_current_percentage(const DeviceConfig& dev, std::uint8_t ratio, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status working_current(const DeviceConfig& dev, std::uint16_t current_ma, bool save_to_flash, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status position_reach_threshold(const DeviceConfig& dev, bool enabled, std::uint16_t threshold, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status reset_and_restart(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;

// ---- CAN settings (groups/can_settings.py) ----
Status bitrate(const DeviceConfig& dev, BitrateMode mode, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status slave_id(const DeviceConfig& dev, std::uint16_t slave_can_id, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status group_id(const DeviceConfig& dev, std::uint16_t group_can_id, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status response_mode(const DeviceConfig& dev, bool respond_enabled, bool active_enabled, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status heartbeat_protection(const DeviceConfig& dev, std::uint32_t protection_time_ms, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status no_verification_mode(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status sync_mark_enabled(const DeviceConfig& dev, bool enabled, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
/// Executes sync mark broadcast; CAN id is forced to 0x00 per protocol.
Status execute_sync_mark(CanFrame& out) noexcept;

// ---- IO (groups/io.py) ----
Status read_status(const DeviceConfig& dev, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status port_mapping(const DeviceConfig& dev, bool enabled, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status configure_in1_port_mode(const DeviceConfig& dev, bool output_mode, CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status write_io_port(const DeviceConfig& dev, std::uint8_t out2_mask, std::uint8_t out1_mask,
                     bool out2_value, bool out1_or_in1_value, CanFrame& out,
                     std::uint16_t can_id = kUseDefaultCanId) noexcept;
Status configure_io_pulse_divider_output(const DeviceConfig& dev, bool div_level, std::uint32_t div_period,
                                         CanFrame& out, std::uint16_t can_id = kUseDefaultCanId) noexcept;

} // namespace mks::encode
