# Error handling and fault confinement (CAN 2.0, Part B text; citations are PDF pages)

| Rule | Value | Citation |
|---|---|---|
| Error types | There are five different error types (which are not mutually exclusive). | p. 101 |
| Bit error | the bit value monitored is different from the bit value being sent | p. 101 |
| Bit error exceptions | sending of a recessive bit during the stuffed bit-stream of the Arbitration Field or during the ACK Slot | p. 101 |
| Stuff error | the bit time of the sixth consecutive equal bit level (6 consecutive dominant or 6 consecutive recessive levels) | p. 101 |
| CRC error | A CRC Error must be recognized if the calculated result is not the same as that received in the CRC sequence. | p. 101 |
| Form error | A Form Error must be detected when a fixed-form bit field contains one or more illegal bits. | p. 102 |
| Acknowledgement error | detected by a transmitter whenever it does not monitor a dominant bit during ACK Slot | p. 102 |
| Error flag start | Bit, Stuff, Form or Acknowledgement Error: start transmission of an Error Flag at the next bit time. | p. 102 |
| CRC error flag start | transmission of an Error Flag will start at the bit following the ACK Delimiter | p. 102 |
| ACTIVE Error flag | ACTIVE Error flag consists of six consecutive dominant bits. | p. 91 |
| PASSIVE Error flag | The PASSIVE Error flag consists of six consecutive recessive bits unless it is overwritten by dominant bits from other nodes. | p. 91 |
| Superposed error flags | The total length of this sequence varies between a minimum of six and a maximum of twelve bits. | p. 91 |
| Error delimiter | The Error Delimiter consists of eight recessive bits. | p. 91 |
| Overload flag | The Overload flag consists of six dominant bits. | p. 93 |
| Overload delimiter | The Overload Delimiter consists of eight recessive bits. | p. 93 |
| Overload frames per delay | At most, two Overload frames may be generated to delay the next Data frame or Remote frame. | p. 92 |
| Error detection measures | Monitoring; Cyclic Redundancy Check (CRC); Bit-Stuffing; Message Frame Check | p. 78 |
| CRC performance | Up to 5 randomly transmitted errors within a sequence are detected; Burst errors of length less than 15 in a message are detected | p. 79 |
| Residual error probability | The total residual error probability of undetected corrupted messages is less than 4.7 x 10-11. | p. 79 |
| Recovery time | The recovery time from detecting an error until the start of the next message is at most 31 bit times, provided there is no further error. | p. 79 |
| Retransmission | Such messages are aborted and will be retransmitted automatically. | p. 79 |
| Node states | a node may be in one of three states: error-active, error-passive, or bus-off. | p. 103 |
| Bus-off node | A bus-off node is not allowed to have any influence on the bus (e.g. output drivers switched off). | p. 103 |
| Counts | TRANSMIT ERROR COUNT; RECEIVE ERROR COUNT | p. 103 |
| Rule 1 | When a RECEIVER detects an error, the Receive Error Count will be increased by 1 | p. 103 |
| Rule 2 | RECEIVER detects a dominant bit as the first bit after sending an Error Flag: Receive Error Count increased by 8 | p. 103 |
| Rule 3 | When a TRANSMITTER sends an Error Flag, the Transmit Error Count is increased by 8. | p. 104 |
| Rule 6 | Any node tolerates up to 7 consecutive dominant bits after sending an ACTIVE Error Flag or a PASSIVE Error Flag. | p. 104 |
| Rule 7 | After the successful transmission of a message, the Transmit Error Count is decreased by 1, unless it was already 0. | p. 104 |
| Rule 8 | the Receive Error Count is decreased by 1, if it was between 1 and 127; if it was greater than 127, then it will be set to a value between 119 and 127. | pp. 104-105 |
| Rule 9, error passive | when the Transmit Error Count equals or exceeds 128, or when the Receive Error Count equals or exceeds 128 | p. 105 |
| Rule 10, bus-off | A node is bus-off when the Transmit Error Count is greater than or equal to 256. | p. 105 |
| Rule 11, back to error-active | both the Transmit Error Count and the Receive Error Count are less than or equal to 127 | p. 105 |
| Rule 12, bus-off recovery | after 128 occurrences of 11 consecutive recessive bits have been monitored on the bus; error counters both set to 0 | p. 105 |
| Heavily disturbed bus | An error count value greater than about 96 indicates a heavily disturbed bus. | p. 105 |
| Start-up with one node | It can become error-passive but not bus-off due to this reason. | p. 105 |
