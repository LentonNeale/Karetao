/**
 * @file snapshot_builder.h
 * @brief Two-buffer snapshot staging and DMA ownership helpers for SPI output.
 */

#ifndef SNAPSHOT_BUILDER_H
#define SNAPSHOT_BUILDER_H

#include <stdbool.h>
#include <stdint.h>

#include "spi_payload_layout.h"

/**
 * @brief Lifecycle state of one serialized SPI frame buffer.
 */
typedef enum
{
    /** Buffer is available for a new serialized snapshot or response. */
    SNAPSHOT_FRAME_FREE = 0,
    /** Buffer contains a complete frame waiting for the host to consume it. */
    SNAPSHOT_FRAME_STAGED,
    /** Buffer is currently owned by the DMA transfer path. */
    SNAPSHOT_FRAME_DMA_ACTIVE
} SnapshotFrame_State;

/** Outcome of attempting to serialize and stage a new SPI frame. */
typedef enum
{
    SNAPSHOT_BUILD_OK = 0,
    SNAPSHOT_BUILD_NOT_READY,
    SNAPSHOT_BUILD_INVALID_ARGUMENT,
    SNAPSHOT_BUILD_NO_BUFFER,
    SNAPSHOT_BUILD_SERIALIZATION_FAILED,
    /** Another caller is staging a frame; nothing was staged, try again later. */
    SNAPSHOT_BUILD_BUSY
} SnapshotBuild_Result;

/**
 * @brief Application serializer used to materialize a complete SPI frame.
 *
 * The callback runs in task context against a free frame buffer supplied by the
 * pool and must report the number of bytes written.
 */
typedef bool (*SnapshotBuilder_SerializeCallback)(uint8_t *frame_buffer,
                                                   uint16_t frame_capacity,
                                                   uint16_t *frame_length,
                                                   void *context);

/** Counters describing snapshot replacement, dropping, and DMA ownership flow. */
typedef struct
{
    uint32_t staged_frame_count;
    uint32_t replaced_unread_frame_count;
    uint32_t dropped_frame_count;
    uint32_t dma_start_count;
    uint32_t dma_complete_count;
} SnapshotFrame_Diagnostics;

/** Double-buffered frame pool used by the SPI service. */
#define SNAPSHOT_FRAME_BUFFER_COUNT UINT8_C(2)

/**
 * @brief Serialized frame buffers and their ownership metadata.
 *
 * The pool starts with every buffer free, promotes one buffer to staged after
 * successful serialization, and transitions that buffer to DMA_ACTIVE until the
 * transfer completion path releases it back to FREE.
 */
typedef struct
{
    uint8_t frame_buffers[SNAPSHOT_FRAME_BUFFER_COUNT][SPI_FRAME_MAX_BYTES];
    uint16_t frame_lengths[SNAPSHOT_FRAME_BUFFER_COUNT];
    SnapshotFrame_State frame_states[SNAPSHOT_FRAME_BUFFER_COUNT];
    SnapshotFrame_Diagnostics diagnostics;
} SnapshotFrame_Pool;

/** Reset the frame pool so both buffers start free with zero diagnostics. */
void SnapshotFramePool_Init(SnapshotFrame_Pool *pool);
/** Serialize into a free or replaceable staged buffer and mark it staged. */
SnapshotBuild_Result SnapshotBuilder_Stage(SnapshotFrame_Pool *pool,
                                          SnapshotBuilder_SerializeCallback serialize,
                                          void *context);
/** Hand the currently staged frame to the DMA path and mark it active. */
bool SnapshotFramePool_BeginDma(SnapshotFrame_Pool *pool,
                                const uint8_t **frame_buffer,
                                uint16_t *frame_length);
/** Release the DMA-owned frame after transfer completion is deferred to task context. */
bool SnapshotFramePool_CompleteDma(SnapshotFrame_Pool *pool);
/** Inspect the currently staged frame without transferring ownership. */
const uint8_t *SnapshotFramePool_GetStagedFrame(const SnapshotFrame_Pool *pool,
                                                uint16_t *frame_length);
/** Read frame-pool diagnostics accumulated across staging and DMA lifecycles. */
const SnapshotFrame_Diagnostics *SnapshotFramePool_GetDiagnostics(const SnapshotFrame_Pool *pool);

#endif /* SNAPSHOT_BUILDER_H */