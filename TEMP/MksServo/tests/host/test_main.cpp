#include <cstdio>

#include "test_util.hpp"

void run_core_tests();
void run_encoder_tests();
void run_decoder_tests();
void run_fuzz_tests();

int main() {
    run_core_tests();
    run_encoder_tests();
    run_decoder_tests();
    run_fuzz_tests();

    std::printf("\nTOTAL: %d checks, %d failures\n", test::checks(), test::failures());
    return test::failures() == 0 ? 0 : 1;
}
