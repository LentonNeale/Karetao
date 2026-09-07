#ifndef CAN_TX_POLICY_H
#define CAN_TX_POLICY_H

#include <stdbool.h>
#include <stdint.h>

#define CAN_TX_QUEUE_CAPACITY UINT8_C(8)

typedef enum { CAN_TX_PRIORITY_SAFETY = 0, CAN_TX_PRIORITY_MOTION, CAN_TX_PRIORITY_POLL } CanTx_Priority;
typedef struct { uint16_t id; uint8_t dlc; uint8_t data[8]; } CanTx_Frame;
typedef struct { CanTx_Frame frame; CanTx_Priority priority; uint8_t retry_count; } CanTx_Entry;
typedef struct { CanTx_Entry entries[CAN_TX_QUEUE_CAPACITY]; uint8_t count; uint32_t dropped_count; } CanTx_Queue;
typedef struct { bool normal_commands_inhibited; bool recovery_due; uint8_t bus_off_events; uint32_t window_start_ms; uint32_t next_recovery_ms; uint32_t recovery_delay_ms; } CanBusOff_State;

void CanTxQueue_Init(CanTx_Queue *queue);
bool CanTxQueue_Enqueue(CanTx_Queue *queue, const CanTx_Frame *frame, CanTx_Priority priority);
bool CanTxQueue_Requeue(CanTx_Queue *queue, const CanTx_Entry *entry);
bool CanTxQueue_Dequeue(CanTx_Queue *queue, CanTx_Entry *entry);
void CanBusOff_Init(CanBusOff_State *state);
bool CanBusOff_Record(CanBusOff_State *state, uint32_t now_ms);
bool CanBusOff_RecoveryDue(const CanBusOff_State *state, uint32_t now_ms);
void CanBusOff_RecoveryResult(CanBusOff_State *state, bool recovered, uint32_t now_ms);
void CanBusOff_AllowNormalCommands(CanBusOff_State *state);

#endif /* CAN_TX_POLICY_H */