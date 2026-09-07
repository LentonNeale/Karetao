// Randomized malformed-frame robustness test: decoder must never crash or read
// out of bounds (ASan/UBSan enabled), and must always return a defined Status.
#include "mksservo/decoder.hpp"
#include "test_util.hpp"

using namespace mks;

namespace {
// Simple deterministic PRNG (xorshift32) — no external deps.
struct Rng {
    std::uint32_t s;
    std::uint32_t next() {
        s ^= s << 13; s ^= s >> 17; s ^= s << 5; return s;
    }
};
} // namespace

void run_fuzz_tests() {
    Rng rng{0x12345678u};
    const int iterations = 200000;
    for (int i = 0; i < iterations; ++i) {
        CanFrame f{};
        f.id = static_cast<std::uint16_t>(rng.next() & 0x1FFF); // sometimes > 0x7FF
        f.dlc = static_cast<std::uint8_t>(rng.next() % 16);     // 0..15 (sometimes > 8)
        for (int b = 0; b < 8; ++b) {
            f.data[b] = static_cast<std::uint8_t>(rng.next() & 0xFF);
        }
        decode::DecodedResponse d{};
        Status st = decode::decode(f, d);
        // Must return a valid enum value in range.
        CHECK(static_cast<int>(st) >= 0 && static_cast<int>(st) <= static_cast<int>(Status::NullPointer));
        // If Ok, payload_len must be consistent with dlc and never exceed max.
        if (st == Status::Ok) {
            CHECK(d.parsed.payload_len <= kMaxPayload);
            CHECK(f.dlc >= 2 && f.dlc <= 8);
        }
        if (test::failures() > 20) break; // fail fast
    }
    test::report("fuzz");
}
