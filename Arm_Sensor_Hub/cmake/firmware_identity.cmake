# Writes the firmware build identity header reported in VERSION (0x04) frames.
#
# Run as a script on every firmware build (cmake -P), so the identity follows the
# tree being built, not the tree at the last configure. The header is rewritten
# only when its content changes, so an unchanged tree rebuilds nothing.
#
# Inputs (-D):
#   SOURCE_DIR        the Arm_Sensor_Hub directory; the dirty check covers it
#   SHARED_DIR        optional second directory the dirty check covers (shared/)
#   OUTPUT            the header to write
#   GIT_EXECUTABLE    git; empty or missing leaves the identity at zero
#   C_COMPILER        the C compiler's id and version, recorded as text
#   CXX_COMPILER      the C++ compiler's id and version, recorded as text

if(NOT SOURCE_DIR OR NOT OUTPUT)
    message(FATAL_ERROR "firmware_identity.cmake needs SOURCE_DIR and OUTPUT")
endif()

set(hash 0)
set(epoch 0)
set(dirty 0)

set(dirty_paths "${SOURCE_DIR}")
if(SHARED_DIR AND IS_DIRECTORY "${SHARED_DIR}")
    get_filename_component(SHARED_DIR "${SHARED_DIR}" ABSOLUTE)
    list(APPEND dirty_paths "${SHARED_DIR}")
endif()

if(GIT_EXECUTABLE)
    # The full hash, cut to eight digits here: --short=8 gives more than eight
    # once eight are ambiguous, and the extra digit would not fit the field.
    execute_process(COMMAND ${GIT_EXECUTABLE} rev-parse HEAD
        WORKING_DIRECTORY ${SOURCE_DIR}
        OUTPUT_VARIABLE git_hash OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_VARIABLE git_hash_error ERROR_STRIP_TRAILING_WHITESPACE RESULT_VARIABLE git_hash_result)
    execute_process(COMMAND ${GIT_EXECUTABLE} log -1 --format=%ct
        WORKING_DIRECTORY ${SOURCE_DIR}
        OUTPUT_VARIABLE git_epoch OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET RESULT_VARIABLE git_epoch_result)
    execute_process(COMMAND ${GIT_EXECUTABLE} status --porcelain -- ${dirty_paths}
        WORKING_DIRECTORY ${SOURCE_DIR}
        OUTPUT_VARIABLE git_status OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_VARIABLE git_status_error ERROR_STRIP_TRAILING_WHITESPACE RESULT_VARIABLE git_status_result)

    # A git that cannot read the tree is not a dirty tree, so say which it is. The
    # identity stays conservative (dirty set, hash zero), but the reason is named.
    if(NOT git_hash_result EQUAL 0 OR NOT git_status_result EQUAL 0)
        set(git_failed TRUE)
        set(git_error "${git_hash_error}")
        if(git_error STREQUAL "")
            set(git_error "${git_status_error}")
        endif()
        message(WARNING
            "git could not read the source tree, so the firmware identity is unknown "
            "(hash 0, dirty bit set): ${git_error}\n"
            "If git reports 'dubious ownership', the checkout belongs to another user (common in "
            "CI containers): allow it with `git config --global --add safe.directory <repository>`.")
    endif()

    if(git_hash_result EQUAL 0 AND git_hash MATCHES "^[0-9a-f]+$")
        string(SUBSTRING "${git_hash}" 0 8 git_hash)
        set(hash "0x${git_hash}")
    endif()
    if(git_epoch_result EQUAL 0 AND git_epoch MATCHES "^[0-9]+$")
        set(epoch ${git_epoch})
    endif()
    if(NOT git_status_result EQUAL 0 OR NOT git_status STREQUAL "")
        set(dirty 1)
    endif()
endif()

# The compiler strings become C string literals.
function(c_string out text)
    if(text STREQUAL "")
        set(text "unknown")
    endif()
    string(REPLACE "\\" "\\\\" text "${text}")
    string(REPLACE "\"" "\\\"" text "${text}")
    set(${out} "\"${text}\"" PARENT_SCOPE)
endfunction()
c_string(c_compiler "${C_COMPILER}")
c_string(cxx_compiler "${CXX_COMPILER}")

set(content "/* Generated on every build by cmake/firmware_identity.cmake. Do not edit. */
#ifndef FIRMWARE_IDENTITY_H
#define FIRMWARE_IDENTITY_H

#include <stdint.h>

#define FIRMWARE_GIT_HASH_ABBREV UINT32_C(${hash})
#define FIRMWARE_COMMIT_EPOCH_SECS UINT32_C(${epoch})
#define FIRMWARE_BUILD_DIRTY ${dirty}
#define FIRMWARE_C_COMPILER ${c_compiler}
#define FIRMWARE_CXX_COMPILER ${cxx_compiler}

#endif /* FIRMWARE_IDENTITY_H */
")

# Writes only when the content differs, so the timestamp (and every compile
# that includes the header) is left alone for an unchanged tree.
file(CONFIGURE OUTPUT "${OUTPUT}" CONTENT "${content}" @ONLY)

if(dirty AND NOT git_failed)
    message(WARNING
        "Building from a dirty working tree: VERSION frames will report build_flags bit 0 "
        "and must not be used as integration-gate evidence.")
endif()
message(STATUS "Firmware identity: hash=${hash} commit_epoch=${epoch} dirty=${dirty} "
               "c=${C_COMPILER} cxx=${CXX_COMPILER}")
