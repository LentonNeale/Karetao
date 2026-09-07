/**
 * @file health_monitor.h
 * @brief Implements the health monitor module.
 */

#ifndef HEALTH_MONITOR_H
#define HEALTH_MONITOR_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Executes monitor init.
 */
void HealthMonitor_Init(void);
/**
 * @brief Executes monitor process.
 */
void HealthMonitor_Process(void);

#ifdef __cplusplus
}
#endif

#endif /* HEALTH_MONITOR_H */
