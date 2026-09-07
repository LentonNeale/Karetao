#include "spi_data_ready.h"

#include <stddef.h>

void SpiDataReady_Init(SpiDataReady_State *state)
{
    if (state != NULL) { *state = (SpiDataReady_State){0}; }
}

bool SpiDataReady_OnFrameStaged(SpiDataReady_State *state, uint32_t now_tick_ms)
{
    if ((state == NULL) || state->high) { return false; }
    state->high = true; state->host_stall_reported = false; state->asserted_tick_ms = now_tick_ms; state->notification_count++;
    return true;
}

bool SpiDataReady_OnFrameConsumed(SpiDataReady_State *state)
{
    if ((state == NULL) || !state->high) { return false; }
    state->high = false; state->host_stall_reported = false; return true;
}

bool SpiDataReady_Poll(SpiDataReady_State *state, bool frame_staged, uint32_t now_tick_ms, uint32_t host_stall_ms)
{
    if (state == NULL) { return false; }
    if (frame_staged && !state->high) { state->high = true; state->host_stall_reported = false; state->asserted_tick_ms = now_tick_ms; state->poll_recovery_count++; return true; }
    if (frame_staged && state->high && !state->host_stall_reported && ((now_tick_ms - state->asserted_tick_ms) >= host_stall_ms)) { state->host_stall_reported = true; state->host_stall_count++; }
    return false;
}