This STM32 is a Sensor hub the collects sensor data from its CAN and I2C connections and sends them over an SPI interface to a raspberry pi.

I needs to:

- Collect encoder values from six AS5600 encoders connected to the STM32 [I2C1] using an 9548A I2C Multiplexer.
- Have skeleton code ready for collecting data from the CAN bus, 
- Individually timestamps each recieved sensor message.These timestamps should ideally match the raspberry Pi time.
- Sent sensor messages over the SPI bus to a raspberry Pi using a DATA_READY pin to trigger an interrupt on the Raspberry Pi. 
- 