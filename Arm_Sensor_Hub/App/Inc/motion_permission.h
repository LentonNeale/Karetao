/**
 * @file motion_permission.h
 * @brief System-level normal-motion permission authority.
 */
#ifndef MOTION_PERMISSION_H
#define MOTION_PERMISSION_H

#include <stdbool.h>
#include <stdint.h>

#include "lifecycle.h"
#include "motor_latest_value.h"
#include "time_service.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum
{
    MOTION_PERMISSION_ALLOWED = 0,
    MOTION_PERMISSION_LIFECYCLE_NOT_ACTIVE,
    MOTION_PERMISSION_PREREQUISITE_INVALID,
    MOTION_PERMISSION_PREREQUISITE_LATCHED,
    MOTION_PERMISSION_MOTOR_NOT_READY
} MotionPermission_Reason;

typedef struct
{
    Lifecycle_State lifecycle_state;
    bool can_active;
    bool required_sensors_valid;
    bool heartbeat_valid;
    bool time_sync_valid;
    bool motor_feedback_fresh;
    bool calibration_valid;
    bool global_motion_inhibit;
    bool motor_ready;
    MotionPermission_Reason reason;
    bool latched;
} MotionPermission_State;

void MotionPermission_Init(void);
void MotionPermission_Reset(void);
void MotionPermission_SetLifecycleState(Lifecycle_State state);
void MotionPermission_SetCanActive(bool active);
void MotionPermission_SetRequiredSensorsValid(bool valid);
void MotionPermission_SetHeartbeatLastSeenUs(uint64_t timestamp_us);
void MotionPermission_SetTimeSyncValid(bool valid);
void MotionPermission_SetMotorFeedbackFresh(bool fresh);
void MotionPermission_SetCalibrationValid(bool valid);
void MotionPermission_SetGlobalMotionInhibit(bool inhibited, bool latched);
void MotionPermission_SetMotorReady(bool ready);
MotionPermission_State MotionPermission_GetState(void);
bool MotionPermission_IsPermitted(MotionPermission_Reason *reason, bool *latched);

#ifdef __cplusplus
}
#endif

#endif /* MOTION_PERMISSION_H */
