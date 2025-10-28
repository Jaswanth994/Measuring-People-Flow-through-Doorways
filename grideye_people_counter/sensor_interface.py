# sensor_interface.py
import time
import board
import busio
import numpy as np
import adafruit_amg88xx
from config import FRAME_INTERVAL

class GridEyeSensor:
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_amg88xx.AMG88XX(i2c)

    def read_frame(self):
        data = np.array(self.sensor.pixels)
        time.sleep(FRAME_INTERVAL)
        return data
