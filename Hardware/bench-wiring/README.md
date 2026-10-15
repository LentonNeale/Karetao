# Bench wiring schematic

`karetao_bench_wiring.kicad_sch` is the system wiring of the Karetao bench at connector level: the STM32F405 hub, the TCA9548A mux and the AS5600 encoders on I2C1, the CAN transceiver and the six MKS drives, the SPI and DATA_READY lines to the Raspberry Pi 5, the motor supply through the rocker switch and the E-stop, and at each drive its motor and its home or limit switch modules. It is a KiCad schematic (KiCad 8 file format, checked with KiCad 10.0.7). Its symbols are in the project library `karetao.kicad_sym`, registered by the project's `sym-lib-table`, and are also embedded in the schematic. Open `karetao_bench_wiring.kicad_pro` in KiCad; `karetao_bench_wiring.pdf` is the same sheet for reading without KiCad.

The arm is the [Arctos](https://arctosrobotics.com/) V2 by Arctos Robotics; its drive, motor and switch wiring here is taken from the original Arctos V2 wiring and marked Provisional until confirmed on the bench. The hub, transceiver, encoders and Pi connections are Karetao's own.

To bring the bench up against this sheet, follow [BRING_UP.md](BRING_UP.md): phased checks from unpowered wiring to the E-stop, and where each fact it finds is recorded.

The file is generated. Edit `generate_schematic.py`, not the schematic, then run:

```bash
cd Hardware/bench-wiring
python3 generate_schematic.py                      # writes the .kicad_sch, .kicad_pro, karetao.kicad_sym, sym-lib-table
kicad-cli sch erc --severity-all karetao_bench_wiring.kicad_sch     # must report 0 errors, 0 warnings
kicad-cli sch export pdf --output karetao_bench_wiring.pdf karetao_bench_wiring.kicad_sch
```

The generator refuses to write a sheet in which a label, no-connect or power symbol is not on a wire, or in which two different net names end up connected (it models KiCad's connectivity: coinciding points and points on a wire join). KiCad's ERC is the second check. Status on 2026-10-15: ERC 0 errors, 0 warnings.

## What the drawing states as fact

| Item | Source |
|---|---|
| STM32 pins: I2C1 PB6/PB7, CAN1 PB8/PB9, SPI3 PA15/PC10/PC11/PC12, DATA_READY PA8, SWD PA13/PA14 | `Documentation/03_COMPONENTS/ARM_SENSOR_HUB.md`, `Arm_Sensor_Hub.ioc` |
| Mux address 0x70 (A0 to A2 low); axis N on channel N+2; SD0 bench sensor; SD1 unpopulated | `Documentation/06_CONFIGURATION/SYSTEM_CONFIGURATION.md` §2.1 |
| Encoder fitted on axes 1, 2, 4, 5; axes 0 and 3 not fitted (drawn as do-not-populate) | same |
| Drive CAN IDs 0x001 to 0x006 on axes 0 to 5; SERVO57D on axes 0 and 1, SERVO42D on axes 2 to 5 | same, §2.2 |
| CAN transceiver: NXP TJA1050, 5 V supply | Lenton Neale, 2026-10-15; NXP TJA1050 data sheet |
| Rocker switch fitted in the motor supply; the E-stop goes in line after it, before the drives | Lenton Neale, 2026-10-15 |
| Drive switch inputs: 57D IN_1 home or left limit, IN_2 right limit; 42D IN_1 only, so two switches need 9EH port mapping (left to En, right to Dir, COM at the high level); EVCC/EGND 5 V, 20 mA (57D with DIP 2 and 3 ON) | MKS manual pp. 10, 12, 19, 56 |
| 57D DIP switches set; 42D switch inputs configured | Lenton Neale, 2026-10-15 (exact settings recorded in `BRING_UP.md` phases 1 and 6) |
| PB8 (CAN1_RX) and PB9 (CAN1_TX) are FT (5 V tolerant) pins, so the TJA1050's 5 V RXD connects directly, provided the STM32 is powered; PB8 has no internal pull (`GPIO_NOPULL`, `Core/Src/stm32f4xx_hal_msp.c`) | Datasheet: STM32F405xx/STM32F407xx, DS8626 Rev 12, Table 7 "pin and ball definitions" (p. 60, PB8 and PB9 rows: I/O structure FT) and its note 5 (p. 61: "FT = 5 V tolerant except when in analog mode or oscillator mode"). Checked 2026-10-15 |
| Pi header pins 19, 21, 23, 24 (SPI0 CE0) and 22 (GPIO25 DATA_READY) | `RaspberryPi_Sensor_Hub/Documentation/README.md` |
| Drive supply 12 to 24 V DC; host and drives share a ground | MKS manual via `icm-project/references/mks-servo42d-57d-can/` |

## What is Provisional (no document states it)

- The STM32 board type and whether it takes 5 V in and regulates 3.3 V (drawn that way).
- The TJA1050's S pin tied low (high-speed mode).
- I2C pull-ups (4k7 on the main bus, drawn to +3V3) and whether the breakout boards carry their own.
- The sensor and mux rails. Lenton reports the AS5600s run on 5 V (2026-10-15), and they are drawn on +5V. The mux is drawn on +3V3, and the rail of the channel (SCx/SDx) pull-ups is not recorded. In 5 V mode an AS5600 needs a logic high of about 0.7 × VDD, so a channel pulled only to 3.3 V would read unreliably. Measure all of them in `BRING_UP.md` phase 2 (B3).
- The mux RESET pull-up (10k); no MCU line drives it (review finding FW-12).
- AS5600 DIR tied low on every sensor.
- CAN termination at both ends (R1 at the hub, R2 at the last drive), with every drive's own terminator off.
- Which switch module is on which drive input, per axis (taken from the original Arctos drawing; confirmed on the bench, `BRING_UP.md` phase 1).
- Motor phase order: phase A crossed at each drive, as in the Arctos drawing (Lenton recalls doing this on the 57D drives).
- The motor supply voltage, and the E-stop itself (SAFE-01; ruling R25b: not yet fitted).
- Decoupling and the sensors' own components are not drawn.

## Owned, not wired

Out of scope for now (charter non-goal, 2026-10-15) and not drawn: the gripper jaw servo; the Arduino Nano with its MCP2515 CAN controller, which turns CAN commands into jaw movements; and a second TJA1050 the STM32 may use to reach it on a separate CAN bus.

Update the script when any of these is confirmed, and move the item to the table above.
