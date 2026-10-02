# I2C master (STM32F4xx HAL driver V1.8.5)

Source files: `stm32f4xx_hal_i2c.c`, `stm32f4xx_hal_i2c.h`, `stm32f4xx_hal_def.h` at tag v1.8.5.

| Rule | Value | Citation |
|---|---|---|
| Internal timeouts: BUSY flag wait | #define I2C_TIMEOUT_BUSY_FLAG     25U         /*!< Timeout 25 ms | "I2C_TIMEOUT_BUSY_FLAG" |
| Internal timeouts: generic flag wait | #define I2C_TIMEOUT_FLAG          35U         /*!< Timeout 35 ms | "I2C_TIMEOUT_FLAG" |
| Internal timeouts: STOP flag wait | #define I2C_TIMEOUT_STOP_FLAG     5U          /*!< Timeout 5 ms | "I2C_TIMEOUT_STOP_FLAG" |
| DevAddress is the 7-bit address shifted left before the call | the device 7 bits address value in datasheet must be shifted to the left before calling the interface | "HAL_I2C_Master_Transmit" |
| Blocking Transmit: if state is not HAL_I2C_STATE_READY it returns HAL_BUSY | if (hi2c->State == HAL_I2C_STATE_READY) ... else { return HAL_BUSY; } | "HAL_I2C_Master_Transmit" |
| Blocking Transmit: BUSY flag still set after I2C_TIMEOUT_BUSY_FLAG returns HAL_BUSY | I2C_WaitOnFlagUntilTimeout(hi2c, I2C_FLAG_BUSY, SET, I2C_TIMEOUT_BUSY_FLAG, tickstart) != HAL_OK) { return HAL_BUSY; | "HAL_I2C_Master_Transmit" |
| Blocking Transmit: ErrorCode is cleared at start of the transfer | hi2c->ErrorCode   = HAL_I2C_ERROR_NONE; | "HAL_I2C_Master_Transmit" |
| Blocking Transmit: on a TXE or BTF wait failure with HAL_I2C_ERROR_AF a STOP is generated, then HAL_ERROR is returned | if (hi2c->ErrorCode == HAL_I2C_ERROR_AF) { /* Generate Stop */ SET_BIT(hi2c->Instance->CR1, I2C_CR1_STOP); } return HAL_ERROR; | "HAL_I2C_Master_Transmit" |
| Blocking Transmit: on success STOP is generated and state returns to READY | Generate Stop ... hi2c->State = HAL_I2C_STATE_READY; hi2c->Mode = HAL_I2C_MODE_NONE; | "HAL_I2C_Master_Transmit" |
| Blocking flag wait: on timeout the handle goes to READY, ErrorCode gets HAL_I2C_ERROR_TIMEOUT, lock is released, return is HAL_ERROR (not HAL_TIMEOUT) | hi2c->ErrorCode = HAL_I2C_ERROR_TIMEOUT; ... __HAL_UNLOCK(hi2c); return HAL_ERROR; | "I2C_WaitOnFlagUntilTimeout" |
| Blocking flag wait is skipped when Timeout is HAL_MAX_DELAY | Check for the Timeout ... if (Timeout != HAL_MAX_DELAY) | "I2C_WaitOnFlagUntilTimeout" |
| HAL_MAX_DELAY value | #define HAL_MAX_DELAY      0xFFFFFFFFU | "HAL_MAX_DELAY" |
| Blocking timeout is measured with HAL_GetTick | ((HAL_GetTick() - Tickstart) > Timeout) | "I2C_WaitOnFlagUntilTimeout" |
| Blocking Receive: state not READY returns HAL_BUSY; BUSY flag wait uses I2C_TIMEOUT_BUSY_FLAG | HAL_I2C_Master_Receive ... I2C_WaitOnFlagUntilTimeout(hi2c, I2C_FLAG_BUSY, SET, I2C_TIMEOUT_BUSY_FLAG, tickstart) != HAL_OK) { return HAL_BUSY; | "HAL_I2C_Master_Receive" |
| Interrupt Transmit: busy-wait count on the BUSY flag, then HAL_BUSY with HAL_I2C_ERROR_TIMEOUT | count = I2C_TIMEOUT_BUSY_FLAG * (SystemCoreClock / 25U / 1000U); ... return HAL_BUSY; | "HAL_I2C_Master_Transmit_IT" |
| Interrupt Transmit: state set to HAL_I2C_STATE_BUSY_TX, Mode HAL_I2C_MODE_MASTER, ErrorCode cleared, XferOptions I2C_NO_OPTION_FRAME | hi2c->State     = HAL_I2C_STATE_BUSY_TX; hi2c->Mode      = HAL_I2C_MODE_MASTER; hi2c->ErrorCode = HAL_I2C_ERROR_NONE; | "HAL_I2C_Master_Transmit_IT" |
| Interrupt Transmit: enables EVT, BUF and ERR interrupts, then generates START, returns HAL_OK immediately | __HAL_I2C_ENABLE_IT(hi2c, I2C_IT_EVT, I2C_IT_BUF, I2C_IT_ERR (the three ORed)); ... SET_BIT(hi2c->Instance->CR1, I2C_CR1_START); return HAL_OK; | "HAL_I2C_Master_Transmit_IT" |
| Interrupt Transmit: state not READY returns HAL_BUSY | if (hi2c->State == HAL_I2C_STATE_READY) ... else { return HAL_BUSY; } | "HAL_I2C_Master_Transmit_IT" |
| Interrupt Receive: same entry checks, state not READY returns HAL_BUSY | HAL_I2C_Master_Receive_IT ... if (hi2c->State == HAL_I2C_STATE_READY) | "HAL_I2C_Master_Receive_IT" |
| Completion callbacks are weak functions the application overrides | __weak void HAL_I2C_MasterTxCpltCallback(I2C_HandleTypeDef *hi2c) | "HAL_I2C_MasterTxCpltCallback" |
| Completion callbacks are weak functions the application overrides (receive) | __weak void HAL_I2C_MasterRxCpltCallback(I2C_HandleTypeDef *hi2c) | "HAL_I2C_MasterRxCpltCallback" |
| Error interrupt handler recognises BERR, ARLO, AF and OVR, clears each flag, ORs the code into ErrorCode, then calls I2C_ITError | error gets HAL_I2C_ERROR_BERR (with OR); ... hi2c->ErrorCode gets error (with OR); I2C_ITError(hi2c); | "HAL_I2C_ER_IRQHandler" |
| On AF in master mode the error handler generates STOP | if ((CurrentMode == HAL_I2C_MODE_MASTER) or  (CurrentMode == HAL_I2C_MODE_MEM)) { /* Generate Stop */ | "HAL_I2C_ER_IRQHandler" |
| I2C_ITError (non-DMA, non-abort path) sets state READY and Mode NONE before the error callback | hi2c->State = HAL_I2C_STATE_READY; hi2c->Mode = HAL_I2C_MODE_NONE; | "I2C_ITError" |
| I2C_ITError calls HAL_I2C_AbortCpltCallback when state is HAL_I2C_STATE_ABORT, and then clears ErrorCode | else if (hi2c->State == HAL_I2C_STATE_ABORT) ... hi2c->ErrorCode = HAL_I2C_ERROR_NONE; ... HAL_I2C_AbortCpltCallback(hi2c); | "I2C_ITError" |
| HAL_I2C_GetError returns the handle's ErrorCode | uint32_t HAL_I2C_GetError(I2C_HandleTypeDef *hi2c) ... return hi2c->ErrorCode; | "HAL_I2C_GetError" |
| Error codes: BERR | #define HAL_I2C_ERROR_BERR              0x00000001U    /*!< BERR error | "HAL_I2C_ERROR_BERR" |
| Error codes: ARLO | #define HAL_I2C_ERROR_ARLO              0x00000002U    /*!< ARLO error | "HAL_I2C_ERROR_ARLO" |
| Error codes: AF | #define HAL_I2C_ERROR_AF                0x00000004U    /*!< AF error | "HAL_I2C_ERROR_AF" |
| Error codes: OVR | #define HAL_I2C_ERROR_OVR               0x00000008U    /*!< OVR error | "HAL_I2C_ERROR_OVR" |
| Error codes: TIMEOUT | #define HAL_I2C_ERROR_TIMEOUT           0x00000020U    /*!< Timeout Error | "HAL_I2C_ERROR_TIMEOUT" |
| States: READY and BUSY_TX and BUSY_RX | HAL_I2C_STATE_READY             = 0x20U, HAL_I2C_STATE_BUSY_TX           = 0x21U, HAL_I2C_STATE_BUSY_RX           = 0x22U | "HAL_I2C_StateTypeDef" |
