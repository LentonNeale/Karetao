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