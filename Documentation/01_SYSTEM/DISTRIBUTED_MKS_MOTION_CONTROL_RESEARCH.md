# Distributed Real-Time MKS Motion Control Research Note

**Status:** Research/design note; non-normative  
**Scope:** Six-axis MKS motor control over CAN, timestamped feedback, synchronized actuation, CAN arbitration/jitter, and experimental timing validation.

> This note records the proposed architecture and research direction. It does **not** establish new Karetao requirements or override the authoritative system timing, synchronization, CAN interface, MKS documentation, safety, or verification records. MKS controller semantics remain external authority.

## 1. Proposed architecture

The proposed six-axis controller is closer to a **time-triggered distributed control loop** than to a sequential CAN polling loop.

```text
                 Control cycle k
──────────────────────────────────────────────────────────

t0
│
├── Receive encoder M1 → timestamp T1
├── Receive encoder M2 → timestamp T2
├── ...
├── Receive encoder M6 → timestamp T6
│
├── State estimation / interpolation
│
├── Calculate M1 command
├── Calculate M2 command
├── ...
├── Calculate M6 command
│
├── Send M1 command with execution time Tk + Δ
├── Send M2 command with execution time Tk + Δ
├── ...
├── Send M6 command with execution time Tk + Δ
│
│          commands wait inside drives
│
│                    ┌── execution time
│                    │
└────────────────────┴───────────────────────
                     │
                     ▼
                  SYNC 4BH
                     │
                     ▼
              all motors execute
                     │
                     ▼
                  cycle k+1
```

The key distinction is:

> **CAN transmission time and physical control-action time need not be the same event.**

This is the property to investigate for the MKS command/synchronization mechanism.

## 2. Research areas

The literature review should be organized around:

| Topic | Relevance |
|---|---|
| **Time-triggered CAN / TTCAN** | Scheduled communication and deterministic timing |
| **CAN communication jitter** | Quantifying arbitration and latency uncertainty |
| **Distributed motion control over CAN** | Multi-axis coordination |
| **CANopen SYNC / PDO** | Established synchronous-drive architectural comparison |
| **Distributed clock synchronization** | Aligning controller and drive time bases |
| **Timestamped sensor/control systems** | Correcting measurement-time differences |

TTCAN is a particularly useful comparison because it explicitly separates a shared time base and scheduled transmission windows from purely event-triggered CAN arbitration.

## 3. Timestamped measurements

Timestamping encoder feedback when the frame reaches the CAN interface is useful, but the timestamp must be interpreted correctly:

$$
T_\text{RX} \neq T_\text{physical measurement}
$$

A useful timing chain is:

$$
T_\text{encoder}
\rightarrow
T_\text{MKS processing}
\rightarrow
T_\text{CAN transmission}
\rightarrow
T_\text{CAN RX}
$$

The measured controller timestamp is:

$$
T_\text{RX}
$$

while the associated physical state corresponds approximately to an earlier time:

$$
T_\text{state}\approx T_\text{RX}-\tau_\text{communication}
$$

This matters because the six encoder messages may arrive at different times.

The existing Karetao CAN contract already requires acquisition timestamps in the synchronized 64-bit monotonic time domain and stores synchronization quality with each motor's latest-value record. See `Documentation/02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md`.

## 4. Observation skew and state reconstruction

For a six-motor feedback burst such as:

```text
M1: 10.000 ms
M2: 10.072 ms
M3: 10.141 ms
M4: 10.209 ms
M5: 10.278 ms
M6: 10.347 ms
```

the raw state is more accurately represented as:

$$
X =
[
\theta_1(t_1),
\theta_2(t_2),
...,
\theta_6(t_6)
]
$$

rather than assuming:

$$
X =
[
\theta_1(t),
\theta_2(t),
...,
\theta_6(t)
]
$$

A common-time estimate at control time (t_c) can use a local motion model. For example, with position and velocity:

$$
\hat{\theta}_i(t_c)
=
\theta_i(t_i)
+
\hat{\omega}_i(t_i)(t_c-t_i)
$$

The applicability of this approximation depends on motion smoothness, estimator quality, and timestamp/communication uncertainty.

Karetao's current system timing documentation already calls out observation skew, acquisition timestamps, and the need to validate end-to-end availability and latency. This research note extends that timing discussion specifically to distributed six-axis MKS control.

## 5. Synchronous command execution

The proposed mechanism is:

```text
Host
 │
 ├── command M1
 ├── command M2
 ├── command M3
 ├── command M4
 ├── command M5
 ├── command M6
 │
 └── 4BH synchronization
      │
      ├── motor 1 executes
      ├── motor 2 executes
      ├── ...
      └── motor 6 executes
```

The hypothesis to validate against the exact MKS controller manual and hardware is that the motion commands can be **held pending synchronization**, with `4BH` acting as the synchronization execution event.

If that behavior is confirmed experimentally, the relevant actuation time becomes approximately:

$$
t_\text{actuation}\approx t_\text{SYNC}
$$

rather than:

$$
t_\text{actuation}=t_\text{CAN transmission}
$$

This would allow commands to be transmitted at different times while targeting a common actuation event.

**Important:** the exact MKS semantics must be verified for the selected controller model and firmware. This document does not treat that behavior as a Karetao normative requirement.

## 6. Comparison with CANopen and distributed clocks

CANopen provides a useful architectural comparison because the SYNC mechanism is designed for coordinated distributed devices.

A conceptual equivalent is:

```text
Master
  │
  ├── command motor 1
  ├── command motor 2
  ├── ...
  ├── command motor 6
  │
  └── SYNC
       │
       ├── motor 1 executes
       ├── motor 2 executes
       ├── ...
       └── motor 6 executes
```

More sophisticated distributed-clock systems also capture SYNC timing at the master and slave and use timestamp information to align device clocks.

That distinction is important:

### Proposed Karetao/MKS investigation

```text
Host clock
   │
   ├── timestamp RX encoder
   │
   ├── calculate commands
   │
   ├── schedule/queue commands
   │
   └── SYNC
```

### Full distributed-clock architecture

```text
Master clock
     │
     ├── SYNC ───────────────► Drive 1 clock
     │
     ├── SYNC ───────────────► Drive 2 clock
     │
     └── timestamp correction
              │
              ▼
        synchronized clocks
```

The latter can provide tighter timing guarantees because device clocks, rather than only bus events, participate in the timing model.

## 7. Future execution time

The most interesting part of the proposed architecture is a future execution point.

For example:

$$
t_k=10.000\,ms
$$

and:

$$
t_\text{execute}=12.000\,ms
$$

The host may transmit the six commands at:

```text
t = 10.1 ms   command M1
t = 10.2 ms   command M2
t = 10.3 ms   command M3
t = 10.4 ms   command M4
t = 10.5 ms   command M5
t = 10.6 ms   command M6

t = 12.0 ms   SYNC
```

The commands therefore spend different amounts of time queued/held before the common synchronization event.

The key experimental question is whether the MKS implementation provides sufficiently deterministic hold-and-release semantics that:

$$
t_{a,1}\approx t_{a,2}\approx...\approx t_{a,6}
$$

despite:

$$
t_{c,1}\neq t_{c,2}\neq...\neq t_{c,6}
$$

where (t_{c,i}) is the CAN command transmission time and (t_{a,i}) is effective physical actuation time.

## 8. Timing quantities to measure

At minimum, instrument the following quantities for each control cycle:

### Sensor timestamp

$$
t_{s,i}
$$

Time at which encoder frame (i) is received by the controller.

### Command transmission timestamp

$$
t_{c,i}
$$

Time at which command (i) enters CAN transmission.

### Synchronization timestamp

$$
t_{\text{sync}}
$$

Time at which the `4BH` synchronization frame is transmitted and, where observable, received.

### Effective actuation time

$$
t_{a,i}
$$

Time at which motor (i) actually applies the synchronized command.

Derived quantities include:

$$
\Delta t_\text{sample}
=
\max(t_{s,i})-\min(t_{s,i})
$$

$$
\Delta t_\text{command}
=
\max(t_{c,i})-\min(t_{c,i})
$$

and:

$$
J_\text{SYNC}
=
t_{\text{SYNC,actual}}-t_{\text{SYNC,target}}
$$

These measurements turn the CAN timing problem into an experimentally observable timing model rather than an assumption of synchronous behavior.

## 9. CAN arbitration and jitter

Classical CAN is priority/event-triggered. A high-priority message can delay a lower-priority frame, including a control command or synchronization frame.

A useful model is:

$$
t_\text{SYNC,actual}
=
t_\text{SYNC,intended}
+
J_\text{CAN}
$$

where (J_\text{CAN}) represents arbitration, queuing, processing, and other communication timing uncertainty.

For Karetao, this is likely more important than whether the host software issues "read then command motor 1" before processing the remaining motors. The system-level question is the resulting worst-case bus and actuation timing.

The existing CAN contract therefore provides a good starting point: the v1 nominal bitrate target is **1 Mbps**, the current polling period is **20 ms**, and the contract explicitly requires measured arbitration latency and worst-case load under realistic traffic before approval.

## 10. Proposed experimental architecture

```text
                    CONTROL LOOP k

       ┌───────────────────────────────────┐
       │       CAN receive subsystem       │
       │                                   │
       │ M1 encoder ──► timestamp          │
       │ M2 encoder ──► timestamp          │
       │ M3 encoder ──► timestamp          │
       │ M4 encoder ──► timestamp          │
       │ M5 encoder ──► timestamp          │
       │ M6 encoder ──► timestamp          │
       └────────────────┬──────────────────┘
                        │
                        ▼
              timestamped state buffer
                        │
                        ▼
                state estimation
                        │
                        ▼
                 control algorithm
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       command M1 ... M6       execution time
             │                     │
             └──────────┬──────────┘
                        ▼
                  CAN transmit
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
      M1               ...               M6
       │                                 │
       └────────── held pending ─────────┘
                        │
                        ▼
                     4BH SYNC
                        │
                        ▼
               simultaneous execution
```

This can be treated as:

> **sample → estimate → compute → schedule → synchronously actuate**

The first implementation should instrument this loop before optimizing it.

## 11. Recommended timing experiment

Do **not** initially try to force the six encoder readings to occur simultaneously.

Instead, record the actual arrival times:

$$
t_{M1},t_{M2},...,t_{M6}
$$

and determine:

$$
\Delta t_\text{sample}
=
\max(t_i)-\min(t_i)
$$

Then measure:

$$
\Delta t_\text{command}
=
\max(t_{c,i})-\min(t_{c,i})
$$

and:

$$
J_\text{SYNC}
=
t_{\text{SYNC,actual}}-t_{\text{SYNC,target}}
$$

Repeat under representative bus load and injected high-priority traffic so that arbitration effects become visible.

The experiment should also capture frame IDs, DLC, direction, queueing time, retry/failure state, and the selected controller's actual response/feedback timing.

## 12. Six-axis 1 Mbps timing model

The next detailed engineering step is a six-axis timing model at the approved/candidate **1 Mbps** bus rate, parameterized by:

- exact DLC of each encoder request/response;
- exact DLC of each selected motor command (`F6`, `FD`, `F4`, etc.);
- standard 11-bit CAN identifier;
- CAN arbitration order;
- CAN bit stuffing;
- CAN controller timestamp location;
- host processing and scheduling time;
- queueing time inside the MKS controller;
- `4BH` synchronization frame transmission time;
- expected synchronization loss/jitter;
- retry/error behavior;
- number of active motors and non-motion traffic.

The model should produce:

$$
T_\text{cycle}
=
T_\text{feedback}
+
T_\text{compute}
+
T_\text{command}
+
T_\text{sync}
+
T_\text{margin}
$$

and therefore an experimentally defensible upper bound on control-loop rate:

$$
f_\text{max}\lesssim\frac{1}{T_\text{cycle}}
$$

This should be used to assess candidate operating points such as **500 Hz** and **1 kHz**, rather than deriving feasibility from nominal frame-time estimates alone.

## 13. Relationship to current Karetao timing

The current Karetao system documentation establishes:

- baseline sensor/state publication and initial control-loop rate: **100 Hz**;
- current EKF operating rate: **500 Hz**, subject to downstream integration constraints;
- normal observation skew target: **<5 ms** with a **<1 ms** dynamic-joint target;
- retention of acquisition timestamps;
- synchronized STM32/Pi timestamp error target: **≤ ±1 ms**;
- TIME_SYNC nominal rate: **1 Hz**, configurable to **10 Hz**;
- invalid synchronization after **5 s** without an accepted update.

These remain authoritative. This research note does not convert the proposed MKS synchronous-actuation architecture into a requirement.

## 14. Open validation items

The following should remain explicit integration/verification gates:

1. Confirm the exact MKS controller model and firmware revision.
2. Confirm the documented semantics of queued/synchronous commands and `4BH`.
3. Measure encoder feedback timing and determine whether the feedback represents a sample time, transmit time, or another internal controller time.
4. Determine the actual host RX timestamp point and its uncertainty.
5. Measure CAN arbitration delay and worst-case queueing under representative load.
6. Determine the actual synchronized command-application event at the motor.
7. Quantify actuation skew across all six motors.
8. Measure behavior when a drive misses a synchronization command.
9. Validate synchronization repetition strategy under interference.
10. Feed the measured timing budget into the control-loop stability and estimator design.

## 15. Literature/reference directions

The literature review should prioritize:

- foundational **Time-Triggered CAN (TTCAN)** work;
- studies of **CAN communication latency and jitter** in closed-loop control;
- deterministic CAN scheduling and worst-case latency analysis;
- six-motor synchronous control over CAN/CANopen;
- CANopen SYNC/PDO coordinated motion;
- distributed-clock and SYNC timestamp mechanisms;
- timestamp-aware distributed sensor/control estimation.

Where a specific paper or vendor document is cited in future revisions, record the complete bibliographic reference and distinguish external evidence from Karetao requirements.

## 16. Design interpretation

The working architectural hypothesis is therefore:

```text
Timestamped feedback
        ↓
State reconstruction at a common control time
        ↓
Six-axis control computation
        ↓
Commands queued ahead of a common execution event
        ↓
CAN arbitration-aware scheduling
        ↓
4BH synchronization
        ↓
Common motor actuation event
```

The central performance quantity is not merely CAN bus utilization. It is the separation between:

$$
\text{communication timing}
$$

and:

$$
\text{effective actuation timing}
$$

and whether the latter remains sufficiently bounded for coordinated six-axis control.
