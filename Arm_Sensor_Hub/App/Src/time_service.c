/**
 * @file time_service.c
 * @brief Implements the time service module.
 */

#include "time_service.h"

#include <stddef.h>

#ifndef TIME_SERVICE_HOST_TEST
#include "main.h"

extern TIM_HandleTypeDef htim2;

static TimeService_State s_tim2_state;
static TimeService_SyncState s_sync_state;

/**
 * @brief Executes service read tim2.
 */
static uint32_t TimeService_ReadTim2(void *context)
{
    TIM_HandleTypeDef *timer = context;

    return __HAL_TIM_GET_COUNTER(timer);
}
#endif

void TimeService_StateInit(TimeService_State *state,
                           TimeService_CounterReader read_counter,
                           void *reader_context)
{
    if (state == NULL)
    {
        return;
    }

    state->read_counter = read_counter;
    state->reader_context = reader_context;
    state->last_counter = 0u;
    state->wrap_base_us = 0u;
    state->initialized = false;

    if (read_counter != NULL)
    {
        state->last_counter = read_counter(reader_context);
        state->initialized = true;
    }
}

/**
 * @brief Executes service state now us.
 */
uint64_t TimeService_StateNowUs(TimeService_State *state)
{
    uint32_t current_counter;

    if ((state == NULL) || !state->initialized || (state->read_counter == NULL))
    {
        return 0u;
    }

    current_counter = state->read_counter(state->reader_context);
    if (current_counter < state->last_counter)
    {
        state->wrap_base_us += (UINT64_C(1) << 32u);
    }

    state->last_counter = current_counter;
    return state->wrap_base_us + current_counter;
}

/**
 * @brief Executes service default sync config.
 */
static TimeService_SyncConfig TimeService_DefaultSyncConfig(void)
{
    TimeService_SyncConfig config;

    config.initial_offset_limit_us = TIME_SERVICE_DEFAULT_INITIAL_OFFSET_LIMIT_US;
    config.runtime_offset_step_limit_us = TIME_SERVICE_DEFAULT_RUNTIME_OFFSET_STEP_LIMIT_US;
    config.validity_timeout_us = TIME_SERVICE_DEFAULT_VALIDITY_TIMEOUT_US;
    return config;
}

/**
 * @brief Executes service abs int64.
 */
static uint64_t TimeService_AbsInt64(int64_t value)
{
    if (value >= 0)
    {
        return (uint64_t)value;
    }

    return (uint64_t)(-(value + 1)) + 1u;
}

/**
 * @brief Executes service offset within limit.
 */
static bool TimeService_OffsetWithinLimit(int64_t offset_us, int64_t limit_us)
{
    return (limit_us >= 0) && (TimeService_AbsInt64(offset_us) <= (uint64_t)limit_us);
}

static bool TimeService_OffsetStepWithinLimit(int64_t current_offset_us,
                                               int64_t candidate_offset_us,
                                               int64_t limit_us)
{
    uint64_t current_magnitude;
    uint64_t candidate_magnitude;

    if (limit_us < 0)
    {
        return false;
    }

    current_magnitude = TimeService_AbsInt64(current_offset_us);
    candidate_magnitude = TimeService_AbsInt64(candidate_offset_us);

    if ((current_offset_us < 0) != (candidate_offset_us < 0))
    {
        return (candidate_magnitude <= (uint64_t)limit_us) &&
               (current_magnitude <= ((uint64_t)limit_us - candidate_magnitude));
    }

    return (current_magnitude >= candidate_magnitude)
               ? ((current_magnitude - candidate_magnitude) <= (uint64_t)limit_us)
               : ((candidate_magnitude - current_magnitude) <= (uint64_t)limit_us);
}

static bool TimeService_CalculateOffset(uint64_t pi_time_us,
                                        uint64_t local_time_us,
                                        int64_t *offset_us)
{
    uint64_t difference;

    if (offset_us == NULL)
    {
        return false;
    }

    if (pi_time_us >= local_time_us)
    {
        difference = pi_time_us - local_time_us;
        if (difference > INT64_MAX)
        {
            return false;
        }

        *offset_us = (int64_t)difference;
        return true;
    }

    difference = local_time_us - pi_time_us;
    if (difference > (UINT64_C(1) << 63u))
    {
        return false;
    }

    if (difference == (UINT64_C(1) << 63u))
    {
        *offset_us = INT64_MIN;
    }
    else
    {
        *offset_us = -(int64_t)difference;
    }

    return true;
}

/**
 * @brief Executes service is sequence newer.
 */
static bool TimeService_IsSequenceNewer(uint32_t candidate, uint32_t previous)
{
    return (candidate != previous) &&
           ((uint32_t)(candidate - previous) < UINT32_C(0x80000000));
}

/**
 * @brief Debug mirror for TIME_SYNC acceptance history (SWD readout).
 *
 * Updated on every TimeService_SyncStateAccept call to track input values,
 * computed offset, and result codes without modifying the SPI protocol.
 */
volatile TimeService_SyncDebugMirror g_time_sync_dbg = {0};

/**
 * @brief Executes service sync state init.
 */
void TimeService_SyncStateInit(TimeService_SyncState *state, const TimeService_SyncConfig *config)
{
    if (state == NULL)
    {
        return;
    }

    state->config = (config == NULL) ? TimeService_DefaultSyncConfig() : *config;
    if ((state->config.initial_offset_limit_us < 0) ||
        (state->config.runtime_offset_step_limit_us < 0) ||
        (state->config.validity_timeout_us == 0u))
    {
        state->config = TimeService_DefaultSyncConfig();
    }

    TimeService_SyncStateReset(state);
}

/**
 * @brief Executes service sync state reset.
 */
void TimeService_SyncStateReset(TimeService_SyncState *state)
{
    if (state == NULL)
    {
        return;
    }

    state->time_offset_us = 0;
    state->last_sync_sequence = 0u;
    state->last_sync_local_time_us = 0u;
    state->has_accepted_sync = false;
    state->valid = false;
    state->quality = TIME_SERVICE_SYNC_QUALITY_UNSYNCHRONIZED;
}

TimeService_SyncResult TimeService_SyncStateAccept(TimeService_SyncState *state,
                                                    uint64_t pi_time_us,
                                                    uint32_t sync_sequence,
                                                    uint64_t local_time_us)
{
    int64_t candidate_offset_us;

    if ((state == NULL) || !TimeService_CalculateOffset(pi_time_us, local_time_us, &candidate_offset_us))
    {
        g_time_sync_dbg.pi_time_us = pi_time_us;
        g_time_sync_dbg.local_capture_us = local_time_us;
        g_time_sync_dbg.candidate_offset_us = 0;
        g_time_sync_dbg.result = TIME_SERVICE_SYNC_REJECTED_ARGUMENT;
        g_time_sync_dbg.reject_count++;
        return TIME_SERVICE_SYNC_REJECTED_ARGUMENT;
    }

    // Store inputs and calculation for debug inspection
    g_time_sync_dbg.pi_time_us = pi_time_us;
    g_time_sync_dbg.local_capture_us = local_time_us;
    g_time_sync_dbg.candidate_offset_us = candidate_offset_us;

    if (state->has_accepted_sync && !TimeService_IsSequenceNewer(sync_sequence, state->last_sync_sequence))
    {
        g_time_sync_dbg.result = TIME_SERVICE_SYNC_REJECTED_SEQUENCE;
        g_time_sync_dbg.reject_count++;
        return TIME_SERVICE_SYNC_REJECTED_SEQUENCE;
    }

    if ((!state->has_accepted_sync &&
         !TimeService_OffsetWithinLimit(candidate_offset_us, state->config.initial_offset_limit_us)) ||
        (state->has_accepted_sync &&
         !TimeService_OffsetStepWithinLimit(state->time_offset_us,
                                            candidate_offset_us,
                                            state->config.runtime_offset_step_limit_us)))
    {
        g_time_sync_dbg.result = TIME_SERVICE_SYNC_REJECTED_OFFSET;
        g_time_sync_dbg.reject_count++;
        return TIME_SERVICE_SYNC_REJECTED_OFFSET;
    }

    state->time_offset_us = candidate_offset_us;
    state->last_sync_sequence = sync_sequence;
    state->last_sync_local_time_us = local_time_us;
    state->has_accepted_sync = true;
    state->valid = true;
    state->quality = TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED;
    g_time_sync_dbg.result = TIME_SERVICE_SYNC_ACCEPTED;
    g_time_sync_dbg.accept_count++;
    return TIME_SERVICE_SYNC_ACCEPTED;
}

/**
 * @brief Executes service sync state refresh.
 */
void TimeService_SyncStateRefresh(TimeService_SyncState *state, uint64_t local_time_us)
{
    if ((state == NULL) || !state->valid || (local_time_us < state->last_sync_local_time_us))
    {
        return;
    }

    if ((local_time_us - state->last_sync_local_time_us) >= state->config.validity_timeout_us)
    {
        state->valid = false;
        state->quality = TIME_SERVICE_SYNC_QUALITY_UNSYNCHRONIZED;
    }
}

void TimeService_SyncStateGetSnapshot(TimeService_SyncState *state,
                                      uint64_t local_time_us,
                                      TimeService_SyncSnapshot *snapshot)
{
    if (snapshot == NULL)
    {
        return;
    }

    if (state == NULL)
    {
        snapshot->time_offset_us = 0;
        snapshot->last_sync_sequence = 0u;
        snapshot->last_sync_local_time_us = 0u;
        snapshot->age_us = UINT64_MAX;
        snapshot->valid = false;
        snapshot->quality = TIME_SERVICE_SYNC_QUALITY_UNSYNCHRONIZED;
        return;
    }

    TimeService_SyncStateRefresh(state, local_time_us);
    snapshot->time_offset_us = state->time_offset_us;
    snapshot->last_sync_sequence = state->last_sync_sequence;
    snapshot->last_sync_local_time_us = state->last_sync_local_time_us;
    snapshot->age_us = state->has_accepted_sync && (local_time_us >= state->last_sync_local_time_us)
                           ? (local_time_us - state->last_sync_local_time_us)
                           : UINT64_MAX;
    snapshot->valid = state->valid;
    snapshot->quality = state->quality;
}

#ifndef TIME_SERVICE_HOST_TEST
/**
 * @brief Executes service init.
 */
void TimeService_Init(void)
{
    (void)HAL_TIM_Base_Start(&htim2);
    TimeService_StateInit(&s_tim2_state, TimeService_ReadTim2, &htim2);
    TimeService_SyncInit(NULL);
}

/**
 * @brief Executes service now us.
 */
uint64_t TimeService_NowUs(void)
{
    return TimeService_StateNowUs(&s_tim2_state);
}

/**
 * @brief Returns raw TIM2 counter for debug timing correlation.
 */
uint32_t TimeService_RawCounter(void)
{
    return __HAL_TIM_GET_COUNTER(&htim2);
}

/**
 * @brief Executes service sync init.
 */
void TimeService_SyncInit(const TimeService_SyncConfig *config)
{
    TimeService_SyncStateInit(&s_sync_state, config);
}

/**
 * @brief Executes service accept sync.
 */
TimeService_SyncResult TimeService_AcceptSync(uint64_t pi_time_us, uint32_t sync_sequence)
{
    return TimeService_SyncStateAccept(&s_sync_state, pi_time_us, sync_sequence, TimeService_NowUs());
}

/**
 * @brief Executes service is sync valid.
 */
bool TimeService_IsSyncValid(void)
{
    TimeService_SyncStateRefresh(&s_sync_state, TimeService_NowUs());
    return s_sync_state.valid;
}

/**
 * @brief Executes service get sync snapshot.
 */
void TimeService_GetSyncSnapshot(TimeService_SyncSnapshot *snapshot)
{
    TimeService_SyncStateGetSnapshot(&s_sync_state, TimeService_NowUs(), snapshot);
}
#endif