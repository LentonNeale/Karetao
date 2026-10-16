# I2C Manager Contract

**Status:** Pre-freeze approval baseline  
**Owner:** `I2CManager`  
**Boundary:** Application I2C users -> I2C1 HAL

## Responsibilities

`I2CManager` owns I2C1 transfer serialization, timeout handling, HAL status mapping, and bus error diagnostics. TCA9548A and AS5600 own device-specific register protocols, not I2C peripheral policy.

## Lifecycle

- `UNCONFIGURED`: static mutex/timing resources are unavailable.
- `INACTIVE`: resources are configured but transfers are inhibited.
- `ACTIVE`: transfers are permitted.
- `ERROR`: persistent bus or resource failure requires recovery.

`I2CManager_Init()` configures resources; `I2CManager_Activate()` permits transfers. Internal states `UNINITIALIZED`, `IDLE`, `BUSY_TX`, `BUSY_RX`, and `ERROR` remain implementation states. As built, lifecycle `ERROR` is entered only when the static mutex cannot be created at `Init()`; a failed transfer is counted and reported to the caller but does not change the lifecycle state. Escalation to `ERROR` on repeated bus faults is part of the open policy below.

## Public API Rules

Defined in `App/Inc/i2c_manager.h`:

- Addresses are seven-bit addresses; the manager performs HAL address shifting.
- Blocking operations reject null buffers and zero lengths.
- Blocking operations return only after HAL completion or timeout.
- `I2CManager_WriteThenWriteRead()` performs two writes followed by a read while holding the manager mutex for the full ownership window; it is the current composite path used for mux-select plus AS5600 register access.

`MasterWriteRead()` currently performs a write followed by a read while retaining manager ownership, but it is not an atomic repeated-start transaction and must not be described as one until the HAL implementation is changed and verified.

## Concurrency and RTOS

- A static mutex serializes transfers.
- The mutex is held for the HAL operation and must not be held across arbitrary callbacks or application processing.
- All APIs are blocking, polled HAL transfers in task context. The I2C1 interrupts are not enabled and the module defines no HAL I2C callback.
- No I2C API is ISR-safe.
- A FreeRTOS mutex held by a task cannot be given from an interrupt (`xQueueGiveFromISR` asserts the holder is NULL). The earlier asynchronous path did exactly that and was removed (#77). An interrupt-driven design, if one is ever built, must signal completion with a binary semaphore or a task notification and keep mutex ownership in task context.

## Timeout and Error Policy

Current status values are `OK`, `ERROR`, `BUSY`, `TIMEOUT`, `BAD_ARG`, and `NOT_READY`. The implementation does not yet define retry counts, backoff, NACK-specific classification, or bus-lock recovery.

Before production approval, define:

- per-transfer and total-operation timeout;
- retryable HAL errors and maximum attempts;
- retry delay/backoff;
- NACK and arbitration-loss classification;
- SDA/SCL stuck detection and GPIO recovery sequence;
- escalation threshold to lifecycle `ERROR`;
- recovery target state and whether explicit activation is required afterward.

## TCA9548A Coordination

Mux selection and the AS5600 transaction must be serialized as one logical operation. From the application contract, `select channel + sensor transaction` is one I2C ownership window. A task must not select a mux channel and then allow another task to select a different channel before the sensor transaction completes. The current implementation provides this ownership window through `TCA9548A_SelectChannelWriteRead()` on top of `I2CManager_WriteThenWriteRead()` for the AS5600 path. Broader multi-device composite arbitration is still an open design area.

## Diagnostics

Required counters include successful transfers, errors, timeouts, busy rejections, and bus recovery attempts. Diagnostics must include the last HAL error and timestamp. Counters are read-only to application callers. As built, only the success, error and timeout counters exist; the busy and recovery counters and the last-error record are not yet implemented.

Diagnostic timestamps use the shared 64-bit monotonic time extension derived from TIM2. The raw 32-bit counter must not be exposed as the system timestamp.

## Verification

Test invalid arguments, lifecycle gating, mutex contention, timeout mapping, mux transaction atomicity, and recovery from a stuck bus.
