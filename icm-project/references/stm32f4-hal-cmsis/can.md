# CAN (STM32F4xx HAL driver V1.8.5)

Source files: `stm32f4xx_hal_can.c`, `stm32f4xx_hal_can.h`, `stm32f4xx_hal_def.h` at tag v1.8.5.

| Rule | Value | Citation |
|---|---|---|
| HAL status codes | HAL_OK       = 0x00U, HAL_ERROR    = 0x01U, HAL_BUSY     = 0x02U, HAL_TIMEOUT  = 0x03U | "HAL_StatusTypeDef" |
| Timeout used inside HAL_CAN_Init, HAL_CAN_Start, HAL_CAN_Stop | #define CAN_TIMEOUT_VALUE 10U | "CAN_TIMEOUT_VALUE" |
| HAL_CAN_Start runs only in state READY; otherwise it sets HAL_CAN_ERROR_NOT_READY and returns HAL_ERROR | if (hcan->State == HAL_CAN_STATE_READY) ... ErrorCode set to HAL_CAN_ERROR_NOT_READY; return HAL_ERROR; | "HAL_CAN_Start" |
| HAL_CAN_Start clears INRQ and waits for INAK to clear; on timeout it sets HAL_CAN_ERROR_TIMEOUT, state HAL_CAN_STATE_ERROR and returns HAL_ERROR | Check for the Timeout ... Update error code ... HAL_CAN_ERROR_TIMEOUT; hcan->State = HAL_CAN_STATE_ERROR; return HAL_ERROR; | "HAL_CAN_Start" |
| HAL_CAN_Start on success resets the error code (so a previous HAL_CAN_ERROR_BOF is cleared) | Reset the CAN ErrorCode ... hcan->ErrorCode = HAL_CAN_ERROR_NONE; | "HAL_CAN_Start" |
| HAL_CAN_Stop runs only in state LISTENING; otherwise HAL_CAN_ERROR_NOT_STARTED and HAL_ERROR | if (hcan->State == HAL_CAN_STATE_LISTENING) ... ErrorCode set to HAL_CAN_ERROR_NOT_STARTED; | "HAL_CAN_Stop" |
| HAL_CAN_Stop requests initialisation (INRQ), waits for INAK, leaves sleep, sets state READY | Request initialisation ... Exit from sleep mode ... hcan->State = HAL_CAN_STATE_READY; | "HAL_CAN_Stop" |
| HAL_CAN_ConfigFilter works only in state READY or LISTENING; otherwise HAL_CAN_ERROR_NOT_INITIALIZED, HAL_ERROR | if (state == HAL_CAN_STATE_READY ... state == HAL_CAN_STATE_LISTENING) ... ErrorCode set to HAL_CAN_ERROR_NOT_INITIALIZED; | "HAL_CAN_ConfigFilter" |
| Filter bank handling with CAN2 defined: CAN2SB is written from SlaveStartFilterBank | SET_BIT(can_ip->FMR, sFilterConfig->SlaveStartFilterBank << CAN_FMR_CAN2SB_Pos); | "HAL_CAN_ConfigFilter" |
| Filter ID mask mode clears FM1R bit; FIFO0 assignment clears FFA1R bit; activation sets FA1R only when CAN_FILTER_ENABLE | if (sFilterConfig->FilterMode == CAN_FILTERMODE_IDMASK) ... CLEAR_BIT(can_ip->FM1R, filternbrbitpos); | "HAL_CAN_ConfigFilter" |
| HAL_CAN_AddTxMessage works only in state READY or LISTENING; otherwise HAL_CAN_ERROR_NOT_INITIALIZED, HAL_ERROR | if (state == HAL_CAN_STATE_READY ... state == HAL_CAN_STATE_LISTENING) ... ErrorCode set to HAL_CAN_ERROR_NOT_INITIALIZED; | "HAL_CAN_AddTxMessage" |
| HAL_CAN_AddTxMessage with all three mailboxes full: HAL_CAN_ERROR_PARAM and HAL_ERROR (no HAL_BUSY) | Check that all the Tx mailboxes are not full ... ErrorCode set to HAL_CAN_ERROR_PARAM; return HAL_ERROR; | "HAL_CAN_AddTxMessage" |
| HAL_CAN_AddTxMessage reads 8 data bytes whatever DLC is | aData[7] << CAN_TDH0R_DATA7_Pos ... aData[0] << CAN_TDL0R_DATA0_Pos | "HAL_CAN_AddTxMessage" |
| HAL_CAN_AddTxMessage sets the mailbox bit in the returned value | *pTxMailbox = (uint32_t)1 << transmitmailbox; | "HAL_CAN_AddTxMessage" |
| HAL_CAN_GetRxMessage with empty FIFO: HAL_CAN_ERROR_PARAM and HAL_ERROR | Check that the Rx FIFO 0 is not empty ... ErrorCode set to HAL_CAN_ERROR_PARAM; return HAL_ERROR; | "HAL_CAN_GetRxMessage" |
| HAL_CAN_GetRxMessage truncates a received DLC above range | Truncate DLC to 8 if received field is over range | "HAL_CAN_GetRxMessage" |
| HAL_CAN_GetRxFifoFillLevel returns 0 outside states READY and LISTENING | uint32_t filllevel = 0U; ... filllevel = hcan->Instance->RF0R & CAN_RF0R_FMP0; | "HAL_CAN_GetRxFifoFillLevel" |
| HAL_CAN_GetError returns the handle's ErrorCode; it does not read hardware | Return CAN error code ... return hcan->ErrorCode; | "HAL_CAN_GetError" |
| Error code HAL_CAN_ERROR_BOF value | #define HAL_CAN_ERROR_BOF             (0x00000004U)  /*!< Bus-off error | "HAL_CAN_ERROR_BOF" |
| Error code HAL_CAN_ERROR_TIMEOUT value | #define HAL_CAN_ERROR_TIMEOUT         (0x00020000U)  /*!< Timeout error | "HAL_CAN_ERROR_TIMEOUT" |
| Error code HAL_CAN_ERROR_NOT_INITIALIZED value | #define HAL_CAN_ERROR_NOT_INITIALIZED (0x00040000U)  /*!< Peripheral not initialized | "HAL_CAN_ERROR_NOT_INITIALIZED" |
| Error code HAL_CAN_ERROR_NOT_READY value | #define HAL_CAN_ERROR_NOT_READY       (0x00080000U)  /*!< Peripheral not ready | "HAL_CAN_ERROR_NOT_READY" |
| Error code HAL_CAN_ERROR_NOT_STARTED value | #define HAL_CAN_ERROR_NOT_STARTED     (0x00100000U)  /*!< Peripheral not started | "HAL_CAN_ERROR_NOT_STARTED" |
| Error code HAL_CAN_ERROR_PARAM value | #define HAL_CAN_ERROR_PARAM           (0x00200000U)  /*!< Parameter error | "HAL_CAN_ERROR_PARAM" |
| Bus-off flag in ErrorCode is set in HAL_CAN_IRQHandler only, and only when CAN_IT_ERROR and CAN_IT_BUSOFF are enabled in IER | if (((interrupts & CAN_IT_BUSOFF) != 0U) && ((esrflags & CAN_ESR_BOFF) != 0U)) ... errorcode set with HAL_CAN_ERROR_BOF; | "HAL_CAN_IRQHandler" |
| Interrupts are enabled by HAL_CAN_ActivateNotification (states READY or LISTENING) | __HAL_CAN_ENABLE_IT(hcan, ActiveITs); | "HAL_CAN_ActivateNotification" |
| Driver guide: with interrupts, the application calls HAL_CAN_IRQHandler from the CAN IRQ handler | In CAN IRQ handler, call HAL_CAN_IRQHandler() | "How to use this driver" |
| CAN states | HAL_CAN_STATE_READY = 0x01U, HAL_CAN_STATE_LISTENING = 0x02U, HAL_CAN_STATE_ERROR = 0x05U | "HAL_CAN_StateTypeDef" |
