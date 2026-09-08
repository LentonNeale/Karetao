/**
 * @file spi_data_ready.h
 * @brief DATA_READY line state tracking for the SPI slave service.
 */

#ifndef SPI_DATA_READY_H
#define SPI_DATA_READY_H

#include <stdbool.h>
#include <stdint.h>

/**
 * @brief Runtime state for the DATA_READY GPIO owned by SpiSlaveService.
 *
 * The state starts low during initialization, rises when a complete frame is
 * staged, and returns low when DMA ownership begins. The counters describe how
 * often the notification path, poll-based recovery, and host-stall detection
 * were exercised across that lifecycle.
 */
typedef struct
{
    bool high;
    bool host_stall_reported;
    uint32_t notification_count;
    uint32_t poll_recovery_count;
    uint32_t host_stall_count;
    uint32_t asserted_tick_ms;
} SpiDataReady_State;

/** Reset DATA_READY tracking to the boot state with the line considered low. */
void SpiDataReady_Init(SpiDataReady_State *state);
/** Record that a complete frame has been staged and DATA_READY should rise. */
bool SpiDataReady_OnFrameStaged(SpiDataReady_State *state, uint32_t now_tick_ms);
/** Record that the staged frame has been consumed and DATA_READY should fall. */
bool SpiDataReady_OnFrameConsumed(SpiDataReady_State *state);
/** Repair missed assertions and count host stalls while a frame remains staged. */
bool SpiDataReady_Poll(SpiDataReady_State *state, bool frame_staged, uint32_t now_tick_ms, uint32_t host_stall_ms);

#endif /* SPI_DATA_READY_H */