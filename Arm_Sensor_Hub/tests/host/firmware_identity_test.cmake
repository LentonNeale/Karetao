# Host test for cmake/firmware_identity.cmake (SPI-19, FW-3, VER-39).
#
# Builds a scratch git repository laid out like this one (fw/ for Arm_Sensor_Hub,
# shared/ beside it, other/ outside the firmware) and runs the identity script
# against it the way each firmware build does: a clean commit reports its hash
# and dirty=0, an unchanged tree leaves the header untouched, an edit or a new
# file under fw/ or shared/ reports dirty=1 without any reconfigure, and an edit
# under other/ does not. The header is compiled as C after each run.
#
# Inputs (-D): SCRIPT (the identity script), WORK_DIR (scratch space),
# GIT_EXECUTABLE, C_COMPILER_PATH (a host C compiler for the compile check).

foreach(input SCRIPT WORK_DIR GIT_EXECUTABLE C_COMPILER_PATH)
    if(NOT ${input})
        message(FATAL_ERROR "firmware_identity_test.cmake needs -D${input}")
    endif()
endforeach()

# Keep the developer's global and system git config (hooks, templates) out.
set(ENV{GIT_CONFIG_NOSYSTEM} 1)
set(ENV{GIT_CONFIG_GLOBAL} /dev/null)

set(repo "${WORK_DIR}/repo")
set(header "${WORK_DIR}/firmware_identity.h")
file(REMOVE_RECURSE "${WORK_DIR}")
file(MAKE_DIRECTORY "${repo}/fw" "${repo}/shared" "${repo}/other")

function(git)
    execute_process(COMMAND ${GIT_EXECUTABLE} -c user.name=test -c user.email=test@example.invalid
                            -c init.defaultBranch=main -c commit.gpgsign=false
                            -c core.hooksPath=/dev/null ${ARGN}
        WORKING_DIRECTORY "${repo}" RESULT_VARIABLE result OUTPUT_VARIABLE out ERROR_VARIABLE err
        OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(NOT result EQUAL 0)
        message(FATAL_ERROR "git ${ARGN} failed: ${err}")
    endif()
    set(git_out "${out}" PARENT_SCOPE)
endfunction()

# Runs the script, reads the header and compiles it as C11.
function(run_identity)
    set(c_compiler "GNU 0.0.0")
    if(ARGC GREATER 0)
        set(c_compiler "${ARGV0}")
    endif()
    execute_process(COMMAND ${CMAKE_COMMAND} -DSOURCE_DIR=${repo}/fw -DSHARED_DIR=${repo}/fw/../shared
                            -DOUTPUT=${header} -DGIT_EXECUTABLE=${GIT_EXECUTABLE}
                            "-DC_COMPILER=${c_compiler}" "-DCXX_COMPILER=GNU 0.0.1"
                            -P ${SCRIPT}
        RESULT_VARIABLE result OUTPUT_VARIABLE out ERROR_VARIABLE err)
    if(NOT result EQUAL 0)
        message(FATAL_ERROR "identity script failed:\n${out}\n${err}")
    endif()
    file(READ "${header}" text)
    set(header_text "${text}" PARENT_SCOPE)

    file(WRITE "${WORK_DIR}/use_identity.c" [=[
#include "firmware_identity.h"
_Static_assert(FIRMWARE_GIT_HASH_ABBREV <= UINT32_MAX, "hash fits the 32-bit field");
_Static_assert(FIRMWARE_BUILD_DIRTY == 0 || FIRMWARE_BUILD_DIRTY == 1, "dirty is a flag");
static const char c_compiler[] = FIRMWARE_C_COMPILER;
static const char cxx_compiler[] = FIRMWARE_CXX_COMPILER;
const char *identity_strings[] = { c_compiler, cxx_compiler };
]=])
    execute_process(COMMAND ${C_COMPILER_PATH} -std=c11 -Wall -Wextra -Werror -fsyntax-only
                            -I ${WORK_DIR} ${WORK_DIR}/use_identity.c
        RESULT_VARIABLE result ERROR_VARIABLE err)
    if(NOT result EQUAL 0)
        message(FATAL_ERROR "generated header does not compile as C:\n${err}\n${text}")
    endif()
endfunction()

function(expect text what)
    string(FIND "${header_text}" "${text}" at)
    if(at EQUAL -1)
        message(FATAL_ERROR "${what}: expected '${text}' in:\n${header_text}")
    endif()
endfunction()

function(expect_head_hash what)
    git(rev-parse HEAD)
    string(SUBSTRING "${git_out}" 0 8 short)
    expect("#define FIRMWARE_GIT_HASH_ABBREV UINT32_C(0x${short})" "${what}")
endfunction()

git(init -q)
file(WRITE "${repo}/fw/source.c" "int x;\n")
file(WRITE "${repo}/shared/vectors.txt" "a\n")
file(WRITE "${repo}/other/notes.md" "n\n")
git(add .)
git(commit -q -m first)

run_identity()
expect_head_hash("clean commit hash")
expect("#define FIRMWARE_BUILD_DIRTY 0" "clean tree")
expect("#include <stdint.h>" "header includes stdint")
expect("#define FIRMWARE_C_COMPILER \"GNU 0.0.0\"" "C compiler")
expect("#define FIRMWARE_CXX_COMPILER \"GNU 0.0.1\"" "C++ compiler")

# An unchanged tree must not touch the header, or every build recompiles.
file(TIMESTAMP "${header}" before "%s")
execute_process(COMMAND ${CMAKE_COMMAND} -E sleep 1.1)
run_identity()
file(TIMESTAMP "${header}" after "%s")
if(NOT before STREQUAL after)
    message(FATAL_ERROR "header rewritten although the identity did not change")
endif()

# A quote or backslash in a compiler string must still give a valid C literal.
run_identity("GNU \"odd\\name\" 1.0")
expect("#define FIRMWARE_C_COMPILER \"GNU \\\"odd\\\\name\\\" 1.0\"" "escaped compiler string")

file(APPEND "${repo}/other/notes.md" "m\n")
run_identity()
expect("#define FIRMWARE_BUILD_DIRTY 0" "edit outside the firmware sources")

file(APPEND "${repo}/fw/source.c" "int y;\n")
run_identity()
expect("#define FIRMWARE_BUILD_DIRTY 1" "edited firmware file")

git(commit -q -am second)
run_identity()
expect_head_hash("new commit hash")
expect("#define FIRMWARE_BUILD_DIRTY 0" "clean after commit")

file(APPEND "${repo}/shared/vectors.txt" "b\n")
run_identity()
expect("#define FIRMWARE_BUILD_DIRTY 1" "edited shared file")
git(commit -q -am third)

file(WRITE "${repo}/fw/new.c" "int z;\n")
run_identity()
expect("#define FIRMWARE_BUILD_DIRTY 1" "untracked firmware file")

# A git that cannot read the tree (as in a CI container that owns the checkout under
# another user) is reported as such, not as a dirty tree, and the identity stays
# conservative: hash zero, dirty set.
set(fake_git "${WORK_DIR}/fake-git")
file(WRITE "${fake_git}" "#!/bin/sh\necho \"fatal: detected dubious ownership in repository\" >&2\nexit 128\n")
file(CHMOD "${fake_git}" PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE)
execute_process(COMMAND ${CMAKE_COMMAND} -DSOURCE_DIR=${repo}/fw -DOUTPUT=${header}
                        -DGIT_EXECUTABLE=${fake_git} "-DC_COMPILER=GNU 0.0.0" "-DCXX_COMPILER=GNU 0.0.1"
                        -P ${SCRIPT}
    RESULT_VARIABLE result OUTPUT_VARIABLE out ERROR_VARIABLE err)
if(NOT result EQUAL 0)
    message(FATAL_ERROR "identity script failed with an unusable git:\n${out}\n${err}")
endif()
foreach(text "git could not read the source tree" "dubious ownership" "safe.directory")
    string(FIND "${err}" "${text}" at)
    if(at EQUAL -1)
        message(FATAL_ERROR "unusable git: expected '${text}' in the warning:\n${err}")
    endif()
endforeach()
string(FIND "${err}" "Building from a dirty working tree" at)
if(NOT at EQUAL -1)
    message(FATAL_ERROR "unusable git: reported as a dirty tree:\n${err}")
endif()
file(READ "${header}" header_text)
expect("#define FIRMWARE_GIT_HASH_ABBREV UINT32_C(0)" "unusable git: hash")
expect("#define FIRMWARE_BUILD_DIRTY 1" "unusable git: dirty")

message(STATUS "firmware identity script: all checks passed")
