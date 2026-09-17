# CAN Bit Timing and Physical-Layer Evidence

**Status:** Engineering calculation; not hardware validation
**Scope:** Candidate v1 1 Mbps bxCAN configuration and provisional bus-load estimate

## Source Evidence

- `Core/Src/main.c` configures the system clock at 168 MHz with APB1 divided by 4, yielding `PCLK1 = 42 MHz`.
- `Arm_Sensor_Hub.ioc` records `RCC.APB1Freq_Value=42000000` and CubeMX's current CAN calculation of 875000 bps.
- The generated `MX_CAN1_Init()` currently uses prescaler 16, BS1 1 TQ, BS2 1 TQ, and SJW 1 TQ. Its rate is $42,000,000 / (16 \times (1 + 1 + 1)) = 875,000$ bps with a 66.7% sample point. It is not the 1 Mbps candidate.

## Candidate 1 Mbps Calculation

The v1 target remains 1 Mbps pending integration validation. A candidate derived from the current 42 MHz PCLK1 is:

| Setting | Candidate value |
| --- | ---: |
| Prescaler | 3 |
| Sync segment | 1 TQ |
| BS1 | 11 TQ |
| BS2 | 2 TQ |
| Total bit time | 14 TQ |
| SJW | 1 TQ |
| Bitrate | $42,000,000 / (3 \times 14) = 1,000,000$ bps |
| Sample point | $(1 + 11) / 14 = 85.7\%$ |

This is a reproducible candidate only. Do not change CubeMX or runtime bxCAN settings from this calculation alone.

## Provisional Bus-Load Estimate

A standard 11-bit CAN data frame with eight data bytes is approximately 111 bits without stuffing. The conservative maximum including bit stuffing is 130 bits per frame. At 1 Mbps, use $130\ \mu s$ per worst-case frame.

The current scheduler sends one poll every 20 ms and alternates request types across registered motors. Assuming one response per poll, its aggregate rate is 50 requests/s plus 50 responses/s:

$$
100\ \mathrm{frames/s} \times 130\ \mathrm{bits/frame} = 13,000\ \mathrm{bits/s} = 1.3\%\ \mathrm{bus\ load}
$$

A deliberately conservative planning scenario of eight motors with one request/response pair per motor at 100 Hz is 1,600 frames/s or 20.8% load. Adding one 100 Hz command frame per motor yields 2,400 frames/s or 31.2% load. Both estimates remain below the 50-60% design target, but neither is a validated worst case because controller traffic, retries, error frames, and command modes are not commissioned.

## Integration and Release Blockers

- Exact MKS controller model, firmware, command/response lengths, feedback rate, and required polling/command traffic.
- CAN transceiver part, supply/standby behavior, common-mode range, and TX/RX signal levels.
- Bus topology, cable type/length, node count, stub lengths, shielding, grounding, and 120-ohm termination at both physical ends.
- Oscillator tolerance, measured sample point/SJW margin, retransmission policy, and bxCAN bus-off recovery behavior.
- Logic-analyzer or CAN-analyzer evidence of actual bitrate, error counters, arbitration latency, worst-case load, and stability through startup, host stalls, and fault recovery.

The target bitrate, candidate timing, and load estimates are integration gates. They do not validate the physical network or authorize energized motion.