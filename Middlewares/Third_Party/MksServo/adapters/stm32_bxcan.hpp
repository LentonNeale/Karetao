// Example adapter: MksServo CanFrame -> STM32 HAL bxCAN transmission.
//
// This is an INTEGRATION EXAMPLE ONLY. It is not compiled into the mksservo
// library and intentionally lives outside the protocol layer. The CAN Service
// in your application owns actual TX/RX, queues, retries, timeouts, and bus-off
// recovery — this header just shows the mechanical frame mapping.
//
// Usage (from a .cpp file in your CAN Service, after HAL CAN is configured):
//     extern CAN_HandleTypeDef hcan1;
//     mks::CanFrame f{};
//     if (mks::encode::set_motor_enable(kServo42, true, f) == mks::Status::Ok) {
//         mks_bxcan::transmit(hcan1, f);
//     }
#pragma once

#include "mksservo/can_frame.hpp"

// CubeMX/HAL header. Adjust the include path/family header to your project.
#include "stm32f4xx_hal.h"

namespace mks_bxcan {

/// Transmit one frame via HAL bxCAN (blocking-free; uses a TX mailbox).
/// Returns HAL status. Caller is responsible for mailbox-full handling/queues.
inline HAL_StatusTypeDef transmit(CAN_HandleTypeDef& hcan, const mks::CanFrame& frame,
                                  uint32_t tx_mailbox /* out via reference */ = 0) {
    CAN_TxHeaderTypeDef header{};
    header.StdId = frame.id & 0x7FFu;   // 11-bit standard identifier
    header.ExtId = 0;
    header.IDE = CAN_ID_STD;
    header.RTR = CAN_RTR_DATA;
    header.DLC = frame.dlc & 0x0Fu;
    header.TransmitGlobalTime = DISABLE;

    return HAL_CAN_AddTxMessage(&hcan, &header,
                                const_cast<uint8_t*>(frame.data), &tx_mailbox);
}

} // namespace mks_bxcan
