#pragma once

#include <cstdio>
#include <cstdint>

#include "mksservo/can_frame.hpp"
#include "mksservo/status.hpp"

namespace test {

inline int& failures() { static int f = 0; return f; }
inline int& checks() { static int c = 0; return c; }

inline void report(const char* name) {
    std::printf("[%s] %d checks, %d failures\n", name, checks(), failures());
}

inline void check_frame(const mks::CanFrame& frame, std::uint16_t id,
                        const std::uint8_t* exp, std::uint8_t exp_len,
                        const char* file, int line) {
    ++checks();
    bool ok = (frame.id == id) && (frame.dlc == exp_len);
    if (ok) {
        for (std::uint8_t i = 0; i < exp_len; ++i) {
            if (frame.data[i] != exp[i]) { ok = false; break; }
        }
    }
    if (!ok) {
        ++failures();
        std::printf("  FAIL %s:%d: frame mismatch (id=0x%03X dlc=%u)\n", file, line, frame.id, frame.dlc);
        std::printf("    got:");
        for (std::uint8_t i = 0; i < frame.dlc; ++i) std::printf(" %02X", frame.data[i]);
        std::printf("\n    exp:");
        for (std::uint8_t i = 0; i < exp_len; ++i) std::printf(" %02X", exp[i]);
        std::printf("\n");
    }
}

} // namespace test

#define CHECK(cond)                                                        \
    do {                                                                   \
        ++::test::checks();                                                \
        if (!(cond)) {                                                     \
            ++::test::failures();                                          \
            std::printf("  FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
        }                                                                  \
    } while (0)

#define CHECK_STATUS(expr, expected)                                                  \
    do {                                                                              \
        ++::test::checks();                                                           \
        ::mks::Status _s = (expr);                                                    \
        if (_s != (expected)) {                                                       \
            ++::test::failures();                                                     \
            std::printf("  FAIL %s:%d: %s => status %d, expected %d\n", __FILE__,     \
                        __LINE__, #expr, static_cast<int>(_s),                        \
                        static_cast<int>(expected));                                  \
        }                                                                             \
    } while (0)

#define CHECK_FRAME(frame, id, dlc, ...)                                        \
    do {                                                                        \
        const std::uint8_t _exp[] = {__VA_ARGS__};                              \
        ::test::check_frame((frame), (id), _exp,                                \
                            static_cast<std::uint8_t>(sizeof(_exp)),            \
                            __FILE__, __LINE__);                                \
        (void)(dlc);                                                            \
    } while (0)
