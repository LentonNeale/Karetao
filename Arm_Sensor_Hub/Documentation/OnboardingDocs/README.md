# Intern Onboarding Docs

This folder collects the fastest path for undergraduate interns to understand the Arm Sensor Hub subtree while using the monorepo root `docs/` tree as the shared source of truth.

## Recommended Reading Order

1. [Project Orientation](Project_Orientation.md)
2. [Monorepo development guide](../../../docs/development.md)
3. [Monorepo architecture guide](../../../docs/architecture.md)
4. [First Week Guide](First_Week_Guide.md)
5. ARM-specific references in [`../`](..)

## Before You Change Code

- Read the project snapshot in [`../../../docs/hardware/arm-sensor-hub-baseline.md`](../../../docs/hardware/arm-sensor-hub-baseline.md).
- Read the contract status matrix in [`../CONTRACT_STATUS.md`](../CONTRACT_STATUS.md).
- Prefer host tests first when touching protocol, serialization, timestamp, or snapshot code.
