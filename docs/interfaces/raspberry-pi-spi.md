# Raspberry Pi SPI Scaffold

This document is the canonical Raspberry Pi-side companion to the ARM-owned SPI contracts.

## Scope

The Raspberry Pi code under `RaspberryPi_Sensor_Hub/src/spi/` is currently a minimal scaffold for:

- SPI bus lifecycle (`spi_bus.py`)
- Frame encode/decode and CRC validation (`spi_protocol.py`)
- High-level request/response access (`spi_device.py`)

It intentionally avoids selecting a production backend (`spidev`, `periphery`, GPIO library, DMA strategy, or systemd integration) until those choices are frozen for the target hardware image.

## Contract Alignment

Use these root docs as the source of truth:

- Transport and framing: [docs/protocols/spi-contract.md](../protocols/spi-contract.md)
- Payload layouts: [docs/protocols/spi-payload-schema.md](../protocols/spi-payload-schema.md)
- STM32 SPI service behavior: [docs/interfaces/spi-service-contract.md](spi-service-contract.md)
- ARM hardware baseline: [docs/hardware/arm-sensor-hub-baseline.md](../hardware/arm-sensor-hub-baseline.md)

## Current Usage

```python
from spi import MessageType, SpiBus, SpiBusConfig, SpiDevice, SpiFrame

bus = SpiBus(SpiBusConfig(), backend=fake_backend)
bus.open()

device = SpiDevice(bus)
request = SpiFrame(message_type=MessageType.GET_STATUS, seq=1)
response = device.transact(request)
```

For unit tests and early integration, inject a fake backend into `SpiBus` rather than assuming Linux SPI devices or GPIO mappings. The scaffold intentionally raises `NotImplementedError` if a transfer is attempted without a backend.

## TODOs Before Production Bring-Up

- Confirm the final Linux SPI backend and bus/device path once Raspberry Pi OS packaging is chosen.
- Confirm `DATA_READY` GPIO polarity, debounce expectations, and user-space access strategy against target hardware.
- Confirm the maximum accepted SPI clock after the ARM-side 5 MHz integration gate is closed.
- Confirm final request/response retry policy for stalled or partial transactions.
- Confirm whether the Raspberry Pi should treat every transfer as fixed 512-byte frames or allow a future transport wrapper.
