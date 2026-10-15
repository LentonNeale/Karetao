Origin: backlog story B134 (WP9, "S9.15 Check the main (interrupt) stack depth at build time")

## Context

`tools/stack_depth.py` checks the task stacks after every build but not the main stack (MSP), which every interrupt handler and nested interrupt uses. An interrupt-side overflow could pass unnoticed. Found in the 2026-10-15 STM32 configuration review.

## Scope

Extend `Arm_Sensor_Hub/tools/stack_depth.py` and its config. Not covered: changing any stack size without first knowing why it is short (`CLAUDE.md`, stack check upkeep).

## Acceptance Criteria

- [ ] The deepest path of each enabled exception and IRQ handler (vector table in `startup_stm32f405xx.s`, `stm32f4xx_it.c`) is combined across NVIC preemption levels, one handler per level, plus the exception frame each level pushes
- [ ] The main stack size comes from `_Min_Stack_Size` in `STM32F405xx_FLASH.ld`, and the pre-scheduler path from `main()` is checked against it
- [ ] Handler priorities are read from the generated code or the `.ioc`, not restated, and a handler whose priority cannot be read fails the check
- [ ] Function-pointer calls in HAL IRQ handlers are resolved through `stack_depth.cfg` with site counts, as for tasks
- [ ] The Debug and Release builds report the main-stack headroom in `stack_depth.txt`
- [ ] HostTests, the Debug build and the Pi tests pass; `doc_check` is clean

## Verification / Evidence

Host tests for the nesting arithmetic (`Arm_Sensor_Hub/tests/tools/test_stack_depth.py`) and the headroom line in both build outputs.

## References

- `Arm_Sensor_Hub/Documentation/BUILD_CONTRACT.md` (Task stack check)
