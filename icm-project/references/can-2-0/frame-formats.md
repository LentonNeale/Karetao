# Frame formats and arbitration (CAN 2.0, Part B text; citations are PDF pages)

Part A of the same file (pp. 29-72) covers only the 11-bit Standard Format; these rows use Part B (pp. 75-111), which covers both formats.

| Rule | Value | Citation |
|---|---|---|
| Frame formats | Frames with 11 bit Identifier fields are denoted Standard Frames, while frames with 12 bit Identifier fields are denoted Extended frames. (printed as "12"; the Extended Identifier is 29 bits, p. 85) | p. 83 |
| Frame types | Message transfer is manifested and controlled by four different frame types: Data, Remote, Error, Overload | p. 83 |
| Data frame fields | Start of frame, Arbitration field, Control field, Data field, CRC field, ACKfield, End of frame. The Data field can be of length zero. | p. 84 |
| Start of frame | It consists of a single dominant bit. | p. 84 |
| Standard arbitration field | the 11 bit Identifier and the RTR-Bit. The Identifier bits are denoted ID-28 ... ID-18. | p. 85 |
| Extended arbitration field | the 29 bit Identifier, the SRR-Bit, the IDE-Bit, and the RTR-Bit. The Identifier bits are denoted ID-28 ... ID-0. | p. 85 |
| Identifier restriction | The 7 most significant bits (ID-28 - ID-22) must not be all recessive. | p. 85 |
| Extended ID split | Base ID with 11 bits and the Extended ID with 18 bits. | p. 85 |
| RTR bit | In Data frames the RTR bit has to be dominant. Within a Remote frame the RTR bit has to be recessive. | p. 86 |
| SRR bit | The SRR is a recessive bit. | p. 86 |
| Standard vs Extended collision | the Standard Frame prevails over the Extended Frame | p. 86 |
| IDE bit | The IDE bit in the Standard Format is transmitted dominant, whereas in the Extended Format the IDE bit is recessive. | p. 86 |
| Control field | The Control field consists of six bits. | p. 86 |
| Reserved bits | The reserved bits must be sent dominant, but the Receivers accept dominant and recessive bits in all combinations. | p. 86 |
| DLC | This Data length code is 4 bits wide; The DLC bits can code data lengths from 0 to 8 bytes; other values are not permitted. | p. 87 |
| Data field | It can contain from 0 to 8 bytes, each of which contain 8 bits which are transferred MSB first. | p. 87 |
| DLC 8 coding | DLC3 r, DLC2 d, DLC1 d, DLC0 d = 8 data bytes (d = dominant, r = recessive) | p. 87 |
| CRC generator polynomial | X15 + X14 + X10 + X8 + X7 + X4 + X3 + 1 | p. 88 |
| CRC register | CRC_RG(14:0) is a 15-bit shift register, initialised to 0; EXOR (4599 hex) | p. 88 |
| CRC input | the destuffed bit-stream consisting of Start of frame, Arbitration field, Control field, Data field (if present) | p. 88 |
| CRC code property | a cyclic redundancy code best suited to frames with bit counts less than 127 bits (BCH Code) | p. 88 |
| CRC delimiter | consists of a single recessive bit | p. 88 |
| ACK field | The ACK field is two bits long and contains the ACK Slot and the ACK Delimiter. | p. 89 |
| ACK slot | A RECEIVER which has received a valid message correctly reports this to the TRANSMITTER by sending a dominant bit during the ACK Slot | p. 89 |
| End of frame | a flag sequence consisting of seven recessive bits | p. 89 |
| Remote frame | There is no Data field in a Remote frame, irrespective of the value of the Data length code | p. 90 |
| Standard Data frame length | number of bits = 44 + 8N (0 ≤ N ≤ 8) | p. 96 |
| Standard Remote frame length | number of bits = 44 | p. 96 |
| Bus loading | Therefore the bus should not be loaded to 100%. | p. 90 |
| INTERMISSION | INTERMISSION consists of three recessive bits. | p. 94 |
| Suspend transmission | After an error-passive node has transmitted a frame, it sends eight recessive bits following INTERMISSION | p. 95 |
| Bus idle | The detection of a dominant bit on the bus is interpreted as Start of frame. | p. 95 |
| Frame-format conformance | Every new controller supports the Standard Format; Every new controller can receive messages of the Extended Format. | p. 95 |
| Message filtering | Message filtering is based upon the whole Identifier. | p. 95 |
| Bit stuffing | Whenever a transmitter detects five consecutive bits of identical value in the bit-stream to be transmitted, it automatically inserts a complementary bit | p. 99 |
| Stuffed fields | Start of frame, Arbitration field, Control field, Data field and CRC Sequence | p. 99 |
| Unstuffed fields | CRC Delimiter, ACK field and End of frame | p. 99 |
| Coding | The bit-stream in a message is coded according to the Non-Return-to-Zero (NRZ) method. | p. 99 |
| Priority | The Identifier defines a static message priority during bus access. | p. 77 |
| Bit-rate uniformity | in a given system the bit-rate is uniform and fixed. | p. 77 |
| Arbitration | the bus access conflict is resolved by bit-wise arbitration using the Identifier | p. 78 |
| Data vs Remote at same ID | the Data frame prevails over the Remote frame | p. 78 |
| Lost arbitration | When a recessive level is sent, but a dominant level is monitored, the node has lost arbitration and must withdraw | p. 78 |
| Message validity, transmitter | The message is valid for the transmitter if there is no error until the End of frame. | p. 99 |
| Message validity, receiver | The message is valid for the receiver if there is no error until the last but one bit of End of frame. | p. 99 |
| Retransmission | If a message is corrupted, retransmission will follow automatically | p. 99 |
