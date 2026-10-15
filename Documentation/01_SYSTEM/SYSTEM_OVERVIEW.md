# System Overview

Scope authority is the [project charter](PROJECT_CHARTER.md).

## Purpose

Karetao is a hobby-level robotic arm platform, built and maintained by one person. It aims for good engineering practice (traceability, recorded decisions, evidence before done) at a size one person can keep up.

## The three parts

- **STM32F405 Arm Sensor Hub:** reads AS5600 joint encoders through a TCA9548A I2C mux, polls the MKS drives over CAN, and serves snapshots to the Pi over SPI as slave.
- **MKS SERVO42D/57D drives and their stepper motors:** each drive is a closed-loop board mounted on its motor and addressed on the CAN bus.
- **Raspberry Pi host:** SPI master and system time authority. It owns the Pi-side ClockSync model, sends single gated commands, and runs the evidence tools.

## Vocabulary

The terms the system documents use for the arm's parts, defined once here (Lenton Neale, 2026-10-15). Component documents and code may keep their own identifiers, but they mean these.

| Term | Meaning | Not the same as |
|---|---|---|
| **Joint** | A physical articulation of the arm with one degree of freedom. Named by the Arctos V2 convention: Joint X, Joint Y, Joint Z, Wrist Joint 1, Wrist Joint 2, Wrist Joint 3. Role names (Base, Shoulder, Elbow, Wrist 1 to 3) are descriptive aliases, not identifiers. | An axis. For the wrist's two coupled motor shafts (SD-26, deferred) they differ. |
| **Axis** | A numbered measurement slot, 0 to 5, in the sensor topology and the snapshot: one shaft that may carry a joint encoder and one motor. The commissioning table ([`SYSTEM_CONFIGURATION.md`](../06_CONFIGURATION/SYSTEM_CONFIGURATION.md) §2.1) is indexed by axis. For axes 0 to 3 the axis is the joint of the same name. Axes 4 and 5 are the two differential motor shafts; their "Wrist Joint 2" and "Wrist Joint 3" labels are axis labels, and the joints those shafts form are deferred (SD-26). | A joint. The mapping record's `logical_joint_id` is the axis number; the field name predates this definition. |
| **Motor** | The stepper motor on an axis: frame, phases and shaft. Identified by motor index. | The drive mounted on it. |
| **Drive** | The MKS SERVO42D or SERVO57D closed-loop board mounted on a motor. It owns the CAN ID, the work mode, the home and limit switch inputs, and its own shaft encoder. Registration, commands, feedback and the snapshot's motor record are exchanges with the drive about its motor. | The motor. Protocol and code names (`motor_index`, `RegisterMotor`, "motor record") address the drive and motor pair by motor index. |
| **Joint encoder** | The AS5600 the hub reads over I2C through the mux. "Encoder fitted" in the commissioning table means this one. | The drive's own encoder, whose reading is the motor shaft position. |
| **Servo** | Appears only inside the product names SERVO42D and SERVO57D. The gripper's jaw actuator (a charter non-goal) is a hobby servo and is called the gripper servo. | |

Two scenarios that show why the split matters. If the wrist is moved so that only one of its joints changes, both motors on axes 4 and 5 can turn, so both axes change while one joint moved; what those joints are is deferred (SD-26). If a drive board fails and is replaced on the same motor, the motor is unchanged but the CAN ID and work mode are set again on the new drive.

### Data from the arm to the host

The words for the data path from an acquisition to the Pi, in pipeline order (Lenton Neale, 2026-10-15). The contracts that define each one are linked; this table only fixes the names.

| Term | Meaning | Not the same as |
|---|---|---|
| **Sample** | One acquisition from one joint encoder, with its acquisition timestamp. "Reading" in prose means a sample. | A record: one sample can appear in many snapshots. |
| **Feedback** | The drive's report of its motor's shaft position and state over CAN. | A sample: feedback comes from the drive's own encoder, not from a joint encoder. |
| **Latest value** | The per-axis and per-motor store holding the most recent sample or feedback with its freshness (valid, invalid, not fitted, stale). The CAN contract's "cache" is this store. | A snapshot: the latest value is live state; a snapshot is a copy taken at build time. |
| **Record** | One entry in a snapshot: a sensor record or a motor record ([`SPI_PAYLOAD_SCHEMA.md`](../02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md)). Other records (mapping record, calibration record, the Pi's transaction record) are always qualified. | |
| **Snapshot** | The SNAPSHOT message: every record copied from the latest values together, so the set is coherent ([`SPI_SYSTEM_INTERFACE.md`](../02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md) §8). Coherent does not mean simultaneous or fresh; each record carries its own timestamp and freshness. | A frame: the snapshot is content, the frame is its container. |
| **Message** | The typed content one frame carries: SNAPSHOT, DIAGNOSTIC, ACK, GET_SNAPSHOT and the others in the SPI contract §5. One frame carries exactly one message. | |
| **SPI frame** | The wire container: header, payload and CRC ([`SPI_SYSTEM_INTERFACE.md`](../02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md) §3). Always written "SPI frame" or "CAN frame" where the bus is not obvious. | A CAN frame, the bus unit of the MKS protocol. The firmware's `SnapshotFrame_Pool` stages every response frame, not only snapshots; the name predates this definition. |
| **Transaction** | One clocked 512-byte full-duplex SPI operation: the Pi sends one request frame and receives the response frame staged before it (SPI contract §4). | An exchange. |
| **Transfer** | The same clocking seen from the bus and the DMA: what the Pi's bus layer transfers and the STM32's DMA transfer arms. | |
| **Exchange** | A request and its correlated response. Because the protocol is pipelined, the response to a request arrives in the following transaction, so an exchange spans two transactions. An unsolicited snapshot belongs to no exchange. The clock-sync model records exchanges. | A transaction. |
| **Publish** | To make a snapshot available to the Pi: stage it as the unsolicited response, arm its DMA transfer and assert DATA_READY (SPI contract §7). | |
| **DATA_READY** | The STM32-to-Pi line that is high while a complete response frame is armed for DMA (SPI contract §7). | |

A scenario: the Pi sends GET_SNAPSHOT with sequence 7. That transaction returns whatever response was staged earlier; the reply to 7 comes in the next transaction. The Pi's timing record for one transaction therefore holds a request and an unrelated response, and the exchange for sequence 7 is stitched back together from the correlated sequence.

### Time and clock sync

Two designs share this vocabulary: the as-built one-way TIME_SYNC that the code still runs, and the target clock sync decided in [Issue #12](../07_DECISIONS/ISSUE_12_CLOCK_SYNCHRONIZATION_DECISIONS.md). The rule (Lenton Neale, 2026-10-15): an unqualified term below means the target design; the as-built mechanism is always named as such.

| Term | Meaning | Not the same as |
|---|---|---|
| **TIME_SYNC** | Only the deprecated message (0x12) and the as-built mechanism built on it: the STM32-held offset, the STM32 sync flag and the legacy step bounds (PRM-TS-05). Retired with Issue #12. | Clock sync. |
| **Clock sync** | The target design: the STM32 does no clock math, every applicable response is an observation, and the Pi converts ([`TIME_SYSTEM_INTERFACE.md`](../02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md)). "Synchronization" on its own means this. | |
| **ClockSync** | The Pi-side model that accepts observations and estimates offset and frequency. It is the single acceptance policy, and `ClockSync.is_valid()` is sync validity. | The STM32 sync flag, which belongs to TIME_SYNC. |
| **Observation** | One clock-sync measurement from one exchange: the Pi's send time, the STM32's request-receipt time (`request_received_local_us`) and the Pi's receive time. | An acquisition. PRM-TS-02's title still says "observation" for an acquisition; it means spread (below). |
| **Offset** and **frequency** | ClockSync's estimates of the difference between the two time domains and of its rate of change. The as-built value is the **STM32-held offset**, always so named. | "Drift", which survives only in the name of the legacy step check. |
| **Slew** | Bending a clock gradually to absorb an observation. ClockSync never does this silently; implausible observations are rejected. | |
| **STM32 local time** | The STM32's monotonic clock, never adjusted. **Pi time** is the system time authority's domain. | |
| **Acquisition timestamp** | The STM32 local instant a sample or feedback was taken. On the wire it is the record's `measurement_timestamp_us`. | The synchronized timestamp. |
| **Synchronized timestamp** | The acquisition timestamp converted into Pi time by ClockSync; marked UNSYNCHRONIZED while ClockSync is invalid. The time contract uses the wire field's name for this value too. | |
| **Spread** | The range of acquisition timestamps within one snapshot, judged against the **sweep** time (PRM-ACQ-02). "Skew" in SYS-TS-001 and PRM-TS-02 means this. | **Sync skew**, the charter's word for the timestamp conversion error (PRM-TS-01). |
| **`link_stale`** | STM32-side SPI liveness. It gates motion permission and is independent of sync validity. | Sync validity, which governs timestamp usability on the Pi. |

### Lifecycle, gating and faults

The lifecycle states, response levels and fault classes are defined in [`SYSTEM_LIFECYCLE.md`](SYSTEM_LIFECYCLE.md); the motion gate in SYS-GATE-001 ([`ARCHITECTURE_DECISIONS.md`](../07_DECISIONS/ARCHITECTURE_DECISIONS.md)). This table fixes the words around them (Lenton Neale, 2026-10-15).

| Term | Meaning | Not the same as |
|---|---|---|
| **Motion gate** | The predicate in SYS-GATE-001: lifecycle ACTIVE, CAN ACTIVE, link not stale, no global motion inhibit, motor ready. "The gate" on its own means this. **Motion permission** is its output: permitted, or a reason code. `motion_permission.c` implements it. | **Gate A** and **Gate B**, the clock-sync validation gates, and the Portal's process gates, which are always named. |
| **Single gated command** | One SET_MOTOR_COMMAND for one motor, accepted or refused by the motion gate (SD-14, SYS-CMD-001). A command that starts several joints together is still one. | Time-dependent motion, of which none exists in the current scope. |
| **Fail closed** | When any gate input is lost the gate turns false: new commands are rejected, a controlled stop follows, then disable. | |
| **Global motion inhibit** | The gate input set by bus-off escalation or a host command. It latches and is cleared only by system-activate (R20). | "Inhibit" as a verb, which the lifecycle document uses for any suppressed output. |
| **Motor ready** | Registered, an ENABLE accepted since the last disable or reset, and no drive fault (R20). | |
| **Latched** | A condition that stays set after its cause has cleared until an explicit action clears it. | |
| **Fault** | A detected failure condition that gets a fault record and a response level. **FAULT** is one of the four response levels. **ERROR** is the lifecycle state. | **Error**: one failed operation (a CRC mismatch, an I2C timeout), counted in diagnostics, which becomes a fault only when its owning service classifies it. |
| **Health level** | The health monitor's summary for the operator: GREEN, YELLOW, RED, UNKNOWN. YELLOW means a fault since boot not yet cleared; only system-activate clears it (R27, pending in the code). | **Response level** (INFORMATIONAL, DEGRADED, FAULT, SAFETY_CRITICAL), which is per fault. |
| **Retry** | Repeating an operation within the owning service's budget after a transient fault. | Recovery. |
| **Recovery** | The lifecycle transition from ERROR to INACTIVE after a bounded attempt. It never resumes motion. Transport self-healing is always qualified: **bus-off recovery**, **poll recovery**. | Reactivation. |
| **Reactivation** | The explicit, dependency-ordered step from INACTIVE to ACTIVE, requested through **system-activate** (R19). | |
| **Stale** | No accepted input within the freshness window. **Link stale** (`link_stale`) is SPI liveness and a gate input. A **stale record** is a latest value past its window and is diagnostic. | |
| **E-stop** | The hardware power cut an operator can reach (SAFE-01). Hardware only; no software stop is an E-stop. | The MKS F7H command, which the vendor calls emergency stop and the firmware's `CanService_SendEmergencyStop` sends; here it is the fallback stop. |
| **Controlled stop** | The running command's own stop form (R21): a position move stopped with its speed set to zero, a velocity move likewise. The STOP command and the link-loss sequence use it. | The **fallback stop**, F7H, used only when a controlled stop is refused or unanswered. |

A scenario through the whole chain: CAN goes bus-off. The peripheral's bus-off recovery runs on its own; the CAN service retries with escalating delay; at the PRM-CAN-08 threshold it escalates to ERROR and sets global motion inhibit; recovery returns the service to INACTIVE; nothing moves until system-activate reactivates it, which also clears the inhibit, and each motor is then enabled again.



## Interfaces

- **SPI:** fixed frames, CRC-32, and a DATA_READY line. See [SPI](../02_INTERFACES/SPI/SPI_SYSTEM_INTERFACE.md) and [payload schema](../02_INTERFACES/SPI/SPI_PAYLOAD_SCHEMA.md).
- **CAN:** the MKS protocol. See [CAN](../02_INTERFACES/CAN/CAN_SYSTEM_INTERFACE.md).
- **Clock sync:** every SPI exchange is an observation, and the Pi does the conversion. The target design is Issue #12. See [TIME](../02_INTERFACES/TIME/TIME_SYSTEM_INTERFACE.md).
- **Lifecycle:** UNCONFIGURED, INACTIVE, ACTIVE, ERROR.
- **Host:** see [HOST](../02_INTERFACES/HOST/HOST_SYSTEM_INTERFACE.md). All interface documents are listed in [00_INDEX.md](../00_INDEX.md).

## Current status (as built, 2026-10-03)

Exists in code:
- SPI framing on both sides, with tests.
- STM32 SPI3 DMA path with DATA_READY.
- Six-axis encoder sweep (measured about 46 ms on 2026-09-17).
- CAN service polling scaffold, with one motor registered.
- Calibration record and joint-mapping models.
- Lifecycle and health monitor.
- A motion-permission module.

Not yet:
- The Issue #12 clock-sync redesign (the code still runs the older one-way TIME_SYNC).
- The DIAGNOSTIC message.
- The SET_MOTOR_COMMAND path.
- Six motors registered.
- A "not fitted" sensor state.

## Future, not now

These are charter non-goals for now and are named only here: ROS 2 integration, a state estimator, the differential end effector, trajectory or motion planning, and the gripper (jaw servo, and an Arduino Nano with an MCP2515 that turns CAN commands into jaw movements, likely on a separate CAN bus from the STM32), and a custom carrier PCB for the STM32F405 and a Raspberry Pi Compute Module 5, developed after the prototype hardware is signed off.
