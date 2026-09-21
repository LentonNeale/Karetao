/**
 * @file spi_slave_service.h
 * @brief Lifecycle-controlled SPI slave orchestration for request/response traffic.
 */

#ifndef SPI_SLAVE_SERVICE_H
#define SPI_SLAVE_SERVICE_H

#include "lifecycle.h"
#include "spi_protocol.h"
#include "spi_data_ready.h"
#include "snapshot_builder.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Debug mirror for SPI transaction timing.
 *
 * This structure records timestamps at four critical points in the SPI transaction
 * lifecycle, allowing observation of pipeline delays between DMA completion,
 * request processing, response staging, and DATA_READY assertion.
 *
 * Declare as: volatile SpiSlaveService_TimingMirror g_spi_timing_dbg
 */
typedef struct
{
    uint32_t dma_complete_raw;     // Raw TIM2 counter at ISR (DMA complete)
    uint32_t process_start_us;     // TimeService_NowUs() at SpiSlaveService_Process() entry
    uint32_t response_staged_us;   // TimeService_NowUs() when response is staged
    uint32_t data_ready_set_us;    // TimeService_NowUs() when DATA_READY GPIO is asserted
    uint8_t  request_type;         // Message type of last processed request
    uint32_t request_seq;          // Sequence number of last processed request
} SpiSlaveService_TimingMirror;

/**
 * @brief Global debug mirror for SPI transaction timing.
 *
 * This volatile global tracks the timing of the last SPI transaction at four key
 * points, allowing hardware debuggers (SWD) to observe pipeline latencies.
 */
extern volatile SpiSlaveService_TimingMirror g_spi_timing_dbg;

/**
 * @brief Initialize SPI service state, protocol state, frame buffers, and DATA_READY.
 *
 * After initialization the service is configured with a boot-status response
 * staged, but publication remains subject to the lifecycle gate.
 */
void SpiSlaveService_Init(void);
/** Transition the SPI service into ACTIVE so frames may be staged and consumed. */
Lifecycle_Result SpiSlaveService_Activate(void);
/** Report the current lifecycle state that gates SPI publication. */
Lifecycle_State SpiSlaveService_GetLifecycleState(void);
/** Run task-context polling and deferred housekeeping for DATA_READY ownership. */
void SpiSlaveService_Process(void);
/** Serialize and stage the next outbound SPI frame using the shared frame pool. */
SnapshotBuild_Result SpiSlaveService_StageSnapshot(SnapshotBuilder_SerializeCallback serialize, void *context);
/** Serialize the latest sensor and motor caches into a compliant snapshot frame. */
SnapshotBuild_Result SpiSlaveService_StageLatestSnapshot(void);
/** Transfer ownership of the staged frame to the DMA path and expose its buffer. */
bool SpiSlaveService_BeginDmaTransfer(const uint8_t **frame_buffer, uint16_t *frame_length);
/** Release the DMA-owned frame after a completed or deferred transfer. */
bool SpiSlaveService_CompleteDmaTransfer(void);
/** Read frame-buffer diagnostics for replacement, drop, and DMA activity. */
const SnapshotFrame_Diagnostics *SpiSlaveService_GetSnapshotDiagnostics(void);
/** Read DATA_READY diagnostics and the current logical signal level. */
const SpiDataReady_State *SpiSlaveService_GetDataReadyState(void);
/** Configure the fallback polling interval used to recover missed DATA_READY assertions. */
void SpiSlaveService_SetPollPeriodMs(uint32_t poll_period_ms);
/** Queue an unsolicited snapshot payload that the next GET_SNAPSHOT may consume. */
bool SpiSlaveService_SetUnsolicitedSnapshot(const uint8_t *payload, uint16_t payload_length);
/** Validate a full host request frame and stage the corresponding response. */
SpiProtocol_Result SpiSlaveService_ProcessRequestFrame(const uint8_t request[SPI_FRAME_MAX_BYTES]);

#ifdef __cplusplus
}
#endif

#endif /* SPI_SLAVE_SERVICE_H */
