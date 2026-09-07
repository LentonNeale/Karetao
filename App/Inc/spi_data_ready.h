/**
 * @file spi_data_ready.h
 * @brief Implements the spi data ready module.
 */

#ifndef SPI_DATA_READY_H
#define SPI_DATA_READY_H

#include <stdbool.h>
#include <stdint.h>

typedef struct
{
    bool high;
    bool host_stall_reported;
    uint32_t notification_count;
    uint32_t poll_recovery_count;
    uint32_t host_stall_count;
    uint32_t asserted_tick_ms;
} SpiDataReady_State;

/**
 * @brief Executes data ready init.
 */
void SpiDataReady_Init(SpiDataReady_State *state);
/**
 * @brief Executes data ready on frame staged.
 */
bool SpiDataReady_OnFrameStaged(SpiDataReady_State *state, uint32_t now_tick_ms);
/**
 * @brief Executes data ready on frame consumed.
 */
bool SpiDataReady_OnFrameConsumed(SpiDataReady_State *state);
/**
 * @brief Executes data ready poll.
 */
bool SpiDataReady_Poll(SpiDataReady_State *state, bool frame_staged, uint32_t now_tick_ms, uint32_t host_stall_ms);

#endif /* SPI_DATA_READY_H */