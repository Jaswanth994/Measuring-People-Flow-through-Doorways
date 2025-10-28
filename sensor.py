# sensor.py
import numpy as np
import os
import time
import cv2
from config import *
from i2c_driver import GridEYEI2CDriver

class GridEYESensor:
    """
    Handles background determination and provides frames to the processor.
    """
    def __init__(self):
        self.background_temp = None
        os.makedirs(DATA_DIR, exist_ok=True)
        # Initialize the low-level I2C driver
        self.driver = GridEYEI2CDriver() 

    def determine_background(self):
        """Calculates the stable background image."""
        print(f"Starting background determination ({BACKGROUND_FRAMES} frames).")
        pixel_sum = np.zeros(TOTAL_PIXELS, dtype=np.float64)
        
        for i in range(BACKGROUND_FRAMES):
            # Use the actual driver to read
            frame = self.driver.read_raw_frame()
            pixel_sum += frame
            time.sleep(1 / FRAME_RATE)
            
        self.background_temp = pixel_sum / BACKGROUND_FRAMES
        print("Background determination complete.")
        return True

    def load_background(self):
        """Attempts to load a previously saved background from file."""
        if os.path.exists(BACKGROUND_FILE):
            print(f"Loading background from {BACKGROUND_FILE}")
            self.background_temp = np.load(BACKGROUND_FILE)
            return True
        else:
            print(f"Warning: Background file not found.")
            return False

    def save_background(self):
        """Saves the calculated background to file."""
        if self.background_temp is not None:
            np.save(BACKGROUND_FILE, self.background_temp)
            print(f"Background saved to {BACKGROUND_FILE}")
            return True
        return False
        
    def get_current_frame(self):
        """Reads a single frame in real-time using the driver."""
        return self.driver.read_raw_frame()

    def get_frame_mat(self, frame):
        """Converts the 1D numpy array to a scaled OpenCV Mat for visualization."""
        mat = frame.reshape((GRID_SIZE, GRID_SIZE)).astype(np.float32)
        scaled_mat = cv2.resize(mat, (320, 320), interpolation=cv2.INTER_LINEAR)
        return scaled_mat