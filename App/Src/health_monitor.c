#include "health_monitor.h"

#include <stddef.h>

#include "app_init.h"
#include "spi_slave_service.h"

static HealthMonitor_Snapshot s_snapshot;

Lifecycle_State I2CManager_GetLifecycleState(void);
uint32_t I2CManager_GetSuccessCount(void);
uint32_t I2CManager_GetErrorCount(void);
uint32_t I2CManager_GetTimeoutCount(void);
Lifecycle_State CanService_GetLifecycleState(void);
uint32_t CanService_GetTxQueueDropCount(void);
uint32_t CanService_GetTxRetryExhaustedCount(void);
uint32_t CanService_GetBusOffCount(void);

static bool HealthMonitor_IsOperationalState(Lifecycle_State state)
{
    return (state == LIFECYCLE_STATE_ACTIVE) || (state == LIFECYCLE_STATE_INACTIVE);
}

static HealthMonitor_Level HealthMonitor_DetermineLevel(void)
{
    bool all_active;
    bool any_fault_counters;

    if ((s_snapshot.app_mks_register_failures > 0u) ||
        (s_snapshot.app_lifecycle_activation_failures > 0u) ||
        (s_snapshot.i2c_state == LIFECYCLE_STATE_ERROR) ||
        (s_snapshot.sensor_state == LIFECYCLE_STATE_ERROR) ||
        (s_snapshot.can_state == LIFECYCLE_STATE_ERROR) ||
        (s_snapshot.spi_state == LIFECYCLE_STATE_ERROR)) {
        return HEALTH_MONITOR_LEVEL_RED;
    }

    if (!HealthMonitor_IsOperationalState(s_snapshot.i2c_state) ||
        !HealthMonitor_IsOperationalState(s_snapshot.sensor_state) ||
        !HealthMonitor_IsOperationalState(s_snapshot.can_state) ||
        !HealthMonitor_IsOperationalState(s_snapshot.spi_state)) {
        return HEALTH_MONITOR_LEVEL_UNKNOWN;
    }

    all_active = (s_snapshot.i2c_state == LIFECYCLE_STATE_ACTIVE) &&
                 (s_snapshot.sensor_state == LIFECYCLE_STATE_ACTIVE) &&
                 (s_snapshot.can_state == LIFECYCLE_STATE_ACTIVE) &&
                 (s_snapshot.spi_state == LIFECYCLE_STATE_ACTIVE);
    any_fault_counters = (s_snapshot.i2c_error_count > 0u) ||
                         (s_snapshot.i2c_timeout_count > 0u) ||
                         (s_snapshot.sensor_comm_error_count > 0u) ||
                         (s_snapshot.sensor_magnet_error_count > 0u) ||
                         (s_snapshot.can_tx_queue_drop_count > 0u) ||
                         (s_snapshot.can_tx_retry_exhausted_count > 0u) ||
                         (s_snapshot.can_bus_off_count > 0u) ||
                         (s_snapshot.spi_dropped_frame_count > 0u);

    if (all_active &&
        (s_snapshot.sensor_result == SENSOR_TASK_BRINGUP_PASS) &&
        s_snapshot.time_sync_valid &&
        !any_fault_counters) {
        return HEALTH_MONITOR_LEVEL_GREEN;
    }

    if ((s_snapshot.i2c_state != LIFECYCLE_STATE_UNCONFIGURED) ||
        (s_snapshot.sensor_state != LIFECYCLE_STATE_UNCONFIGURED) ||
        (s_snapshot.can_state != LIFECYCLE_STATE_UNCONFIGURED) ||
        (s_snapshot.spi_state != LIFECYCLE_STATE_UNCONFIGURED)) {
        return HEALTH_MONITOR_LEVEL_YELLOW;
    }

    return HEALTH_MONITOR_LEVEL_UNKNOWN;
}

void HealthMonitor_Init(void)
{
    s_snapshot = (HealthMonitor_Snapshot){0};
    s_snapshot.timestamp_us = TimeService_NowUs();
    s_snapshot.level = HEALTH_MONITOR_LEVEL_UNKNOWN;
}

void HealthMonitor_Process(void)
{
    TimeService_SyncSnapshot time_sync_snapshot;
    const SensorTask_BringupSnapshot *sensor_snapshot = SensorTask_GetBringupSnapshot();
    const SnapshotFrame_Diagnostics *spi_diagnostics = SpiSlaveService_GetSnapshotDiagnostics();

    TimeService_GetSyncSnapshot(&time_sync_snapshot);
    s_snapshot.timestamp_us = TimeService_NowUs();
    s_snapshot.time_sync_valid = time_sync_snapshot.valid;
    s_snapshot.time_sync_quality = time_sync_snapshot.quality;
    s_snapshot.i2c_state = I2CManager_GetLifecycleState();
    s_snapshot.sensor_state = SensorTask_GetLifecycleState();
    s_snapshot.can_state = CanService_GetLifecycleState();
    s_snapshot.spi_state = SpiSlaveService_GetLifecycleState();
    s_snapshot.i2c_success_count = I2CManager_GetSuccessCount();
    s_snapshot.i2c_error_count = I2CManager_GetErrorCount();
    s_snapshot.i2c_timeout_count = I2CManager_GetTimeoutCount();
    s_snapshot.can_tx_queue_drop_count = CanService_GetTxQueueDropCount();
    s_snapshot.can_tx_retry_exhausted_count = CanService_GetTxRetryExhaustedCount();
    s_snapshot.can_bus_off_count = CanService_GetBusOffCount();
    s_snapshot.app_mks_register_failures = App_GetMksRegisterFailureCount();
    s_snapshot.app_lifecycle_activation_failures = App_GetLifecycleActivationFailureCount();

    if (sensor_snapshot != NULL) {
        s_snapshot.sensor_result = sensor_snapshot->result;
        s_snapshot.sensor_sample_ok_count = sensor_snapshot->sample_ok_count;
        s_snapshot.sensor_comm_error_count = sensor_snapshot->comm_error_count;
        s_snapshot.sensor_magnet_error_count = sensor_snapshot->magnet_error_count;
    } else {
        s_snapshot.sensor_result = SENSOR_TASK_BRINGUP_UNKNOWN;
        s_snapshot.sensor_sample_ok_count = 0u;
        s_snapshot.sensor_comm_error_count = 0u;
        s_snapshot.sensor_magnet_error_count = 0u;
    }

    if (spi_diagnostics != NULL) {
        s_snapshot.spi_staged_frame_count = spi_diagnostics->staged_frame_count;
        s_snapshot.spi_replaced_unread_frame_count = spi_diagnostics->replaced_unread_frame_count;
        s_snapshot.spi_dropped_frame_count = spi_diagnostics->dropped_frame_count;
        s_snapshot.spi_dma_start_count = spi_diagnostics->dma_start_count;
        s_snapshot.spi_dma_complete_count = spi_diagnostics->dma_complete_count;
    } else {
        s_snapshot.spi_staged_frame_count = 0u;
        s_snapshot.spi_replaced_unread_frame_count = 0u;
        s_snapshot.spi_dropped_frame_count = 0u;
        s_snapshot.spi_dma_start_count = 0u;
        s_snapshot.spi_dma_complete_count = 0u;
    }

    s_snapshot.level = HealthMonitor_DetermineLevel();
}

const HealthMonitor_Snapshot *HealthMonitor_GetSnapshot(void)
{
    return &s_snapshot;
}

HealthMonitor_Level HealthMonitor_GetLevel(void)
{
    return s_snapshot.level;
}
