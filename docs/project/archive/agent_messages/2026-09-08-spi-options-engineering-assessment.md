# SPI Options Engineering Assessment for Initial Driver Design

Date: 2026-09-08
Status: Final report for systems engineering review
Scope: STM32 sensor hub → Raspberry Pi SPI path, DMA strategy, CPU impact, and integration evidence requirements

---

1. Executive Summary

The repository documents a clear architectural direction: STM32 acts as SPI3 slave using DMA, Raspberry Pi acts as SPI master, with a pipelined request/response protocol, 512‑byte maximum frame size, and an initial 5 MHz clock gate. The SPI service contract already separates DMA callbacks from application work, defines buffer ownership, and specifies drop/replace behavior.

This assessment confirms that:

· The STM32 DMA‑based direction is appropriate for minimizing CPU involvement, but several hardware integration gaps must be closed before implementation freeze.
· The Raspberry Pi backend is intentionally open; for an initial driver, the standard Linux spidev interface is the most pragmatic starting point, with a measured upgrade path if CPU overhead proves unacceptable.
· CPU independence is achievable but only with hard evidence collected under continuous traffic, host stalls, and signal‑integrity stress.
· Additional constraints must be added to the SPI service and protocol contracts, particularly around flow control, inter‑frame timing, and RX DMA arming.

---

2. Documented State and Clarifications

Based on repository documents and the local developer agent’s response, the current state is:

· Implemented and host‑tested: protocol framing/CRC, ACK/NACK generation, staged snapshot/response ownership, logical DATA_READY tracking, lifecycle gating, and task‑context TIME_SYNC handling.
· Design intent only (not yet verified on target hardware): live DMA transfer path, SPI RX capture, NSS abort/re‑arm behavior, and all target‑hardware timing/signal validation.
· No hardware evidence has been collected; all SPI acceptance items remain blocked.
· No separate hardware flow control signal (e.g., BUSY or NOT_READY) is documented. The system currently relies solely on DATA_READY timing.
· No minimum inter‑frame gap is specified.
· Raspberry Pi backend is undecided; candidates mentioned are spidev, python‑periphery, or a custom bridge.

---

3. Assessment of STM32 DMA‑Based SPI Direction

3.1 Suitability for Minimizing CPU Involvement

Conclusion: Yes, DMA is the correct direction for the STM32 slave side.

At a 5 MHz SPI clock and 512‑byte frames, interrupt‑driven byte‑by‑byte servicing would consume a substantial fraction of CPU time. DMA1 Stream 0 (RX) and Stream 5 (TX) as documented are valid for SPI3. The service contract’s requirement for minimal DMA callbacks and deferred task‑context processing is essential and correct.

3.2 Critical Gaps to Close Before Implementation Freeze

1. Flow control / backpressure
      SPI has no inherent flow control. The master controls the clock; the slave cannot stop it. The absence of a separate BUSY or NOT_READY signal means the master must strictly respect DATA_READY deassertion and stop clocking. This behavior is not currently contractually enforced.
      Required: Either add a dedicated hardware flow‑control line or explicitly require the master to stop issuing clocks when DATA_READY is low, with a defined timeout.
2. RX DMA pre‑arm policy
      For slave‑mode reception, the RX DMA must be armed before the master asserts NSS and clocks data. The documentation does not specify whether the RX DMA is permanently enabled or re‑armed after each frame. The current source does not implement live DMA, so this is unresolved.
      Required: Define the RX DMA arming policy: either keep it always active (with careful buffer management) or re‑arm it in the NSS falling‑edge interrupt / after each frame, with a clear guarantee that no clocks arrive before arming completes.
3. Minimum inter‑frame gap
      Continuous back‑to‑back frames without a gap can cause RX overrun or TX underrun if the DMA cannot keep up. No minimum gap is documented.
      Required: Specify a minimum deassertion time for NSS between frames (e.g., ≥ 1 µs or enough for DMA buffer switching) based on target hardware measurements.
4. Error recovery
      DMA transfer errors (overrun, underrun, abort) must be handled predictably. The contract mentions re‑arming from task context but lacks a detailed error recovery procedure.
      Required: Add explicit error handling: count errors, discard corrupted frame, re‑arm DMA, and notify the application.

---

4. Raspberry Pi Backend and DMA Strategy Options

The repository intentionally leaves the Raspberry Pi production backend open. The following options should be considered.

4.1 Candidate Backends

Backend Description CPU Impact Complexity Recommendation
Linux spidev (user space) Standard character device; supports DMA for large transfers via kernel SPI core. Low for 512‑byte frames if DMA is used by kernel; otherwise moderate with interrupts. Minimal; available in mainline kernel. Recommended starting point.
python‑periphery Python wrapper over spidev; easy prototyping. Higher CPU due to Python overhead; not suitable for low‑latency continuous traffic. Very low. Prototype only.
Custom kernel driver / RTDM Bypasses user space; full DMA control; minimal latency. Very low. High; requires kernel expertise and maintenance. Fallback if spidev proves insufficient.
Memory‑mapped GPIO + DMA controller (e.g., pigpio) User space access to BCM peripherals; can set up DMA for SPI. Low if DMA properly configured. Medium; hardware‑specific. Investigate only if spidev cannot meet requirements.

4.2 DMA Strategy for Raspberry Pi

The Raspberry Pi SPI controller (BCM2835/BCM2711) supports DMA for SPI transfers. The Linux spidev driver can use DMA when the transfer length exceeds a threshold or when dma is enabled via device tree overlay. For 512‑byte frames at 5 MHz, DMA is feasible but may not be necessary if interrupt overhead is acceptable.

Initial driver recommendation:
Use spidev in user space with the SPI device tree overlay enabling DMA (dtoverlay=spi0-1cs or similar). Measure CPU load and interrupt rates. If CPU impact is too high, transition to a custom kernel driver or direct DMA control.

---

5. CPU Impact and Independence Assessment

5.1 Can Normal System Activity Remain Independent of SPI Traffic?

Possibly, but not guaranteed without evidence.

· STM32 side: DMA offloads byte transfer; CPU is only involved in DMA completion callbacks and deferred buffer management. If callbacks are minimal and buffer replacement/drop works as documented, continuous SPI traffic should not stall sensor acquisition. However, if the host stalls and the STM32’s two‑buffer staging fills, frames will be dropped, which is acceptable per contract.
· Raspberry Pi side: With spidev and DMA, the kernel handles SPI transfers asynchronously. User‑space application can be scheduled independently. However, if spidev uses interrupts for 512‑byte transfers (depending on driver configuration), each frame may generate many interrupts (one per FIFO threshold), increasing CPU load. Proper use of DMA reduces this to one interrupt per transfer.
· Host stalls: If the Raspberry Pi stops clocking, the STM32 slave simply waits; no CPU impact on STM32. On the Pi, a stalled transfer may block the spidev user‑space thread, but the kernel remains responsive. The contract’s 1 ms polling fallback on STM32 ensures DATA_READY is reasserted if a complete frame exists.

Conclusion: The design can achieve CPU independence, but it hinges on:

· STM32 RX DMA always ready or arming fast enough,
· Raspberry Pi using DMA for SPI transfers,
· Buffer management preventing blocking,
· Proper master behavior on DATA_READY.

5.2 Required Evidence to Prove Acceptable CPU Impact and Independence

The following measurements must be collected on target hardware:

1. STM32 CPU load under continuous SPI traffic (e.g., % time in ISR, % time in task context, idle time).
2. Raspberry Pi CPU load during continuous transfers (user, system, interrupt time) using top, mpstat, or perf.
3. Interrupt counts on both sides (e.g., /proc/interrupts on Pi, NVIC counts on STM32).
4. DMA timing:
   · NSS assertion to first DMA transfer,
   · DMA completion time for 512 bytes,
   · TX buffer update time relative to next frame.
5. Overrun/underrun error rates under continuous back‑to‑back frames and with deliberate host stalls.
6. Host stall recovery: time for STM32 to reassert DATA_READY after stall ends; number of frames dropped.
7. Signal integrity: oscilloscope captures of SCK, MOSI, MISO, NSS, DATA_READY at 5 MHz; verify setup/hold times, ringing, crosstalk.
8. Raspberry Pi driver settings: actual spidev configuration (speed, mode, DMA enabled, buffer size), recorded in test logs.

---

6. Additional Constraints to Add Before Implementation Freeze

Based on the assessment and clarifications, the following items should be added to the SPI service contract and protocol contract:

1. Flow control / master behavior:
   · The Raspberry Pi master must stop clocking when DATA_READY is deasserted.
   · Define a maximum time the master may ignore DATA_READY deassertion (e.g., 1 ms) before the STM32 may consider the host stalled and drop the frame.
   · Alternatively, add a dedicated BUSY/NOT_READY GPIO line and make its use mandatory.
2. RX DMA arming policy:
   · Specify whether RX DMA is permanently enabled or re‑armed per frame.
   · If re‑armed, define the maximum allowable time from NSS deassertion to arming, and guarantee no clock edges occur before arming completes (e.g., via minimum inter‑frame gap).
3. Minimum inter‑frame gap:
   · Establish a minimum NSS high time (e.g., ≥ 2 µs at 5 MHz) based on worst‑case DMA buffer switch time.
   · This gap must be enforced by the master and verified in testing.
4. Host stall timeout:
   · Define a contract‑level timeout for how long the STM32 will keep a staged frame before dropping it if the host does not clock it out. The current 1 ms polling fallback should become an explicit timing requirement.
5. DMA error recovery:
   · Specify the exact sequence for handling DMA overrun, underrun, and abort errors, including counters, re‑arming, and notification to the application layer.
6. Raspberry Pi backend acceptance criteria:
   · Before freezing the contract, select a backend or define measurable acceptance criteria (e.g., CPU load < 10%, interrupt rate < N/sec) that any backend must meet. This prevents future rework.

---

7. Conclusions and Recommendations for Initial Driver

1. Proceed with STM32 DMA‑based SPI slave direction – it is the right choice for low CPU involvement, but close the gaps identified above.
2. Start the Raspberry Pi driver using Linux spidev with DMA enabled – this is the fastest path to a working system while allowing empirical measurement.
3. Implement the driver in two phases:
   · Phase 1: Use the existing staged ownership model without live DMA, verifying framing, lifecycle, and host‑stall behavior.
   · Phase 2: Add DMA with explicit pre‑arm, error recovery, and inter‑frame gap enforcement, then collect the full evidence set.
4. Add the additional constraints (flow control, inter‑frame gap, RX arming, error recovery) to the contracts before implementation freeze to avoid architectural rework.
5. Collect hardware evidence as soon as target hardware is available, focusing first on NSS‑to‑DMA timing and host‑stall behavior, as these are the highest risk.

The documented architecture is sound and aligns with standard best practices for SPI slave DMA operation. With the recommended additions and a measured initial driver, the system can achieve the goal of keeping CPU impact low and normal system activity independent of SPI traffic.

---

Source documents reviewed:

· docs/hardware/arm-sensor-hub-baseline.md
· docs/interfaces/raspberry-pi-spi.md
· docs/interfaces/spi-service-contract.md
· docs/protocols/spi-contract.md
· docs/protocols/spi-payload-schema.md
· Arm_Sensor_Hub/Documentation/LIFECYCLE_CONTRACT.md
· Arm_Sensor_Hub/Documentation/SAFETY_RELEASE_CHECKLIST.md
· Clarifications from local developer agent (email dated 2026‑09‑08).