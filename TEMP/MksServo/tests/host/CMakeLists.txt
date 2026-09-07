add_executable(mksservo_host_tests
    test_main.cpp
    test_core.cpp
    test_encoder.cpp
    test_decoder.cpp
    test_fuzz.cpp
)

target_link_libraries(mksservo_host_tests PRIVATE mksservo)
target_compile_features(mksservo_host_tests PRIVATE cxx_std_17)
target_compile_options(mksservo_host_tests PRIVATE
    -fno-exceptions -fno-rtti -Wall -Wextra -Wpedantic
    -fsanitize=address,undefined
)
target_link_options(mksservo_host_tests PRIVATE -fsanitize=address,undefined)

add_test(NAME mksservo_host_tests COMMAND mksservo_host_tests)
