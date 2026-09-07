#pragma once

#include <cstdint>
#include <cstddef>

namespace mks {

/// Command bytes used by protocol request frames. Mirrors command.py.
enum class CommandCode : std::uint8_t {
    ConfigurationParameter = 0x00,
    AutoReadParameter      = 0x01,
    NoVerificationMode     = 0x0F,

    EncoderValue                = 0x30,
    CumulativeEncoderValue      = 0x31,
    RealtimeSpeed               = 0x32,
    ReceivedPulses              = 0x33,
    ReadStatus                  = 0x34,
    RawAccumulatedEncoderValue  = 0x35,
    WriteIoPort                 = 0x36,
    PositionAngleError          = 0x39,
    MotorEnableStatus           = 0x3A,
    ReturnToZeroStatus          = 0x3B,
    ReleaseStallState           = 0x3D,
    MotorStallStatus            = 0x3E,
    RestoreFactorySettings      = 0x3F,
    VersionInformation          = 0x40,

    ResetAndRestart  = 0x41,
    UserId           = 0x42,
    SyncMarkEnabled  = 0x4A,
    ExecuteSyncMark  = 0x4B,

    CalibrateEncoder         = 0x80,
    WorkMode                 = 0x82,
    WorkingCurrent           = 0x83,
    Subdivisions             = 0x84,
    EnPinActiveLevel         = 0x85,
    MotorRotationDirection   = 0x86,
    AutoScreenOff            = 0x87,
    OvercurrentProtection    = 0x88,
    SubdivisionInterpolation = 0x89,

    Bitrate      = 0x8A,
    SlaveId      = 0x8B,
    ResponseMode = 0x8C,
    GroupId      = 0x8D,
    KeyLockFunction   = 0x8F,
    HomingParameters  = 0x90,

    ExecuteZeroReturn        = 0x91,
    SetZeroPoint             = 0x92,
    HomingOffsetAndCurrent   = 0x94,
    PositionReachThreshold   = 0x95,
    PidParamsVFoc            = 0x96,
    PidParamsClose           = 0x97,
    HeartbeatProtection      = 0x98,
    IoPulseDividerOutput     = 0x99,
    SingleTurnZeroReturnParams = 0x9A,
    HoldingCurrentPercentage   = 0x9B,
    PositionDeviationProtection = 0x9D,
    PortMapping                 = 0x9E,
    IoPortMode                  = 0x9F,

    MotorOperatingStatus   = 0xF1,
    MotorEnableState       = 0xF3,
    CoordinateRelativeMove = 0xF4,
    CoordinateAbsoluteMove = 0xF5,
    SpeedModeRun           = 0xF6,
    EmergencyStop          = 0xF7,
    RelativePulseMove      = 0xFD,
    AbsolutePulseMove      = 0xFE,
    PowerOnAutoRun         = 0xFF,
};

/// Central per-command metadata. Single source of truth for payload-length rules
/// so encoders and the decoder don't duplicate protocol rules.
struct CommandSpec {
    CommandCode code;
    /// Bitmask of valid request payload lengths (bit N set => length N valid, N in 0..6).
    std::uint8_t request_len_mask;
    /// Minimum payload bytes expected in a response (baseline; detailed rules in decoder).
    std::uint8_t min_response_payload;
    /// Whether an empty response payload is valid for this command.
    bool empty_response_ok;
    /// Category/namespace string (debug/traceability; stored in flash).
    const char* category;
};

/// Number of entries in the registry (one per command code).
inline constexpr std::size_t kCommandSpecCount = 58;

/// Static registry (not ordered by code value).
/// Defined in src/command.cpp.
extern const CommandSpec kCommandSpecs[kCommandSpecCount];

/// Look up a spec by command code. Returns nullptr if unknown.
const CommandSpec* find_command_spec(CommandCode code) noexcept;
const CommandSpec* find_command_spec(std::uint8_t code) noexcept;

} // namespace mks
