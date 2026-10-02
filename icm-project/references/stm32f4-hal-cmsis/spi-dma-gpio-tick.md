# SPI slave DMA, DMA, GPIO and tick (STM32F4xx HAL driver V1.8.5)

Source files: `stm32f4xx_hal_spi.c/.h`, `stm32f4xx_hal_dma.c/.h`, `stm32f4xx_hal_gpio.c`, `stm32f4xx_hal.c`, `stm32f4xx_hal_def.h` at tag v1.8.5.

| Rule | Value | Citation |
|---|---|---|
| HAL_SPI_TransmitReceive_DMA entry: needs state READY (or master 2-line BUSY_RX); otherwise HAL_BUSY | return HAL_BUSY; | "HAL_SPI_TransmitReceive_DMA" |
| NULL buffer or zero Size returns HAL_ERROR | if ((pTxData == NULL) or (pRxData == NULL) or (Size == 0U)) { return HAL_ERROR; | "HAL_SPI_TransmitReceive_DMA" |
| Size is uint16_t | uint16_t Size) | "HAL_SPI_TransmitReceive_DMA" |
| State becomes busy TX/RX and ErrorCode is cleared | hspi->State = HAL_SPI_STATE_BUSY_TX_RX; ... hspi->ErrorCode   = HAL_SPI_ERROR_NONE; | "HAL_SPI_TransmitReceive_DMA" |
| Rx DMA completion callback is SPI_DMATransmitReceiveCplt; DMA error callback is SPI_DMAError; Tx DMA callbacks are set to NULL | hspi->hdmarx->XferCpltCallback     = SPI_DMATransmitReceiveCplt; ... hspi->hdmarx->XferErrorCallback = SPI_DMAError; | "HAL_SPI_TransmitReceive_DMA" |
| DMA start failure sets HAL_SPI_ERROR_DMA, unlocks, returns HAL_ERROR | SET_BIT(hspi->ErrorCode, HAL_SPI_ERROR_DMA); ... return HAL_ERROR; | "HAL_SPI_TransmitReceive_DMA" |
| SPI error interrupt (ERR) is enabled, then Tx DMA request is enabled last | __HAL_SPI_ENABLE_IT(hspi, (SPI_IT_ERR)); ... SET_BIT(hspi->Instance->CR2, SPI_CR2_TXDMAEN); | "HAL_SPI_TransmitReceive_DMA" |
| On Rx DMA complete in normal mode: ERR interrupt disabled, DMA requests disabled, state READY | Disable ERR interrupt ... hspi->State = HAL_SPI_STATE_READY; | "SPI_DMATransmitReceiveCplt" |
| If ErrorCode is not NONE at completion, HAL_SPI_ErrorCallback is called and TxRxCplt is not | if (hspi->ErrorCode != HAL_SPI_ERROR_NONE) { /* Call user error callback */ ... return; | "SPI_DMATransmitReceiveCplt" |
| Otherwise HAL_SPI_TxRxCpltCallback is called from DMA interrupt context | Call user TxRx complete callback | "SPI_DMATransmitReceiveCplt" |
| Completion waits for end of transaction with SPI_DEFAULT_TIMEOUT using HAL_GetTick; failure sets HAL_SPI_ERROR_FLAG | SPI_EndRxTxTransaction(hspi, SPI_DEFAULT_TIMEOUT, tickstart) != HAL_OK) ... SET_BIT(hspi->ErrorCode, HAL_SPI_ERROR_FLAG); | "SPI_DMATransmitReceiveCplt" |
| SPI_DEFAULT_TIMEOUT | #define SPI_DEFAULT_TIMEOUT 100U | "SPI_DEFAULT_TIMEOUT" |
| DMA error callback sets HAL_SPI_ERROR_DMA, state READY, calls HAL_SPI_ErrorCallback | SET_BIT(hspi->ErrorCode, HAL_SPI_ERROR_DMA); hspi->State = HAL_SPI_STATE_READY; | "SPI_DMAError" |
| SPI error interrupt: OVR, MODF, FRE set HAL_SPI_ERROR_OVR, HAL_SPI_ERROR_MODF, HAL_SPI_ERROR_FRE | SET_BIT(hspi->ErrorCode, HAL_SPI_ERROR_OVR); | "HAL_SPI_IRQHandler" |
| On SPI error with DMA enabled: interrupts disabled, state READY, DMA requests cleared, DMA aborted with HAL_DMA_Abort_IT, HAL_SPI_ErrorCallback called at end of abort | Disable all interrupts ... hspi->hdmarx->XferAbortCallback = SPI_DMAAbortOnError; | "HAL_SPI_IRQHandler" |
| HAL_SPI_Abort is blocking; on return the abort is considered complete | This procedure is executed in blocking mode : when exiting function, Abort is considered as completed. | "HAL_SPI_Abort" |
| HAL_SPI_Abort wait loop length | resetcount = SPI_DEFAULT_TIMEOUT * (SystemCoreClock / 24U / 1000U); | "HAL_SPI_Abort" |
| HAL_SPI_Abort on DMA Tx or Rx: HAL_DMA_Abort (no callback), error HAL_SPI_ERROR_ABORT, returns HAL_ERROR when ErrorCode equals HAL_SPI_ERROR_ABORT | if (HAL_DMA_Abort(hspi->hdmatx) != HAL_OK) { hspi->ErrorCode = HAL_SPI_ERROR_ABORT; | "HAL_SPI_Abort" |
| HAL_SPI_Abort clears ERRIE first and disables the SPI peripheral in the Rx DMA branch | Clear ERRIE interrupt to avoid error interrupts generation during Abort procedure | "HAL_SPI_Abort" |
| HAL_SPI_Abort on success resets ErrorCode and sets state READY | else { /* Reset errorCode */ hspi->ErrorCode = HAL_SPI_ERROR_NONE; | "HAL_SPI_Abort" |
| SPI error codes | HAL_SPI_ERROR_MODF (0x00000001U), HAL_SPI_ERROR_OVR (0x00000004U), HAL_SPI_ERROR_FRE (0x00000008U), HAL_SPI_ERROR_DMA (0x00000010U), HAL_SPI_ERROR_FLAG (0x00000020U), HAL_SPI_ERROR_ABORT (0x00000040U) | "HAL_SPI_ERROR_NONE" |
| SPI states | HAL_SPI_STATE_READY = 0x01U, HAL_SPI_STATE_BUSY_TX_RX = 0x05U, HAL_SPI_STATE_ABORT = 0x07U | "HAL_SPI_StateTypeDef" |
| HAL_SPI_Init in slave mode (non-TI) forces the baudrate prescaler | Baudrate prescaler not use in Motoraola Slave mode. force to default value | "HAL_SPI_Init" |
| HAL_DMA_Abort returns HAL_ERROR (HAL_DMA_ERROR_NO_XFER) if state is not HAL_DMA_STATE_BUSY | if(hdma->State != HAL_DMA_STATE_BUSY) ... hdma->ErrorCode = HAL_DMA_ERROR_NO_XFER; ... return HAL_ERROR; | "HAL_DMA_Abort" |
| HAL_DMA_Abort wait for the stream to be disabled uses this timeout | HAL_TIMEOUT_DMA_ABORT    5U  /* 5 ms */ | "HAL_TIMEOUT_DMA_ABORT" |
| HAL_DMA_Abort on timeout returns HAL_TIMEOUT with HAL_DMA_ERROR_TIMEOUT | hdma->ErrorCode = HAL_DMA_ERROR_TIMEOUT; ... return HAL_TIMEOUT; | "HAL_DMA_Abort" |
| HAL_DMA_IRQHandler handles transfer error, FIFO error and the other flags per stream and calls the stream's callbacks; application must call it from the DMA stream interrupt | void HAL_DMA_IRQHandler(DMA_HandleTypeDef *hdma) ... Transfer Error Interrupt management | "HAL_DMA_IRQHandler" |
| HAL_GPIO_WritePin writes BSRR; set uses the pin mask, reset uses the mask shifted by 16 | GPIOx->BSRR = GPIO_Pin; ... GPIOx->BSRR = (uint32_t)GPIO_Pin << 16U; | "HAL_GPIO_WritePin" |
| HAL_GPIO_WritePin note | This function uses GPIOx_BSRR register to allow atomic read/modify accesses. | "HAL_GPIO_WritePin" |
| HAL_GetTick returns uwTick; HAL_IncTick adds uwTickFreq | return uwTick; ... uwTick += uwTickFreq; | "HAL_GetTick" |
| HAL_InitTick, HAL_IncTick and HAL_GetTick are __weak | __weak void HAL_IncTick(void) | "HAL_IncTick" |
| Default tick frequency | HAL_TickFreqTypeDef uwTickFreq = HAL_TICK_FREQ_DEFAULT;  /* 1KHz */ | "uwTickFreq" |
