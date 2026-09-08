#pragma once

#include <cstdint>

#include "enums.hpp"

namespace mks {

/// Sentinel for "use the device default CAN id".
inline constexpr std::uint16_t kUseDefaultCanId = 0xFFFF;

/// Device/model configuration, kept separate from low-level serialization.
/// Model current limits belong here, not in protocol primitives.
struct DeviceConfig {
    std::uint16_t default_can_id{0x01};
    /// Max working current in mA; 0 means "no limit enforced".
    std::uint16_t max_working_current_ma{0};
};

/// Preset for MKS Servo42 (max working current 3000 mA).
inline constexpr DeviceConfig kServo42{0x01, 3000};
/// Preset for MKS Servo57 (max working current 5200 mA).
inline constexpr DeviceConfig kServo57{0x01, 5200};

/// Build a config for a given motor type with the library's known limits.
inline constexpr DeviceConfig config_for(MotorType type, std::uint16_t default_can_id = 0x01) {
    return DeviceConfig{
        default_can_id,
        static_cast<std::uint16_t>(type == MotorType::Servo57 ? 5200 : 3000),
    };
}

} // namespace mks
