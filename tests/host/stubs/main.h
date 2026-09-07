#ifndef MAIN_H
#define MAIN_H

#include "stm32f4xx_hal.h"

extern I2C_HandleTypeDef hi2c1;
extern CAN_HandleTypeDef hcan1;
extern TIM_HandleTypeDef htim2;
extern void *Data_Ready_GPIO_Port;
extern uint16_t Data_Ready_Pin;

#endif
