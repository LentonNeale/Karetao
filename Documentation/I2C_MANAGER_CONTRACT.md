# I2C Manager Contract

**Status:** Pre-freeze approval baseline  
**Owner:** `I2CManager`  
**Boundary:** Application I2C users -> I2C1 HAL

## Responsibilities

`I2CManager` owns I2C1 transfer serialization, timeout handling, HAL status mapping, asynchronous completion signaling, timestamps, and bus error diagnostics. TCA9548A and AS5600 own device-specific register protocols, not I2C peripheral policy.

## Lifecycle

- `UNCONFIGURED`: static mutex/timing resources are unavailable.
- `INACTIVE`: resources are configured but transfers are inhibited.
- `ACTIVE`: transfers are permitted.
- `ERROR`: persistent bus or resource failure requires recovery.

`I2CManager_Init()` configures resources; `I2CManager_Activate()` permits transfers. Internal states `UNINITIALIZED`, `IDLE`, `BUSY_TX`, `BUSY_RX`, and `ERROR` remain implementation states.

## Public API Rules

Defined in `App/Inc/i2c_manager.h`:

- Addresses are seven-bit addresses; the manager performs HAL address shifting.
- Blocking operations reject null buffers and zero lengths.
- Blocking operations return only after HAL completion or timeout.
- `I2CManager_SubmitAsync()` copies the transfer descriptor but not the caller buffer or context.
- Async buffers and context must remain valid until completion/error callback.
- `I2CManager_Process()` commits deferred lifecycle faults from task context.

`MasterWriteRead()` currently performs a write followed by a read through two manager calls. It must not be described as an atomic repeated-start transaction until the HAL implementation is changed and verified.

## Concurrency and RTOS

- A static mutex serializes transfers.
- The mutex is held for the HAL operation and must not be held across arbitrary callbacks or application processing.
- Blocking APIs are task-context only.
- HAL callbacks are ISR-context and may signal events, release synchronization, and set pending fault data only.
- Lifecycle mutation, recovery, and user callbacks that can block are deferred to task context.
- No I2C API is ISR-safe in the current implementation.

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

Mux selection and the AS5600 transaction must be serialized as one logical operation. From the application contract, `select channel + sensor transaction` is one I2C ownership window. A task must not select a mux channel and then allow another task to select a different channel before the sensor transaction completes. The current manager API does not yet provide this composite operation; it must be added or the sensor task must be the sole owner of the complete sequence before multi-task sensor access.

## Diagnostics

Required counters include successful transfers, errors, timeouts, busy rejections, async aborts, and bus recovery attempts. Diagnostics must include the last HAL error and timestamp. Counters are read-only to application callers.

Diagnostic timestamps use the shared 64-bit monotonic time extension derived from TIM2. The raw 32-bit counter must not be exposed as the system timestamp.

## Verification

Test invalid arguments, lifecycle gating, mutex contention, timeout mapping, callback ordering, ISR-to-task fault handoff, mux transaction atomicity, and recovery from a stuck bus.
