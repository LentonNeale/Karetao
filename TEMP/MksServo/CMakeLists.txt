cmake_minimum_required(VERSION 3.16)
project(mksservo CXX)

option(MKSSERVO_BUILD_TESTS "Build host tests" ON)

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
