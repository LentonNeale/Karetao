# Error Handling and Escalation Strategy

**Status:** System policy draft  
**Owner:** Application/system coordinator and HealthMonitor  
**Boundary:** Service faults -> lifecycle state -> diagnostics/host

## Firmware Response Levels

- **INFORMATIONAL:** report an event; no output inhibit is required.
- **DEGRADED:** preserve bounded operation with explicit validity/quality reporting; the owning service retains recovery responsibility.
- **FAULT:** inhibit the affected normal output or operation and escalate through lifecycle recovery.
- **SAFETY_CRITICAL:** immediately inhibit motion/outputs through the defined safety response and enter the required lifecycle fault path.

These are firmware response levels, not a PL/SIL mapping or a formal machine safety rating. The machine risk assessment and independent safety validation determine formal PL/SIL requirements.

## Fault Classes

- **Transient:** expected to recover locally, such as one timeout or temporary busy result. Retry within the service budget.
- **Persistent:** repeated or sustained failure that makes normal operation unreliable. Escalate the owning service to lifecycle `ERROR` or degrade the affected channel.
- **Fatal:** unsafe system condition requiring motor inhibition, safe shutdown, or a controlled halt.
- **Configuration:** invalid parameters or unavailable dependencies. Do not activate the dependent service.

Every fault record should identify subsystem, operation, code, timestamp, occurrence count, and lifecycle state.

Fault timestamps use the shared 64-bit monotonic time extension. A Pi-synchronized timestamp is valid only when the last accepted TIME_SYNC update is no older than five seconds; otherwise the record carries an unsynchronized quality indication.

After TIME_SYNC validity expires, acquisition and diagnostics continue, but time-dependent motion commands are rejected or inhibited until a new accepted update restores synchronization. Reset and recovery leave services `INACTIVE`; motion requires explicit reactivation after prerequisites pass.

## Ownership

The service that detects a fault owns local retry and recovery. The lifecycle owner decides state transition. HealthMonitor aggregates and reports; it must not silently recover a service unless a future contract explicitly grants that authority.

ISR callbacks set minimal pending flags/counters and defer classification, lifecycle mutation, and recovery to task context.

## Escalation

Initial policy:

1. classify the returned status;
2. perform the service-local retry budget;
3. reset consecutive-failure count after success;
4. enter `ERROR` after persistent threshold or any unsafe condition;
5. recover to `INACTIVE` after verified recovery;
6. require explicit activation afterward.

Thresholds and retry delays remain per-service contract decisions and must not be invented globally.

## Safety

- CAN not `ACTIVE`: inhibit normal motor commands.
- Sensor not `ACTIVE`: publish records as invalid/stale.
- SPI not `ACTIVE`: DATA_READY low and no normal publication.
- Any motor safety fault: inhibit motion and preserve emergency-stop policy.
- Shutdown: stop normal outputs, preserve diagnostics, and leave hardware safe.

## Reporting

Diagnostics should be available internally first, then through SPI `DIAGNOSTIC`/`EVENT` messages when the transport is operational. A fault must not be cleared merely because it is no longer visible; recovery and clear semantics must be explicit.

## Open Decisions

- numeric fault-code registry;
- retry and escalation thresholds per service;
- automatic versus operator-requested recovery;
- watchdog ownership;
- persistent fault history size;
- host acknowledgement/clear semantics.
- independent safety validation and machine risk assessment for energized-motion release.
