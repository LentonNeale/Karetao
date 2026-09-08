/**
 * @file snapshot_builder.c
 * @brief Frame-pool ownership helpers for SPI snapshot and response staging.
 */

#include "snapshot_builder.h"

#include <stddef.h>
#include <string.h>

/** Find the first frame buffer currently in the requested ownership state. */
static int32_t SnapshotFramePool_FindState(const SnapshotFrame_Pool *pool, SnapshotFrame_State state)
{
    uint8_t frame_index;

    for (frame_index = 0u; frame_index < SNAPSHOT_FRAME_BUFFER_COUNT; ++frame_index)
    {
        if (pool->frame_states[frame_index] == state)
        {
            return (int32_t)frame_index;
        }
    }

    return -1;
}

/** Reset both frame buffers so the SPI service starts from an empty pool. */
void SnapshotFramePool_Init(SnapshotFrame_Pool *pool)
{
    if (pool != NULL)
    {
        memset(pool, 0, sizeof(*pool));
    }
}

/**
 * Serialize a new frame into a free buffer or replace the unread staged frame
 * when that is the only non-DMA-owned slot left.
 */
SnapshotBuild_Result SnapshotBuilder_Stage(SnapshotFrame_Pool *pool,
                                           SnapshotBuilder_SerializeCallback serialize,
                                           void *context)
{
    int32_t free_index;
    int32_t staged_index;
    uint16_t frame_length = 0u;
    bool replacing_staged_in_place;

    if ((pool == NULL) || (serialize == NULL))
    {
        return SNAPSHOT_BUILD_INVALID_ARGUMENT;
    }

    free_index = SnapshotFramePool_FindState(pool, SNAPSHOT_FRAME_FREE);
    staged_index = SnapshotFramePool_FindState(pool, SNAPSHOT_FRAME_STAGED);
    if ((free_index < 0) && (staged_index < 0))
    {
        pool->diagnostics.dropped_frame_count++;
        return SNAPSHOT_BUILD_NO_BUFFER;
    }

    replacing_staged_in_place = free_index < 0;
    if (replacing_staged_in_place)
    {
        free_index = staged_index;
    }

    if (!serialize(pool->frame_buffers[free_index], SPI_FRAME_MAX_BYTES, &frame_length, context) ||
        (frame_length == 0u) || (frame_length > SPI_FRAME_MAX_BYTES))
    {
        if (replacing_staged_in_place)
        {
            pool->frame_states[free_index] = SNAPSHOT_FRAME_FREE;
            pool->frame_lengths[free_index] = 0u;
            pool->diagnostics.dropped_frame_count++;
        }

        return SNAPSHOT_BUILD_SERIALIZATION_FAILED;
    }

    if ((staged_index >= 0) && (staged_index != free_index))
    {
        pool->frame_states[staged_index] = SNAPSHOT_FRAME_FREE;
        pool->frame_lengths[staged_index] = 0u;
    }

    if (staged_index >= 0)
    {
        pool->diagnostics.replaced_unread_frame_count++;
    }

    pool->frame_lengths[free_index] = frame_length;
    pool->frame_states[free_index] = SNAPSHOT_FRAME_STAGED;
    pool->diagnostics.staged_frame_count++;
    return SNAPSHOT_BUILD_OK;
}

/** Hand the staged frame to the DMA path while preventing double ownership. */
bool SnapshotFramePool_BeginDma(SnapshotFrame_Pool *pool,
                                const uint8_t **frame_buffer,
                                uint16_t *frame_length)
{
    int32_t staged_index;

    if ((pool == NULL) || (frame_buffer == NULL) || (frame_length == NULL) ||
        (SnapshotFramePool_FindState(pool, SNAPSHOT_FRAME_DMA_ACTIVE) >= 0))
    {
        return false;
    }

    staged_index = SnapshotFramePool_FindState(pool, SNAPSHOT_FRAME_STAGED);
    if (staged_index < 0)
    {
        return false;
    }

    pool->frame_states[staged_index] = SNAPSHOT_FRAME_DMA_ACTIVE;
    *frame_buffer = pool->frame_buffers[staged_index];
    *frame_length = pool->frame_lengths[staged_index];
    pool->diagnostics.dma_start_count++;
    return true;
}

/** Return the DMA-owned frame buffer to the free pool after transfer completion. */
bool SnapshotFramePool_CompleteDma(SnapshotFrame_Pool *pool)
{
    int32_t active_index;

    if (pool == NULL)
    {
        return false;
    }

    active_index = SnapshotFramePool_FindState(pool, SNAPSHOT_FRAME_DMA_ACTIVE);
    if (active_index < 0)
    {
        return false;
    }

    pool->frame_states[active_index] = SNAPSHOT_FRAME_FREE;
    pool->frame_lengths[active_index] = 0u;
    pool->diagnostics.dma_complete_count++;
    return true;
}

/** Inspect the currently staged frame without changing ownership. */
const uint8_t *SnapshotFramePool_GetStagedFrame(const SnapshotFrame_Pool *pool,
                                                uint16_t *frame_length)
{
    int32_t staged_index;

    if ((pool == NULL) || (frame_length == NULL))
    {
        return NULL;
    }

    staged_index = SnapshotFramePool_FindState(pool, SNAPSHOT_FRAME_STAGED);
    if (staged_index < 0)
    {
        return NULL;
    }

    *frame_length = pool->frame_lengths[staged_index];
    return pool->frame_buffers[staged_index];
}

/** Expose accumulated frame-pool diagnostics to higher-level SPI service code. */
const SnapshotFrame_Diagnostics *SnapshotFramePool_GetDiagnostics(const SnapshotFrame_Pool *pool)
{
    return (pool == NULL) ? NULL : &pool->diagnostics;
}