# Vendored version and firmware call sites (STM32CubeF4 V1.28.3)

Rows cite project lines (`path:start-end`, relative to the Karetao repo root). Version identity (V1.8.5, V2.6.11, V1.28.3) is in `CONTEXT.md`, because `verify_citations` cannot match three-part version numbers.

| Rule | Value | Citation |
|---|---|---|
| Vendored HAL driver version macros | __STM32F4xx_HAL_VERSION_MAIN   (0x01U) ... __STM32F4xx_HAL_VERSION_SUB1   (0x08U) ... __STM32F4xx_HAL_VERSION_SUB2   (0x05U) | Arm_Sensor_Hub/Drivers/STM32F4xx_HAL_Driver/Src/stm32f4xx_hal.c:55-58 |
| Vendored CMSIS device version macros | __STM32F4xx_CMSIS_VERSION_MAIN   (0x02U) ... __STM32F4xx_CMSIS_VERSION_SUB1   (0x06U) ... __STM32F4xx_CMSIS_VERSION_SUB2   (0x0BU) | Arm_Sensor_Hub/Drivers/CMSIS/Device/ST/STM32F4xx/Include/stm32f4xx.h:110-113 |
| HAL CAN module enabled | #define HAL_CAN_MODULE_ENABLED | Arm_Sensor_Hub/Core/Inc/stm32f4xx_hal_conf.h:42-42 |
| HAL I2C module enabled | #define HAL_I2C_MODULE_ENABLED | Arm_Sensor_Hub/Core/Inc/stm32f4xx_hal_conf.h:56-56 |
| HAL SPI module enabled | #define HAL_SPI_MODULE_ENABLED | Arm_Sensor_Hub/Core/Inc/stm32f4xx_hal_conf.h:65-65 |
| HAL DMA module enabled | #define HAL_DMA_MODULE_ENABLED | Arm_Sensor_Hub/Core/Inc/stm32f4xx_hal_conf.h:86-86 |
| CAN register callbacks disabled (weak callbacks are used) | #define  USE_HAL_CAN_REGISTER_CALLBACKS         0U | Arm_Sensor_Hub/Core/Inc/stm32f4xx_hal_conf.h:158-158 |
| Tick interrupt priority | #define  TICK_INT_PRIORITY            15U   /*!< tick interrupt priority */ | Arm_Sensor_Hub/Core/Inc/stm32f4xx_hal_conf.h:151-151 |
| CAN1 init: normal mode, prescaler 16, BS1 11 TQ, BS2 2 TQ, SJW 1 TQ, AutoBusOff DISABLE, AutoRetransmission DISABLE | hcan1.Init.Prescaler = 16; hcan1.Init.Mode = CAN_MODE_NORMAL; hcan1.Init.TimeSeg1 = CAN_BS1_11TQ; hcan1.Init.TimeSeg2 = CAN_BS2_2TQ; hcan1.Init.AutoBusOff = DISABLE; hcan1.Init.AutoRetransmission = DISABLE; | Arm_Sensor_Hub/Core/Src/main.c:241-249 |
| CAN bus-off check reads HAL_CAN_GetError for HAL_CAN_ERROR_BOF, then HAL_CAN_Stop, later HAL_CAN_Start | if ((HAL_CAN_GetError(&hcan1) & HAL_CAN_ERROR_BOF) != 0u) { ... (void)HAL_CAN_Stop(&hcan1); ... bool recovered = HAL_CAN_Start(&hcan1) == HAL_OK; | Arm_Sensor_Hub/App/Src/can_service.c:50-62 |
| CAN accept-all filter: bank 0, ID-mask, 32-bit, FIFO0, SlaveStartFilterBank 14 | filter.FilterBank = 0; filter.FilterMode = CAN_FILTERMODE_IDMASK; filter.FilterScale = CAN_FILTERSCALE_32BIT; filter.FilterFIFOAssignment = CAN_RX_FIFO0; filter.SlaveStartFilterBank = 14; | Arm_Sensor_Hub/App/Src/can_service.c:124-133 |
| CAN transmit: standard ID, data frame, any HAL status other than HAL_OK is mapped to one error | header.IDE = CAN_ID_STD; header.RTR = CAN_RTR_DATA; hal_status = HAL_CAN_AddTxMessage(&hcan1, &header, tx_data, &tx_mailbox); | Arm_Sensor_Hub/App/Src/can_service.c:299-306 |
| CAN receive: drain RX FIFO0 by fill level, HAL_CAN_GetRxMessage | while (HAL_CAN_GetRxFifoFillLevel(&hcan1, CAN_RX_FIFO0) > 0U) { | Arm_Sensor_Hub/App/Src/can_service.c:159-166 |
| I2C1 init: clock speed and duty cycle | hi2c1.Init.ClockSpeed = 400000; hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2; | Arm_Sensor_Hub/Core/Src/main.c:278-279 |
| I2C blocking write passes the address shifted left by one and a caller timeout | HAL_I2C_Master_Transmit(&hi2c1, (uint16_t)(address_7bit << 1u), (uint8_t *)data, size, timeout_ms); | Arm_Sensor_Hub/App/Src/i2c_manager.c:83-83 |
| I2C interrupt write uses HAL_I2C_Master_Transmit_IT | hal_status = HAL_I2C_Master_Transmit_IT(&hi2c1, | Arm_Sensor_Hub/App/Src/i2c_manager.c:450-450 |
| I2C error callback stores HAL_I2C_GetError | s_pending_fault_code = HAL_I2C_GetError(hi2c); | Arm_Sensor_Hub/App/Src/i2c_manager.c:553-553 |
| I2C interrupt priorities (EV and ER) | HAL_NVIC_SetPriority(I2C1_EV_IRQn, 5, 0); ... HAL_NVIC_SetPriority(I2C1_ER_IRQn, 5, 0); | Arm_Sensor_Hub/Core/Src/stm32f4xx_hal_msp.c:181-184 |
| SPI3 init: slave, hardware NSS input, CRC disabled | hspi3.Init.Mode = SPI_MODE_SLAVE; hspi3.Init.NSS = SPI_NSS_HARD_INPUT; hspi3.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE; | Arm_Sensor_Hub/Core/Src/main.c:313-321 |
| SPI3 DMA arm and abort calls | HAL_SPI_TransmitReceive_DMA(&hspi3, tx_frame, s_rx_frame, SPI_FRAME_MAX_BYTES) != HAL_OK | Arm_Sensor_Hub/App/Src/spi_slave_service.c:110-110 |
| SPI3 callbacks overridden: TxRxCplt and Error | void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *hspi) ... void HAL_SPI_ErrorCallback(SPI_HandleTypeDef *hspi) | Arm_Sensor_Hub/App/Src/spi_slave_service.c:396-406 |
| DMA interrupt priorities, stream 0 and stream 5 | HAL_NVIC_SetPriority(DMA1_Stream0_IRQn, 5, 0); ... HAL_NVIC_SetPriority(DMA1_Stream5_IRQn, 6, 0); | Arm_Sensor_Hub/Core/Src/main.c:389-393 |
| SPI3 interrupt priority | HAL_NVIC_SetPriority(SPI3_IRQn, 5, 0); | Arm_Sensor_Hub/Core/Src/stm32f4xx_hal_msp.c:300-300 |
| Data-ready GPIO write | HAL_GPIO_WritePin(Data_Ready_GPIO_Port, Data_Ready_Pin, high ? GPIO_PIN_SET : GPIO_PIN_RESET); | Arm_Sensor_Hub/App/Src/spi_slave_service.c:45-45 |
| HAL tick comes from TIM6, incremented in the period-elapsed callback | if (htim->Instance == TIM6) { HAL_IncTick(); | Arm_Sensor_Hub/Core/Src/main.c:472-474 |
