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

void SpiDataReady_Init(SpiDataReady_State *state);
bool SpiDataReady_OnFrameStaged(SpiDataReady_State *state, uint32_t now_tick_ms);
bool SpiDataReady_OnFrameConsumed(SpiDataReady_State *state);
bool SpiDataReady_Poll(SpiDataReady_State *state, bool frame_staged, uint32_t now_tick_ms, uint32_t host_stall_ms);

#endif /* SPI_DATA_READY_H */