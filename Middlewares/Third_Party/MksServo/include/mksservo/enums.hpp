#pragma once

#include <cstdint>

namespace mks {

/// Motor model (protocol-level identity; limits live in device_config.hpp).
enum class MotorType : std::uint8_t {
    Servo42 = 42,
    Servo57 = 57,
};

enum class BitrateMode : std::uint8_t {
    Mode0 = 0,
    Mode1 = 1,
    Mode2 = 2,
    Mode3 = 3,
};

enum class WorkMode : std::uint8_t {
    CrOpen  = 0,
    CrClose = 1,
    CrVFoc  = 2,
    SrOpen  = 3,
    SrClose = 4,
    SrVFoc  = 5,
};

enum class GoZeroMode : std::uint8_t {
    Origin     = 0,
    Coordinate = 1,
};

enum class EnPinActiveLevel : std::uint8_t {
    ActiveLow    = 0,
    ActiveHigh   = 1,
    ActiveAlways = 2,
};

enum class MotorRotationDirection : std::uint8_t {
    Cw  = 0,
    Ccw = 1,
};

/// Generic command status values present in MKS responses.
enum class CommandStatus : std::uint8_t {
    Failed  = 0x00,
    Success = 0x01,
};

} // namespace mks
