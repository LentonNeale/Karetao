#pragma once

#include <cstdint>

namespace mks {

/// Error/result codes for all codec operations. No exceptions are used.
enum class Status : std::uint8_t {
    Ok = 0,
    InvalidArgument,        ///< generic argument validation failure
    SpeedOutOfRange,        ///< speed outside 0..3000
    CurrentOutOfRange,      ///< current outside u16 or per-model max
    WorkingCurrentExceeded, ///< working current exceeds device max
    CanIdOutOfRange,        ///< CAN id outside 0..0x7FF
    PayloadTooLong,         ///< payload would exceed max DLC
    FrameTooShort,          ///< frame has fewer than 2 bytes (cmd+checksum)
    InvalidDlc,             ///< dlc > 8 or inconsistent
    ChecksumMismatch,       ///< checksum8 verification failed
    EmptyPayloadNotAllowed, ///< known command returned empty payload
    UnknownCommand,         ///< command code not in registry
    InvalidStatusPayload,   ///< status byte not a known CommandStatus
    NullPointer,            ///< null out-param / buffer
};

} // namespace mks
