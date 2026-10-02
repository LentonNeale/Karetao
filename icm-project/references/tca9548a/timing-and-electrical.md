# Timing and electrical limits (TCA9548A)

Printed pages (same as PDF pages of the local copy). Fast mode is the 400 kHz row set.

| Rule | Value | Citation |
|---|---|---|
| Clock frequency | 0 to 400kHz | p. 1 |
| Fast mode fscl | 0 min, 400 max kHz | p. 7 |
| Fast mode tsch, I2C clock high time | 0.6 μs min | p. 7 |
| Fast mode tscl, I2C clock low time | 1.3 μs min | p. 7 |
| Fast mode tsp, spike time | 50 ns max | p. 7 |
| Fast mode tsds, data setup time | 100 ns min | p. 7 |
| Fast mode tsdh, data hold time | 0 μs min | p. 7 |
| Fast mode ticr, input rise time | 20 + 0.1Cb min, 300 ns max | p. 7 |
| Fast mode ticf, input fall time | 20 + 0.1Cb min, 300 ns max | p. 7 |
| Fast mode tocf, SDn output fall time (10-pF to 400-pF bus) | 20 + 0.1Cb min, 300 ns max | p. 7 |
| Fast mode tbuf, bus free time between stop and start | 1.3 μs min | p. 7 |
| Fast mode tsts, start or repeated start setup | 0.6 μs min | p. 7 |
| Fast mode tsth, start or repeated start hold | 0.6 μs min | p. 7 |
| Fast mode tsps, stop condition setup | 0.6 μs min | p. 7 |
| Fast mode tvdL(Data) | 1 μs max | p. 7 |
| Fast mode tvdH(Data) | 0.6 μs max | p. 7 |
| Fast mode tvd(ack) | 1 μs max | p. 7 |
| Standard mode fscl | 0 min, 100 max kHz | p. 7 |
| Cb, I2C bus capacitive load | 400 pF max | p. 8 |
| Data hold footnote | A device internally must provide a hold time of at least 300 ns for the SDA signal | p. 8 |
| tW(L), RESET low pulse duration | 6 ns min | p. 8 |
| tREC(STA), recovery from RESET to start | 0 ns min | p. 8 |
| trst, RESET time (SDA clear) | 500 ns max | p. 8 |
| tpd, propagation delay SDA/SCL to SDn/SCn | 0.3 ns max (RON = 20 Ω, CL = 15 pF); 1 ns max (RON = 20 Ω, CL = 50 pF) | p. 8 |
| Supply voltage VCC | 1.65 to 5.5 V (-40 ℃ ≤ TA ≤ 85 ℃); 1.65 to 3.6 V (85 ℃ < TA ≤ 125 ℃) | p. 4 |
| Input high VIH, SCL and SDA | 0.7 × VCC min, 6 V max | p. 4 |
| Input low VIL, SCL and SDA | –0.5 V min, 0.3 × VCC max | p. 4 |
| Operating temperature TA | –40 to 85 ℃ (3.6 V < VCC ≤ 5.5 V); –40 to 125 ℃ (1.65 V ≤ VCC ≤ 3.6 V) | p. 4 |
| Absolute maximum VCC | –0.5 to 7 V | p. 4 |
| Power-on reset VPORR (VCC rising) | 1.2 typ, 1.5 max V | p. 6 |
| Power-on reset VPORF (VCC falling) | 0.8 min, 1 typ V | p. 6 |
| IOL, SDA | 3 mA min at VOL = 0.4 V; 6 mA min at VOL = 0.6 V | p. 6 |
| Switch on-resistance RON, VCC 3 V to 3.6 V | 5 min, 12 typ, 30 max Ω (VO = 0.4 V, IO = 15 mA) | p. 7 |
| Switch on-resistance RON, VCC 4.5 V to 5.5 V | 4 min, 10 typ, 20 max Ω (VO = 0.4 V, IO = 15 mA) | p. 7 |
| Capacitance Cio(off), SCL / SDA | 20 typ, 28 max pF (switch off) | p. 6 |
