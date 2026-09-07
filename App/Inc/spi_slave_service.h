/**
 * @file spi_slave_service.h
 * @brief Implements the spi slave service module.
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
 * @brief Executes slave service init.
 */
void SpiSlaveService_Init(void);
/**
 * @brief Executes slave service activate.
 */
Lifecycle_Result SpiSlaveService_Activate(void);
/**
 * @brief Executes slave service get lifecycle state.
 */
Lifecycle_State SpiSlaveService_GetLifecycleState(void);
/**
 * @brief Executes slave service process.
 */
void SpiSlaveService_Process(void);
/**
 * @brief Executes slave service stage snapshot.
 */
SnapshotBuild_Result SpiSlaveService_StageSnapshot(SnapshotBuilder_SerializeCallback serialize, void *context);
/**
 * @brief Executes slave service begin dma transfer.
 */
bool SpiSlaveService_BeginDmaTransfer(const uint8_t **frame_buffer, uint16_t *frame_length);
/**
 * @brief Executes slave service complete dma transfer.
 */
bool SpiSlaveService_CompleteDmaTransfer(void);
const SnapshotFrame_Diagnostics *SpiSlaveService_GetSnapshotDiagnostics(void);
const SpiDataReady_State *SpiSlaveService_GetDataReadyState(void);
/**
 * @brief Executes slave service set poll period ms.
 */
void SpiSlaveService_SetPollPeriodMs(uint32_t poll_period_ms);
/**
 * @brief Executes slave service set unsolicited snapshot.
 */
bool SpiSlaveService_SetUnsolicitedSnapshot(const uint8_t *payload, uint16_t payload_length);
/**
 * @brief Executes slave service process request frame.
 */
SpiProtocol_Result SpiSlaveService_ProcessRequestFrame(const uint8_t request[SPI_FRAME_MAX_BYTES]);

#ifdef __cplusplus
}
#endif

#endif /* SPI_SLAVE_SERVICE_H */
