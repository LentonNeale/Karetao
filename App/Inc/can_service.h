#ifndef CAN_SERVICE_H
#define CAN_SERVICE_H

#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>

#include "motor_latest_value.h"
#include "mks_api.h"
#include "lifecycle.h"

#define CAN_SERVICE_MAX_MKS_MOTORS 8u

typedef enum {
	CAN_SERVICE_MKS_SERVO42 = 0,
	CAN_SERVICE_MKS_SERVO57 = 1
} CanService_MksModel;

#ifdef __cplusplus
extern "C" {
#endif

void CanService_Init(void);
Lifecycle_Result CanService_Activate(void);
Lifecycle_State CanService_GetLifecycleState(void);
void CanService_Process(void);

MksStatus CanService_RegisterMotor(uint8_t motor_index,
								   uint8_t logical_joint_id,
								   uint32_t configuration_version,
								   CanService_MksModel model,
								   uint16_t can_id);

MksStatus CanService_SendMotorEnable(uint8_t motor_index, bool enable);
MksStatus CanService_SendEmergencyStop(uint8_t motor_index);
MksStatus CanService_SendAbsolutePulseMove(uint8_t motor_index, uint16_t speed, uint8_t acc, int32_t absolute_pulses);
MksStatus CanService_SendRelativePulseMove(uint8_t motor_index, bool dir_cw, uint16_t speed, uint8_t acc,
										   uint32_t relative_pulses);
MksStatus CanService_RequestEncoderValue(uint8_t motor_index);
MksStatus CanService_RequestRealtimeSpeed(uint8_t motor_index);

void CanService_SetPollPeriodMs(uint32_t period_ms);
uint32_t CanService_GetTxQueueDropCount(void);
uint32_t CanService_GetTxRetryExhaustedCount(void);
uint32_t CanService_GetBusOffCount(void);
bool CanService_GetLastResponse(uint8_t motor_index, MksParsedResponse *out_response);
uint32_t CanService_GetRxOkCount(uint8_t motor_index);
uint32_t CanService_GetRxDecodeErrorCount(uint8_t motor_index);
const Motor_LatestValue *CanService_GetLatestMotorValues(size_t *record_count);

#ifdef __cplusplus
}
#endif

#endif /* CAN_SERVICE_H */
