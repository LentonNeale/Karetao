cmake_minimum_required(VERSION 3.22)

#
# This file is generated only once,
# and is not re-generated if converter is called multiple times.
#
# User is free to modify the file as much as necessary
#

# Setup compiler settings
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)


# Define the build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Debug")
endif()

# Set the project name
set(CMAKE_PROJECT_NAME Arm_Sensor_Hub)

# Enable compile command to ease indexing with e.g. clangd
set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

# Core project settings
project(${CMAKE_PROJECT_NAME})
message("Build type: " ${CMAKE_BUILD_TYPE})

option(ARM_SENSOR_HUB_BUILD_HOST_TESTS "Build native Sprint 1 protocol tests only" OFF)

if(ARM_SENSOR_HUB_BUILD_HOST_TESTS)
    enable_testing()
    add_subdirectory(tests/host)
    return()
endif()

# Enable CMake support for ASM, C, and C++ languages
enable_language(C CXX ASM)

# Create an executable object type
add_executable(${CMAKE_PROJECT_NAME})

# Add STM32CubeMX generated sources
add_subdirectory(cmake/stm32cubemx)

# Add MKS Servo protocol library (C++17, transport-agnostic)
set(MKSSERVO_BUILD_TESTS OFF CACHE BOOL "" FORCE)
add_subdirectory(Middlewares/Third_Party/MksServo)

# Link directories setup
target_link_directories(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined library search paths
)

# Add sources to executable
target_sources(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user sources here
    App/Src/app_init.c
    App/Src/lifecycle.c
    App/Src/time_service.c
    App/Src/calibration_record.c
    App/Src/joint_mapping.c
    App/Src/sensor_latest_value.c
    App/Src/motor_latest_value.c
    App/Src/snapshot_builder.c
    App/Src/crc32_iso_hdlc.c
    App/Src/spi_protocol.c
    App/Src/spi_data_ready.c
    App/Src/can_tx_policy.c
    App/Src/i2c_manager.c
    App/Src/tca9548a_mux.c
    App/Src/as5600.c
    App/Src/sensor_task.c
    App/Src/can_service.c
    App/Src/spi_slave_service.c
    App/Src/health_monitor.c
)

# Add include paths
target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined include paths
    App/Inc
)

# Firmware build identity reported in VERSION (0x04) frames. Sourced from the
# commit rather than the build clock so rebuilds of the same source agree.
# The header is regenerated on every build, not at configure time, so an
# edit followed by `cmake --build` reports the dirty bit (SPI-19, FW-3).
find_package(Git QUIET)
set(FIRMWARE_IDENTITY_HEADER ${CMAKE_BINARY_DIR}/generated/firmware_identity.h)
add_custom_target(firmware_identity
    COMMAND ${CMAKE_COMMAND}
        -DSOURCE_DIR=${CMAKE_SOURCE_DIR}
        -DSHARED_DIR=${CMAKE_SOURCE_DIR}/../shared
        -DOUTPUT=${FIRMWARE_IDENTITY_HEADER}
        -DGIT_EXECUTABLE=${GIT_EXECUTABLE}
        "-DC_COMPILER=${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION}"
        "-DCXX_COMPILER=${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}"
        -P ${CMAKE_SOURCE_DIR}/cmake/firmware_identity.cmake
    BYPRODUCTS ${FIRMWARE_IDENTITY_HEADER}
    COMMENT "Updating the firmware build identity"
    VERBATIM
)
add_dependencies(${CMAKE_PROJECT_NAME} firmware_identity)
target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE ${CMAKE_BINARY_DIR}/generated)

# Add project symbols (macros)
target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined symbols
    FIRMWARE_IDENTITY_GENERATED=1
)

# Remove wrong libob.a library dependency when using cpp files
list(REMOVE_ITEM CMAKE_C_IMPLICIT_LINK_LIBRARIES ob)

# Add linked libraries
target_link_libraries(${CMAKE_PROJECT_NAME}
    stm32cubemx
    mksservo

    # Add user defined libraries
)

# Emit the flashable images beside the ELF. st-flash cannot consume an ELF, so
# without these the build produces nothing that can reach the board.
add_custom_command(TARGET ${CMAKE_PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary
            $<TARGET_FILE:${CMAKE_PROJECT_NAME}> $<TARGET_FILE_DIR:${CMAKE_PROJECT_NAME}>/${CMAKE_PROJECT_NAME}.bin
    COMMAND ${CMAKE_OBJCOPY} -O ihex
            $<TARGET_FILE:${CMAKE_PROJECT_NAME}> $<TARGET_FILE_DIR:${CMAKE_PROJECT_NAME}>/${CMAKE_PROJECT_NAME}.hex
    COMMENT "Generating ${CMAKE_PROJECT_NAME}.bin and .hex for flashing"
)
