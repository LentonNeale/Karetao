#include "can_tx_policy.h"

#include <stddef.h>
#include <string.h>

#define CAN_BUS_OFF_WINDOW_MS UINT32_C(60000)
#define CAN_BUS_OFF_INITIAL_DELAY_MS UINT32_C(100)
#define CAN_BUS_OFF_MAX_DELAY_MS UINT32_C(1000)

void CanTxQueue_Init(CanTx_Queue *queue) { if (queue != NULL) { memset(queue, 0, sizeof(*queue)); } }
bool CanTxQueue_Enqueue(CanTx_Queue *queue, const CanTx_Frame *frame, CanTx_Priority priority)
{
    uint8_t index;
    if ((queue == NULL) || (frame == NULL) || (frame->dlc > 8u) || (priority > CAN_TX_PRIORITY_POLL)) { return false; }
    if (queue->count == CAN_TX_QUEUE_CAPACITY) { queue->dropped_count++; return false; }
    index = queue->count++;
    while ((index > 0u) && (priority < queue->entries[index - 1u].priority)) { queue->entries[index] = queue->entries[index - 1u]; --index; }
    queue->entries[index] = (CanTx_Entry){.frame = *frame, .priority = priority, .retry_count = 0u}; return true;
}
bool CanTxQueue_Requeue(CanTx_Queue *queue, const CanTx_Entry *entry)
{
    uint8_t index;
    if ((queue == NULL) || (entry == NULL) || (queue->count == CAN_TX_QUEUE_CAPACITY)) { return false; }
    index = queue->count++;
    while ((index > 0u) && (entry->priority < queue->entries[index - 1u].priority)) { queue->entries[index] = queue->entries[index - 1u]; --index; }
    queue->entries[index] = *entry;
    return true;
}
bool CanTxQueue_Dequeue(CanTx_Queue *queue, CanTx_Entry *entry)
{
    if ((queue == NULL) || (entry == NULL) || (queue->count == 0u)) { return false; }
    *entry = queue->entries[0]; memmove(&queue->entries[0], &queue->entries[1], (queue->count - 1u) * sizeof(queue->entries[0])); queue->count--; return true;
}
void CanBusOff_Init(CanBusOff_State *state) { if (state != NULL) { *state = (CanBusOff_State){.recovery_delay_ms = CAN_BUS_OFF_INITIAL_DELAY_MS}; } }
bool CanBusOff_Record(CanBusOff_State *state, uint32_t now_ms)
{
    if (state == NULL) { return true; }
    if ((now_ms - state->window_start_ms) > CAN_BUS_OFF_WINDOW_MS) { state->window_start_ms = now_ms; state->bus_off_events = 0u; state->recovery_delay_ms = CAN_BUS_OFF_INITIAL_DELAY_MS; }
    state->normal_commands_inhibited = true; state->bus_off_events++; state->next_recovery_ms = now_ms + state->recovery_delay_ms; state->recovery_due = true;
    return state->bus_off_events >= 3u;
}
bool CanBusOff_RecoveryDue(const CanBusOff_State *state, uint32_t now_ms) { return (state != NULL) && state->recovery_due && ((int32_t)(now_ms - state->next_recovery_ms) >= 0); }
void CanBusOff_RecoveryResult(CanBusOff_State *state, bool recovered, uint32_t now_ms)
{
    if (state == NULL) { return; }
    state->recovery_due = !recovered;
    if (!recovered) { state->recovery_delay_ms = (state->recovery_delay_ms < CAN_BUS_OFF_MAX_DELAY_MS / 2u) ? state->recovery_delay_ms * 2u : CAN_BUS_OFF_MAX_DELAY_MS; state->next_recovery_ms = now_ms + state->recovery_delay_ms; }
}
void CanBusOff_AllowNormalCommands(CanBusOff_State *state) { if (state != NULL) { state->normal_commands_inhibited = false; } }