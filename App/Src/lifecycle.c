#include "lifecycle.h"

#include <stddef.h>

static bool Lifecycle_IsValidTransition(Lifecycle_State state, Lifecycle_Transition transition)
{
    switch (transition)
    {
    case LIFECYCLE_TRANSITION_CONFIGURE:
        return state == LIFECYCLE_STATE_UNCONFIGURED;
    case LIFECYCLE_TRANSITION_ACTIVATE:
        return state == LIFECYCLE_STATE_INACTIVE;
    case LIFECYCLE_TRANSITION_DEACTIVATE:
        return state == LIFECYCLE_STATE_ACTIVE;
    case LIFECYCLE_TRANSITION_CLEANUP:
        return state == LIFECYCLE_STATE_INACTIVE;
    case LIFECYCLE_TRANSITION_RECOVER:
        return state == LIFECYCLE_STATE_ERROR;
    case LIFECYCLE_TRANSITION_SHUTDOWN:
    case LIFECYCLE_TRANSITION_FAIL:
        return true;
    default:
        return false;
    }
}

void Lifecycle_Init(Lifecycle_Record *record, const char *identity)
{
    if (record == NULL)
    {
        return;
    }

    record->identity = identity;
    record->state = LIFECYCLE_STATE_UNCONFIGURED;
    record->last_transition = LIFECYCLE_TRANSITION_CONFIGURE;
    record->last_result = LIFECYCLE_RESULT_OK;
    record->fault_code = 0u;
    record->transition_count = 0u;
}

Lifecycle_Result Lifecycle_Apply(Lifecycle_Record *record,
                                 Lifecycle_Transition transition,
                                 bool operation_ok,
                                 uint32_t fault_code)
{
    Lifecycle_State next_state;

    if (record == NULL)
    {
        return LIFECYCLE_RESULT_INVALID_ARGUMENT;
    }

    if (!Lifecycle_IsValidTransition(record->state, transition))
    {
        record->last_transition = transition;
        record->last_result = LIFECYCLE_RESULT_INVALID_TRANSITION;
        return LIFECYCLE_RESULT_INVALID_TRANSITION;
    }

    record->last_transition = transition;
    record->fault_code = operation_ok ? 0u : fault_code;
    record->transition_count++;

    if (!operation_ok)
    {
        record->state = LIFECYCLE_STATE_ERROR;
        record->last_result = LIFECYCLE_RESULT_OPERATION_FAILED;
        return LIFECYCLE_RESULT_OPERATION_FAILED;
    }

    switch (transition)
    {
    case LIFECYCLE_TRANSITION_CONFIGURE:
        next_state = LIFECYCLE_STATE_INACTIVE;
        break;
    case LIFECYCLE_TRANSITION_ACTIVATE:
        next_state = LIFECYCLE_STATE_ACTIVE;
        break;
    case LIFECYCLE_TRANSITION_DEACTIVATE:
        next_state = LIFECYCLE_STATE_INACTIVE;
        break;
    case LIFECYCLE_TRANSITION_CLEANUP:
    case LIFECYCLE_TRANSITION_SHUTDOWN:
        next_state = LIFECYCLE_STATE_UNCONFIGURED;
        break;
    case LIFECYCLE_TRANSITION_RECOVER:
        next_state = LIFECYCLE_STATE_INACTIVE;
        break;
    case LIFECYCLE_TRANSITION_FAIL:
        next_state = LIFECYCLE_STATE_ERROR;
        break;
    default:
        record->last_result = LIFECYCLE_RESULT_INVALID_TRANSITION;
        return LIFECYCLE_RESULT_INVALID_TRANSITION;
    }

    record->state = next_state;
    record->last_result = LIFECYCLE_RESULT_OK;
    return LIFECYCLE_RESULT_OK;
}

Lifecycle_Result Lifecycle_Fail(Lifecycle_Record *record, uint32_t fault_code)
{
    return Lifecycle_Apply(record, LIFECYCLE_TRANSITION_FAIL, false, fault_code);
}

Lifecycle_State Lifecycle_GetState(const Lifecycle_Record *record)
{
    if (record == NULL)
    {
        return LIFECYCLE_STATE_ERROR;
    }

    return record->state;
}

bool Lifecycle_IsActive(const Lifecycle_Record *record)
{
    return Lifecycle_GetState(record) == LIFECYCLE_STATE_ACTIVE;
}

bool Lifecycle_IsOperational(const Lifecycle_Record *record)
{
    Lifecycle_State state = Lifecycle_GetState(record);
    return (state == LIFECYCLE_STATE_ACTIVE) || (state == LIFECYCLE_STATE_INACTIVE);
}
