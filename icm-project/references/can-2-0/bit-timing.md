# Bit timing (CAN 2.0, Part B section 13; citations are PDF pages)

| Rule | Value | Citation |
|---|---|---|
| Nominal bit time | NOMINAL BIT TIME = 1 / NOMINAL BIT RATE | p. 107 |
| Segments | SYNC_SEG, PROP_SEG, PHASE_SEG1, PHASE_SEG2 | p. 107 |
| SYNC_SEG | An edge is expected to lie within this segment | p. 108 |
| PROP_SEG | twice the sum of the signal's propagation time on the bus line, the input comparator delay, and the output driver delay | p. 108 |
| PHASE_SEG1, PHASE_SEG2 | These segments can be lengthened or shortened by resynchronization. | p. 108 |
| Sample point | Its location is at the end of PHASE_SEG1. | p. 108 |
| Information processing time | the time segment starting with the Sample point reserved for calculation of the subsequent bit level | p. 108 |
| Time quantum | TIME QUANTUM = m × MINIMUM TIME QUANTUM, m the prescaler value | p. 108 |
| Prescaler range | integral values (with a range of at least 1 to 32) | p. 108 |
| SYNC_SEG length | SYNC_SEG is 1 Time quantum long | p. 109 |
| PROP_SEG length | PROP_SEG is programmable to be 1, 2, ......8 Time quanta long | p. 109 |
| PHASE_SEG1 length | PHASE_SEG1 is programmable to be 1, 2, ......8 Time quanta long | p. 109 |
| PHASE_SEG2 length | PHASE_SEG2 is the maximum of PHASE_SEG1 and the Information processing time | p. 109 |
| Information processing time length | less than or equal to 2 Time quanta long | p. 109 |
| Quanta per bit | The total number of Time quanta in a bit time must be programmable over a range of at least 8 to 25. | p. 109 |
| Fixed-timing devices (no CPU) | 1 Time quantum SYNC, 1 Time quantum PROP, 4 Time quanta PHASE_SEG1, 4 Time quanta PHASE_SEG2, 10 Time quanta per bit | p. 109 |
| Sample point rule | The position of the sample point, however, should be selected in common for all nodes. | p. 109 |
| Hard synchronization | After a Hard synchronization the internal bit time is restarted with SYNC_SEG. | p. 110 |
| Resynchronization jump width | programmable between 1 and the smaller of 4 and PHASE_SEG1 Time quanta | p. 110 |
| Resync edge spacing | The maximum length between two transitions which can be used for resynchronization is 29 bit times. | p. 110 |
| Resync with large phase error | positive: PHASE_SEG1 is lengthened by an amount equal to the Resynchronization jump width | p. 110 |
| Resync with large negative error | PHASE_SEG2 is shortened by an amount equal to the Resynchronization jump width | p. 111 |
| Sync rule 1 | Only one Synchronization within one bit time is allowed. | p. 111 |
| Sync rule 3 | Hard synchronization is performed whenever there is a recessive to dominant edge during Bus idle. | p. 111 |
