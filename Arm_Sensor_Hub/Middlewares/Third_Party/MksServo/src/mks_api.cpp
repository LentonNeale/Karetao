/* C API implementation — the only file that bridges C and C++.
 * Translates C PODs to C++ types and back. No C++ escapes past this boundary.
 */
#include "mks_api.h"

#include "mksservo/decoder.hpp"
#include "mksservo/encoder.hpp"

namespace {

mks::DeviceConfig to_cpp(const MksDevice* dev) {
    mks::DeviceConfig cfg{};
    if (dev != nullptr) {
        cfg.default_can_id = dev->default_can_id;
        cfg.max_working_current_ma = dev->max_working_current_ma;
    }
    return cfg;
}

void to_c(const mks::CanFrame& in, MksCanFrame* out) {
    out->id = in.id;
    out->dlc = in.dlc;
    for (uint8_t i = 0; i < MKS_MAX_DLC; ++i) {
        out->data[i] = in.data[i];
    }
}

MksStatus to_c_status(mks::Status s) {
    return static_cast<MksStatus>(static_cast<int>(s));
}

} // namespace

extern "C" {

MksDevice mks_device_servo42(uint16_t default_can_id) {
    MksDevice d; d.default_can_id = default_can_id; d.max_working_current_ma = 3000; return d;
}
MksDevice mks_device_servo57(uint16_t default_can_id) {
    MksDevice d; d.default_can_id = default_can_id; d.max_working_current_ma = 5200; return d;
}

MksStatus mks_encode_set_motor_enable(const MksDevice* dev, bool enable, MksCanFrame* out, uint16_t can_id) {
    if (out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    MksStatus st = to_c_status(mks::encode::set_motor_enable(to_cpp(dev), enable, f, can_id));
    if (st == MKS_OK) to_c(f, out);
    return st;
}

MksStatus mks_encode_emergency_stop(const MksDevice* dev, MksCanFrame* out, uint16_t can_id) {
    if (out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    MksStatus st = to_c_status(mks::encode::emergency_stop(to_cpp(dev), f, can_id));
    if (st == MKS_OK) to_c(f, out);
    return st;
}

MksStatus mks_encode_speed_mode_run(const MksDevice* dev, bool dir_cw, uint16_t speed, uint8_t acc,
                                    bool has_runtime, uint32_t runtime_10ms, MksCanFrame* out, uint16_t can_id) {
    if (out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    MksStatus st = to_c_status(mks::encode::speed_mode_run(to_cpp(dev), dir_cw, speed, acc, has_runtime, runtime_10ms, f, can_id));
    if (st == MKS_OK) to_c(f, out);
    return st;
}

MksStatus mks_encode_relative_pulse_move(const MksDevice* dev, bool dir_cw, uint16_t speed, uint8_t acc,
                                         uint32_t relative_pulses, MksCanFrame* out, uint16_t can_id) {
    if (out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    MksStatus st = to_c_status(mks::encode::relative_pulse_move(to_cpp(dev), dir_cw, speed, acc, relative_pulses, f, can_id));
    if (st == MKS_OK) to_c(f, out);
    return st;
}

MksStatus mks_encode_absolute_pulse_move(const MksDevice* dev, uint16_t speed, uint8_t acc,
                                         int32_t absolute_pulses, MksCanFrame* out, uint16_t can_id) {
    if (out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    MksStatus st = to_c_status(mks::encode::absolute_pulse_move(to_cpp(dev), speed, acc, absolute_pulses, f, can_id));
    if (st == MKS_OK) to_c(f, out);
    return st;
}

MksStatus mks_encode_encoder_value(const MksDevice* dev, MksCanFrame* out, uint16_t can_id) {
    if (out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    MksStatus st = to_c_status(mks::encode::encoder_value(to_cpp(dev), f, can_id));
    if (st == MKS_OK) to_c(f, out);
    return st;
}

MksStatus mks_encode_realtime_speed(const MksDevice* dev, MksCanFrame* out, uint16_t can_id) {
    if (out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    MksStatus st = to_c_status(mks::encode::realtime_speed(to_cpp(dev), f, can_id));
    if (st == MKS_OK) to_c(f, out);
    return st;
}

MksStatus mks_encode_working_current(const MksDevice* dev, uint16_t current_ma, bool save_to_flash,
                                     MksCanFrame* out, uint16_t can_id) {
    if (out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    MksStatus st = to_c_status(mks::encode::working_current(to_cpp(dev), current_ma, save_to_flash, f, can_id));
    if (st == MKS_OK) to_c(f, out);
    return st;
}

MksStatus mks_encode_set_zero_point(const MksDevice* dev, MksCanFrame* out, uint16_t can_id) {
    if (out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    MksStatus st = to_c_status(mks::encode::set_zero_point(to_cpp(dev), f, can_id));
    if (st == MKS_OK) to_c(f, out);
    return st;
}

MksStatus mks_encode_execute_zero_return(const MksDevice* dev, bool has_mode, uint8_t mode,
                                         MksCanFrame* out, uint16_t can_id) {
    if (out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    MksStatus st = to_c_status(mks::encode::execute_zero_return(to_cpp(dev), has_mode, static_cast<mks::GoZeroMode>(mode), f, can_id));
    if (st == MKS_OK) to_c(f, out);
    return st;
}

MksStatus mks_decode(const MksCanFrame* frame, MksParsedResponse* out) {
    if (frame == nullptr || out == nullptr) return MKS_NULL_POINTER;
    mks::CanFrame f{};
    f.id = frame->id;
    f.dlc = frame->dlc;
    for (uint8_t i = 0; i < MKS_MAX_DLC; ++i) {
        f.data[i] = frame->data[i];
    }
    mks::decode::DecodedResponse d{};
    MksStatus st = to_c_status(mks::decode::decode(f, d));
    if (st != MKS_OK) return st;
    out->can_id = d.parsed.can_id;
    out->code = d.parsed.code;
    out->payload_len = d.parsed.payload_len;
    for (uint8_t i = 0; i < MKS_MAX_PAYLOAD; ++i) {
        out->payload[i] = d.parsed.payload[i];
    }
    out->checksum = d.parsed.checksum;
    out->status = static_cast<uint8_t>(d.status);
    out->has_status = d.has_status;
    return MKS_OK;
}

} /* extern "C" */
