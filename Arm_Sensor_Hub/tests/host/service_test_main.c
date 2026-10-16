#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include "host_test_assert.h"

#include "FreeRTOS.h"
#include "semphr.h"
#include "task.h"
#include "app_init.h"
#include "as5600.h"
#include "can_service.h"
#include "crc32_iso_hdlc.h"
#include "health_monitor.h"
#include "i2c_manager.h"
#include "latest_value.h"
#include "sensor_task.h"
#include "spi_slave_service.h"
#include "stack_monitor.h"
#include "tca9548a_mux.h"
#include "time_service.h"
#include "timers.h"

I2C_HandleTypeDef hi2c1 = {.Instance = I2C1};
CAN_HandleTypeDef hcan1 = {.Instance = (void *)0x2};
TIM_HandleTypeDef htim2 = {.Instance = (void *)0x3};
SPI_HandleTypeDef hspi3 = {.Instance = SPI3};
void *Data_Ready_GPIO_Port = (void *)0x4;
uint16_t Data_Ready_Pin = 9u;

typedef struct
{
    uint16_t address;
    uint8_t data[8];
    uint16_t size;
} I2CWriteLog;

typedef struct
{
    CAN_RxHeaderTypeDef header;
    uint8_t data[8];
} CanRxScript;

static uint32_t s_hal_tick;
static uint64_t s_time_now_us;
static TimeService_SyncSnapshot s_time_sync_snapshot;
static TimeService_SyncResult s_time_sync_result;
static uint32_t s_time_sync_accept_count;
static uint64_t s_last_time_sync_pi_time_us;
static uint32_t s_last_time_sync_sequence;
static GPIO_PinState s_last_gpio_state;
static uint32_t s_gpio_write_count;
static bool s_force_semaphore_timeout;
static I2CWriteLog s_i2c_writes[16];
static uint32_t s_i2c_write_count;
static HAL_StatusTypeDef s_i2c_tx_statuses[16];
static HAL_StatusTypeDef s_i2c_rx_statuses[16];
static uint8_t s_i2c_rx_payloads[16][8];
static uint16_t s_i2c_rx_sizes[16];
static uint32_t s_i2c_tx_call_count;
static uint32_t s_i2c_rx_call_count;
static HAL_StatusTypeDef s_can_filter_status = HAL_OK;
static HAL_StatusTypeDef s_can_start_status = HAL_OK;
static HAL_StatusTypeDef s_can_stop_status = HAL_OK;
static HAL_StatusTypeDef s_can_add_tx_status = HAL_OK;
static uint32_t s_can_error_bits;
static uint32_t s_can_rx_count;
static uint32_t s_can_rx_index;
static CanRxScript s_can_rx_script[8];
static uint32_t s_can_last_tx_count;
static CAN_TxHeaderTypeDef s_can_last_tx_header;
static uint8_t s_can_last_tx_data[8];
static MksStatus s_mks_encode_status = MKS_OK;
static MksStatus s_mks_decode_status = MKS_OK;
static MksParsedResponse s_mks_decoded_response;
static HAL_StatusTypeDef s_spi_dma_status = HAL_OK;
static uint32_t s_spi_dma_start_count;
static uint32_t s_spi_abort_count;
static const uint8_t *s_spi_last_tx_buffer;
static uint8_t *s_spi_last_rx_buffer;
static uint16_t s_spi_last_transfer_size;

static void ResetHalState(void)
{
    uint32_t i;

    s_hal_tick = 0u;
    s_time_now_us = 0u;
    s_time_sync_snapshot = (TimeService_SyncSnapshot){0};
    s_time_sync_result = TIME_SERVICE_SYNC_ACCEPTED;
    s_time_sync_accept_count = 0u;
    s_last_time_sync_pi_time_us = 0u;
    s_last_time_sync_sequence = 0u;
    s_last_gpio_state = GPIO_PIN_RESET;
    s_gpio_write_count = 0u;
    s_force_semaphore_timeout = false;
    memset(s_i2c_writes, 0, sizeof(s_i2c_writes));
    s_i2c_write_count = 0u;
    s_i2c_tx_call_count = 0u;
    s_i2c_rx_call_count = 0u;
    for (i = 0u; i < 16u; ++i) {
        s_i2c_tx_statuses[i] = HAL_OK;
        s_i2c_rx_statuses[i] = HAL_OK;
        s_i2c_rx_sizes[i] = 0u;
        memset(s_i2c_rx_payloads[i], 0, sizeof(s_i2c_rx_payloads[i]));
    }
    s_can_filter_status = HAL_OK;
    s_can_start_status = HAL_OK;
    s_can_stop_status = HAL_OK;
    s_can_add_tx_status = HAL_OK;
    s_can_error_bits = 0u;
    s_can_rx_count = 0u;
    s_can_rx_index = 0u;
    s_can_last_tx_count = 0u;
    memset(&s_can_last_tx_header, 0, sizeof(s_can_last_tx_header));
    memset(s_can_last_tx_data, 0, sizeof(s_can_last_tx_data));
    s_mks_encode_status = MKS_OK;
    s_mks_decode_status = MKS_OK;
    memset(&s_mks_decoded_response, 0, sizeof(s_mks_decoded_response));
    s_spi_dma_status = HAL_OK;
    s_spi_dma_start_count = 0u;
    s_spi_abort_count = 0u;
    s_spi_last_tx_buffer = NULL;
    s_spi_last_rx_buffer = NULL;
    s_spi_last_transfer_size = 0u;
    htim2.Counter = 0u;
}

void TimeService_Init(void)
{
}

uint64_t TimeService_NowUs(void)
{
    return s_time_now_us;
}

uint32_t TimeService_RawCounter(void)
{
    return 0u;  /* Stub: return zero in host tests. */
}

void TimeService_SyncInit(const TimeService_SyncConfig *config)
{
    (void)config;
    s_time_sync_snapshot = (TimeService_SyncSnapshot){0};
}

TimeService_SyncResult TimeService_AcceptSync(uint64_t pi_time_us, uint32_t sync_sequence)
{
    s_time_sync_accept_count++;
    s_last_time_sync_pi_time_us = pi_time_us;
    s_last_time_sync_sequence = sync_sequence;
    if (s_time_sync_result != TIME_SERVICE_SYNC_ACCEPTED) {
        return s_time_sync_result;
    }
    s_time_sync_snapshot.time_offset_us = (int64_t)pi_time_us - (int64_t)s_time_now_us;
    s_time_sync_snapshot.last_sync_sequence = sync_sequence;
    s_time_sync_snapshot.last_sync_local_time_us = s_time_now_us;
    s_time_sync_snapshot.age_us = 0u;
    s_time_sync_snapshot.valid = true;
    s_time_sync_snapshot.quality = TIME_SERVICE_SYNC_QUALITY_SYNCHRONIZED;
    return TIME_SERVICE_SYNC_ACCEPTED;
}

bool TimeService_IsSyncValid(void)
{
    return s_time_sync_snapshot.valid;
}

void TimeService_GetSyncSnapshot(TimeService_SyncSnapshot *snapshot)
{
    if (snapshot != NULL) {
        *snapshot = s_time_sync_snapshot;
    }
}

HAL_StatusTypeDef HAL_TIM_Base_Start(TIM_HandleTypeDef *htim)
{
    (void)htim;
    return HAL_OK;
}

uint32_t HAL_GetTick(void)
{
    return s_hal_tick;
}

/* Stack monitor stubs: three distinct handles, each with its own high-water mark
 * (words). The calling task (NULL) is a fourth, so reading it by mistake shows. */
static int s_default_task_tag;
static int s_idle_task_tag;
static int s_timer_task_tag;
static bool s_idle_task_exists;
static uint32_t s_idle_handle_calls;
static uint32_t s_default_handle_calls;
static UBaseType_t s_default_free_words = 300u;
static UBaseType_t s_idle_free_words = 40u;
static UBaseType_t s_timer_free_words = 90u;
static UBaseType_t s_calling_task_free_words = 7u;
extern uint32_t g_stack_monitor_host_stop_count;

UBaseType_t uxTaskGetStackHighWaterMark(TaskHandle_t task)
{
    if (task == &s_default_task_tag) return s_default_free_words;
    if (task == &s_idle_task_tag) return s_idle_free_words;
    if (task == &s_timer_task_tag) return s_timer_free_words;
    return s_calling_task_free_words;
}

TaskHandle_t xTaskGetHandle(const char *name)
{
    if (strcmp(name, "defaultTask") == 0) {
        s_default_handle_calls++;
        return &s_default_task_tag;
    }
    assert(strcmp(name, "IDLE") == 0);
    s_idle_handle_calls++;
    return s_idle_task_exists ? &s_idle_task_tag : NULL;
}

TaskHandle_t xTimerGetTimerDaemonTaskHandle(void)
{
    return &s_timer_task_tag;
}

void HAL_GPIO_WritePin(void *gpio_port, uint16_t gpio_pin, GPIO_PinState state)
{
    (void)gpio_port;
    (void)gpio_pin;
    s_last_gpio_state = state;
    s_gpio_write_count++;
}

HAL_StatusTypeDef HAL_SPI_TransmitReceive_DMA(SPI_HandleTypeDef *hspi,
                                              const uint8_t *tx_data,
                                              uint8_t *rx_data,
                                              uint16_t size)
{
    (void)hspi;
    s_spi_dma_start_count++;
    s_spi_last_tx_buffer = tx_data;
    s_spi_last_rx_buffer = rx_data;
    s_spi_last_transfer_size = size;
    return s_spi_dma_status;
}

HAL_StatusTypeDef HAL_SPI_Abort(SPI_HandleTypeDef *hspi)
{
    (void)hspi;
    s_spi_abort_count++;
    return HAL_OK;
}

HAL_StatusTypeDef HAL_I2C_Master_Transmit(I2C_HandleTypeDef *hi2c,
                                          uint16_t address,
                                          uint8_t *data,
                                          uint16_t size,
                                          uint32_t timeout_ms)
{
    uint32_t index = s_i2c_tx_call_count++;
    (void)hi2c;
    (void)timeout_ms;

    if (index < 16u) {
        s_i2c_writes[index].address = address;
        s_i2c_writes[index].size = size;
        if (size <= sizeof(s_i2c_writes[index].data)) {
            memcpy(s_i2c_writes[index].data, data, size);
        }
    }
    s_i2c_write_count = s_i2c_tx_call_count;
    return (index < 16u) ? s_i2c_tx_statuses[index] : HAL_OK;
}

HAL_StatusTypeDef HAL_I2C_Master_Receive(I2C_HandleTypeDef *hi2c,
                                         uint16_t address,
                                         uint8_t *data,
                                         uint16_t size,
                                         uint32_t timeout_ms)
{
    uint32_t index = s_i2c_rx_call_count++;
    (void)hi2c;
    (void)address;
    (void)timeout_ms;

    if ((index < 16u) && (size > 0u)) {
        memcpy(data, s_i2c_rx_payloads[index], size);
    }
    return (index < 16u) ? s_i2c_rx_statuses[index] : HAL_OK;
}

HAL_StatusTypeDef HAL_CAN_ConfigFilter(CAN_HandleTypeDef *hcan, CAN_FilterTypeDef *filter)
{
    (void)hcan;
    (void)filter;
    return s_can_filter_status;
}

HAL_StatusTypeDef HAL_CAN_Start(CAN_HandleTypeDef *hcan)
{
    (void)hcan;
    return s_can_start_status;
}

HAL_StatusTypeDef HAL_CAN_Stop(CAN_HandleTypeDef *hcan)
{
    (void)hcan;
    return s_can_stop_status;
}

uint32_t HAL_CAN_GetError(CAN_HandleTypeDef *hcan)
{
    (void)hcan;
    return s_can_error_bits;
}

uint32_t HAL_CAN_GetRxFifoFillLevel(CAN_HandleTypeDef *hcan, uint32_t fifo)
{
    (void)hcan;
    (void)fifo;
    return s_can_rx_count - s_can_rx_index;
}

HAL_StatusTypeDef HAL_CAN_GetRxMessage(CAN_HandleTypeDef *hcan,
                                       uint32_t fifo,
                                       CAN_RxHeaderTypeDef *header,
                                       uint8_t *data)
{
    (void)hcan;
    (void)fifo;

    if (s_can_rx_index >= s_can_rx_count) {
        return HAL_ERROR;
    }

    *header = s_can_rx_script[s_can_rx_index].header;
    memcpy(data, s_can_rx_script[s_can_rx_index].data, sizeof(s_can_rx_script[s_can_rx_index].data));
    s_can_rx_index++;
    return HAL_OK;
}

HAL_StatusTypeDef HAL_CAN_AddTxMessage(CAN_HandleTypeDef *hcan,
                                       CAN_TxHeaderTypeDef *header,
                                       uint8_t *data,
                                       uint32_t *mailbox)
{
    (void)hcan;
    if (header != NULL) {
        s_can_last_tx_header = *header;
    }
    if (data != NULL) {
        memcpy(s_can_last_tx_data, data, sizeof(s_can_last_tx_data));
    }
    if (mailbox != NULL) {
        *mailbox = 0u;
    }
    s_can_last_tx_count++;
    return s_can_add_tx_status;
}

SemaphoreHandle_t xSemaphoreCreateMutexStatic(StaticSemaphore_t *storage)
{
    if (storage != NULL) {
        storage->locked = pdFALSE;
    }
    return storage;
}

BaseType_t xSemaphoreTake(SemaphoreHandle_t semaphore, TickType_t wait_ticks)
{
    (void)wait_ticks;
    if ((semaphore == NULL) || s_force_semaphore_timeout || semaphore->locked) {
        return pdFALSE;
    }

    semaphore->locked = pdTRUE;
    return pdTRUE;
}

BaseType_t xSemaphoreGive(SemaphoreHandle_t semaphore)
{
    if (semaphore == NULL) {
        return pdFALSE;
    }

    semaphore->locked = pdFALSE;
    return pdTRUE;
}

static MksStatus FillTestFrame(const MksDevice *dev, uint8_t code, MksCanFrame *out, uint16_t can_id)
{
    if ((dev == NULL) || (out == NULL)) {
        return MKS_NULL_POINTER;
    }

    out->id = (can_id == MKS_CAN_ID_DEFAULT) ? dev->default_can_id : can_id;
    out->dlc = 2u;
    out->data[0] = code;
    out->data[1] = 0u;
    return s_mks_encode_status;
}

MksDevice mks_device_servo42(uint16_t default_can_id)
{
    MksDevice device = {.default_can_id = default_can_id, .max_working_current_ma = 0u};
    return device;
}

MksDevice mks_device_servo57(uint16_t default_can_id)
{
    MksDevice device = {.default_can_id = default_can_id, .max_working_current_ma = 0u};
    return device;
}

MksStatus mks_encode_set_motor_enable(const MksDevice *dev, bool enable, MksCanFrame *out, uint16_t can_id)
{
    (void)enable;
    return FillTestFrame(dev, 0xF1u, out, can_id);
}

MksStatus mks_encode_emergency_stop(const MksDevice *dev, MksCanFrame *out, uint16_t can_id)
{
    return FillTestFrame(dev, 0xFEu, out, can_id);
}

MksStatus mks_encode_speed_mode_run(const MksDevice *dev, bool dir_cw, uint16_t speed, uint8_t acc,
                                    bool has_runtime, uint32_t runtime_10ms, MksCanFrame *out, uint16_t can_id)
{
    (void)dir_cw;
    (void)speed;
    (void)acc;
    (void)has_runtime;
    (void)runtime_10ms;
    return FillTestFrame(dev, 0xA2u, out, can_id);
}

MksStatus mks_encode_relative_pulse_move(const MksDevice *dev, bool dir_cw, uint16_t speed, uint8_t acc,
                                         uint32_t relative_pulses, MksCanFrame *out, uint16_t can_id)
{
    (void)dir_cw;
    (void)speed;
    (void)acc;
    (void)relative_pulses;
    return FillTestFrame(dev, 0xA3u, out, can_id);
}

MksStatus mks_encode_absolute_pulse_move(const MksDevice *dev, uint16_t speed, uint8_t acc,
                                         int32_t absolute_pulses, MksCanFrame *out, uint16_t can_id)
{
    (void)speed;
    (void)acc;
    (void)absolute_pulses;
    return FillTestFrame(dev, 0xA4u, out, can_id);
}

MksStatus mks_encode_encoder_value(const MksDevice *dev, MksCanFrame *out, uint16_t can_id)
{
    return FillTestFrame(dev, 0x31u, out, can_id);
}

MksStatus mks_encode_realtime_speed(const MksDevice *dev, MksCanFrame *out, uint16_t can_id)
{
    return FillTestFrame(dev, 0x32u, out, can_id);
}

MksStatus mks_encode_working_current(const MksDevice *dev, uint16_t current_ma, bool save_to_flash,
                                     MksCanFrame *out, uint16_t can_id)
{
    (void)current_ma;
    (void)save_to_flash;
    return FillTestFrame(dev, 0x33u, out, can_id);
}

MksStatus mks_encode_set_zero_point(const MksDevice *dev, MksCanFrame *out, uint16_t can_id)
{
    return FillTestFrame(dev, 0x34u, out, can_id);
}

MksStatus mks_encode_execute_zero_return(const MksDevice *dev, bool has_mode, uint8_t mode,
                                         MksCanFrame *out, uint16_t can_id)
{
    (void)has_mode;
    (void)mode;
    return FillTestFrame(dev, 0x35u, out, can_id);
}

MksStatus mks_decode(const MksCanFrame *frame, MksParsedResponse *out)
{
    (void)frame;
    if ((out == NULL) && (s_mks_decode_status == MKS_OK)) {
        return MKS_NULL_POINTER;
    }
    if ((out != NULL) && (s_mks_decode_status == MKS_OK)) {
        *out = s_mks_decoded_response;
    }
    return s_mks_decode_status;
}

static bool SerializeTestFrame(uint8_t *frame_buffer,
                               uint16_t frame_capacity,
                               uint16_t *frame_length,
                               void *context)
{
    const uint8_t *value = context;

    if ((frame_buffer == NULL) || (frame_length == NULL) || (value == NULL) ||
        (frame_capacity < 2u)) {
        return false;
    }

    frame_buffer[0] = *value;
    frame_buffer[1] = 0xAAu;
    *frame_length = 2u;
    return true;
}

static uint16_t ReadU16(const uint8_t *data)
{
    return (uint16_t)data[0] | ((uint16_t)data[1] << 8u);
}

static uint32_t ReadU32(const uint8_t *data)
{
    return (uint32_t)data[0] |
           ((uint32_t)data[1] << 8u) |
           ((uint32_t)data[2] << 16u) |
           ((uint32_t)data[3] << 24u);
}

static uint64_t ReadU64(const uint8_t *data)
{
    return (uint64_t)data[0] |
           ((uint64_t)data[1] << 8u) |
           ((uint64_t)data[2] << 16u) |
           ((uint64_t)data[3] << 24u) |
           ((uint64_t)data[4] << 32u) |
           ((uint64_t)data[5] << 40u) |
           ((uint64_t)data[6] << 48u) |
           ((uint64_t)data[7] << 56u);
}

static void BuildRequest(uint8_t frame[SPI_FRAME_MAX_BYTES], uint8_t type, uint16_t length, uint32_t sequence)
{
    uint32_t crc32;
    memset(frame, 0, SPI_FRAME_MAX_BYTES);
    frame[SPI_FRAME_OFFSET_MAGIC] = (uint8_t)SPI_FRAME_MAGIC;
    frame[SPI_FRAME_OFFSET_MAGIC + 1u] = (uint8_t)(SPI_FRAME_MAGIC >> 8u);
    frame[SPI_FRAME_OFFSET_PROTOCOL_VERSION] = SPI_PROTOCOL_VERSION;
    frame[SPI_FRAME_OFFSET_MESSAGE_TYPE] = type;
    frame[SPI_FRAME_OFFSET_PAYLOAD_LENGTH] = (uint8_t)length;
    frame[SPI_FRAME_OFFSET_PAYLOAD_LENGTH + 1u] = (uint8_t)(length >> 8u);
    frame[SPI_FRAME_OFFSET_SEQUENCE] = (uint8_t)sequence;
    frame[SPI_FRAME_OFFSET_SEQUENCE + 1u] = (uint8_t)(sequence >> 8u);
    frame[SPI_FRAME_OFFSET_SEQUENCE + 2u] = (uint8_t)(sequence >> 16u);
    frame[SPI_FRAME_OFFSET_SEQUENCE + 3u] = (uint8_t)(sequence >> 24u);
    crc32 = Crc32IsoHdlc_Compute(frame, SPI_FRAME_HEADER_BYTES + length);
    Crc32IsoHdlc_WriteLittleEndian(crc32, &frame[SPI_FRAME_CRC_OFFSET(length)]);
}

static void BuildTimeSyncRequest(uint8_t frame[SPI_FRAME_MAX_BYTES],
                                 uint32_t request_sequence,
                                 uint64_t pi_time_us,
                                 uint32_t sync_sequence)
{
    uint32_t crc32;

    BuildRequest(frame, SPI_MESSAGE_TIME_SYNC, SPI_TIME_SYNC_PAYLOAD_BYTES, request_sequence);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 0u] = SPI_TIME_SYNC_SCHEMA_VERSION;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 1u] = 0u;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 2u] = 0u;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 3u] = 0u;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 4u] = (uint8_t)pi_time_us;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 5u] = (uint8_t)(pi_time_us >> 8u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 6u] = (uint8_t)(pi_time_us >> 16u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 7u] = (uint8_t)(pi_time_us >> 24u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 8u] = (uint8_t)(pi_time_us >> 32u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 9u] = (uint8_t)(pi_time_us >> 40u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 10u] = (uint8_t)(pi_time_us >> 48u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 11u] = (uint8_t)(pi_time_us >> 56u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 12u] = (uint8_t)sync_sequence;
    frame[SPI_FRAME_OFFSET_PAYLOAD + 13u] = (uint8_t)(sync_sequence >> 8u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 14u] = (uint8_t)(sync_sequence >> 16u);
    frame[SPI_FRAME_OFFSET_PAYLOAD + 15u] = (uint8_t)(sync_sequence >> 24u);
    crc32 = Crc32IsoHdlc_Compute(frame, SPI_FRAME_HEADER_BYTES + SPI_TIME_SYNC_PAYLOAD_BYTES);
    Crc32IsoHdlc_WriteLittleEndian(crc32, &frame[SPI_FRAME_CRC_OFFSET(SPI_TIME_SYNC_PAYLOAD_BYTES)]);
}

static void TestI2CManagerCore(void)
{
    uint8_t data = 0x12u;
    uint8_t rx = 0u;

    I2CManager_Init();
    if (I2CManager_GetLifecycleState() == LIFECYCLE_STATE_INACTIVE) {
        assert(I2CManager_Activate() == LIFECYCLE_RESULT_OK);
    }
    assert(I2CManager_MasterWriteRead(0x36u, NULL, 1u, &rx, 1u, 1u) == I2C_MANAGER_STATUS_BAD_ARG);
    assert(I2CManager_MasterWriteRead(0x36u, &data, 0u, &rx, 1u, 1u) == I2C_MANAGER_STATUS_BAD_ARG);
    assert(I2CManager_MasterWriteRead(0x36u, &data, 1u, NULL, 1u, 1u) == I2C_MANAGER_STATUS_BAD_ARG);
    assert(I2CManager_WriteThenWriteRead(0x70u, &data, 1u, 0x36u, &data, 1u, &rx, 0u, 1u) == I2C_MANAGER_STATUS_BAD_ARG);

    assert(I2CManager_MasterWriteRead(0x70u, &data, 1u, &rx, 1u, 1u) == I2C_MANAGER_STATUS_OK);
    assert(s_i2c_write_count == 1u);
    assert(s_i2c_writes[0].address == (uint16_t)(0x70u << 1u));
    assert(s_i2c_writes[0].data[0] == 0x12u);
    assert(I2CManager_GetSuccessCount() == 2u);
}

static void TestMuxAndAs5600Core(void)
{
    AS5600_Device device;
    uint8_t status = 0u;
    uint64_t timestamp_us = 0u;

    TCA9548A_Init(TCA9548A_ADDR_0);
    assert(TCA9548A_SelectChannelWriteRead(8u, AS5600_I2C_ADDR_7BIT, &status, 1u, &status, 1u, 10u) == I2C_MANAGER_STATUS_BAD_ARG);

    AS5600_InitDevice(&device, 2u);
    assert(AS5600_ReadStatus(&device, NULL, NULL) == AS5600_STATUS_BAD_ARG);

    s_time_now_us = 222u;
    s_i2c_rx_payloads[0][0] = AS5600_STATUS_MD;
    assert(AS5600_ReadStatus(&device, &status, &timestamp_us) == AS5600_STATUS_OK);
    assert(status == AS5600_STATUS_MD);
    assert(timestamp_us == 222u);
    assert(s_i2c_write_count == 2u);
    assert(s_i2c_writes[0].address == (uint16_t)(TCA9548A_ADDR_0 << 1u));
    assert(s_i2c_writes[0].data[0] == (1u << 2u));
    assert(s_i2c_writes[1].address == (uint16_t)(AS5600_I2C_ADDR_7BIT << 1u));
    assert(s_i2c_writes[1].data[0] == 0x0Bu);
}

#define TEST_SENSOR_WINDOW_US UINT64_C(100000)
#define TEST_MOTOR_WINDOW_US UINT64_C(200000)

/* App_Init configures the store from the commissioning tables; a test that drives one service
 * alone configures it here. NULL fitted means every axis is fitted. */
static void ConfigureStore(const bool *fitted, bool motor0_registered, uint16_t motor0_can_id)
{
    LatestValue_Config config;
    size_t axis;

    memset(&config, 0, sizeof(config));
    for (axis = 0u; axis < LATEST_VALUE_SENSOR_COUNT; ++axis) {
        config.sensor_fitted[axis] = (fitted == NULL) || fitted[axis];
    }
    config.motors[0].registered = motor0_registered;
    config.motors[0].logical_joint_id = 0u;
    config.motors[0].can_id = motor0_can_id;
    config.motors[0].configuration_version = 1u;
    config.sensor_window_us = TEST_SENSOR_WINDOW_US;
    config.motor_window_us = TEST_MOTOR_WINDOW_US;
    assert(LatestValue_Configure(&config) == LATEST_VALUE_OK);
}

static void TestSensorTaskCore(void)
{
    static LatestValue_Snapshot copy;

    ConfigureStore(NULL, false, 0u);
    SensorTask_Init();
    assert(SensorTask_Activate() == LIFECYCLE_RESULT_OK);
    s_hal_tick = 20u;
    s_i2c_tx_statuses[0] = HAL_ERROR;
    SensorTask_Process();
    assert(SensorTask_GetBringupResult() == SENSOR_TASK_BRINGUP_FAIL_COMM);
    /* The mux probe failed before any axis was read: nothing was accepted. */
    LatestValue_CopySnapshot(s_time_now_us, &copy);
    assert(!copy.sensors[0].has_sample);
    assert(copy.sensors[0].freshness == LATEST_VALUE_FRESHNESS_NONE);
    s_i2c_tx_statuses[0] = HAL_OK;
}

static void TestSensorTaskMuxMapping(void)
{
    static const uint8_t commissioned[SENSOR_TASK_AXIS_COUNT] = {2u, 3u, 4u, 5u, 6u, 7u};
    static const uint8_t out_of_range[SENSOR_TASK_AXIS_COUNT] = {2u, 3u, 4u, 5u, 6u, 8u};
    static const uint8_t duplicated[SENSOR_TASK_AXIS_COUNT] = {2u, 3u, 4u, 5u, 6u, 6u};

    TCA9548A_Init(TCA9548A_ADDR_0);
    ConfigureStore(NULL, false, 0u);
    SensorTask_Init();

    /* Rejected maps change nothing. */
    assert(!SensorTask_ConfigureMuxChannels(NULL, SENSOR_TASK_AXIS_COUNT));
    assert(!SensorTask_ConfigureMuxChannels(commissioned, SENSOR_TASK_AXIS_COUNT - 1u));
    assert(!SensorTask_ConfigureMuxChannels(out_of_range, SENSOR_TASK_AXIS_COUNT));
    assert(!SensorTask_ConfigureMuxChannels(duplicated, SENSOR_TASK_AXIS_COUNT));

    assert(SensorTask_ConfigureMuxChannels(commissioned, SENSOR_TASK_AXIS_COUNT));
    assert(SensorTask_Activate() == LIFECYCLE_RESULT_OK);

    /* Rebinding a live acquisition path is refused. */
    assert(!SensorTask_ConfigureMuxChannels(commissioned, SENSOR_TASK_AXIS_COUNT));

    /* Bring-up probes the mux, then addresses axis 0 through SD2 rather than SD0. */
    s_i2c_rx_payloads[0][0] = 0x01u;
    s_hal_tick = 20u;
    SensorTask_Process();

    assert(s_i2c_writes[0].address == (uint16_t)(TCA9548A_ADDR_0 << 1u));
    assert(s_i2c_writes[0].data[0] == 0x01u);
    assert(s_i2c_writes[1].address == (uint16_t)(TCA9548A_ADDR_0 << 1u));
    assert(s_i2c_writes[1].data[0] == (1u << 2u));
    assert(s_i2c_writes[2].address == (uint16_t)(AS5600_I2C_ADDR_7BIT << 1u));
    assert(s_i2c_writes[2].data[0] == 0x0Bu);
    /* Axis 1 follows on SD3. */
    assert(s_i2c_writes[3].data[0] == (1u << 3u));
    /* Axis 5 is the last bring-up access and lands on SD7. */
    assert(s_i2c_writes[11].data[0] == (1u << 7u));
    assert(SensorTask_GetBringupResult() == SENSOR_TASK_BRINGUP_PASS);

    /* Logical identity stays 0-5 no matter which channels are bound. */
    {
        static LatestValue_Snapshot copy;
        size_t axis;

        LatestValue_CopySnapshot(s_time_now_us, &copy);
        for (axis = 0u; axis < LATEST_VALUE_SENSOR_COUNT; ++axis) {
            assert(copy.sensors[axis].logical_id == (uint8_t)axis);
        }
    }
}

static void TestSensorTaskNotFitted(void)
{
    static const uint8_t commissioned[SENSOR_TASK_AXIS_COUNT] = {2u, 3u, 4u, 5u, 6u, 7u};
    static const bool fitted[SENSOR_TASK_AXIS_COUNT] = {true, true, true, false, true, true};
    static LatestValue_Snapshot copy;
    static uint8_t payload[SPI_SNAPSHOT_MAX_PAYLOAD_BYTES];
    uint16_t payload_length = 0u;
    unsigned critical_entries;
    uint32_t write;
    size_t axis;

    TCA9548A_Init(TCA9548A_ADDR_0);
    ConfigureStore(fitted, false, 0u);
    SensorTask_Init();
    assert(SensorTask_ConfigureMuxChannels(commissioned, SENSOR_TASK_AXIS_COUNT));

    assert(!SensorTask_ConfigureFittedAxes(NULL, SENSOR_TASK_AXIS_COUNT));
    assert(!SensorTask_ConfigureFittedAxes(fitted, SENSOR_TASK_AXIS_COUNT - 1u));
    assert(SensorTask_ConfigureFittedAxes(fitted, SENSOR_TASK_AXIS_COUNT));
    assert(SensorTask_Activate() == LIFECYCLE_RESULT_OK);
    assert(!SensorTask_ConfigureFittedAxes(fitted, SENSOR_TASK_AXIS_COUNT));

    /* Bring-up never addresses SD5, the mux channel of the unfitted axis 3. */
    s_i2c_rx_payloads[0][0] = 0x01u;
    s_hal_tick = 20u;
    SensorTask_Process();
    for (write = 0u; write < s_i2c_write_count; ++write) {
        assert(s_i2c_writes[write].data[0] != (1u << 5u));
    }
    assert(SensorTask_GetBringupResult() == SENSOR_TASK_BRINGUP_PASS);
    assert(SensorTask_GetBringupSnapshot()->comm_error_count == 0u);

    /* Polling does not address it either. Every fitted axis is read and accepted, each accept
     * inside the store's critical section. */
    s_i2c_write_count = 0u;
    s_i2c_tx_call_count = 0u;
    s_i2c_rx_call_count = 0u;
    s_hal_tick = 40u;
    critical_entries = HostStub_CriticalEntryCount();
    SensorTask_Process();
    assert(HostStub_CriticalEntryCount() == critical_entries + 5u);
    assert(HostStub_CriticalDepth() == 0u);
    for (write = 0u; write < s_i2c_write_count; ++write) {
        assert(s_i2c_writes[write].data[0] != (1u << 5u));
    }
    assert(SensorTask_GetBringupSnapshot()->comm_error_count == 0u);

    /* The not-fitted axis is a slot property, refreshed at copy time and serialised with only
     * the NOT_FITTED bit; the fitted axes hold the samples the sweep accepted. */
    s_time_now_us = 5000u;
    LatestValue_CopySnapshot(s_time_now_us, &copy);
    assert(SpiProtocol_SerializeSnapshot(&copy, 0u, payload, &payload_length) == SPI_PROTOCOL_OK);
    for (axis = 0u; axis < LATEST_VALUE_SENSOR_COUNT; ++axis) {
        const uint8_t *record = &payload[SPI_SNAPSHOT_PREFIX_BYTES + (axis * SPI_SENSOR_RECORD_BYTES)];
        uint16_t flags = ReadU16(&record[SPI_SENSOR_RECORD_OFFSET_VALIDITY_FLAGS]);
        if (axis == 3u) {
            assert(!copy.sensors[axis].fitted);
            assert(flags == SPI_SENSOR_VALIDITY_NOT_FITTED);
            assert(ReadU64(&record[SPI_SENSOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US]) == UINT64_C(5000));
        } else {
            assert(copy.sensors[axis].fitted && copy.sensors[axis].has_sample);
            assert((flags & SPI_SENSOR_VALIDITY_NOT_FITTED) == 0u);
        }
    }
}

static void TestCanServiceCore(void)
{
    assert(CanService_RegisterMotor(CAN_SERVICE_MAX_MKS_MOTORS, CAN_SERVICE_MKS_SERVO42, 1u) ==
           MKS_INVALID_ARGUMENT);

    CanService_Init();
    assert(CanService_RequestEncoderValue(0u) == MKS_INVALID_ARGUMENT);
    assert(CanService_Activate() == LIFECYCLE_RESULT_OK);
    assert(CanService_RegisterMotor(0u, CAN_SERVICE_MKS_SERVO42, 0x800u) ==
           MKS_CAN_ID_OUT_OF_RANGE);
    assert(CanService_RegisterMotor(0u, CAN_SERVICE_MKS_SERVO42, 0x123u) == MKS_OK);
    assert(CanService_RequestEncoderValue(0u) == MKS_OK);
}

/* Queues one received frame for motor CAN ID can_id. The host build stubs mks_decode (above), so
 * the decoded reply is set directly: code, then the bytes between the code and the checksum. */
static void ScriptMksReply(uint16_t can_id, const uint8_t *reply, uint8_t reply_length)
{
    CanRxScript *entry = &s_can_rx_script[s_can_rx_count++];

    memset(entry, 0, sizeof(*entry));
    entry->header.StdId = can_id;
    entry->header.IDE = CAN_ID_STD;
    entry->header.DLC = (uint32_t)reply_length + 1u;
    memset(&s_mks_decoded_response, 0, sizeof(s_mks_decoded_response));
    s_mks_decoded_response.can_id = can_id;
    s_mks_decoded_response.code = reply[0];
    s_mks_decoded_response.payload_len = (uint8_t)(reply_length - 1u);
    memcpy(s_mks_decoded_response.payload, &reply[1], (size_t)reply_length - 1u);
    s_mks_decode_status = MKS_OK;
}

static void TestCanServiceFeedbackIntoStore(void)
{
    /* 30H: carry -1 (int32) and value 0x3FFE (uint16), big-endian, so -2 counts; the first data
     * byte 0x00 variant is covered by the status check below. 32H: speed -300 rpm as int16. */
    static const uint8_t position_reply[7] = {0x30u, 0xFFu, 0xFFu, 0xFFu, 0xFFu, 0x3Fu, 0xFEu};
    static const uint8_t low_position_reply[7] = {0x30u, 0x00u, 0x00u, 0x00u, 0x01u, 0x00u, 0x05u};
    static const uint8_t speed_reply[3] = {0x32u, 0xFEu, 0xD4u};
    static LatestValue_Snapshot copy;
    static uint8_t first[SPI_SNAPSHOT_MAX_PAYLOAD_BYTES];
    static uint8_t second[SPI_SNAPSHOT_MAX_PAYLOAD_BYTES];
    uint16_t length = 0u;
    const uint8_t *motor_record = &first[SPI_SNAPSHOT_PAYLOAD_BYTES(0u)];

    CanService_Init();
    assert(CanService_Activate() == LIFECYCLE_RESULT_OK);
    assert(CanService_RegisterMotor(0u, CAN_SERVICE_MKS_SERVO42, 0x001u) == MKS_OK);
    ConfigureStore(NULL, true, 0x001u);
    CanService_SetPollPeriodMs(0u);

    s_time_now_us = 1000u;
    ScriptMksReply(0x001u, position_reply, sizeof(position_reply));
    CanService_Process();
    assert(CanService_GetRxOkCount(0u) == 1u);
    LatestValue_CopySnapshot(UINT64_C(1500), &copy);
    assert(copy.motors[0].has_position);
    assert(copy.motors[0].position_counts == INT64_C(-2));
    assert(copy.motors[0].position_timestamp_us == UINT64_C(1000));
    assert(copy.motors[0].freshness == LATEST_VALUE_FRESHNESS_FRESH);
    assert(!copy.motors[0].has_speed);
    assert(SpiProtocol_SerializeSnapshot(&copy, 0u, first, &length) == SPI_PROTOCOL_OK);
    assert(length == SPI_SNAPSHOT_PAYLOAD_BYTES(1u));
    assert(motor_record[SPI_MOTOR_RECORD_OFFSET_COMMAND_CODE] == 0x30u);
    assert(motor_record[SPI_MOTOR_RECORD_OFFSET_PAYLOAD_LENGTH] == 6u);
    assert(memcmp(&motor_record[SPI_MOTOR_RECORD_OFFSET_PAYLOAD], &position_reply[1], 6u) == 0);
    assert(ReadU64(&motor_record[SPI_MOTOR_RECORD_OFFSET_MEASUREMENT_TIMESTAMP_US]) == UINT64_C(1000));

    /* A speed reply is merged with its own timestamp and leaves the v1 record unchanged (R10). */
    s_time_now_us = 1200u;
    ScriptMksReply(0x001u, speed_reply, sizeof(speed_reply));
    CanService_Process();
    LatestValue_CopySnapshot(UINT64_C(1500), &copy);
    assert(copy.motors[0].has_speed);
    assert(copy.motors[0].speed_rpm == -300);
    assert(copy.motors[0].speed_timestamp_us == UINT64_C(1200));
    assert(copy.motors[0].position_counts == INT64_C(-2));
    assert(SpiProtocol_SerializeSnapshot(&copy, 0u, second, &length) == SPI_PROTOCOL_OK);
    assert(memcmp(first, second, length) == 0);

    /* A position whose first data byte is 0x00 (or 0x01) looks like a status byte to the decoder
     * (has_status); the record must not report a drive status for it. */
    s_time_now_us = 1300u;
    ScriptMksReply(0x001u, low_position_reply, sizeof(low_position_reply));
    s_mks_decoded_response.has_status = true;
    s_mks_decoded_response.status = 0u;
    CanService_Process();
    LatestValue_CopySnapshot(UINT64_C(1500), &copy);
    assert(copy.motors[0].position_counts == INT64_C(0x4005));
    assert(SpiProtocol_SerializeSnapshot(&copy, 0u, first, &length) == SPI_PROTOCOL_OK);
    assert(motor_record[SPI_MOTOR_RECORD_OFFSET_STATUS] == 0u);
    assert(ReadU16(&motor_record[SPI_MOTOR_RECORD_OFFSET_VALIDITY_FLAGS]) == SPI_MOTOR_VALIDITY_FEEDBACK_VALID);
    assert(HostStub_CriticalDepth() == 0u);
}

static void TestSpiSlaveServiceCore(void)
{
    uint8_t frame_value = 0x33u;
    const uint8_t *frame_buffer = NULL;
    uint16_t frame_length = 0u;
    uint8_t request[SPI_FRAME_MAX_BYTES];
    const SnapshotFrame_Diagnostics *diagnostics;

    /* Armed-then-assert model (approved 2026-09-17): DATA_READY rises only after
     * the staged frame is handed to DMA ownership and the transfer is armed. */
    s_time_now_us = 111u;
    SpiSlaveService_Init();
    assert(SpiSlaveService_StageSnapshot(SerializeTestFrame, &frame_value) == SNAPSHOT_BUILD_NOT_READY);
    assert(s_spi_dma_start_count == 0u);
    assert(s_last_gpio_state == GPIO_PIN_RESET);
    assert(SpiSlaveService_Activate() == LIFECYCLE_RESULT_OK);
    assert(s_spi_dma_start_count == 1u);
    assert(s_spi_last_transfer_size == SPI_FRAME_MAX_BYTES);
    assert(s_spi_last_tx_buffer != NULL);
    assert(s_spi_last_rx_buffer != NULL);
    assert(s_spi_last_tx_buffer[SPI_FRAME_OFFSET_MESSAGE_TYPE] == SPI_MESSAGE_DIAGNOSTIC);
    assert(ReadU64(&s_spi_last_tx_buffer[SPI_FRAME_OFFSET_TIME_US]) == UINT64_C(111));
    assert(s_last_gpio_state == GPIO_PIN_SET);
    /* The armed buffer is DMA-owned: a second handoff is refused. */
    assert(!SpiSlaveService_BeginDmaTransfer(&frame_buffer, &frame_length));
    diagnostics = SpiSlaveService_GetSnapshotDiagnostics();
    assert(diagnostics->dma_start_count == 1u);
    assert(diagnostics->dma_complete_count == 0u);
    /* Staging while a transfer is armed lands in the free buffer without re-arming. */
    assert(SpiSlaveService_StageSnapshot(SerializeTestFrame, &frame_value) == SNAPSHOT_BUILD_OK);
    assert(s_spi_dma_start_count == 1u);

    /* INACTIVE request handling: NACK is staged but not armed until ACTIVE. */
    ResetHalState();
    s_time_now_us = 500u;
    SpiSlaveService_Init();
    BuildRequest(request, SPI_MESSAGE_GET_STATUS, 0u, 1u);
    assert(SpiSlaveService_ProcessRequestFrame(request) == SPI_PROTOCOL_BAD_STATE);
    assert(s_spi_dma_start_count == 0u);
    assert(s_last_gpio_state == GPIO_PIN_RESET);
    assert(SpiSlaveService_Activate() == LIFECYCLE_RESULT_OK);
    assert(s_spi_dma_start_count == 1u);
    assert(s_last_gpio_state == GPIO_PIN_SET);
    assert(s_spi_last_tx_buffer[3] == SPI_MESSAGE_NACK);
    assert(ReadU16(&s_spi_last_tx_buffer[SPI_FRAME_OFFSET_PAYLOAD + 2u]) == SPI_PROTOCOL_BAD_STATE);
    assert(ReadU32(&s_spi_last_tx_buffer[SPI_FRAME_OFFSET_PAYLOAD + 4u]) == 1u);
    assert(ReadU64(&s_spi_last_tx_buffer[SPI_FRAME_OFFSET_TIME_US]) == UINT64_C(500));

    /* TIME_SYNC is accepted while INACTIVE; the ACK is armed on activation. */
    ResetHalState();
    s_time_now_us = 500u;
    SpiSlaveService_Init();
    BuildTimeSyncRequest(request, 2u, 900u, 7u);
    assert(SpiSlaveService_ProcessRequestFrame(request) == SPI_PROTOCOL_OK);
    assert(s_time_sync_accept_count == 1u);
    assert(s_last_time_sync_pi_time_us == 900u);
    assert(s_last_time_sync_sequence == 7u);
    assert(TimeService_IsSyncValid());
    assert(SpiSlaveService_Activate() == LIFECYCLE_RESULT_OK);
    assert(s_spi_dma_start_count == 1u);
    assert(s_last_gpio_state == GPIO_PIN_SET);
    assert(s_spi_last_tx_buffer[3] == SPI_MESSAGE_ACK);
    /* Verify SPI transaction timing mirror fields are captured correctly.
     * In this direct ProcessRequestFrame path:
     * - dma_complete_raw: not captured (HAL_SPI_TxRxCpltCallback not called)
     * - process_start_us: not captured (SpiSlaveService_Process() not called)
     * - response_staged_us: captured during ProcessRequestFrame
     * - data_ready_set_us: captured during Activate (when lifecycle becomes ACTIVE)
     * - request_type, request_seq: captured during ProcessRequestFrame
     */
    assert(g_spi_timing_dbg.dma_complete_raw == 0u);  /* Not captured in this path. */
    assert(g_spi_timing_dbg.process_start_us == 0u);  /* Not captured in this path. */
    assert(g_spi_timing_dbg.response_staged_us == 500u);
    assert(g_spi_timing_dbg.data_ready_set_us == 500u);
    assert(g_spi_timing_dbg.request_type == SPI_MESSAGE_TIME_SYNC);
    assert(g_spi_timing_dbg.request_seq == 2u);

    BuildRequest(request, SPI_MESSAGE_GET_STATUS, 0u, 7u);
    request[0] ^= 1u;
    assert(SpiSlaveService_ProcessRequestFrame(request) == SPI_PROTOCOL_BAD_MAGIC);

    BuildRequest(request, SPI_MESSAGE_TIME_SYNC, 0u, 8u);
    assert(SpiSlaveService_ProcessRequestFrame(request) == SPI_PROTOCOL_BAD_TIME_SYNC);
    assert(s_time_sync_accept_count == 1u);

    BuildTimeSyncRequest(request, 9u, 950u, 7u);
    s_time_sync_result = TIME_SERVICE_SYNC_REJECTED_SEQUENCE;
    assert(SpiSlaveService_ProcessRequestFrame(request) == SPI_PROTOCOL_BAD_TIME_SYNC);
    assert(s_time_sync_accept_count == 2u);

    BuildTimeSyncRequest(request, 10u, 1000u, 8u);
    s_time_sync_result = TIME_SERVICE_SYNC_REJECTED_OFFSET;
    assert(SpiSlaveService_ProcessRequestFrame(request) == SPI_PROTOCOL_BAD_TIME_SYNC);
    assert(s_time_sync_accept_count == 3u);
}

static void TestSpiSlaveServiceDmaLoop(void)
{
    uint8_t frame_value = 0x44u;
    SPI_HandleTypeDef other_spi = {.Instance = (void *)0x6};
    const SnapshotFrame_Diagnostics *diagnostics;

    s_time_now_us = 111u;
    SpiSlaveService_Init();
    assert(SpiSlaveService_Activate() == LIFECYCLE_RESULT_OK);
    assert(s_spi_dma_start_count == 1u);
    assert(s_last_gpio_state == GPIO_PIN_SET);
    diagnostics = SpiSlaveService_GetSnapshotDiagnostics();

    /* A completion for another SPI instance is ignored. */
    HAL_SPI_TxRxCpltCallback(&other_spi);
    SpiSlaveService_Process();
    assert(diagnostics->dma_complete_count == 0u);
    assert(s_spi_dma_start_count == 1u);

    /* Host clocks the transaction carrying GET_STATUS seq 1. The ISR only flags;
     * ownership release and request processing happen in Process(). */
    BuildRequest(s_spi_last_rx_buffer, SPI_MESSAGE_GET_STATUS, 0u, 1u);
    HAL_SPI_TxRxCpltCallback(&hspi3);
    assert(diagnostics->dma_complete_count == 0u);
    SpiSlaveService_Process();
    assert(diagnostics->dma_complete_count == 1u);
    assert(s_spi_dma_start_count == 2u);
    assert(s_spi_last_tx_buffer[3] == SPI_MESSAGE_ACK);
    assert(ReadU32(&s_spi_last_tx_buffer[SPI_FRAME_OFFSET_PAYLOAD + 4u]) == 1u);
    assert(s_last_gpio_state == GPIO_PIN_SET);
    assert(s_spi_abort_count == 0u);

    /* DMA error: abort, release, DATA_READY low, boot status re-staged and re-armed. */
    HAL_SPI_ErrorCallback(&hspi3);
    assert(s_spi_abort_count == 0u);
    SpiSlaveService_Process();
    assert(s_spi_abort_count == 1u);
    assert(diagnostics->dma_complete_count == 2u);
    assert(s_spi_dma_start_count == 3u);
    assert(s_spi_last_tx_buffer[SPI_FRAME_OFFSET_MESSAGE_TYPE] == SPI_MESSAGE_DIAGNOSTIC);
    assert(s_last_gpio_state == GPIO_PIN_SET);

    /* Host stall: no completion within 100 ms produces the same recovery. */
    s_hal_tick = 99u;
    SpiSlaveService_Process();
    assert(s_spi_abort_count == 1u);
    s_hal_tick = 100u;
    SpiSlaveService_Process();
    assert(s_spi_abort_count == 2u);
    assert(diagnostics->dma_complete_count == 3u);
    assert(s_spi_dma_start_count == 4u);
    assert(s_spi_last_tx_buffer[SPI_FRAME_OFFSET_MESSAGE_TYPE] == SPI_MESSAGE_DIAGNOSTIC);
    assert(s_last_gpio_state == GPIO_PIN_SET);

    /* A DMA start failure releases the handed-off buffer and leaves DATA_READY low. */
    ResetHalState();
    s_time_now_us = 111u;
    s_spi_dma_status = HAL_ERROR;
    SpiSlaveService_Init();
    assert(SpiSlaveService_Activate() == LIFECYCLE_RESULT_OK);
    assert(s_spi_dma_start_count == 1u);
    assert(s_last_gpio_state == GPIO_PIN_RESET);
    diagnostics = SpiSlaveService_GetSnapshotDiagnostics();
    assert(diagnostics->dma_start_count == 1u);
    assert(diagnostics->dma_complete_count == 1u);
    /* With the HAL healthy again, a newly staged frame is armed and signalled. */
    s_spi_dma_status = HAL_OK;
    assert(SpiSlaveService_StageSnapshot(SerializeTestFrame, &frame_value) == SNAPSHOT_BUILD_OK);
    assert(s_spi_dma_start_count == 2u);
    assert(s_spi_last_tx_buffer[0] == 0x44u);
    assert(s_last_gpio_state == GPIO_PIN_SET);
}

/* A serializer that tries to stage again from inside a staging, as a second
 * caller would; it then writes a small frame so the outer staging succeeds. */
static SnapshotBuild_Result s_nested_stage_result;

static bool TestNestedStageSerializer(uint8_t *frame_buffer, uint16_t frame_capacity,
                                      uint16_t *frame_length, void *context)
{
    (void)context;
    s_nested_stage_result = SpiSlaveService_StageLatestSnapshot();
    if ((frame_buffer == NULL) || (frame_length == NULL) || (frame_capacity < 16u)) return false;
    memset(frame_buffer, 0, 16u);
    *frame_length = 16u;
    return true;
}

static void TestSpiSlaveServiceLatestSnapshot(void)
{
    const uint8_t *frame;
    uint16_t expected_payload_length = SPI_SNAPSHOT_PAYLOAD_BYTES(1u);
    uint16_t sensor0_offset = SPI_FRAME_OFFSET_PAYLOAD + SPI_SNAPSHOT_PREFIX_BYTES;
    uint16_t sensor1_offset = sensor0_offset + SPI_SENSOR_RECORD_BYTES;
    uint16_t motor0_offset = SPI_FRAME_OFFSET_PAYLOAD + SPI_SNAPSHOT_PREFIX_BYTES +
                             (SPI_SNAPSHOT_SENSOR_RECORD_COUNT * SPI_SENSOR_RECORD_BYTES);

    uint16_t sensor3_offset = sensor0_offset + (3u * SPI_SENSOR_RECORD_BYTES);
    static const bool fitted[SENSOR_TASK_AXIS_COUNT] = {true, true, true, false, true, true};

    SensorTask_Init();
    assert(SensorTask_ConfigureFittedAxes(fitted, SENSOR_TASK_AXIS_COUNT));
    CanService_Init();
    assert(CanService_RegisterMotor(0u, CAN_SERVICE_MKS_SERVO42, 0x123u) == MKS_OK);
    ConfigureStore(fitted, true, 0x123u);
    s_time_now_us = 700u;
    /* Leave the DMA idle after activation so the staged snapshot is the frame armed. */
    s_spi_dma_status = HAL_ERROR;
    SpiSlaveService_Init();
    assert(SpiSlaveService_Activate() == LIFECYCLE_RESULT_OK);
    s_spi_dma_status = HAL_OK;
    assert(SpiSlaveService_StageLatestSnapshot() == SNAPSHOT_BUILD_OK);
    assert(s_spi_dma_start_count == 2u);
    assert(s_last_gpio_state == GPIO_PIN_SET);
    frame = s_spi_last_tx_buffer;
    assert(frame != NULL);
    assert(frame[SPI_FRAME_OFFSET_MESSAGE_TYPE] == SPI_MESSAGE_SNAPSHOT);
    assert(ReadU16(&frame[SPI_FRAME_OFFSET_PAYLOAD_LENGTH]) == expected_payload_length);
    assert(ReadU64(&frame[SPI_FRAME_OFFSET_TIME_US]) == UINT64_C(700));
    assert(frame[SPI_FRAME_OFFSET_PAYLOAD + SPI_SNAPSHOT_OFFSET_SCHEMA_VERSION] == 1u);
    assert(frame[SPI_FRAME_OFFSET_PAYLOAD + SPI_SNAPSHOT_OFFSET_SENSOR_COUNT] == 6u);
    assert(frame[SPI_FRAME_OFFSET_PAYLOAD + SPI_SNAPSHOT_OFFSET_MOTOR_COUNT] == 1u);
    assert(ReadU32(&frame[SPI_FRAME_OFFSET_PAYLOAD + SPI_SNAPSHOT_OFFSET_RESPONSE_TO_SEQUENCE]) == 0u);
    assert(frame[sensor0_offset + SPI_SENSOR_RECORD_OFFSET_SENSOR_ID] == 0u);
    assert(ReadU16(&frame[sensor0_offset + SPI_SENSOR_RECORD_OFFSET_VALIDITY_FLAGS]) == 0u);
    assert(ReadU16(&frame[sensor0_offset + SPI_SENSOR_RECORD_OFFSET_MAGNITUDE]) == 0u);
    assert(frame[sensor0_offset + SPI_SENSOR_RECORD_OFFSET_AGC] == 0u);
    assert(frame[sensor1_offset + SPI_SENSOR_RECORD_OFFSET_SENSOR_ID] == 1u);
    assert(ReadU16(&frame[sensor1_offset + SPI_SENSOR_RECORD_OFFSET_VALIDITY_FLAGS]) == 0u);
    assert(frame[sensor3_offset + SPI_SENSOR_RECORD_OFFSET_SENSOR_ID] == 3u);
    assert(ReadU16(&frame[sensor3_offset + SPI_SENSOR_RECORD_OFFSET_VALIDITY_FLAGS]) ==
           SPI_SENSOR_VALIDITY_NOT_FITTED);
    assert(frame[motor0_offset + SPI_MOTOR_RECORD_OFFSET_MOTOR_INDEX] == 0u);
    assert(ReadU16(&frame[motor0_offset + SPI_MOTOR_RECORD_OFFSET_CAN_ID]) == 0x123u);
    assert(frame[motor0_offset + SPI_MOTOR_RECORD_OFFSET_PAYLOAD_LENGTH] == 0u);

    /* The staging guard is released after each build, so the next one succeeds. */
    assert(SpiSlaveService_StageLatestSnapshot() == SNAPSHOT_BUILD_OK);

    /* A caller that arrives while another is staging is refused, not interleaved. */
    s_nested_stage_result = SNAPSHOT_BUILD_OK;
    assert(SpiSlaveService_StageSnapshot(TestNestedStageSerializer, NULL) == SNAPSHOT_BUILD_OK);
    assert(s_nested_stage_result == SNAPSHOT_BUILD_BUSY);
    assert(SpiSlaveService_StageLatestSnapshot() == SNAPSHOT_BUILD_OK);
}

static void TestAppInitCore(void)
{
    App_Init();
    assert(App_GetMksRegisterFailureCount() == 0u);
    App_Start();
    assert(App_GetLifecycleActivationFailureCount() == 0u);
}

static void TestStackMonitor(void)
{
    /* Not read until the first refresh. */
    assert(g_stack_monitor_dbg.sample_count == 0u);
    assert(g_stack_monitor_dbg.default_task_min_free_bytes == STACK_MONITOR_NOT_READ);

    /* First refresh: the idle task is not found yet, so its figure stays unread. */
    s_hal_tick = 5000u;
    s_idle_task_exists = false;
    StackMonitor_Process();
    assert(g_stack_monitor_dbg.sample_count == 1u);
    assert(g_stack_monitor_dbg.default_task_min_free_bytes == 300u * 4u);
    assert(g_stack_monitor_dbg.timer_task_min_free_bytes == 90u * 4u);
    assert(g_stack_monitor_dbg.idle_task_min_free_bytes == STACK_MONITOR_NOT_READ);

    /* Within the refresh period nothing is read again. */
    s_default_free_words = 250u;
    s_hal_tick = 5999u;
    StackMonitor_Process();
    assert(g_stack_monitor_dbg.sample_count == 1u);
    assert(g_stack_monitor_dbg.default_task_min_free_bytes == 300u * 4u);

    /* After it, every figure is refreshed and the idle handle is looked up again. */
    s_idle_task_exists = true;
    s_hal_tick = 6000u;
    StackMonitor_Process();
    assert(g_stack_monitor_dbg.sample_count == 2u);
    assert(g_stack_monitor_dbg.default_task_min_free_bytes == 250u * 4u);
    assert(g_stack_monitor_dbg.idle_task_min_free_bytes == 40u * 4u);
    assert(s_idle_handle_calls == 2u);

    /* Once found, the handles are cached; defaultTask is found by name, not by caller. */
    s_hal_tick = 7000u;
    StackMonitor_Process();
    assert(g_stack_monitor_dbg.sample_count == 3u);
    assert(s_idle_handle_calls == 2u);
    assert(s_default_handle_calls == 1u);
    assert(g_stack_monitor_dbg.default_task_min_free_bytes != s_calling_task_free_words * 4u);

    /* Overflow: the outputs are stopped first and the task name is recorded. */
    StackMonitor_OnOverflow("defaultTask");
    assert(g_stack_monitor_host_stop_count == 1u);
    assert(g_stack_monitor_dbg.overflow_detected == 1u);
    assert(strcmp((const char *)g_stack_monitor_dbg.overflow_task, "defaultTask") == 0);

    /* A name longer than the field is cut and still terminated. */
    StackMonitor_OnOverflow("a_task_name_longer_than_sixteen");
    assert(strlen((const char *)g_stack_monitor_dbg.overflow_task) == STACK_MONITOR_TASK_NAME_BYTES - 1u);
    assert(strncmp((const char *)g_stack_monitor_dbg.overflow_task, "a_task_name_lon", 15u) == 0);

    /* No name at all leaves an empty string. */
    StackMonitor_OnOverflow(NULL);
    assert(g_stack_monitor_dbg.overflow_task[0] == '\0');
    assert(g_stack_monitor_host_stop_count == 3u);
}

int main(void)
{
    ResetHalState();
    TestAppInitCore();

    ResetHalState();
    TestI2CManagerCore();

    ResetHalState();
    TestMuxAndAs5600Core();

    ResetHalState();
    TestSensorTaskCore();

    ResetHalState();
    TestSensorTaskMuxMapping();

    ResetHalState();
    TestSensorTaskNotFitted();

    ResetHalState();
    TestCanServiceCore();

    ResetHalState();
    TestCanServiceFeedbackIntoStore();

    ResetHalState();
    TestSpiSlaveServiceCore();

    ResetHalState();
    TestSpiSlaveServiceDmaLoop();

    ResetHalState();
    TestSpiSlaveServiceLatestSnapshot();

    ResetHalState();
    TestStackMonitor();

    return 0;
}
