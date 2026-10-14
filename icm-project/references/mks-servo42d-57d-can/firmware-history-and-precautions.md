# Firmware history, precautions and compatibility (MKS SERVO42D/57D CAN manual V1.0.9)

The version notes (pp. 1-2), precautions and error messages (Part 14) and schematics (Part 15).

## Firmware history

| Rule | Value | Citation |
|---|---|---|
| Manual version | This manual corresponds to firmware version V 1.0.9 | p. 1 |
| V1.0.1 | Apr-2023: Added a command to set the current position to 0; Added group CAN ID management | p. 1 |
| V1.0.3 | Jul-2023: single-turn zero return parameter (9AH); command lock button (8FH); IO port status reading (34H); Add left and right limit functions | p. 1 |
| V1.0.4 | Sep-2023: holding current percentage (9BH); absolute motion based on pulse count (FEH); emergency stop command (F7H); limit port remapping instruction (9EH) | p. 1 |
| V1.0.5 | May-2024: Supports zero-return function for infinite position switch; Add (94H) instruction; reset and restart motor command (41H) | p. 1 |
| V1.0.6 | Sep-2024: read the encoder's raw value (35H); En signal-triggered single-turn zeroing and position over-tolerance protection (9DH); write I/O port instruction (36H) | p. 2 |
| V1.0.7 | Mar-2025: 3BH reads the zero-state value; 83H changes the current during operation without saving it; F6H sets the runtime | p. 2 |
| V1.0.8 | Jul-2025: no recalibration after restoring defaults; multi-motor synchronous control (Part 12); location arrival threshold (5.2.16); PID parameters (5.3) | p. 2 |
| V1.0.9 | Nov-2025: automatically returning read-only parameters at regular intervals (5.1.9); heart rate protection time (5.2.15); coordinate zeroing (7.2, 7.7); no-verification mode (5.2.17) | p. 2 |

## Precautions (14.1)

| Rule | Value | Citation |
|---|---|---|
| Supply | Power input voltage 12V-24V | p. 103 |
| Hot plugging | Do not plug or unplug the power cord or signal cable while the circuit is powered on, as this may damage the driver board | p. 103 |
| Factory reset | Press and hold the "Next" button, then power on the device to quickly restore factory default settings | p. 103 |
| Calibration load | Do not apply a load when calibrating the motor | p. 103 |
| Recalibration | the driver board is first installed on the motor, or after the motor wiring sequence is changed, the motor needs to be recalibrated | p. 103 |
| Phase Line Error | Check the motor wiring sequence; check the power supply voltage and output power (24V/1A, 12V/2A) | p. 103 |
| Third-party motors | The motor step distance is 1.8 degrees; internal resistance is less than 10 ohms; A radial magnet can be installed on the back of the motor | p. 103 |

## Screen error messages (14.2)

| Rule | Value | Citation |
|---|---|---|
| Not Cal | Calibrate the motor | p. 104 |
| Reverse Lookup Error! | Calibrate Fail, Check magnet and motor shaft | p. 104 |
| Magnet Loss! / Strong! / Weak! | Not install the magent; the magnet too near; the magnet too far | p. 104 |
| Encoder Error! | Check magnet and motor shaft | p. 104 |
| Offset Current Error! | Reference voltage error | p. 104 |
| Phase Line Error! | The motor line sequence is wrong or the power supply is not enough | p. 104 |
| Wrong Protect! | Locked-rotor protection | p. 104 |
| Low Voltage Error! | The supply voltage is too low | p. 104 |
| Other messages | Coming Back to Origin..; Reboot Again; Press Next Key To Fixed | p. 104 |

## Host software compatibility (14.3)

| Rule | Value | Citation |
|---|---|---|
| Firmware 1.0.3 | host computer 1.0.3/1.0.3.1 | p. 105 |
| Firmware 1.0.4 and 1.0.5 | host computer 1.0.3.1 | p. 105 |
| Firmware 1.0.6 to 1.0.8 | host computer Version 1.0.6.1/1.0.6.2 | p. 105 |
| Firmware 1.0.9 | host computer 1.0.9 | p. 105 |
| Reading the firmware version | viewed on the screen when the driver board is powered on; with no screen, send a serial port 40H command | p. 105 |

## Schematics (Part 15)

| Rule | Value | Citation |
|---|---|---|
| Schematic links | https://github.com/makerbase-motor/MKS-SERVO42D and https://github.com/makerbase-motor/MKS-SERVO57D | p. 106 |

Checked 2026-10-15: `MKS-SERVO42D` returns 404 and `MKS-SERVO57D` redirects to the combined repo
https://github.com/makerbase-motor/MKS-SERVO42D-57D. That repo's `Hardware/` folder holds the
schematics, including `MKS SERVO42D_CAN V1.0_003 Schematic.pdf` and
`MKS SERVO57D_CAN V1.1_001 Schematic.pdf` (the CAN boards this project uses).
