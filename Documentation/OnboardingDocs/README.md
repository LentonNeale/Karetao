# Intern Onboarding Docs

This folder collects the fastest path for undergraduate interns to understand the Arm Sensor Hub repository, set up a development environment, and make safe early contributions.

## Recommended Reading Order

1. [Project Orientation](Project_Orientation.md)
2. [Development Setup and Workflow](Development_Setup_and_Workflow.md)
3. [Architecture and Runtime Flow](Architecture_and_Runtime_Flow.md)
4. [First Week Guide](First_Week_Guide.md)
5. Core engineering references in [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation`](..)

## What These Docs Assume

- You are comfortable with basic C programming.
- You have limited or no prior STM32, FreeRTOS, or embedded systems experience.
- You need to understand both the current implementation and the important unfinished areas.

## Before You Change Code

- Read the project snapshot in [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/README.md`](../../README.md).
- Read the contract status matrix in [`/home/runner/work/Arm_Sensor_Hub/Arm_Sensor_Hub/Documentation/CONTRACT_STATUS.md`](../CONTRACT_STATUS.md).
- Prefer host tests first when touching protocol, serialization, timestamp, or snapshot code.

