I've researched each of the 25 decisions from your `SYSTEM_DECISIONS_V1.md` document. Below is a comprehensive breakdown of what each decision means and the industry and academic best practices that can guide your choices.

---

### A. Timing & Performance

#### SD-01 — System Timing Requirements

**What it means:** This defines the fundamental operating rhythm of your system—how fast sensors are read, how often the Raspberry Pi receives updates, and how quickly the EKF and control loops run.

**Industry & Academic Practice:**
- **Control Loops:** A 100 Hz control loop is common for basic mobile robots, but high-performance systems (e.g., balancing robots, manipulators) often run at **1 kHz**.
- **Sensor Acquisition:** Often runs faster than the control loop to allow for filtering. The 100 Hz target you have is a solid starting point.
- **Latency:** For stable control, total latency (sensor → actuator) should be **under one control cycle**, ideally less than 1–2 ms.

**Recommendation:** Keep the 100 Hz target, but design the system to be capable of higher rates if needed.

---

#### SD-18 — Timestamp Accuracy

**What it means:** The required accuracy of timestamps applied to sensor data, critical for fusing data from different sources.

**Industry & Academic Practice:**
- For IMU/encoder fusion in EKFs, timestamp errors as low as **1–5 ms** can cause significant state estimation errors.
- **±1 ms** is often the minimum acceptable accuracy for dynamic robots.
- For high-speed applications, sub-millisecond accuracy is preferred.

**Recommendation:** Target **±1 ms** or better.

---

#### SD-19 — TIME_SYNC Frequency

**What it means:** How often the Pi sends time synchronization messages to correct drift in the STM32’s clock.

**Industry & Academic Practice:**
- For typical crystal oscillators (20–50 ppm), a clock can drift by 20–50 µs per second. A 1 Hz sync would keep error under ~1 ms.
- **1 Hz** is a common minimum. For high-accuracy applications, 10 Hz is used.

**Recommendation:** Use **1 Hz** as a baseline, increasing to 10 Hz if timestamp accuracy requirements are tight.

---

### B. Safety & Failure Policy

#### SD-02 — System-Wide Failure Classification

**What it means:** How different failures are categorized (Informational, Degraded, Fault, Safety-Critical) to determine the system's response.

**Industry & Academic Practice:**
- This is the foundation of functional safety, guided by standards like **ISO 13849** (Performance Levels) and **IEC 62061** (SIL - Safety Integrity Levels).
- Failures are classified by their severity and the required response to maintain safety.

**Recommendation:** Define a classification scheme that maps directly to safety standards, ensuring high-severity failures trigger immediate, safe actions.

---

#### SD-03 — Raspberry Pi Communication Loss

**What it means:** The robot's behavior if the Pi (the main controller) stops communicating.

**Industry & Academic Practice:**
- **Heartbeat/Watchdog:** A common practice is a heartbeat signal. If it's lost for a certain time (e.g., **500 ms**), an emergency stop is triggered.
- **Safety Policy:** The safest policy is to *not* hold the last command. Instead, command a **controlled stop** and then **disable motors**.

**Recommendation:** Implement a heartbeat with a timeout (e.g., 500 ms). On timeout, command a controlled stop and then disable motors.

---

#### SD-04 — Motor Feedback/Command Timeout

**What it means:** The timeout and response if a motor controller stops responding.

**Industry & Academic Practice:**
- Timeouts are typically set to **2–5x** the expected feedback period.
- After a timeout, the motor should be commanded to stop or disabled.
- Repeated timeouts indicate a fault.

**Recommendation:** Define a feedback period, a timeout (e.g., 5x period), and a number of consecutive failures (e.g., 3) before escalating to a fault.

---

#### SD-06 — CAN Bus Failure

**What it means:** How the system responds to a CAN bus-off event.

**Industry & Academic Practice:**
- CAN controllers automatically enter bus-off after excessive errors.
- Recovery requires the CPU to clear the `INIT` bit, after which the controller waits for **128 occurrences of 11 recessive bits (bus idle)** before re-joining.
- Systems often implement an **escalating delay** and a **fault-logging threshold**. After a certain number of bus-offs in a time window, a hard fault is reported.

**Recommendation:** Implement escalating delays for recovery attempts. After a set number of bus-offs (e.g., 3) in a short period, escalate to a system fault.

---

### C. CAN Network

#### SD-05 — CAN Network Requirements

**What it means:** The fundamental CAN network specifications, primarily the bitrate.

**Industry & Academic Practice:**
- **1 Mbps** is the maximum standard CAN bitrate and is widely used in robotics for motor controllers.
- **Bus Length:** At 1 Mbps, the maximum bus length is approximately **25 meters**.
- **Bus Load:** For a 1 Mbps CAN bus, sending a 20-byte position command to 20 motors at a 4 ms control cycle consumes about **0.8 Mbps (80% load)**, which is very high.

**Recommendation:** Target 1 Mbps if supported by your motor controllers. Be mindful of bus load and keep it under 50–60% for reliable operation.

---

### D. Mechanical & State-Estimation Architecture

#### SD-07 — Joint/Motor Mapping

**What it means:** Confirming the one-to-one relationship between a logical joint, its angle sensor, and its motor.

**Industry & Academic Practice:**
- This is a fundamental system architecture definition. It's usually one-to-one, but can be more complex (e.g., differential drives).
- The mapping must be deterministic and known to the control system.

**Recommendation:** Confirm the one-to-one mapping and that the transmission relationship (e.g., gear ratio) is fixed and known.

---

#### SD-08 — Motor/Joint Temporal Alignment

**What it means:** The maximum acceptable time difference between a joint angle measurement and its corresponding motor encoder measurement.

**Industry & Academic Practice:**
- **This is critical for EKF-based state estimation.** If the measurements are not time-aligned, the filter will fuse data from different points in time, leading to poor state estimates.
- For dynamic robots, misalignment of **>5-10 ms** can cause significant problems.

**Recommendation:** Target a maximum misalignment of **<5 ms**, ideally less than 1 ms.

---

#### SD-09 — Measurement History Ownership

**What it means:** Which system is responsible for storing historical sensor data.

**Industry & Academic Practice:**
- **State Estimation (EKF):** EKF implementations like `robot_localization` maintain their own **measurement queues** and **state histories** to handle delayed measurements and perform smoothing.
- **Best Practice:** The EKF (on the Pi) owns the historical buffer. The STM32 provides the latest state.

**Recommendation:** The Raspberry Pi/EKF should own the historical measurement buffer. The STM32 only needs to provide the latest coherent snapshot.

---

### E. Sensor Calibration

#### SD-10 — Calibration Ownership & SD-11 — Calibration Storage

**What it means:** Where calibration (e.g., zero offset) is computed and stored.

**Industry & Academic Practice:**
- **Ownership:** Calibration is often a complex, non-real-time process. It's typically performed on the **Raspberry Pi** (or a PC) and the resulting parameters (offsets, gains) are then stored and applied.
- **Storage:** Parameters are commonly stored in **non-volatile memory on the STM32** or on the **Pi's filesystem**. Storing them on the STM32 makes the sensor hub self-contained.

**Recommendation:** Perform calibration on the Pi, store the resulting parameters in STM32 flash, and apply them on the STM32. This makes the sensor hub self-contained.

---

#### SD-12 — Authoritative Angle Representation

**What it means:** The definitive angle format sent from the STM32 to the Pi.

**Industry & Academic Practice:**
- **Calibrated radians** is the standard for robotics and control systems.
- It's often best to send the **raw counts** alongside the calibrated angle for diagnostics.

**Recommendation:** Send the final, calibrated angle in **radians** as the authoritative representation, with raw counts as an optional diagnostic field.

---

### F. ROS 2 / Control Interface

#### SD-13 — Required Joint State & SD-14 — Required Command Interface

**What it means:** The data the Pi needs from the STM32 (state) and the commands the Pi sends to it.

**Industry & Academic Practice:**
- **`ros2_control`**: Standard hardware interfaces are **`position`**, **`velocity`**, and **`effort`**. A `joint_state_broadcaster` publishes these states.
- **Minimum State:** At a minimum, you need `position` and `velocity`. `Effort` is optional. Your `measurement_timestamp_us` is crucial.
- **Minimum Command:** You need to support at least one command type (position, velocity, or effort). `Enable/Disable` is also mandatory for safety.

**Recommendation:** Expose `position`, `velocity`, and `timestamp` states. Support `position` and `velocity` commands, along with `enable`/`disable`.

---

### G. SPI Protocol Policy

#### SD-15 — Fixed SPI Transaction & SD-17 — SPI Host Transaction Strategy

**What it means:** The physical length of an SPI transaction (SD-15) and how the Pi initiates them (SD-17).

**Industry & Academic Practice:**
- **Fixed Length:** A fixed 512-byte transaction is a common and robust choice for SPI slaves. Some SPI slaves have **hardware limits of 512 bytes**. It makes DMA configuration deterministic and simpler.
- **Transaction Strategy:** A **hybrid approach** is best: Use a GPIO interrupt on the rising edge of `DATA_READY` for low-latency notification, and also have a **periodic poll** (e.g., every 1 ms) as a backup.

**Recommendation:** Approve the fixed 512-byte transaction. Implement a hybrid strategy: use a `DATA_READY` interrupt and periodic polling.

---

#### SD-16 — GET_SNAPSHOT Priority

**What it means:** Whether a specific request for a snapshot should override an asynchronous (unsolicited) one.

**Industry & Academic Practice:**
- It's standard practice for **explicit requests to take priority** over asynchronous data.
- **Your proposed policy is excellent.** It protects a DMA-active response and prioritizes a correlated request-response.

**Recommendation:** Approve the proposed policy.

---

### H. Time Synchronization & Validity

#### SD-20 — Loss of Time Synchronization

**What it means:** The system's behavior if TIME_SYNC messages stop arriving.

**Industry & Academic Practice:**
- For safety, **never present stale data as valid**. The system should mark timestamps as `UNSYNCHRONIZED`.
- The system should continue operating, but the EKF should be aware of the degraded timestamp quality.

**Recommendation:** Mark timestamps as `UNSYNCHRONIZED` but continue operating. Escalate to a fault only if synchronization loss is prolonged.

---

#### SD-21 — Time Offset Validation

**What it means:** Rejecting implausible changes in the time offset.

**Industry & Academic Practice:**
- This is a **sanity check**. A sudden large jump indicates an error.
- The proposed two-stage policy (wide initial, narrow subsequent) is standard.

**Recommendation:** Approve the two-stage policy. Set the subsequent limit to a configurable value (e.g., ±1 second).

---

#### SD-22 — Time Behaviour After Reset

**What it means:** The state of time synchronization after an STM32 reset.

**Industry & Academic Practice:**
- It's standard that after a reset, the local clock starts a new epoch and **synchronization is invalid** until a new TIME_SYNC is received.
- This must be explicitly handled to prevent the system from using a stale, incorrect offset.

**Recommendation:** Approve the policy: after reset, `TIME_SYNC_VALID = false`. All timestamps are marked `UNSYNCHRONIZED` until a new sync is received.

---

### I. Recovery & Lifecycle

#### SD-23 — Transient vs Persistent Fault Recovery

**What it means:** The strategy for handling temporary vs. permanent faults.

**Industry & Academic Practice:**
- **Transient faults** (e.g., a single I2C NACK) are handled with bounded retries.
- **Persistent faults** (e.g., 3 consecutive retry failures) escalate to a service `ERROR` state.
- Recovery from `ERROR` should return to `INACTIVE`, requiring explicit reactivation.

**Recommendation:** Approve this pattern.

---

#### SD-24 — System Restart and Recovery Behaviour

**What it means:** The system's behavior after a reset or recovery.

**Industry & Academic Practice:**
- Returning to `INACTIVE` after recovery is the safe default. It prevents a system from automatically re-entering a state that might have caused the fault.

**Recommendation:** Return to `INACTIVE` after recovery, requiring explicit activation.

---

### J. Independent Safety Architecture

#### SD-25 — Independent Safety Mechanisms

**What it means:** Confirming the existence of safety mechanisms outside the STM32/Pi software.

**Industry & Academic Practice:**
- This is a critical question. A software-only safety architecture is often insufficient.
- Hardware watchdogs, motor-disable signals, and emergency stop circuits are essential for a safe robot.

**Recommendation:** Document all independent safety mechanisms. This information is crucial for defining the correct software fault response.