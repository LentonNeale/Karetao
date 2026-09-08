/**
 * @file spi_data_ready.c
 * @brief DATA_READY line tracking for staged SPI response frames.
 */

#include "spi_data_ready.h"

#include <stddef.h>

/**
 * Reset the GPIO-tracking state so the SPI service starts with no staged frame
 * advertised to the host.
 */
void SpiDataReady_Init(SpiDataReady_State *state)
{
    if (state != NULL) { *state = (SpiDataReady_State){0}; }
}

/** Promote a newly staged frame into a visible DATA_READY assertion. */
bool SpiDataReady_OnFrameStaged(SpiDataReady_State *state, uint32_t now_tick_ms)
{
    if ((state == NULL) || state->high) { return false; }
    state->high = true; state->host_stall_reported = false; state->asserted_tick_ms = now_tick_ms; state->notification_count++;
    return true;
}

/** Clear DATA_READY state once the staged frame transfers into DMA ownership. */
bool SpiDataReady_OnFrameConsumed(SpiDataReady_State *state)
{
    if ((state == NULL) || !state->high) { return false; }
    state->high = false; state->host_stall_reported = false; return true;
}

/**
 * Recover missed assertions and report the first observed host stall for the
 * current staged frame.
 */
bool SpiDataReady_Poll(SpiDataReady_State *state, bool frame_staged, uint32_t now_tick_ms, uint32_t host_stall_ms)
{
    if (state == NULL) { return false; }
    if (frame_staged && !state->high) { state->high = true; state->host_stall_reported = false; state->asserted_tick_ms = now_tick_ms; state->poll_recovery_count++; return true; }
    if (frame_staged && state->high && !state->host_stall_reported && ((now_tick_ms - state->asserted_tick_ms) >= host_stall_ms)) { state->host_stall_reported = true; state->host_stall_count++; }
    return false;
}