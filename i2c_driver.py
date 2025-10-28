# i2c_driver.py
import smbus
import numpy as np
import time

# I2C constants for Panasonic GridEYE (AMG8833)
I2C_BUS = 1             # Default I2C bus number on Raspberry Pi
GRIDEYE_ADDR = 0x68     # Default I2C address for GridEYE
TEMP_START_REG = 0x80   # Start register for temperature data
PIXEL_COUNT = 64        # 8x8 sensor = 64 pixels

class GridEYEI2CDriver:
    """Handles raw I2C communication with the GridEYE sensor."""
    
    def __init__(self):
        try:
            self.bus = smbus.SMBus(I2C_BUS)
            print(f"I2C bus {I2C_BUS} opened successfully.")
        except FileNotFoundError:
            print("ERROR: Could not open I2C bus. Is I2C enabled on Raspberry Pi?")
            self.bus = None

    def read_raw_frame(self):
        """Reads 64 pixel values (128 bytes) from the GridEYE."""
        if not self.bus:
            # Fallback to simulation if I2C fails (for development on non-RPi)
            return self._simulate_frame()

        try:
            # Read 128 bytes (64 pixels * 2 bytes/pixel)
            raw_data = self.bus.read_i2c_block_data(GRIDEYE_ADDR, TEMP_START_REG, PIXEL_COUNT * 2)
            temperatures = np.zeros(PIXEL_COUNT, dtype=np.float64)
            
            for i in range(PIXEL_COUNT):
                raw_temp = raw_data[i * 2] | (raw_data[i * 2 + 1] << 8)
                
                # Check for negative temperature (11th bit)
                if raw_temp & 0x0800:
                    raw_temp = -(0x1000 - (raw_temp & 0x0FFF))
                
                temperatures[i] = raw_temp * 0.25  # Convert to Celsius
                
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

# NOTE: Ensure smbus is installed:
# sudo apt-get install python3-smbus
# and I2C is enabled using 'sudo raspi-config'
