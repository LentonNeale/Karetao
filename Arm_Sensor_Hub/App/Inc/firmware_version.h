/**
 * @file firmware_version.h
 * @brief Firmware build identity reported in VERSION (0x04) frames.
 */

#ifndef FIRMWARE_VERSION_H
#define FIRMWARE_VERSION_H

#include <stdint.h>

#define FIRMWARE_VERSION_MAJOR UINT8_C(0)
#define FIRMWARE_VERSION_MINOR UINT8_C(1)
#define FIRMWARE_VERSION_PATCH UINT8_C(0)

/* Supplied by the header the firmware build regenerates on every build
 * (cmake/firmware_identity.cmake). The fallbacks keep host test builds and
 * any out-of-tree build working without a git checkout. */
#ifdef FIRMWARE_IDENTITY_GENERATED
#include "firmware_identity.h"
#endif

#ifndef FIRMWARE_GIT_HASH_ABBREV
#define FIRMWARE_GIT_HASH_ABBREV UINT32_C(0)
#endif

#ifndef FIRMWARE_COMMIT_EPOCH_SECS
#define FIRMWARE_COMMIT_EPOCH_SECS UINT32_C(0)
#endif

#ifndef FIRMWARE_BUILD_DIRTY
#define FIRMWARE_BUILD_DIRTY 0
#endif

/* Not on the wire: VERSION has no field for them. The generated header and
 * the build log record them for evidence records (ruling R28). */
#ifndef FIRMWARE_C_COMPILER
#define FIRMWARE_C_COMPILER "unknown"
#endif

#ifndef FIRMWARE_CXX_COMPILER
#define FIRMWARE_CXX_COMPILER "unknown"
#endif

/** Set when the firmware was built from uncommitted changes. */
#define FIRMWARE_BUILD_FLAG_DIRTY UINT8_C(0x01)

#if FIRMWARE_BUILD_DIRTY
#define FIRMWARE_BUILD_FLAGS FIRMWARE_BUILD_FLAG_DIRTY
#else
#define FIRMWARE_BUILD_FLAGS UINT8_C(0)
#endif

#endif /* FIRMWARE_VERSION_H */
