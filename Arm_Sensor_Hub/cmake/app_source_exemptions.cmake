# App/Src modules deliberately left out of a build, each with its reason.
#
# cmake/app_source_check.cmake (story B54) fails configure when an App/Src module is
# missing from the firmware or host-test source lists and is not listed here. It also
# fails on an entry here for a module that is built, or that no longer exists, so a
# module leaves this list the moment it is added to a build.

# Not in the firmware build. motion_permission.c is the motion gate; it is rebuilt
# around D-3, compiled and wired by the gated-motion work (WP14, B106; finding FW-4).
set(ARM_SENSOR_HUB_APP_NOT_IN_FIRMWARE
    motion_permission.c
)

# Not in any host-test executable. A firmware-only module belongs here only when it
# cannot be built against tests/host/stubs; say why. motion_permission.c: as above,
# its host tests come with B106.
set(ARM_SENSOR_HUB_APP_NOT_IN_HOST_TESTS
    motion_permission.c
)
