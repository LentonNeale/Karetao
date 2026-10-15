/**
 * @file host_test_assert.h
 * @brief assert() for the host tests, refusing to build when NDEBUG would compile it out.
 *
 * C11 7.2 makes assert() expand to ((void)0) when NDEBUG is defined, and CMake's default
 * Release flags define it. A host test whose checks are asserts would then pass without
 * checking anything (finding VER-34). The HostTests preset sets no build type; any other
 * configuration that defines NDEBUG fails here, at compile time.
 */

#ifndef HOST_TEST_ASSERT_H
#define HOST_TEST_ASSERT_H

#ifdef NDEBUG
#error "The host tests check behaviour with assert(); NDEBUG would compile every check out. Configure without NDEBUG (the HostTests preset sets no build type)."
#endif

#include <assert.h>

#endif /* HOST_TEST_ASSERT_H */
