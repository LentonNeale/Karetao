cmake_minimum_required(VERSION 3.16)

if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    project(mksservo CXX)
endif()

option(MKSSERVO_BUILD_TESTS "Build host tests" OFF)

add_library(mksservo STATIC
    src/command.cpp
    src/protocol_core.cpp
    src/encoder.cpp
    src/decoder.cpp
    src/mks_api.cpp
)

target_include_directories(mksservo PUBLIC include)

target_compile_features(mksservo PUBLIC cxx_std_17)

# Embedded-friendly: no exceptions, no RTTI, warnings on.
target_compile_options(mksservo PRIVATE
    -fno-exceptions
    -fno-rtti
    -Wall
    -Wextra
    -Wpedantic
)

if(MKSSERVO_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests/host)
endif()
