/* C-compatible API boundary for the MKS Servo protocol library.
 *
 * This header is the ONLY seam between the C11 application layer and the C++17
 * library. It exposes POD structs and functions only — no C++ types, STL,
 * exceptions, or RTTI cross this boundary.
 *
 * The library is a pure protocol codec: it builds/verifies generic CAN frames.
 * Transport (queues, retries, timeouts, bus-off recovery, HAL/bxCAN) belongs to
 * the CAN Service layer, not here.
 */
#ifndef MKS_API_H
#define MKS_API_H

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define MKS_MAX_DLC 8u
#define MKS_MAX_PAYLOAD (MKS_MAX_DLC - 2u)
#define MKS_CAN_ID_DEFAULT 0xFFFFu /* use device default */

/* Status codes (mirror mksservo::Status). */
typedef enum {
    MKS_OK = 0,
    MKS_INVALID_ARGUMENT,
    MKS_SPEED_OUT_OF_RANGE,
    MKS_CURRENT_OUT_OF_RANGE,
    MKS_WORKING_CURRENT_EXCEEDED,
    MKS_CAN_ID_OUT_OF_RANGE,
    MKS_PAYLOAD_TOO_LONG,
    MKS_FRAME_TOO_SHORT,
    MKS_INVALID_DLC,
    MKS_CHECKSUM_MISMATCH,
    MKS_EMPTY_PAYLOAD_NOT_ALLOWED,
    MKS_UNKNOWN_COMMAND,
    MKS_INVALID_STATUS_PAYLOAD,
    MKS_NULL_POINTER
} MksStatus;

/* Generic CAN frame (transport-agnostic). */
typedef struct {
    uint16_t id;
    uint8_t  dlc;
    uint8_t  data[MKS_MAX_DLC];
} MksCanFrame;

/* Device/model configuration. */
typedef struct {
    uint16_t default_can_id;
    uint16_t max_working_current_ma; /* 0 = no limit enforced */
} MksDevice;

/* Parsed response (fixed-size). */
typedef struct {
    uint16_t can_id;
    uint8_t  code;
    uint8_t  payload[MKS_MAX_PAYLOAD];
    uint8_t  payload_len;
    uint8_t  checksum;
    uint8_t  status;      /* 0=Failed,1=Success, valid only if has_status */
    bool     has_status;
} MksParsedResponse;

/* Device config presets. */
MksDevice mks_device_servo42(uint16_t default_can_id);
MksDevice mks_device_servo57(uint16_t default_can_id);

/* ---- Encoder entry points (subset; see mksservo/encoder.hpp for full C++ API) ---- */
MksStatus mks_encode_set_motor_enable(const MksDevice* dev, bool enable, MksCanFrame* out, uint16_t can_id);
MksStatus mks_encode_emergency_stop(const MksDevice* dev, MksCanFrame* out, uint16_t can_id);
MksStatus mks_encode_speed_mode_run(const MksDevice* dev, bool dir_cw, uint16_t speed, uint8_t acc,
                                    bool has_runtime, uint32_t runtime_10ms, MksCanFrame* out, uint16_t can_id);
MksStatus mks_encode_relative_pulse_move(const MksDevice* dev, bool dir_cw, uint16_t speed, uint8_t acc,
                                         uint32_t relative_pulses, MksCanFrame* out, uint16_t can_id);
MksStatus mks_encode_absolute_pulse_move(const MksDevice* dev, uint16_t speed, uint8_t acc,
                                         int32_t absolute_pulses, MksCanFrame* out, uint16_t can_id);
MksStatus mks_encode_encoder_value(const MksDevice* dev, MksCanFrame* out, uint16_t can_id);
MksStatus mks_encode_realtime_speed(const MksDevice* dev, MksCanFrame* out, uint16_t can_id);
MksStatus mks_encode_working_current(const MksDevice* dev, uint16_t current_ma, bool save_to_flash,
                                     MksCanFrame* out, uint16_t can_id);
MksStatus mks_encode_set_zero_point(const MksDevice* dev, MksCanFrame* out, uint16_t can_id);
MksStatus mks_encode_execute_zero_return(const MksDevice* dev, bool has_mode, uint8_t mode,
                                         MksCanFrame* out, uint16_t can_id);

/* ---- Decoder ---- */
MksStatus mks_decode(const MksCanFrame* frame, MksParsedResponse* out);

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* MKS_API_H */
