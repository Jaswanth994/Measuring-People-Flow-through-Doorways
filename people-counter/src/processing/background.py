"""
Background Estimation Module
Calculates and maintains background temperature reference
"""

import numpy as np
import logging
import os
import pickle
from datetime import datetime


class BackgroundEstimator:
    """
    Estimates and maintains background temperature profile
    """
    
    def __init__(self, config):
        """
        Initialize background estimator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.num_frames = config['background']['num_frames']
        self.temp_variance = config['background']['temperature_variance']
        
        self.background = None
        self.background_std = None
        self.is_initialized = False
        
        self.background_file = 'data/background/background.pkl'
    
    def calculate_background(self, sensor_reader):
        """
        Calculate background from sensor frames
        
        Args:
            sensor_reader: GridEyeReader instance
            
        Returns:
            numpy.ndarray: Background temperature matrix
        """
        self.logger.info(f"Collecting {self.num_frames} frames for background calculation...")
        
        frames = []
        
        for i in range(self.num_frames):
            frame = sensor_reader.read_frame()
            
            if frame is not None:
                frames.append(frame)
                
                if (i + 1) % 50 == 0:
                    self.logger.info(f"Collected {i + 1}/{self.num_frames} frames")
        
        if len(frames) < self.num_frames:
            self.logger.warning(f"Only collected {len(frames)} frames")
        
        # Calculate pixel-wise average
        frames_array = np.array(frames)
        self.background = np.mean(frames_array, axis=0)
        self.background_std = np.std(frames_array, axis=0)
        
        self.is_initialized = True
        
        self.logger.info(f"Background calculated. Mean temp: {np.mean(self.background):.2f}°C")
        
        # Save background
        self.save_background()
        
        return self.background
    
    def get_background(self):
        """
        Get current background
        
        Returns:
            numpy.ndarray: Background temperature matrix
        """
        if not self.is_initialized:
            self.logger.warning("Background not initialized")
            return None
        
        return self.background
    
    def get_background_std(self):
        """
        Get background standard deviation
        
        Returns:
            numpy.ndarray: Standard deviation matrix
        """
        return self.background_std
    
    def save_background(self):
        """Save background to file"""
        try:
            os.makedirs(os.path.dirname(self.background_file), exist_ok=True)
            
            data = {
                'background': self.background,
                'background_std': self.background_std,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.background_file, 'wb') as f:
                pickle.dump(data, f)
            
            self.logger.info(f"Background saved to {self.background_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save background: {e}")
    
    def load_background(self):
        """
        Load background from file
        
        Returns:
            bool: True if loaded successfully
        """
        try:
            if not os.path.exists(self.background_file):
                self.logger.info("No saved background found")
                return False
            
            with open(self.background_file, 'rb') as f:
                data = pickle.load(f)
            
            self.background = data['background']
            self.background_std = data['background_std']
            self.is_initialized = True
            
            self.logger.info(f"Background loaded from {self.background_file}")
            self.logger.info(f"Background timestamp: {data['timestamp']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load background: {e}")
            return False
    
    def get_difference_frame(self, frame):
        """
        Calculate difference from background
        
        Args:
            frame: Current frame
            
        Returns:
            numpy.ndarray: Difference frame
        """
        if not self.is_initialized:
            return None
        
        return frame - self.background
    
    def is_background_valid(self, frame):
        """
        Check if current frame is similar to background
        
        Args:
            frame: Current frame
            
        Returns:
            bool: True if frame is background-like
        """
        if not self.is_initialized:
            return False
        
        diff = np.abs(frame - self.background)
        mean_diff = np.mean(diff)
        
        return mean_diff < self.temp_variance