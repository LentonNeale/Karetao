/**
 * @file health_monitor.h
 * @brief Implements the health monitor module.
 */

#ifndef HEALTH_MONITOR_H
#define HEALTH_MONITOR_H

#include <stdbool.h>
#include <stdint.h>

#include "lifecycle.h"
#include "sensor_task.h"
#include "time_service.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum
{
    HEALTH_MONITOR_LEVEL_UNKNOWN = 0,
    HEALTH_MONITOR_LEVEL_GREEN,
    HEALTH_MONITOR_LEVEL_YELLOW,
    HEALTH_MONITOR_LEVEL_RED
} HealthMonitor_Level;

typedef struct
{
    uint64_t timestamp_us;
    HealthMonitor_Level level;
    bool time_sync_valid;
    TimeService_SyncQuality time_sync_quality;
    Lifecycle_State i2c_state;
    Lifecycle_State sensor_state;
    Lifecycle_State can_state;
    Lifecycle_State spi_state;
    SensorTask_BringupResult sensor_result;
    uint32_t i2c_success_count;
    uint32_t i2c_error_count;
    uint32_t i2c_timeout_count;
    uint32_t sensor_sample_ok_count;
    uint32_t sensor_comm_error_count;
    uint32_t sensor_magnet_error_count;
    uint32_t can_tx_queue_drop_count;
    uint32_t can_tx_retry_exhausted_count;
    uint32_t can_bus_off_count;
    uint32_t spi_staged_frame_count;
    uint32_t spi_replaced_unread_frame_count;
    uint32_t spi_dropped_frame_count;
    uint32_t spi_dma_start_count;
    uint32_t spi_dma_complete_count;
    uint32_t app_mks_register_failures;
    uint32_t app_lifecycle_activation_failures;
} HealthMonitor_Snapshot;

void HealthMonitor_Init(void);
void HealthMonitor_Process(void);
const HealthMonitor_Snapshot *HealthMonitor_GetSnapshot(void);
HealthMonitor_Level HealthMonitor_GetLevel(void);

#ifdef __cplusplus
}
#endif

#endif /* HEALTH_MONITOR_H */
