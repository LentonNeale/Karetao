/**
 * @file can_service.h
 * @brief Implements the can service module.
 */

#ifndef CAN_SERVICE_H
#define CAN_SERVICE_H

#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>

#include "mks_api.h"
#include "lifecycle.h"

#define CAN_SERVICE_MAX_MKS_MOTORS 8u
/**
 * Poll scheduler period (PRM-CAN-05): each tick sends one request, alternating 30H and 32H per
 * motor round-robin, so a motor's position interval is 2 x this x registered motors. The motor
 * freshness window derives from it (app_init.c); CanService_SetPollPeriodMs does not move it.
 */
#define CAN_SERVICE_DEFAULT_POLL_PERIOD_MS 20u

typedef enum {
	CAN_SERVICE_MKS_SERVO42 = 0,
	CAN_SERVICE_MKS_SERVO57 = 1
} CanService_MksModel;

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Executes service init.
 */
void CanService_Init(void);
/**
 * @brief Executes service activate.
 */
Lifecycle_Result CanService_Activate(void);
/**
 * @brief Executes service get lifecycle state.
 */
Lifecycle_State CanService_GetLifecycleState(void);
/**
 * @brief Executes service process.
 */
void CanService_Process(void);

/**
 * Registers a drive in a slot. The record identity it publishes (logical joint, configuration
 * version) is a latest-value slot property, set by LatestValue_Configure from the same table.
 */
MksStatus CanService_RegisterMotor(uint8_t motor_index,
								   CanService_MksModel model,
								   uint16_t can_id);

/**
 * @brief Executes service send motor enable.
 */
MksStatus CanService_SendMotorEnable(uint8_t motor_index, bool enable);
/**
 * @brief Executes service send emergency stop.
 */
MksStatus CanService_SendEmergencyStop(uint8_t motor_index);
/**
 * @brief Executes service send absolute pulse move.
 */
MksStatus CanService_SendAbsolutePulseMove(uint8_t motor_index, uint16_t speed, uint8_t acc, int32_t absolute_pulses);
MksStatus CanService_SendRelativePulseMove(uint8_t motor_index, bool dir_cw, uint16_t speed, uint8_t acc,
										   uint32_t relative_pulses);
/**
 * @brief Executes service request encoder value.
 */
MksStatus CanService_RequestEncoderValue(uint8_t motor_index);
/**
 * @brief Executes service request realtime speed.
 */
MksStatus CanService_RequestRealtimeSpeed(uint8_t motor_index);

/**
 * @brief Executes service set poll period ms.
 */
void CanService_SetPollPeriodMs(uint32_t period_ms);
/**
 * @brief Executes service get tx queue drop count.
 */
uint32_t CanService_GetTxQueueDropCount(void);
/**
 * @brief Executes service get tx retry exhausted count.
 */
uint32_t CanService_GetTxRetryExhaustedCount(void);
/**
 * @brief Executes service get bus off count.
 */
uint32_t CanService_GetBusOffCount(void);
/**
 * @brief Executes service get last response.
 */
bool CanService_GetLastResponse(uint8_t motor_index, MksParsedResponse *out_response);
/**
 * @brief Executes service get rx ok count.
 */
uint32_t CanService_GetRxOkCount(uint8_t motor_index);
/**
 * @brief Executes service get rx decode error count.
 */
uint32_t CanService_GetRxDecodeErrorCount(uint8_t motor_index);

#ifdef __cplusplus
}
#endif

#endif /* CAN_SERVICE_H */
