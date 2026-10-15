add_executable(sprint1_protocol_tests
    protocol_test_main.c
    ${CMAKE_SOURCE_DIR}/App/Src/lifecycle.c
    ${CMAKE_SOURCE_DIR}/App/Src/health_monitor.c
    ${CMAKE_SOURCE_DIR}/App/Src/time_service.c
    ${CMAKE_SOURCE_DIR}/App/Src/calibration_record.c
    ${CMAKE_SOURCE_DIR}/App/Src/joint_mapping.c
    ${CMAKE_SOURCE_DIR}/App/Src/sensor_latest_value.c
    ${CMAKE_SOURCE_DIR}/App/Src/motor_latest_value.c
    ${CMAKE_SOURCE_DIR}/App/Src/snapshot_builder.c
    ${CMAKE_SOURCE_DIR}/App/Src/crc32_iso_hdlc.c
    ${CMAKE_SOURCE_DIR}/App/Src/spi_protocol.c
    ${CMAKE_SOURCE_DIR}/App/Src/spi_data_ready.c
    ${CMAKE_SOURCE_DIR}/App/Src/can_tx_policy.c
)

target_include_directories(sprint1_protocol_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/App/Inc
)

target_compile_definitions(sprint1_protocol_tests PRIVATE
    TIME_SERVICE_HOST_TEST
)

add_test(NAME sprint1_protocol_tests COMMAND sprint1_protocol_tests)

# The shared SPI golden frames (shared/test-vectors/spi), asserted byte for byte against
# spi_protocol.c. The Python suite asserts the same file (SYS-SPI-001 acceptance), so the
# test reads it from the repository rather than a copy.
get_filename_component(KARETAO_ROOT ${CMAKE_SOURCE_DIR} DIRECTORY)
set(SPI_GOLDEN_FRAMES ${KARETAO_ROOT}/shared/test-vectors/spi/frames.txt)
if(NOT EXISTS ${SPI_GOLDEN_FRAMES})
    message(FATAL_ERROR "Shared SPI golden frames not found: ${SPI_GOLDEN_FRAMES}")
endif()
add_executable(spi_golden_vector_tests
    spi_golden_vector_tests.c
    ${CMAKE_SOURCE_DIR}/App/Src/crc32_iso_hdlc.c
    ${CMAKE_SOURCE_DIR}/App/Src/spi_protocol.c
)
target_include_directories(spi_golden_vector_tests PRIVATE
    ${CMAKE_SOURCE_DIR}/App/Inc
)
target_compile_definitions(spi_golden_vector_tests PRIVATE
    TIME_SERVICE_HOST_TEST
)
add_test(NAME spi_golden_vector_tests COMMAND spi_golden_vector_tests ${SPI_GOLDEN_FRAMES})

add_executable(service_smoke_tests
    service_test_main.c
    ${CMAKE_SOURCE_DIR}/App/Src/app_init.c
    ${CMAKE_SOURCE_DIR}/App/Src/as5600.c
    ${CMAKE_SOURCE_DIR}/App/Src/can_service.c
    ${CMAKE_SOURCE_DIR}/App/Src/can_tx_policy.c
    ${CMAKE_SOURCE_DIR}/App/Src/crc32_iso_hdlc.c
    ${CMAKE_SOURCE_DIR}/App/Src/health_monitor.c
    ${CMAKE_SOURCE_DIR}/App/Src/i2c_manager.c
    ${CMAKE_SOURCE_DIR}/App/Src/joint_mapping.c
    ${CMAKE_SOURCE_DIR}/App/Src/lifecycle.c
    ${CMAKE_SOURCE_DIR}/App/Src/motor_latest_value.c
    ${CMAKE_SOURCE_DIR}/App/Src/sensor_latest_value.c
    ${CMAKE_SOURCE_DIR}/App/Src/sensor_task.c
    ${CMAKE_SOURCE_DIR}/App/Src/snapshot_builder.c
    ${CMAKE_SOURCE_DIR}/App/Src/spi_data_ready.c
    ${CMAKE_SOURCE_DIR}/App/Src/spi_protocol.c
    ${CMAKE_SOURCE_DIR}/App/Src/spi_slave_service.c
    ${CMAKE_SOURCE_DIR}/App/Src/stack_monitor.c
    ${CMAKE_SOURCE_DIR}/App/Src/tca9548a_mux.c
)

target_include_directories(service_smoke_tests PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/stubs
    ${CMAKE_SOURCE_DIR}/App/Inc
    ${CMAKE_SOURCE_DIR}/Middlewares/Third_Party/MksServo/include
)

target_compile_definitions(service_smoke_tests PRIVATE
    TIME_SERVICE_HOST_TEST
    STACK_MONITOR_HOST_TEST
)

add_test(NAME service_smoke_tests COMMAND service_smoke_tests)

# The firmware identity script is a build step, not C code: run it against a
# scratch repository (needs git; skipped without it).
find_package(Git QUIET)
if(GIT_FOUND)
    add_test(NAME firmware_identity_script
        COMMAND ${CMAKE_COMMAND}
            -DSCRIPT=${CMAKE_SOURCE_DIR}/cmake/firmware_identity.cmake
            -DWORK_DIR=${CMAKE_CURRENT_BINARY_DIR}/firmware_identity_test
            -DGIT_EXECUTABLE=${GIT_EXECUTABLE}
            -DC_COMPILER_PATH=${CMAKE_C_COMPILER}
            -P ${CMAKE_CURRENT_SOURCE_DIR}/firmware_identity_test.cmake
    )
else()
    message(WARNING "git not found: the firmware_identity_script host test is skipped")
endif()

# The task stack check the firmware build runs (tools/stack_depth.py).
find_package(Python3 COMPONENTS Interpreter)
if(Python3_Interpreter_FOUND)
    add_test(NAME stack_depth_tool
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tests/tools/test_stack_depth.py
    )
else()
    message(WARNING "python3 not found: the stack_depth_tool host test is skipped")
endif()

# The App/Src source-list check (B54): its comparison logic, then this side's lists.
add_test(NAME app_source_check
    COMMAND ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_SOURCE_DIR}/app_source_check_test.cmake
)
# Every executable defined in this directory counts, so a new test executable is
# covered without being named here.
include(${CMAKE_SOURCE_DIR}/cmake/app_source_check.cmake)
get_property(host_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
set(host_executables "")
foreach(target IN LISTS host_targets)
    get_target_property(type ${target} TYPE)
    if(type STREQUAL "EXECUTABLE")
        list(APPEND host_executables ${target})
    endif()
endforeach()
arm_sensor_hub_check_app_sources("host tests" ${host_executables})
