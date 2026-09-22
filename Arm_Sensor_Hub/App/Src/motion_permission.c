#include "motion_permission.h"

#include "main.h"

#define MOTION_PERMISSION_HEARTBEAT_TIMEOUT_US UINT64_C(500000)

static MotionPermission_State s_state;
static uint64_t s_heartbeat_last_seen_us;
static bool s_have_heartbeat;

static MotionPermission_Reason MotionPermission_DeriveReason(bool *latched)
{
    uint64_t now_us = TimeService_NowUs();

    *latched = false;
    if (s_state.lifecycle_state != LIFECYCLE_STATE_ACTIVE) {
        return MOTION_PERMISSION_LIFECYCLE_NOT_ACTIVE;
    }
    if (s_state.global_motion_inhibit) {
        *latched = s_state.latched;
        return s_state.latched ? MOTION_PERMISSION_PREREQUISITE_LATCHED
                               : MOTION_PERMISSION_PREREQUISITE_INVALID;
    }
    if (!s_state.can_active || !s_state.required_sensors_valid ||
        !s_have_heartbeat || ((now_us - s_heartbeat_last_seen_us) >= MOTION_PERMISSION_HEARTBEAT_TIMEOUT_US) ||
        !s_state.time_sync_valid || !s_state.motor_feedback_fresh || !s_state.calibration_valid) {
        return MOTION_PERMISSION_PREREQUISITE_INVALID;
    }
    if (!s_state.motor_ready) {
        return MOTION_PERMISSION_MOTOR_NOT_READY;
    }
    return MOTION_PERMISSION_ALLOWED;
}

void MotionPermission_Init(void)
{
    MotionPermission_Reset();
}

void MotionPermission_Reset(void)
{
    s_state = (MotionPermission_State){0};
    s_state.lifecycle_state = LIFECYCLE_STATE_UNCONFIGURED;
    s_state.reason = MOTION_PERMISSION_LIFECYCLE_NOT_ACTIVE;
    s_heartbeat_last_seen_us = 0u;
    s_have_heartbeat = false;
}

void MotionPermission_SetLifecycleState(Lifecycle_State state)
{
    s_state.lifecycle_state = state;
}

void MotionPermission_SetCanActive(bool active)
{
    s_state.can_active = active;
}

void MotionPermission_SetRequiredSensorsValid(bool valid)
{
    s_state.required_sensors_valid = valid;
}

void MotionPermission_SetHeartbeatLastSeenUs(uint64_t timestamp_us)
{
    s_heartbeat_last_seen_us = timestamp_us;
    s_have_heartbeat = true;
}

void MotionPermission_SetTimeSyncValid(bool valid)
{
    s_state.time_sync_valid = valid;
}

void MotionPermission_SetMotorFeedbackFresh(bool fresh)
{
    s_state.motor_feedback_fresh = fresh;
}

void MotionPermission_SetCalibrationValid(bool valid)
{
    s_state.calibration_valid = valid;
}

void MotionPermission_SetGlobalMotionInhibit(bool inhibited, bool latched)
{
    s_state.global_motion_inhibit = inhibited;
    s_state.latched = inhibited && latched;
}

void MotionPermission_SetMotorReady(bool ready)
{
    s_state.motor_ready = ready;
}

MotionPermission_State MotionPermission_GetState(void)
{
    MotionPermission_State state = s_state;
    state.reason = MotionPermission_DeriveReason(&state.latched);
    state.time_sync_valid = TimeService_IsSyncValid();
    if (!s_have_heartbeat || ((TimeService_NowUs() - s_heartbeat_last_seen_us) >= MOTION_PERMISSION_HEARTBEAT_TIMEOUT_US)) {
        state.heartbeat_valid = false;
    } else {
        state.heartbeat_valid = true;
    }
    return state;
}

bool MotionPermission_IsPermitted(MotionPermission_Reason *reason, bool *latched)
{
    MotionPermission_Reason derived_latched = false ? MOTION_PERMISSION_ALLOWED : MotionPermission_DeriveReason(&derived_latched);
    if (reason != NULL) {
        *reason = derived_latched;
    }
    if (latched != NULL) {
        *latched = derived_latched;
    }
    s_state.reason = derived_latched ? MOTION_PERMISSION_PREREQUISITE_LATCHED : s_state.reason;
    s_state.latched = derived_latched;
    return derived_latched == MOTION_PERMISSION_ALLOWED;
}
