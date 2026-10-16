#ifndef STM32F4XX_HAL_H
#define STM32F4XX_HAL_H

#include <stdbool.h>
#include <stdint.h>

typedef enum {
    HAL_OK = 0,
    HAL_ERROR,
    HAL_BUSY,
    HAL_TIMEOUT
} HAL_StatusTypeDef;

typedef enum {
    GPIO_PIN_RESET = 0,
    GPIO_PIN_SET
} GPIO_PinState;

typedef struct {
    void *Instance;
    uint32_t Counter;
} TIM_HandleTypeDef;

typedef struct {
    void *Instance;
} I2C_HandleTypeDef;

typedef struct {
    void *Instance;
} CAN_HandleTypeDef;

typedef struct {
    void *Instance;
} SPI_HandleTypeDef;

typedef struct {
    uint32_t FilterBank;
    uint32_t FilterMode;
    uint32_t FilterScale;
    uint32_t FilterIdHigh;
    uint32_t FilterIdLow;
    uint32_t FilterMaskIdHigh;
    uint32_t FilterMaskIdLow;
    uint32_t FilterFIFOAssignment;
    uint32_t FilterActivation;
    uint32_t SlaveStartFilterBank;
} CAN_FilterTypeDef;

typedef struct {
    uint32_t StdId;
    uint32_t ExtId;
    uint32_t IDE;
    uint32_t RTR;
    uint32_t DLC;
    uint32_t Timestamp;
    uint32_t FilterMatchIndex;
} CAN_RxHeaderTypeDef;

typedef struct {
    uint32_t StdId;
    uint32_t ExtId;
    uint32_t IDE;
    uint32_t RTR;
    uint32_t DLC;
    uint32_t TransmitGlobalTime;
} CAN_TxHeaderTypeDef;

#define I2C1 ((void *)0x1)
#define SPI3 ((void *)0x5)
#define CAN_RX_FIFO0 0u
#define CAN_ID_STD 0u
#define CAN_RTR_DATA 0u
#define CAN_FILTERMODE_IDMASK 0u
#define CAN_FILTERSCALE_32BIT 0u
#define ENABLE 1u
#define DISABLE 0u
#define HAL_CAN_ERROR_BOF (1u << 0)

#define __HAL_TIM_GET_COUNTER(handle) ((handle)->Counter)

HAL_StatusTypeDef HAL_I2C_Master_Transmit(I2C_HandleTypeDef *hi2c,
                                          uint16_t address,
                                          uint8_t *data,
                                          uint16_t size,
                                          uint32_t timeout_ms);
HAL_StatusTypeDef HAL_I2C_Master_Receive(I2C_HandleTypeDef *hi2c,
                                         uint16_t address,
                                         uint8_t *data,
                                         uint16_t size,
                                         uint32_t timeout_ms);

HAL_StatusTypeDef HAL_TIM_Base_Start(TIM_HandleTypeDef *htim);

HAL_StatusTypeDef HAL_CAN_ConfigFilter(CAN_HandleTypeDef *hcan, CAN_FilterTypeDef *filter);
HAL_StatusTypeDef HAL_CAN_Start(CAN_HandleTypeDef *hcan);
HAL_StatusTypeDef HAL_CAN_Stop(CAN_HandleTypeDef *hcan);
uint32_t HAL_CAN_GetError(CAN_HandleTypeDef *hcan);
uint32_t HAL_CAN_GetRxFifoFillLevel(CAN_HandleTypeDef *hcan, uint32_t fifo);
HAL_StatusTypeDef HAL_CAN_GetRxMessage(CAN_HandleTypeDef *hcan,
                                       uint32_t fifo,
                                       CAN_RxHeaderTypeDef *header,
                                       uint8_t *data);
HAL_StatusTypeDef HAL_CAN_AddTxMessage(CAN_HandleTypeDef *hcan,
                                       CAN_TxHeaderTypeDef *header,
                                       uint8_t *data,
                                       uint32_t *mailbox);

HAL_StatusTypeDef HAL_SPI_TransmitReceive_DMA(SPI_HandleTypeDef *hspi,
                                              const uint8_t *tx_data,
                                              uint8_t *rx_data,
                                              uint16_t size);
HAL_StatusTypeDef HAL_SPI_Abort(SPI_HandleTypeDef *hspi);
void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *hspi);
void HAL_SPI_ErrorCallback(SPI_HandleTypeDef *hspi);

uint32_t HAL_GetTick(void);
void HAL_GPIO_WritePin(void *gpio_port, uint16_t gpio_pin, GPIO_PinState state);

#endif
