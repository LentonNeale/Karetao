"""Generate golden vectors from the Python reference implementation.

Emits lines: name|can_id_hex|data_hex  for valid frames, and name|ERR for
expected failures. Used by the C++ host tests to assert byte-for-byte parity.
"""
from __future__ import annotations

import os
import sys

# Make the repo's src importable.
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from src.devices.mksservo import MksServoEncoder, MotorType  # noqa: E402
from src.devices.mksservo.enums import (  # noqa: E402
    BitrateMode,
    EnPinActiveLevel,
    GoZeroMode,
    MotorRotationDirection,
    WorkMode,
)

enc = MksServoEncoder(default_can_id=0x01, motor_type=MotorType.SERVO42)
enc57 = MksServoEncoder(default_can_id=0x01, motor_type=MotorType.SERVO57)


def line(name, frame):
    print(f"{name}|{frame.can_id:03X}|{bytes(frame.data).hex().upper()}")


def err(name, fn):
    try:
        fn()
    except Exception:
        print(f"{name}|ERR")
    else:
        print(f"{name}|NOERR")


# Motion
line("set_motor_enable_on", enc.motion.set_motor_enable(True))
line("set_motor_enable_off", enc.motion.set_motor_enable(False))
line("power_on_auto_run_on", enc.motion.power_on_auto_run(True))
line("power_on_auto_run_off", enc.motion.power_on_auto_run(False))
line("speed_mode_run_cw", enc.motion.speed_mode_run(True, 3000, 10))
line("speed_mode_run_ccw", enc.motion.speed_mode_run(False, 0, 0))
line("speed_mode_run_timed", enc.motion.speed_mode_run(True, 1000, 5, runtime_10ms=12345))
err("speed_mode_run_over", lambda: enc.motion.speed_mode_run(True, 3001, 10))
line("emergency_stop", enc.motion.emergency_stop())
line("relative_pulse_move", enc.motion.relative_pulse_move(True, 2000, 8, 100000))
line("absolute_pulse_move_pos", enc.motion.absolute_pulse_move(2000, 8, 8388607))
line("absolute_pulse_move_neg", enc.motion.absolute_pulse_move(2000, 8, -8388607))
err("absolute_pulse_move_over", lambda: enc.motion.absolute_pulse_move(2000, 8, 8388608))
err("absolute_pulse_move_under", lambda: enc.motion.absolute_pulse_move(2000, 8, -8388608))
err("absolute_pulse_move_speed_over", lambda: enc.motion.absolute_pulse_move(3001, 8, 0))
line("coordinate_relative_move", enc.motion.coordinate_relative_move(1500, 4, -500000))
line("coordinate_absolute_move", enc.motion.coordinate_absolute_move(1500, 4, 123456))

# Read
line("motor_stall_status", enc.read.motor_stall_status())
line("read_version_information", enc.read.read_version_information())
line("write_user_id", enc.read.write_user_id(0xDEADBEEF))
line("read_user_id", enc.read.read_user_id())
line("received_pulses", enc.read.received_pulses())
line("raw_accumulated_encoder_value", enc.read.raw_accumulated_encoder_value())
line("position_angle_error", enc.read.position_angle_error())
line("motor_enable_status", enc.read.motor_enable_status())
line("return_to_zero_status", enc.read.return_to_zero_status())
line("motor_operating_status", enc.read.motor_operating_status())
line("encoder_value", enc.read.encoder_value())
line("cumulative_encoder_value", enc.read.cumulative_encoder_value())
line("realtime_speed", enc.read.realtime_speed())
line("configuration_parameter", enc.read.configuration_parameter(0x42))
line("auto_read_parameter", enc.read.auto_read_parameter(0x30, 500))

# Homing
line("set_zero_point", enc.homing.set_zero_point())
line("execute_zero_return_default", enc.homing.execute_zero_return())
line("execute_zero_return_origin", enc.homing.execute_zero_return(GoZeroMode.ORIGIN))
line("execute_zero_return_coordinate", enc.homing.execute_zero_return(GoZeroMode.COORDINATE))
line("set_homing_parameters", enc.homing.set_homing_parameters(1, 0, 1500, 1, 2))
line("set_homing_offset_and_current", enc.homing.set_homing_offset_and_current(0x12345678, 1000))
line("set_single_turn_zero_return_parameters", enc.homing.set_single_turn_zero_return_parameters(2, 1, 3, 0))

# Controller
line("set_overcurrent_protection", enc.controller.set_overcurrent_protection(True))
line("set_position_deviation_protection", enc.controller.set_position_deviation_protection(True, 100, 5))
line("release_stall_state", enc.controller.release_stall_state())
line("restore_factory_settings", enc.controller.restore_factory_settings())
line("calibrate_encoder", enc.controller.calibrate_encoder())
line("work_mode", enc.controller.work_mode(WorkMode.SR_VFOC))
line("pid_kp_ki_vfoc", enc.controller.pid_kp_ki_vfoc(500, 600))
line("pid_kd_kv_vfoc", enc.controller.pid_kd_kv_vfoc(100, 200))
line("pid_kp_ki_close", enc.controller.pid_kp_ki_close(700, 800))
line("pid_kd_kv_close", enc.controller.pid_kd_kv_close(300, 400))
line("subdivisions", enc.controller.subdivisions(16))
line("en_pin_active_level", enc.controller.en_pin_active_level(EnPinActiveLevel.ACTIVE_LOW))
line("motor_rotation_direction", enc.controller.motor_rotation_direction(MotorRotationDirection.CCW))
line("auto_screen_off", enc.controller.auto_screen_off(True))
line("subdivision_interpolation", enc.controller.subdivision_interpolation(False))
line("key_lock_function", enc.controller.key_lock_function(True))
line("holding_current_percentage", enc.controller.holding_current_percentage(8))
line("working_current_save", enc.controller.working_current(3000, save_to_flash=True))
line("working_current_nosave", enc.controller.working_current(2000, save_to_flash=False))
err("working_current_over_42", lambda: enc.controller.working_current(3001))
line("working_current_57_max", enc57.controller.working_current(5200))
line("position_reach_threshold", enc.controller.position_reach_threshold(True, 50))
line("reset_and_restart", enc.controller.reset_and_restart())

# CAN settings
line("bitrate", enc.can_settings.bitrate(BitrateMode.MODE_2))
line("slave_id", enc.can_settings.slave_id(0x123))
line("group_id", enc.can_settings.group_id(0x45))
line("response_mode", enc.can_settings.response_mode(True, False))
line("heartbeat_protection", enc.can_settings.heartbeat_protection(0x00010000))
line("no_verification_mode", enc.can_settings.no_verification_mode())
line("sync_mark_enabled", enc.can_settings.sync_mark_enabled(True))
line("execute_sync_mark", enc.can_settings.execute_sync_mark())

# IO
line("read_status", enc.io.read_status())
line("port_mapping", enc.io.port_mapping(True))
line("configure_in1_port_mode", enc.io.configure_in1_port_mode(True))
line("write_io_port", enc.io.write_io_port(2, 1, True, False))
line("configure_io_pulse_divider_output", enc.io.configure_io_pulse_divider_output(True, 0x0000FFFF))
