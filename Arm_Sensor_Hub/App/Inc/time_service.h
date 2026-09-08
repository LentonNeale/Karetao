/**
 * @file time_service.h
 * @brief Implements the time service module.
 */

#ifndef TIME_SERVICE_H
#define TIME_SERVICE_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef uint32_t (*TimeService_CounterReader)(void *context);

typedef struct
{
    TimeService_CounterReader read_counter;
    void *reader_context;
    uint32_t last_counter;
    uint64_t wrap_base_us;
    bool initialized;
} TimeService_State;

typedef enum
{
    TIME_SERVICE_SYNC_QUALITY_UNSYNCHRONIZED = 0,
    TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED
} TimeService_SyncQuality;

typedef enum
{
    TIME_SERVICE_SYNC_ACCEPTED = 0,
    TIME_SERVICE_SYNC_REJECTED_ARGUMENT,
    TIME_SERVICE_SYNC_REJECTED_SEQUENCE,
    TIME_SERVICE_SYNC_REJECTED_OFFSET
} TimeService_SyncResult;

typedef struct
{
    int64_t initial_offset_limit_us;
    int64_t runtime_offset_step_limit_us;
    uint64_t validity_timeout_us;
} TimeService_SyncConfig;

typedef struct
{
    TimeService_SyncConfig config;
    int64_t time_offset_us;
    uint32_t last_sync_sequence;
    uint64_t last_sync_local_time_us;
    bool has_accepted_sync;
    bool valid;
    TimeService_SyncQuality quality;
} TimeService_SyncState;

typedef struct
{
    int64_t time_offset_us;
    uint32_t last_sync_sequence;
    uint64_t last_sync_local_time_us;
    uint64_t age_us;
    bool valid;
    TimeService_SyncQuality quality;
} TimeService_SyncSnapshot;

#define TIME_SERVICE_DEFAULT_INITIAL_OFFSET_LIMIT_US INT64_C(86400000000)
#define TIME_SERVICE_DEFAULT_RUNTIME_OFFSET_STEP_LIMIT_US INT64_C(1000000)
#define TIME_SERVICE_DEFAULT_VALIDITY_TIMEOUT_US UINT64_C(5000000)

void TimeService_StateInit(TimeService_State *state,
                           TimeService_CounterReader read_counter,
                           void *reader_context);
/**
 * @brief Executes service state now us.
 */
uint64_t TimeService_StateNowUs(TimeService_State *state);
/**
 * @brief Executes service sync state init.
 */
void TimeService_SyncStateInit(TimeService_SyncState *state, const TimeService_SyncConfig *config);
/**
 * @brief Executes service sync state reset.
 */
void TimeService_SyncStateReset(TimeService_SyncState *state);
TimeService_SyncResult TimeService_SyncStateAccept(TimeService_SyncState *state,
                                                    uint64_t pi_time_us,
                                                    uint32_t sync_sequence,
                                                    uint64_t local_time_us);
/**
 * @brief Executes service sync state refresh.
 */
void TimeService_SyncStateRefresh(TimeService_SyncState *state, uint64_t local_time_us);
void TimeService_SyncStateGetSnapshot(TimeService_SyncState *state,
                                      uint64_t local_time_us,
                                      TimeService_SyncSnapshot *snapshot);

/**
 * @brief Executes service init.
 */
void TimeService_Init(void);
/**
 * @brief Executes service now us.
 */
uint64_t TimeService_NowUs(void);
/**
 * @brief Executes service sync init.
 */
void TimeService_SyncInit(const TimeService_SyncConfig *config);
/**
 * @brief Executes service accept sync.
 */
TimeService_SyncResult TimeService_AcceptSync(uint64_t pi_time_us, uint32_t sync_sequence);
/**
 * @brief Executes service is sync valid.
 */
bool TimeService_IsSyncValid(void);
/**
 * @brief Executes service get sync snapshot.
 */
void TimeService_GetSyncSnapshot(TimeService_SyncSnapshot *snapshot);

#ifdef __cplusplus
}
#endif

#endif /* TIME_SERVICE_H */