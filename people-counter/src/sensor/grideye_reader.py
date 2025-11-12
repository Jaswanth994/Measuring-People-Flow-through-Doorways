"""
GridEye AMG8833 Sensor Reader Module
Handles sensor initialization and frame acquisition
"""

import time
import numpy as np
import board
import busio
import adafruit_amg88xx
from collections import deque
import logging


class GridEyeReader:
    """
    Manages GridEye AMG8833 thermal sensor
    """
    
    def __init__(self, config):
        """
        Initialize GridEye sensor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Sensor parameters
        self.resolution = tuple(config['sensor']['resolution'])
        self.frame_rate = config['sensor']['frame_rate']
        self.frame_interval = 1.0 / self.frame_rate
        
        # Frame queue for buffering
        self.frame_queue = deque(maxlen=100)
        
        # Initialize sensor
        self._init_sensor()
        
        self.logger.info(f"GridEye sensor initialized at {self.frame_rate} Hz")
    
    def _init_sensor(self):
        """Initialize I2C connection and sensor"""
        try:
            # Initialize I2C bus
            i2c = busio.I2C(board.SCL, board.SDA)
            
            # Initialize AMG8833
            self.sensor = adafruit_amg88xx.AMG88XX(i2c)
            
            # Wait for sensor to stabilize
            time.sleep(0.1)
            
            self.logger.info("Sensor connected successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sensor: {e}")
            raise
    
    def read_frame(self):
        """
        Read a single frame from the sensor
        
        Returns:
            numpy.ndarray: 8x8 temperature array
        """
        try:
            # Read temperature data
            pixels = self.sensor.pixels
            
            # Convert to numpy array
            frame = np.array(pixels)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error reading frame: {e}")
            return None
    
    def start_acquisition(self):
        """
        Start continuous frame acquisition
        Adds frames to queue at specified frame rate
        """
        self.logger.info("Starting frame acquisition")
        self.running = True
        
        while self.running:
            start_time = time.time()
            
            # Read frame
            frame = self.read_frame()
            
            if frame is not None:
                # Add timestamp
                frame_data = {
                    'frame': frame,
                    'timestamp': time.time()
                }
                self.frame_queue.append(frame_data)
            
            # Maintain frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, self.frame_interval - elapsed)
            time.sleep(sleep_time)
    
    def get_frame(self):
        """
        Get the latest frame from queue
        
        Returns:
            dict: Frame data with timestamp, or None if queue is empty
        """
        if len(self.frame_queue) > 0:
            return self.frame_queue.popleft()
        return None
    
    def stop_acquisition(self):
        """Stop frame acquisition"""
        self.running = False
        self.logger.info("Stopped frame acquisition")
    
    def get_frame_sync(self):
        """
        Get a single frame synchronously (for testing/debugging)
        
        Returns:
            numpy.ndarray: Temperature frame
        """
        return self.read_frame()