# SPI System Interface

## Authority

This document defines the Karetao system-level SPI contract. Component repositories own SPI driver/service implementation details.

## System contract

- Fixed transaction frame: **512 bytes**.
- Maximum payload: **490 bytes**.
- SPI mode: **Mode 0**.
- Multi-byte fields: **little-endian**.
- Integrity: **CRC-32/ISO-HDLC**.
- Request/response ownership is deterministic (SD-15).
- Correlated GET_SNAPSHOT response takes priority; active DMA buffers remain immutable; replacement frames use replace-if-new semantics (SD-16).
- Pi is SPI clock master.
- DATA_READY is the preferred low-latency notification mechanism when physically assigned; polling is retained for recovery, initially at **1 ms** (SD-17).
- The 5 MHz operating point remains an empirical integration limit until live Pi/STM32 and physical-layer evidence is accepted (SD-01, SD-15).

## Boundary

The system contract defines externally visible framing, ownership, timing and data semantics. Concrete STM32 DMA/buffer ownership and Raspberry-side driver implementation remain component authority.
