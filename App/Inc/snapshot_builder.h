#ifndef SNAPSHOT_BUILDER_H
#define SNAPSHOT_BUILDER_H

#include <stdbool.h>
#include <stdint.h>

#include "spi_payload_layout.h"

typedef enum
{
    SNAPSHOT_FRAME_FREE = 0,
    SNAPSHOT_FRAME_STAGED,
    SNAPSHOT_FRAME_DMA_ACTIVE
} SnapshotFrame_State;

typedef enum
{
    SNAPSHOT_BUILD_OK = 0,
    SNAPSHOT_BUILD_NOT_READY,
    SNAPSHOT_BUILD_INVALID_ARGUMENT,
    SNAPSHOT_BUILD_NO_BUFFER,
    SNAPSHOT_BUILD_SERIALIZATION_FAILED
} SnapshotBuild_Result;

typedef bool (*SnapshotBuilder_SerializeCallback)(uint8_t *frame_buffer,
                                                   uint16_t frame_capacity,
                                                   uint16_t *frame_length,
                                                   void *context);

typedef struct
{
    uint32_t staged_frame_count;
    uint32_t replaced_unread_frame_count;
    uint32_t dropped_frame_count;
    uint32_t dma_start_count;
    uint32_t dma_complete_count;
} SnapshotFrame_Diagnostics;

#define SNAPSHOT_FRAME_BUFFER_COUNT UINT8_C(2)

typedef struct
{
    uint8_t frame_buffers[SNAPSHOT_FRAME_BUFFER_COUNT][SPI_FRAME_MAX_BYTES];
    uint16_t frame_lengths[SNAPSHOT_FRAME_BUFFER_COUNT];
    SnapshotFrame_State frame_states[SNAPSHOT_FRAME_BUFFER_COUNT];
    SnapshotFrame_Diagnostics diagnostics;
} SnapshotFrame_Pool;

void SnapshotFramePool_Init(SnapshotFrame_Pool *pool);
SnapshotBuild_Result SnapshotBuilder_Stage(SnapshotFrame_Pool *pool,
                                           SnapshotBuilder_SerializeCallback serialize,
                                           void *context);
bool SnapshotFramePool_BeginDma(SnapshotFrame_Pool *pool,
                                const uint8_t **frame_buffer,
                                uint16_t *frame_length);
bool SnapshotFramePool_CompleteDma(SnapshotFrame_Pool *pool);
const uint8_t *SnapshotFramePool_GetStagedFrame(const SnapshotFrame_Pool *pool,
                                                uint16_t *frame_length);
const SnapshotFrame_Diagnostics *SnapshotFramePool_GetDiagnostics(const SnapshotFrame_Pool *pool);

#endif /* SNAPSHOT_BUILDER_H */