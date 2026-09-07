#ifndef SPI_SLAVE_SERVICE_H
#define SPI_SLAVE_SERVICE_H

#include "lifecycle.h"
#include "spi_protocol.h"
#include "spi_data_ready.h"
#include "snapshot_builder.h"

#ifdef __cplusplus
extern "C" {
#endif

void SpiSlaveService_Init(void);
Lifecycle_Result SpiSlaveService_Activate(void);
Lifecycle_State SpiSlaveService_GetLifecycleState(void);
void SpiSlaveService_Process(void);
SnapshotBuild_Result SpiSlaveService_StageSnapshot(SnapshotBuilder_SerializeCallback serialize, void *context);
bool SpiSlaveService_BeginDmaTransfer(const uint8_t **frame_buffer, uint16_t *frame_length);
bool SpiSlaveService_CompleteDmaTransfer(void);
const SnapshotFrame_Diagnostics *SpiSlaveService_GetSnapshotDiagnostics(void);
const SpiDataReady_State *SpiSlaveService_GetDataReadyState(void);
void SpiSlaveService_SetPollPeriodMs(uint32_t poll_period_ms);
bool SpiSlaveService_SetUnsolicitedSnapshot(const uint8_t *payload, uint16_t payload_length);
SpiProtocol_Result SpiSlaveService_ProcessRequestFrame(const uint8_t request[SPI_FRAME_MAX_BYTES]);

#ifdef __cplusplus
}
#endif

#endif /* SPI_SLAVE_SERVICE_H */
