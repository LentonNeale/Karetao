#include "mksservo/command.hpp"

#include <initializer_list>

namespace mks {

namespace {
/// Build a payload-length mask from allowed lengths (0..6).
constexpr std::uint8_t len_mask(std::initializer_list<int> lengths) {
    std::uint8_t m = 0;
    for (int len : lengths) {
        if (len >= 0 && len <= 7) m |= static_cast<std::uint8_t>(1u << len);
    }
    return m;
}
} // namespace

const CommandSpec kCommandSpecs[kCommandSpecCount] = {
    {CommandCode::ConfigurationParameter, len_mask({1}), 1, false, "read"},
    {CommandCode::AutoReadParameter,      len_mask({3}), 1, false, "read"},
    {CommandCode::NoVerificationMode,     len_mask({1}), 1, false, "can_settings"},

    {CommandCode::EncoderValue,               len_mask({0}), 1, false, "read"},
    {CommandCode::CumulativeEncoderValue,     len_mask({0}), 1, false, "read"},
    {CommandCode::RealtimeSpeed,              len_mask({0}), 1, false, "read"},
    {CommandCode::ReceivedPulses,             len_mask({0}), 1, false, "read"},
    {CommandCode::ReadStatus,                 len_mask({0}), 1, false, "io"},
    {CommandCode::RawAccumulatedEncoderValue, len_mask({0}), 1, false, "read"},
    {CommandCode::WriteIoPort,                len_mask({1}), 1, false, "io"},
    {CommandCode::PositionAngleError,         len_mask({0}), 1, false, "read"},
    {CommandCode::MotorEnableStatus,          len_mask({0}), 1, false, "read"},
    {CommandCode::ReturnToZeroStatus,         len_mask({0}), 1, false, "read"},
    {CommandCode::ReleaseStallState,          len_mask({0}), 1, false, "controller"},
    {CommandCode::MotorStallStatus,           len_mask({0}), 1, false, "read"},
    {CommandCode::RestoreFactorySettings,     len_mask({0}), 1, false, "controller"},
    {CommandCode::VersionInformation,         len_mask({0}), 1, false, "read"},

    {CommandCode::ResetAndRestart, len_mask({0}), 1, false, "controller"},
    {CommandCode::UserId,          len_mask({0, 4}), 1, false, "read"},
    {CommandCode::SyncMarkEnabled, len_mask({1}), 1, false, "can_settings"},
    {CommandCode::ExecuteSyncMark, len_mask({0}), 1, false, "can_settings"},

    {CommandCode::CalibrateEncoder,         len_mask({1}), 1, false, "controller"},
    {CommandCode::WorkMode,                 len_mask({1}), 1, false, "controller"},
    {CommandCode::WorkingCurrent,           len_mask({2, 3}), 1, false, "controller"},
    {CommandCode::Subdivisions,             len_mask({1}), 1, false, "controller"},
    {CommandCode::EnPinActiveLevel,         len_mask({1}), 1, false, "controller"},
    {CommandCode::MotorRotationDirection,   len_mask({1}), 1, false, "controller"},
    {CommandCode::AutoScreenOff,            len_mask({1}), 1, false, "controller"},
    {CommandCode::OvercurrentProtection,    len_mask({1}), 1, false, "controller"},
    {CommandCode::SubdivisionInterpolation, len_mask({1}), 1, false, "controller"},

    {CommandCode::Bitrate,      len_mask({1}), 1, false, "can_settings"},
    {CommandCode::SlaveId,      len_mask({2}), 1, false, "can_settings"},
    {CommandCode::ResponseMode, len_mask({2}), 1, false, "can_settings"},
    {CommandCode::GroupId,      len_mask({2}), 1, false, "can_settings"},
    {CommandCode::KeyLockFunction,  len_mask({1}), 1, false, "controller"},
    {CommandCode::HomingParameters, len_mask({6}), 1, false, "homing"},

    {CommandCode::ExecuteZeroReturn,       len_mask({0, 1}), 1, false, "homing"},
    {CommandCode::SetZeroPoint,            len_mask({0}), 1, false, "homing"},
    {CommandCode::HomingOffsetAndCurrent,  len_mask({6}), 1, false, "homing"},
    {CommandCode::PositionReachThreshold,  len_mask({3}), 1, false, "controller"},
    {CommandCode::PidParamsVFoc,           len_mask({5}), 1, false, "controller"},
    {CommandCode::PidParamsClose,          len_mask({5}), 1, false, "controller"},
    {CommandCode::HeartbeatProtection,     len_mask({4}), 1, false, "can_settings"},
    {CommandCode::IoPulseDividerOutput,    len_mask({5}), 1, false, "io"},
    {CommandCode::SingleTurnZeroReturnParams, len_mask({4}), 1, false, "homing"},
    {CommandCode::HoldingCurrentPercentage,   len_mask({1}), 1, false, "controller"},
    {CommandCode::PositionDeviationProtection, len_mask({5}), 1, false, "controller"},
    {CommandCode::PortMapping,             len_mask({1}), 1, false, "io"},
    {CommandCode::IoPortMode,              len_mask({1}), 1, false, "io"},

    {CommandCode::MotorOperatingStatus,   len_mask({0}), 1, false, "read"},
    {CommandCode::MotorEnableState,       len_mask({1}), 1, false, "motion"},
    {CommandCode::CoordinateRelativeMove, len_mask({6}), 1, false, "motion"},
    {CommandCode::CoordinateAbsoluteMove, len_mask({6}), 1, false, "motion"},
    {CommandCode::SpeedModeRun,           len_mask({3, 6}), 1, false, "motion"},
    {CommandCode::EmergencyStop,          len_mask({0}), 1, false, "motion"},
    {CommandCode::RelativePulseMove,      len_mask({6}), 1, false, "motion"},
    {CommandCode::AbsolutePulseMove,      len_mask({6}), 1, false, "motion"},
    {CommandCode::PowerOnAutoRun,         len_mask({1}), 1, false, "motion"},
};

const CommandSpec* find_command_spec(CommandCode code) noexcept {
    return find_command_spec(static_cast<std::uint8_t>(code));
}

const CommandSpec* find_command_spec(std::uint8_t code) noexcept {
    for (const auto& spec : kCommandSpecs) {
        if (static_cast<std::uint8_t>(spec.code) == code) {
            return &spec;
        }
    }
    return nullptr;
}

} // namespace mks
