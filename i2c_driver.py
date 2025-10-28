# i2c_driver.py
from smbus2 import SMBus, i2c_msg
import numpy as np
import time

# I2C constants for Panasonic GridEYE (AMG8833)
I2C_BUS = 1             # Default I2C bus number on Raspberry Pi
GRIDEYE_ADDR = 0x69     # Detected address (from i2cdetect)
TEMP_START_REG = 0x80   # Start register for temperature data
PIXEL_COUNT = 64        # 8x8 sensor = 64 pixels

class GridEYEI2CDriver:
    """Handles raw I2C communication with the GridEYE sensor."""
    
    def __init__(self):
        try:
            self.bus = SMBus(I2C_BUS)
            print(f"I2C bus {I2C_BUS} opened successfully (smbus2).")
        except FileNotFoundError:
            print("ERROR: Could not open I2C bus. Is I2C enabled on Raspberry Pi?")
            self.bus = None

    def read_raw_frame(self):
        """Reads 64 pixel values (128 bytes) from the GridEYE using smbus2."""
        if not self.bus:
            return self._simulate_frame()

        try:
            # Create write message (register pointer) and read message (128 bytes)
            write = i2c_msg.write(GRIDEYE_ADDR, [TEMP_START_REG])
            read = i2c_msg.read(GRIDEYE_ADDR, PIXEL_COUNT * 2)
            
            # Perform I2C transaction
            self.bus.i2c_rdwr(write, read)
            raw_data = list(read)

            # Convert raw data to temperature (Celsius)
            temperatures = np.zeros(PIXEL_COUNT, dtype=np.float64)
            for i in range(PIXEL_COUNT):
                raw_temp = raw_data[i * 2] | (raw_data[i * 2 + 1] << 8)

                # Handle negative temperature (bit 11)
                if raw_temp & 0x0800:
                    raw_temp = -(0x1000 - (raw_temp & 0x0FFF))

                temperatures[i] = raw_temp * 0.25  # Convert to °C

            return temperatures

        except Exception as e:
            print(f"I2C Read Error: {e}. Retrying with simulation mode.")
            return self._simulate_frame()

    def _simulate_frame(self):
        """Fallback simulation mode: generates synthetic temperature frames."""
        frame = np.full(PIXEL_COUNT, 21.0, dtype=np.float64)
        noise = (np.random.rand(PIXEL_COUNT) - 0.5) * 1.0
        frame += noise
        
        # Randomly simulate a person presence
        if np.random.random() < 0.5:
            center_x, center_y = 5, 4
            for i in range(8):
                for j in range(8):
                    if abs(i - center_y) < 2 and abs(j - center_x) < 3:
                        frame[i * 8 + j] += 5 + (np.random.random() * 2)
        return frame

# NOTE: Install smbus2 if not already installed:
# pip install smbus2
# And ensure I2C is enabled using 'sudo raspi-config'
