# First Week Guide

## Goal

By the end of the first week, an intern should be able to:

- explain the purpose of the sensor hub,
- build the host tests,
- describe the major services,
- identify which parts of the system are fully implemented and which are still scaffolds,
- make a small safe documentation or test contribution.

## Day 1-2: Understand The Problem

Read in this order:

1. [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/OnboardingDocs/Project_Orientation.md`](Project_Orientation.md)
2. [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/README.md`](../../README.md)
3. [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/README.md`](../README.md)
4. [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/CONTRACT_STATUS.md`](../CONTRACT_STATUS.md)

Questions you should be able to answer:

- What data enters over I2C, CAN, and SPI?
- What does `DATA_READY` do?
- Why does the project use contracts so heavily?
- Which areas still need hardware validation?

## Day 2-3: Build And Run Existing Validation

Run:

```bash
cmake --preset HostTests
cmake --build --preset HostTests
ctest --preset HostTests
```

Then inspect `tests/host/protocol_test_main.c` and map each test area back to its production module.

## Day 3-4: Trace Runtime Flow

Read these files in order:

1. `Core/Src/main.c`
2. `App/Src/app_init.c`
3. `App/Src/sensor_task.c`
4. `App/Src/can_service.c`
5. `App/Src/spi_slave_service.c`

While reading, write down:

- what initializes each service,
- what runs every loop iteration,
- where timing metadata enters the system,
- where data is cached before it is sent to the host.

## Day 4-5: Make A Safe First Contribution

Good first tasks:

- clarify documentation,
- strengthen or extend host tests,
- improve a narrow validation path,
- trace one contract to its implementation and fix a mismatch.

Higher-risk tasks that usually need more supervision:

- HAL interrupt or DMA integration,
- CAN recovery behavior changes,
- SPI framing contract changes,
- changes that affect safety or activation gating.

## Working Style Expectations

- ask when a behavior is contract-approved but not clearly implemented,
- cite the file you used to support a claim,
- prefer small pull requests,
- keep documentation and implementation aligned.

## Quick Self-Check

You are ready for a small independent task when you can explain:

- why the firmware uses both C and C++,
- why host tests exist separately from target builds,
- what the lifecycle model protects,
- why a coherent snapshot matters before SPI transfer.

