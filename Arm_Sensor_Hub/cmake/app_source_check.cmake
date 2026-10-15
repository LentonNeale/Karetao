# Configure-time check that every App/Src module is compiled where it should be
# (story B54, finding FW-4).
#
# The firmware and the host tests list their sources by hand, so a new module can be
# left out of one and nobody notices; motion_permission.c was in neither. Each build
# checks its own targets at configure time: the firmware configure checks the firmware
# target, the HostTests configure checks the host-test executables. CI configures
# both, so both lists are checked on every change. Deliberate omissions, each with its
# reason, are in app_source_exemptions.cmake.

include_guard(GLOBAL)
include(${CMAKE_CURRENT_LIST_DIR}/app_source_exemptions.cmake)

# The comparison itself, free of targets so it can be tested in script mode.
#   out          variable to receive the list of problems (empty when all is well)
#   side         "firmware" or "host tests", for the messages
#   on_disk      absolute paths of the App/Src/*.c files
#   built        absolute paths of the sources the side's targets compile
#   exempt_names file names exempted for this side
function(arm_sensor_hub_app_source_problems out side on_disk built exempt_names)
    set(problems "")
    set(names_on_disk "")
    foreach(file IN LISTS on_disk)
        get_filename_component(name "${file}" NAME)
        list(APPEND names_on_disk "${name}")
        list(FIND built "${file}" built_at)
        list(FIND exempt_names "${name}" exempt_at)
        if(built_at EQUAL -1 AND exempt_at EQUAL -1)
            list(APPEND problems "${name} is in App/Src but not in the ${side} source list: add it there, or exempt it with the reason in cmake/app_source_exemptions.cmake")
        elseif(NOT built_at EQUAL -1 AND NOT exempt_at EQUAL -1)
            list(APPEND problems "${name} is built for ${side} but still exempted: remove it from cmake/app_source_exemptions.cmake")
        endif()
    endforeach()
    foreach(name IN LISTS exempt_names)
        list(FIND names_on_disk "${name}" on_disk_at)
        if(on_disk_at EQUAL -1)
            list(APPEND problems "${name} is exempted for ${side} but is not in App/Src: remove the exemption")
        endif()
    endforeach()
    set(${out} "${problems}" PARENT_SCOPE)
endfunction()

# Check the App/Src modules against the sources of the given targets.
#   side     "firmware" or "host tests"
#   ARGN     the targets that make up that side
# Only each target's own SOURCES are read. No App source reaches a target through a
# linked library (INTERFACE_SOURCES) today; if one ever does, read those here too.
function(arm_sensor_hub_check_app_sources side)
    set(app_src "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../App/Src")
    get_filename_component(app_src "${app_src}" ABSOLUTE)
    # App code is C by convention, but a C++ or assembly module left out of a list
    # would fail the same way, so they are checked too.
    file(GLOB on_disk CONFIGURE_DEPENDS
        "${app_src}/*.c" "${app_src}/*.cpp" "${app_src}/*.s" "${app_src}/*.S")

    set(built "")
    foreach(target IN LISTS ARGN)
        get_target_property(sources ${target} SOURCES)
        get_target_property(source_dir ${target} SOURCE_DIR)
        foreach(source IN LISTS sources)
            if(source MATCHES "^\\$<")
                continue()  # a generator expression, never an App/Src path here
            endif()
            get_filename_component(path "${source}" ABSOLUTE BASE_DIR "${source_dir}")
            list(APPEND built "${path}")
        endforeach()
    endforeach()

    if(side STREQUAL "firmware")
        set(exempt ${ARM_SENSOR_HUB_APP_NOT_IN_FIRMWARE})
    else()
        set(exempt ${ARM_SENSOR_HUB_APP_NOT_IN_HOST_TESTS})
    endif()

    arm_sensor_hub_app_source_problems(problems "${side}" "${on_disk}" "${built}" "${exempt}")
    if(problems)
        list(JOIN problems "\n  " text)
        message(FATAL_ERROR "App source list check (B54) failed for the ${side} build:\n  ${text}")
    endif()
    list(LENGTH on_disk count)
    message(STATUS "App source lists: all ${count} App/Src modules are in the ${side} build or exempted")
endfunction()
