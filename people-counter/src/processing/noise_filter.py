"""
Noise Filter Module
Implements noise detection and filtering techniques from the paper
"""

import numpy as np
import cv2
import logging
from scipy import stats


class NoiseFilter:
    """
    Filters noise and detects frames containing humans
    Uses combination of heat distribution, Otsu's thresholding, and temperature filtering
    """
    
    def __init__(self, config):
        """
        Initialize noise filter
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Filter parameters
        self.temp_threshold = config['noise_filter']['temperature_threshold']
        self.otsu_threshold = config['noise_filter']['otsu_threshold']
        self.width_threshold = config['noise_filter']['heat_distribution']['width_threshold']
        self.amplitude_threshold = config['noise_filter']['heat_distribution']['amplitude_threshold']
    
    #def has_human(self, diff_frame, background_temp):
        #Detect if frame contains a human using multi-stage filtering
        
        #Args:
         #   diff_frame: Difference from background
          #  background_temp: Background average temperature
            
        #Returns:
         #   bool: True if human detected
        # Stage 1: Heat distribution check
        #if not self._check_heat_distribution(diff_frame):
         #   return False
        
        # Stage 2: Otsu's thresholding
        #if not self._check_otsu_threshold(diff_frame):
         #   return False
        
        # Stage 3: Temperature filter
        #if not self._check_temperature_filter(diff_frame, background_temp):
         #   return False
        
        #return True
    
    def has_human(self, diff_frame, background_temp):
        """
        Detect if frame contains a human using a simple max pixel check
        
        Args:
            diff_frame: Difference from background
            background_temp: Background average temperature
            
        Returns:
            bool: True if human detected
        """
        # This is a much simpler check.
        # We re-purpose 'otsu_threshold' from the config
        # to be our new "Max Pixel Threshold".
        
        # If any single pixel is 1.25C (or whatever we set)
        # hotter than the background, we check for a body.
        max_pixel_threshold = self.otsu_threshold
        
        if np.max(diff_frame) >= max_pixel_threshold:
            return True
        
        return False
    def _check_heat_distribution(self, diff_frame):
        """
        Check heat distribution pattern
        
        Args:
            diff_frame: Difference from background
            
        Returns:
            bool: True if distribution indicates human presence
        """
        # Flatten and create histogram
        flat_diff = diff_frame.flatten()
        
        # Create histogram with 20 bins
        hist, bin_edges = np.histogram(flat_diff, bins=20)
        
        # Find peaks in histogram
        peaks = self._find_peaks(hist)
        
        if len(peaks) < 2:
            return False
        
        # Sort peaks by amplitude
        peak_amplitudes = [(hist[p], p) for p in peaks]
        peak_amplitudes.sort(reverse=True)
        
        # Check if second peak is significant
        if len(peak_amplitudes) < 2:
            return False
        
        max_amplitude = peak_amplitudes[0][0]
        second_amplitude = peak_amplitudes[1][0]
        
        # Calculate width of second peak
        second_peak_idx = peak_amplitudes[1][1]
        peak_width = self._calculate_peak_width(hist, second_peak_idx)
        max_width = len(hist)
        
        # Check thresholds
        width_ratio = peak_width / max_width
        amplitude_ratio = second_amplitude / max_amplitude
        
        return (width_ratio > self.width_threshold and 
                amplitude_ratio > self.amplitude_threshold)
    
    def _find_peaks(self, histogram):
        """
        Find peaks in histogram
        
        Args:
            histogram: 1D array
            
        Returns:
            list: Indices of peaks
        """
        peaks = []
        
        for i in range(1, len(histogram) - 1):
            if histogram[i] > histogram[i-1] and histogram[i] > histogram[i+1]:
                # Local maximum
                if histogram[i] > 2:  # Minimum threshold
                    peaks.append(i)
        
        return peaks
    
    def _calculate_peak_width(self, histogram, peak_idx):
        """
        Calculate width of a peak at half maximum
        
        Args:
            histogram: 1D array
            peak_idx: Index of peak
            
        Returns:
            int: Peak width
        """
        peak_value = histogram[peak_idx]
        half_max = peak_value / 2
        
        # Find left boundary
        left = peak_idx
        while left > 0 and histogram[left] > half_max:
            left -= 1
        
        # Find right boundary
        right = peak_idx
        while right < len(histogram) - 1 and histogram[right] > half_max:
            right += 1
        
        return right - left
    
    def _check_otsu_threshold(self, diff_frame):
        """
        Apply Otsu's thresholding to classify pixels
        
        Args:
            diff_frame: Difference from background
            
        Returns:
            bool: True if temperature difference between classes is significant
        """
        # Normalize to 0-255 for Otsu
        normalized = cv2.normalize(diff_frame, None, 0, 255, cv2.NORM_MINMAX)
        normalized = normalized.astype(np.uint8)
        
        # Apply Otsu's thresholding
        threshold_value, binary = cv2.threshold(
            normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        
        # Calculate average temperature in each class
        human_pixels = diff_frame[binary == 255]
        background_pixels = diff_frame[binary == 0]
        
        if len(human_pixels) == 0 or len(background_pixels) == 0:
            return False
        
        human_avg = np.mean(human_pixels)
        background_avg = np.mean(background_pixels)
        
        temp_diff = abs(human_avg - background_avg)
        
        return temp_diff >= self.otsu_threshold
    
    def _check_temperature_filter(self, diff_frame, background_temp):
        """
        Check if average temperature is higher than background
        
        Args:
            diff_frame: Difference from background
            background_temp: Background average temperature
            
        Returns:
            bool: True if temperature is significantly higher
        """
        frame_avg_diff = np.mean(diff_frame)
        
        return frame_avg_diff >= self.temp_threshold
    
    def get_binary_mask(self, diff_frame, background_temp):
        """
        Create binary mask of human pixels
        
        Args:
            diff_frame: Difference from background
            background_temp: Background average temperature
            
        Returns:
            numpy.ndarray: Binary mask (0 or 1)
        """
        # Threshold: background + temperature threshold
        threshold = self.temp_threshold
        
        # Create binary mask
        mask = (diff_frame >= threshold).astype(np.uint8)
        
        return mask
