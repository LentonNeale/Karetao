# Bench bring-up: wiring and electronics

This procedure takes the Karetao bench from loose parts to a powered, wired and checked rig. It works in phases: unpowered checks, logic power, firmware and SWD, I2C and encoders, the Pi SPI link, the drives one at a time, the CAN bus, and the E-stop. It follows the generated sheet in this folder (`karetao_bench_wiring.pdf`; see [README.md](README.md)). It ends where the Stage 2 encoder procedure and the Stage 3 link measurements begin. **It does not cover gated motion.**

This is a working procedure, not a documentation authority. Requirements, safety rules and numeric parameters stay in `Documentation/`. When a step finds a fact, record it where the "Record to" column points. Then move the matching item in [README.md](README.md) from "Provisional" to "fact" and update `generate_schematic.py`.

Status: written 2026-10-15 from the schematic, the WP8 review rulings (R9, R17, R25, R26, R28) and the MKS CAN manual V1.0.9 extracts in `icm-project/references/mks-servo42d-57d-can/`. Nothing in it has been run yet.

---

## 1. Read this first: known blockers and conflicts

| # | Item | Effect on bring-up | Source |
|---|---|---|---|
| B1 | The firmware's CAN is generated at 187.5 kbit/s (prescaler 16, BS1 11, BS2 2), which MKS drives cannot use. Ruling R9 sets 1 Mbit/s (PRM-CAN-03), but this is not applied yet. | Phase 7b (STM32 to drives) cannot pass until WP11 S11.1 is applied. Phase 7a (drives through a USB-CAN adapter) can go ahead. | WP8 review, CAN-1; `main.c` CAN init |
| B2 | The firmware never stages a SNAPSHOT: GET_SNAPSHOT returns ACK. | `spi_link_probe.py --snapshot` shows no sensor records. Read the sensors over SWD with `check-sensors.sh` (phase 4). The link probe still shows VERSION and STATUS. | WP8 review headline defect |
| B3 | **The sensor supply voltage conflicts.** The schematic draws the AS5600s, the mux and the pull-ups on +3V3. `Arm_Sensor_Hub/tools/check-sensors.sh` defaults `AS5600_VDD_5V=1` and says "this rig runs the sensors on a 5 V bus". | Measure it in phase 2 and record it. The schematic or the script is wrong. See the I2C voltage notes in phase 4. | `check-sensors.sh` header; README Provisional list |
| B4 | No E-stop or power cut is fitted (ruling R25b). | Phase 6 powers each drive alone from a supply whose switch is within reach. Phase 8 (E-stop) must pass before any session that powers all drives together with the arm assembled, and before Stage 4. | `04_SAFETY/SAFETY_REQUIREMENTS.md` SAFE-01; RULINGS R25 |
| B5 | The MKS power-on auto-run (FFH) and the En-pin mode (85H) have not been read (ruling R25a). | Read both in phase 6, before the drive is powered with its motor coupled to the arm. | RULINGS R25 |
| B6 | The drive facts are unknown: CanRate, CAN ID, model, firmware, work mode and response mode for all six drives (ruling R9b). | Read them in phase 6. They are a hard prerequisite for WP11 S11.1. | RULINGS R9; `SYSTEM_CONFIGURATION.md` §2.1 |
| B7 | No MCU line drives the mux RESET (FW-12). A wedged mux can only be cleared by a power cycle. | If the I2C bus hangs, power-cycle the logic supply instead of resetting the STM32. | WP8 review FW-12 |

## 2. Equipment

| Item | Used in | Note |
|---|---|---|
| Multimeter (continuity, Ω, DC V) | 1, 2, 6 | Required |
| Current-limited bench supply, 0 to 30 V | 2, 6 | For first power-up of the logic rail and of each drive. Otherwise use the motor PSU with a switch within reach. |
| ST-Link probe and `stlink-tools`, `gdb-multiarch` | 3, 4 | `check-sensors.sh` needs `st-util`, `st-flash`, `st-info`, `gdb-multiarch` |
| Logic analyser or oscilloscope | 4, 5, 7 | Available (ruling R17a) |
| USB-CAN adapter or CAN analyser | 6, 7 | Available (ruling R17a). With a 120 Ω terminator if it sits at the end of the bus. |
| Raspberry Pi 5, provisioned | 5 | Per `RaspberryPi_Sensor_Hub/Documentation/RASPBERRY_PI_BRINGUP_V1.md` (SPI enabled, user in `dialout`) |
| E-stop, two-pole, rated for the motor supply current | 8 | To be fitted (B4) |

## 3. Bench rules for every session

- [ ] Before motor power is switched on, the arm is in a position where a sudden move or a **drop under gravity** does no harm. A drive that loses power, or is cut by the E-stop, stops holding its joint.
- [ ] Motor phase wires and drive connectors are never plugged or unplugged while the drive has power.
- [ ] Power-up order: logic 5 V first (the STM32 and the CAN transceiver hold the bus recessive), then the Pi, then motor power (rocker switch on, E-stop released). Power down in the reverse order: motor power off first.
- [ ] The TJA1050 is never powered while the STM32 is not (for example, the STM32 board unplugged from a live 5 V rail). Its RXD output would put 5 V on an unpowered PB8.
- [ ] Only one person changes wiring, and only with all supplies off.
- [ ] Each session goes in the log (§6).

---

## 4. Phases and checklist

Each phase has an entry condition, checks with an expected result, and an exit condition. A failed check stops the phase. Fix the cause and repeat the check before moving on.

### Phase 0: Inventory (no power)

Record the parts the schematic draws as Provisional.

| Check | Expected | Record to |
|---|---|---|
| ☐ STM32 board: make, model, and whether it takes 5 V in and regulates 3.3 V | Matches the drawing, or the drawing is corrected | README fact table; `generate_schematic.py` U1 |
| ☐ CAN transceiver: TJA1050 (Lenton Neale, 2026-10-15). Its supply, and what its S pin is tied to | 5 V supply (4.75 to 5.25 V, Datasheet). S low or open = high-speed mode; S high = silent, the transmitter is off (Datasheet) | README; U10 |
| ☐ The TJA1050 takes its 5 V from the same rail that powers the STM32 board | Yes. PB8 (CAN1_RX) is 5 V tolerant only while the STM32 is powered: an FT pin may see at most VDD + 4.0 V, so 5 V from RXD with the STM32 off can damage it. TXD needs no level shift: the TJA1050 HIGH threshold is 2.0 V (Datasheet) | README; U10 |
| ☐ Pull-ups on each AS5600 breakout and on the mux breakout (values, and the rail each pulls to) | Recorded; total pull-up per bus segment worked out | README; R3/R4 |
| ☐ AS5600 breakout: does VCC feed VDD5V only, or VDD5V and VDD3V3 bridged? | Recorded (it matters at 3.3 V, see phase 4) | README |
| ☐ Mux breakout: A0 to A2 strapping, RESET pull-up present | A0 to A2 low (address 0x70); pull-up recorded | README; R5 |
| ☐ Logic PSU: make, rated voltage and current | 5 V, recorded | README; PS2 |
| ☐ Motor PSU: make, rated voltage and current | Within the 12 to 24 V drive range (MKS manual p. 9), recorded | README; PS1 |
| ☐ Cable types and lengths: SPI harness, I2C runs per axis, CAN trunk and stubs | Recorded. SPI length checked against PRM-SPI-05 (20 to 30 cm, Provisional). CAN as twisted pair, shielded where possible (MKS manual p. 18). | Session log; Stage 3 input |

**Exit:** every Provisional part in the README has a recorded make or value, or is marked "not known yet" with a reason.

### Phase 1: Unpowered wiring checks

**Entry:** all supplies off and unplugged. The Pi is not connected.

| Check | Expected |
|---|---|
| ☐ Resistance from +5V to GND, from +3V3 to GND, and from VMOT_SW to GND (E-stop closed, drives connected) | No short. Write down the readings; they settle as capacitors charge from the meter. |
| ☐ Continuity of each named net end to end, from the schematic: I2C1_SCL, I2C1_SDA, SCL_CH0, SDA_CH0, SCL_CH2 to SCL_CH7, SDA_CH2 to SDA_CH7, CAN_TX, CAN_RX, SPI_NSS, SPI_SCK, SPI_MISO, SPI_MOSI, DATA_READY, SWDIO, SWCLK, NRST | Each net connects only its drawn pins. Spot-check neighbours for shorts (SCL to SDA on each channel, MOSI to MISO). |
| ☐ SPI harness against the Pi table (`RaspberryPi_Sensor_Hub/Documentation/README.md`): pin 19 to PC12, 21 to PC11, 23 to PC10, 24 to PA15, 22 to PA8, 20 to GND | All six continuous. No other Pi pin wired; Pi 5 V and 3.3 V are left unconnected. |
| ☐ Resistance from CAN_H to CAN_L with the whole bus connected | About 60 Ω, two 120 Ω terminators in parallel (Derived). About 40 Ω means a third terminator, often inside a drive or the USB-CAN adapter; about 120 Ω means one is missing. |
| ☐ Resistance from CAN_H and from CAN_L to GND | High (kΩ or more). No short. |
| ☐ Ground: the STM32 GND, each drive's CAN GND, the motor PSU V- (through the E-stop) and the Pi GND pin 20 are all common | Continuous (MKS manual p. 18: host and motor share a ground) |
| ☐ Ground return path | Motor current returns to the motor PSU through the heavy VIN- wires, not through the logic or CAN ground wires. Logic GND and motor GND meet at one point. (This is a recommendation; the schematic shows connectivity only.) |
| ☐ Mux A0, A1, A2 to GND | Continuous (address 0x70) |
| ☐ AS5600 DIR on each sensor | Tied to GND, as drawn (Provisional), or recorded as found |
| ☐ Axes 0 and 3 (mux channels 2 and 5) and SD1 | No sensor on channels 2 and 5 (axes 0 and 3 not fitted) and nothing on SD1, as `SYSTEM_CONFIGURATION.md` §2.1 states |
| ☐ Each drive's own CAN terminator (57D DIP 1, 42D shorting cap) | Off on every drive while R1 and R2 are fitted; or record which drive is the far end in place of R2 |
| ☐ 57D DIP 2 and 3 | ON, so EVCC supplies 5 V to the switch modules (MKS manual p. 19) |
| ☐ Switch module wiring at each drive, against the drive blocks on the schematic | As drawn, or recorded as found and `generate_schematic.py` corrected |
| ☐ 42D drives with switches on En and Dir: COM to EVCC | Continuous. COM must be at the high level once the ports are remapped (MKS manual p. 12); the Arctos drawing leaves it open on two 42D drives |
| ☐ Motor phase order at each drive (optional) | Recorded: phase A crossed as drawn, or as found. Do not rewire to change it: any change of motor wiring needs a recalibration (MKS manual p. 103) |

**Exit:** no shorts. Every net is continuous. CAN resistance is about 60 Ω, or the extra or missing terminator is found and fixed.

### Phase 2: Logic power only

**Entry:** phase 1 passed. Motor PSU off. Pi not connected. The bench supply is set to 5 V with a low current limit (start at about 200 mA and raise it only if the board will not start).

| Check | Expected | Record to |
|---|---|---|
| ☐ Apply 5 V and note the current | Steady, no current limiting. Write the value down. | Session log |
| ☐ +5V at the STM32 board input | Matches the supply | Session log |
| ☐ +3V3 at the STM32 board and the mux VCC | 3.3 V nominal. STM32F405 VDD 1.8 to 3.6 V (Datasheet) | Session log |
| ☐ +5V at the TJA1050 VCC | 4.75 to 5.25 V (Datasheet) | Session log |
| ☐ **Supply at each AS5600 VDD (resolves B3)** | 3.3 V or 5 V. Write down which. AS5600 3.3 V mode is 3.0 to 3.6 V; 5 V mode is 4.5 to 5.5 V (Datasheet). | README; schematic; `check-sensors.sh` default |
| ☐ Idle level of I2C1_SCL and I2C1_SDA, and of one downstream SCL_CHn/SDA_CHn | High, at the pull-up rail found in phase 0 | Session log |
| ☐ Idle CAN_H and CAN_L to GND | Both about the same, about 2.5 V (recessive; TJA1050 2.0 to 3.0 V, Datasheet) | Session log |
| ☐ Touch test after one minute | No part warm | none |

**Exit:** both rails are in range, the sensor supply is known, and nothing is warm.

### Phase 3: Firmware and SWD

**Entry:** phase 2 passed. ST-Link connected to the SWD header (3V3, SWDIO, SWCLK, NRST, GND).

| Check | Expected |
|---|---|
| ☐ `st-info --probe` | One STM32F4 target found, 1024 KiB flash |
| ☐ Build the Debug firmware with the CLI preset, from `Arm_Sensor_Hub/`: `cmake --preset Debug && cmake --build --preset Debug` | `build/Debug/Arm_Sensor_Hub.elf` builds. Evidence firmware must come from the CLI preset (ruling R28a). The VS Code ST-bundle build is for development only. |
| ☐ Flash it, write down the commit, and check `git status` is clean | Flash succeeds. A dirty tree is fine for bring-up but cannot produce an evidence record (R28b). |
| ☐ Reset and let it run 10 s | The current draw stays steady and the board does not keep resetting |

**Exit:** the ST-Link reaches the target, and a known Debug build is running.

### Phase 4: I2C, mux and encoders

**Entry:** phase 3 passed. Magnets fitted on the shafts of axes 1, 2, 4 and 5, and on the bench sensor.

I2C voltage notes for B3. The TCA9548A translates levels: each downstream channel may be pulled up to its own rail. If the sensors run at 5 V with pull-ups to 5 V, then the upstream bus (I2C1 to the STM32) must still be pulled to a level PB6/PB7 can take. Check PB6/PB7 are marked FT (5 V tolerant) in the STM32F405 datasheet pin table before any pull-up goes to 5 V. If the sensors run at 3.3 V, the AS5600 datasheet requires VDD5V and VDD3V3 tied together. Check the breakout (phase 0).

| Check | Expected | Record to |
|---|---|---|
| ☐ From `Arm_Sensor_Hub/`: `AS5600_VDD_5V=<0 or 1 per phase 2> tools/check-sensors.sh build/Debug/Arm_Sensor_Hub.elf` | Exit 0: every commissioned axis valid. Axes 0 and 3 show NOT_FITTED, which is not a fault (SYS-ENC-002). | Session log (paste the output) |
| ☐ Magnet status per axis (MD set; ML and MH clear) | MD set on every fitted axis. ML or MH alone is a warning, not invalid (ruling R6a). Adjust the magnet gap if AGC is at a limit. | Session log |
| ☐ Turn each fitted shaft by hand and rerun | `raw_angle` changes on that axis only. This confirms the mux channel map: axis N on channel N+2. | Session log; a mismatch is a defect against `SYSTEM_CONFIGURATION.md` §2.1 |
| ☐ Bench sensor on SD0 | Readable, and excluded from the arm axes | Session log |
| ☐ Logic analyser on I2C1_SCL and SDA during a sweep | 400 kHz clock (PRM-ACQ-04). Clean edges: the rise reaches the high level well before the next clock edge. No stuck-low bus. | Session log; capture file |
| ☐ Optional: time one full sweep on the analyser (first mux select to last read) | Write the value down as an input to the Stage 3 PRM-ACQ-02 re-measure (ruling R6c). It is not a register value. | Session log |

**Exit:** all four fitted axes read valid and follow the hand. Axes 0 and 3 are NOT_FITTED. The sensor supply voltage is recorded, and the schematic or the script is corrected.

### Phase 5: Raspberry Pi SPI link

**Entry:** phase 4 passed. The Pi is provisioned with SPI enabled. Its ground is connected (pin 20) **before** any signal wire, and it runs from its own supply. Connect the harness with both boards powered off.

| Check | Expected | Record to |
|---|---|---|
| ☐ On the Pi: `ls /dev/spidev0.0` and `gpioinfo gpiochip4 \| grep -w 25` | The device exists; line 25 is free | Session log |
| ☐ From the repo root on the Pi: `python3 RaspberryPi_Sensor_Hub/tools/spi_link_probe.py` | Magic 0xA55A seen; VERSION decoded with `git_hash_abbrev` matching the flashed commit; STATUS reply. The working clock is 1 MHz, the tool default (ruling R17c). | Session log; Pi commit hash |
| ☐ The same with `--data-ready` | Every transfer is gated on a GPIO25 rising edge; no timeouts | Session log |
| ☐ The same with `--snapshot` | Expected to show **no sensor records** until the snapshot-staging defect is fixed (B2). Record what it shows. | Session log |
| ☐ Logic analyser on NSS, SCK, MOSI, MISO and DATA_READY for one probe run | Mode 0 (CPOL 0, CPHA 0), NSS low for the whole 512-byte transfer, DATA_READY rises before NSS falls, and no glitches on SCK | Capture file; input to the Stage 3 SPI §16 electrical validation |
| ☐ DATA_READY high level at the Pi pin | About 3.3 V (STM32 push-pull). Never above 3.3 V: Pi 5 GPIO are not 5 V tolerant. | Session log |

**Exit:** VERSION and STATUS are read reliably at 1 MHz, with and without DATA_READY.

### Phase 6: MKS drives, one at a time

**Entry:** phases 1 and 2 passed. Every drive's motor is **uncoupled from the arm, or its joint is in a safe position** (§3). Power each drive alone from the current-limited bench supply, or from the motor PSU with its switch within reach. The STM32 is unplugged from the CAN bus or powered off. Use the drive's menu and OLED, or the USB-CAN adapter at the drive's current rate (the factory default is 500K, MKS manual p. 21).

For each drive M1 to M6:

| Check | Expected | Record to |
|---|---|---|
| ☐ Supply at the drive VIN+ with the drive idle | Within 12 to 24 V (MKS manual p. 9) | Session log |
| ☐ Model (SERVO42D or 57D), from the label | Recorded | `SYSTEM_CONFIGURATION.md` §2.1, MKS model column |
| ☐ Firmware version, from the boot screen or 40H | Recorded. F7H and FEH need V1.0.4 or later; F5H needs V1.0.5 or later. | §2.1, MKS firmware column |
| ☐ CAN ID (menu CanID or by command) | Unique on the bus. Write the planned axis next to it. An ID above 0xFF needs its checksum rule confirmed on a drive before it is commissioned (ruling R9d). | §2.1 CAN ID column; README |
| ☐ CanRate | Recorded as found, then **set to 1M** (ruling R9a; menu or 8AH with value 03) | §2.1; session log |
| ☐ Work mode (82H) | Recorded as found. Bus motion needs an SR mode; the factory default CR_vFOC ignores bus motion commands (ruling R9). The Provisional choice is SR_CLOSE (82H value 04H; `ARCHITECTURE_DECISIONS.md`, "MKS drive work mode"). Change it only when WP11 needs it or for the phase 9 check, and note the change. | §2.1 (new column if needed); session log |
| ☐ Response mode (8CH) | Recorded (default: respond enabled, active enabled) | §2.1; session log |
| ☐ FFH power-on auto-run | **Off** (CA). If it is on, turn it off before the drive is ever powered with its motor coupled. | §2.1, new column (ruling R25a) |
| ☐ 85H En-pin mode | Recorded (L, H, or Hold) | §2.1, new column (ruling R25a) |
| ☐ 98H heartbeat time | Recorded as found (default 0, off). The firmware sets 500 ms at CAN activation later (ruling R23b). | Session log |
| ☐ 9EH port mapping, as found | On for every drive whose switches are wired to En and Dir (the 42D drives as drawn) | §2.2; session log |
| ☐ EVCC current with the switch modules connected | Within 20 mA (MKS manual pp. 10, 19). If over, the switch supply needs a change before use | Session log |
| ☐ Each switch: read the I/O port status (34H) with the magnet away, then near | The matching input changes, and only that one | Session log; README |
| ☐ Encoder calibration status | If the drive was ever remounted on its motor or the motor wiring changed, it needs recalibration (MKS manual p. 103). Calibration turns the shaft, so do it uncoupled. | Session log |
| ☐ Power the drive off and on again | The shaft does not move by itself at power-up | Session log |

**Exit:** all six drives have every column recorded, CanRate is 1M, the IDs are unique and FFH is off. Ruling R9b and R25a facts are complete.

### Phase 7: CAN bus

**7a: Drives through the USB-CAN adapter (no STM32 on the bus)**

**Entry:** phase 6 passed. All drives daisy-chained on the trunk with the two terminators as planned in phase 1. The adapter is set to 1 Mbit/s and its own terminator is off unless it sits at a bus end.

| Check | Expected | Record to |
|---|---|---|
| ☐ CAN_H to CAN_L resistance, unpowered | About 60 Ω | Session log |
| ☐ Power the drives. Send a read-only request to each ID in turn (for example 31H, read cumulative encoder) | Each drive answers from its own ID with a valid 8-bit checksum. No error frames. | Session log; adapter log |
| ☐ Adapter error counters after 1 minute of polling all six | Zero error frames, zero bus-off | Session log |
| ☐ Scope on CAN_H and CAN_L | Clean edges on the pair at 1 Mbit/s (1 µs bit), no ringing that crosses the threshold | Capture file |

**7b: STM32 to drives (blocked by B1 until WP11 S11.1)**

**Entry:** firmware built with the 1 Mbit/s timing (prescaler 3, BS1 11, BS2 2; PRM-CAN-03), and the commissioning table in `app_init.c` matches §2.1.

| Check | Expected | Record to |
|---|---|---|
| ☐ Analyser on the bus at 1 Mbit/s while the STM32 boots | STM32 frames decode at 1 Mbit/s, the drives reply, and there are no error frames | Session log; input to the Stage 3 bus-load measurement (ruling R17b) |
| ☐ Motor 0 (0x001) feedback appears in the firmware's latest-value store (SWD) | Valid record that tracks a hand-turned shaft (drive disabled) | Session log |

**Exit:** 7a passed now. 7b passed after WP11 S11.1.

### Phase 8: E-stop (SAFE-01 hardware)

**Entry:** E-stop fitted as drawn: two-pole, in the motor supply after the rocker switch and before VMOT_SW (B4). Arm in a safe position (§3).

| Check | Expected | Record to |
|---|---|---|
| ☐ Unpowered: E-stop pressed, then the resistance from PS1 V+ to VMOT_SW and from PS1 V- to the drive GND side | Open on both poles | Session log |
| ☐ Powered, drives idle: press the E-stop | Every drive's VIN falls to 0 V; the OLEDs go dark | Session log |
| ☐ Drive holding torque (enabled through the adapter, or En per its 85H mode), then press the E-stop | All shafts lose torque at once, with no software involved | Session log; later the SAFE-01 record |
| ☐ Release the E-stop | No shaft moves (FFH off on every drive) | Session log |
| ☐ The E-stop can be reached from where the operator stands | Yes | Session log |

**Exit:** the E-stop removes motor power from all drives with no software involved. Record the fitted part in `SAFETY_REQUIREMENTS.md`, which closes the open item "The actual E-stop hardware fitted is unknown" through the WP16 story. The SAFE-01 evidence record itself comes from the session-safety procedure (VER-45) once it exists.

### Phase 9: SR_CLOSE holding check (one joint at a time)

This check confirms or replaces the Provisional SR_CLOSE decision (`Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md`, "MKS drive work mode"). In SR_CLOSE a stopped joint holds with only the 9BH holding percentage of its working current (MKS manual p. 20).

**Entry:** phase 8 passed (the E-stop works). The joint is coupled to the arm. The working current (Ma), holding percentage, run time and drift and temperature limits are entered in `PARAMETER_REGISTER.md` as Provisional rows. A second person, or a support, can catch the joint.

| Check | Expected | Record to |
|---|---|---|
| ☐ Set the drive to SR_CLOSE (82H 04H), the planned Ma (83H) and holding percentage (9BH) | Each command returns status 1 | Session log |
| ☐ Enable the drive through the USB-CAN adapter with the joint supported in its worst gravity pose, then remove the support | The joint holds | Session log |
| ☐ Read the position (31H) at the start and after the run time | Drift within the registered limit | Session log; evidence record if it is used for the decision |
| ☐ Motor case temperature after the run time | Within the registered limit | Session log |
| ☐ Press the E-stop with the joint still supported by hand | The joint loses torque; it is caught, not dropped | Session log |

**Exit:** every fitted joint passes, and the decision becomes Decided; or a joint fails, it is moved to SR_vFOC and the decision is revised.

### Phase 10: MKS heartbeat and synchronisation behaviour (USB-CAN adapter)

This phase answers what the MKS manual leaves open about the 98H heartbeat (ruling R23b) and the synchronisation-mark function (`Documentation/07_DECISIONS/ARCHITECTURE_DECISIONS.md`, "MKS multi-motor synchronisation"; open questions in `icm-project/references/mks-servo42d-57d-can/multi-motor-synchronisation.md` §10). Commands come from the USB-CAN adapter, not the STM32.

**Entry:** phase 8 passed (the E-stop works). Two drives on the bus at 1M, in SR_CLOSE, with their motors **uncoupled** or their joints where a sudden move does no harm. Their firmware versions are recorded; the synchronisation checks need V1.0.8 or later (MKS manual p. 2). Use slow speeds throughout.

**10a: Heartbeat (98H)**

| Check | Expected | Record to |
|---|---|---|
| ☐ Set 98H to 500 ms on one drive; enable it and start a slow speed run | Status 1; the motor runs | Session log |
| ☐ Keep sending only read requests (31H) every 100 ms | Record whether the motor keeps running. If it stops, read requests do not count as "instructions" and the firmware must send something else to keep the drive alive | Session log; input to the WP14 heartbeat design |
| ☐ Stop sending anything | The motor stops within about 500 ms (MKS manual p. 44) | Session log |
| ☐ After the heartbeat stop | Record whether the shaft holds (torque on) or goes limp, and what the drive reports (F1H status) | Session log; input to the stop-and-hold design (ruling R21) |
| ☐ Power-cycle the drive and read the heartbeat behaviour again | Record whether 98H survived the power cycle (the firmware sets it at every CAN start either way) | Session log |

**10b: Synchronisation (4AH, 4BH)**

| Check | Expected | Record to |
|---|---|---|
| ☐ Enable 4AH on both drives (4AH 01) | Status 1 from each | Session log |
| ☐ Send each drive a different slow motion command | Neither motor moves (MKS manual p. 96) | Session log |
| ☐ Send 4BH on the broadcast ID (`00 4B 4B`) | Both motors start; no reply is expected (p. 97) | Session log |
| ☐ Start skew between the two drives (encoder read-back, or a scope on the motor phases) | Recorded; the manual gives no figure | Session log; Stage 3 input |
| ☐ Stage a command, wait 10 s, then release | Record whether it still runs (staged-command lifetime) | Session log |
| ☐ Stage a command, then send a stop (F7H), a disable, or 4AH 00, then 4BH | Record, for each, whether the staged command is discarded. The firmware needs a reliable way to cancel a staged move on link loss | Session log; input to the command-path design |
| ☐ Stage a command, let the heartbeat time out, then 4BH | Record whether the staged command is discarded | Session log |
| ☐ Send 4BH with nothing staged | Nothing moves | Session log |
| ☐ With 4AH still on, send a single command and no 4BH | The motor does not move (every command waits while 4AH is on) | Session log |
| ☐ Set 4AH 00 on both drives before leaving the bench | Status 1 | Session log |

**Exit:** every row is recorded. The answers go into the heartbeat and command-path designs, and the decision is confirmed or dropped.

---

## 5. What "bring-up done" means

Done when phases 0 to 6, 7a and 8 have passed, and the facts in the table below are recorded. Phases 9 and 10 are not part of bring-up: phase 9 settles the drive work mode before gated motion, and phase 10 feeds the heartbeat and command-path designs. The rig is then ready for:

- The Stage 2 encoder procedure (`Documentation/05_VERIFICATION/ENCODER_BENCH_PROCEDURE.md`). That procedure reads sensors through `--snapshot`, so it waits for the snapshot fix (B2).
- The Stage 3 link measurements (SPI clock and cable sweep, CAN bitrate and bus load, DATA_READY electrical timing). They need 7b for the CAN parts.
- WP11 S11.1, whose bench prerequisites (ruling R9) phase 6 supplies.

It is **not** ready for gated motion. Gated motion on X, Y and Z needs SAFE-01, SAFE-02 and the gate evidence (ruling R26a; register §2), none of which this procedure produces.

| Fact | Phase | Goes to |
|---|---|---|
| STM32 board, transceiver, PSUs, pull-ups, breakout details | 0 | `README.md` fact table; `generate_schematic.py` |
| Sensor supply voltage (B3) | 2 | README; schematic; `check-sensors.sh` default |
| Per drive: model, firmware, CAN ID, CanRate, work mode, response mode | 6 | `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` §2.1 |
| Per drive: FFH auto-run, 85H En mode | 6 | §2.1, two new columns (ruling R25a) |
| Termination placement and measured CAN_H to CAN_L resistance | 1, 7a | README; schematic R1 and R2 |
| Per drive: switch wiring, terminator setting, 9EH mapping, EVCC current | 1, 6 | README; schematic drive blocks; `SYSTEM_CONFIGURATION.md` §2.2 |
| Cable lengths | 0 | Session log; Stage 3 input (PRM-SPI-05) |
| E-stop part and placement | 8 | `Documentation/04_SAFETY/SAFETY_REQUIREMENTS.md` open item; schematic SW1 |

A fact that changes a requirement or a parameter goes through its owning document under `Documentation/DOCUMENTATION_RULES.md`. This file only says where it goes.

## 6. Session log

One block per session, appended under `Hardware/bench-wiring/logs/<date>.md`. A session log is a working note, not an evidence record. Evidence records follow `Documentation/05_VERIFICATION/EVIDENCE_RECORD_FORMAT.md`.

```markdown
## YYYY-MM-DD session N

- Operator: Lenton Neale
- Phases run: 
- Firmware: commit <hash>, dirty <yes/no>, preset Debug (CLI)
- Pi: commit <hash>, dirty <yes/no>
- Supplies: logic <V, mA>; motor <V, A limit>; E-stop fitted <yes/no>
- Arm state: <uncoupled / coupled, safe position described>

| Phase.check | Result (pass/fail/blocked) | Measured value or observation |
|---|---|---|
|  |  |  |

- Facts recorded and where:
- Faults found and fixes:
- Captures and files:
- Next session starts at:
```
