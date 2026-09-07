#ifndef LIFECYCLE_H
#define LIFECYCLE_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum
{
    LIFECYCLE_STATE_UNCONFIGURED = 0,
    LIFECYCLE_STATE_INACTIVE,
    LIFECYCLE_STATE_ACTIVE,
    LIFECYCLE_STATE_ERROR
} Lifecycle_State;

typedef enum
{
    LIFECYCLE_TRANSITION_CONFIGURE = 0,
    LIFECYCLE_TRANSITION_ACTIVATE,
    LIFECYCLE_TRANSITION_DEACTIVATE,
    LIFECYCLE_TRANSITION_CLEANUP,
    LIFECYCLE_TRANSITION_RECOVER,
    LIFECYCLE_TRANSITION_SHUTDOWN,
    LIFECYCLE_TRANSITION_FAIL
} Lifecycle_Transition;

typedef enum
{
    LIFECYCLE_RESULT_OK = 0,
    LIFECYCLE_RESULT_INVALID_ARGUMENT,
    LIFECYCLE_RESULT_INVALID_TRANSITION,
    LIFECYCLE_RESULT_OPERATION_FAILED,
    LIFECYCLE_RESULT_DEPENDENCY_FAILED,
    LIFECYCLE_RESULT_ALREADY_IN_STATE
} Lifecycle_Result;

typedef struct
{
    const char *identity;
    Lifecycle_State state;
    Lifecycle_Transition last_transition;
    Lifecycle_Result last_result;
    uint32_t fault_code;
    uint32_t transition_count;
} Lifecycle_Record;

void Lifecycle_Init(Lifecycle_Record *record, const char *identity);
Lifecycle_Result Lifecycle_Apply(Lifecycle_Record *record,
                                 Lifecycle_Transition transition,
                                 bool operation_ok,
                                 uint32_t fault_code);
Lifecycle_Result Lifecycle_Fail(Lifecycle_Record *record, uint32_t fault_code);
Lifecycle_State Lifecycle_GetState(const Lifecycle_Record *record);
bool Lifecycle_IsActive(const Lifecycle_Record *record);
bool Lifecycle_IsOperational(const Lifecycle_Record *record);

#ifdef __cplusplus
}
#endif

#endif /* LIFECYCLE_H */
