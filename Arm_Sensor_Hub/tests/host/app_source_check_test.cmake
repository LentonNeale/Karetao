# Host test for the comparison in cmake/app_source_check.cmake (B54), run in script mode.

include(${CMAKE_CURRENT_LIST_DIR}/../../cmake/app_source_check.cmake)

set(disk /src/App/Src/a.c /src/App/Src/b.c /src/App/Src/gate.c)

function(expect_problems what expected_count expected_text built exempt)
    arm_sensor_hub_app_source_problems(problems "firmware" "${disk}" "${built}" "${exempt}")
    list(LENGTH problems count)
    if(NOT count EQUAL expected_count)
        message(FATAL_ERROR "${what}: expected ${expected_count} problem(s), got ${count}: ${problems}")
    endif()
    if(expected_text)
        string(FIND "${problems}" "${expected_text}" at)
        if(at EQUAL -1)
            message(FATAL_ERROR "${what}: expected '${expected_text}' in: ${problems}")
        endif()
    endif()
endfunction()

# Everything built, or the one gap exempted: no problem.
expect_problems("all built" 0 "" "/src/App/Src/a.c;/src/App/Src/b.c;/src/App/Src/gate.c" "")
expect_problems("gap exempted" 0 "" "/src/App/Src/a.c;/src/App/Src/b.c;/other/x.c" "gate.c")

# A module in App/Src that the build leaves out, without an exemption.
expect_problems("missing" 1 "b.c is in App/Src but not in the firmware source list"
                "/src/App/Src/a.c" "gate.c")

# An exemption that is no longer needed, or names a removed module, is itself a failure.
expect_problems("stale: now built" 1 "gate.c is built for firmware but still exempted"
                "/src/App/Src/a.c;/src/App/Src/b.c;/src/App/Src/gate.c" "gate.c")
expect_problems("stale: removed" 1 "old.c is exempted for firmware but is not in App/Src"
                "/src/App/Src/a.c;/src/App/Src/b.c;/src/App/Src/gate.c" "old.c")

# Matching is by full path, so a same-named file elsewhere does not count as built.
expect_problems("other directory" 1 "a.c is in App/Src but not in the firmware source list"
                "/elsewhere/a.c;/src/App/Src/b.c;/src/App/Src/gate.c" "")

# A C++ module is checked like a C one.
set(disk /src/App/Src/a.c /src/App/Src/glue.cpp)
expect_problems("C++ module missing" 1 "glue.cpp is in App/Src but not in the firmware source list"
                "/src/App/Src/a.c" "")

message(STATUS "app source check: all cases passed")
