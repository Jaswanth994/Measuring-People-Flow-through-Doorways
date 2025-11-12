"""
Body Extractor Module
Extracts and locates human bodies from thermal frames
"""

import numpy as np
import cv2
import logging


class BodyExtractor:
    """
    Extracts human bodies from thermal frames using multi-level thresholding
    """
    
    def __init__(self, config):
        """
        Initialize body extractor
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Body detection parameters
        self.min_body_area = config['body_detection']['min_body_area']
        self.max_body_area = config['body_detection']['max_body_area']
        self.large_body_threshold = config['body_detection']['large_body_threshold']
        self.temp_increment = config['body_detection']['temperature_increment']
    
    def extract_bodies(self, frame, background, diff_frame):
        """
        Extract bodies from frame
        
        Args:
            frame: Current thermal frame
            background: Background frame
            diff_frame: Difference from background
            
        Returns:
            list: List of body dictionaries with location and features
        """
        bodies = []
        
        # Start with base threshold
        threshold = self.temp_increment
        frame_area = frame.shape[0] * frame.shape[1]
        
        # Initial body extraction
        binary_mask, contours = self._get_contours(diff_frame, threshold)
        
        if len(contours) == 0:
            return bodies
        
        # Find largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        largest_area = cv2.contourArea(largest_contour) / frame_area
        
        # Check if we might have multiple people
        if largest_area > self.large_body_threshold:
            # Try to separate multiple bodies
            bodies = self._separate_bodies(diff_frame, frame, threshold)
        else:
            # Single body
            body = self._create_body_dict(largest_contour, frame, diff_frame)
            if body:
                bodies.append(body)
        
        return bodies
    
    def _separate_bodies(self, diff_frame, frame, initial_threshold):
        """
        Separate multiple bodies using incremental thresholding
        
        Args:
            diff_frame: Difference from background
            frame: Current frame
            initial_threshold: Starting threshold
            
        Returns:
            list: List of separated bodies
        """
        threshold = initial_threshold
        max_iterations = 8
        frame_area = frame.shape[0] * frame.shape[1]
        
        for iteration in range(max_iterations):
            binary_mask, contours = self._get_contours(diff_frame, threshold)
            
            if len(contours) == 0:
                threshold += self.temp_increment
                continue
            
            # Check if we found valid bodies
            valid_contours = []
            for contour in contours:
                area_ratio = cv2.contourArea(contour) / frame_area
                if self.min_body_area <= area_ratio <= self.max_body_area:
                    valid_contours.append(contour)
            
            # If we found 2 valid bodies, we're done
            if len(valid_contours) >= 2:
                bodies = []
                for contour in valid_contours[:2]:  # Max 2 people
                    body = self._create_body_dict(contour, frame, diff_frame)
                    if body:
                        bodies.append(body)
                return bodies
            
            # If we found 1 small body, accept it
            if len(valid_contours) == 1:
                area_ratio = cv2.contourArea(valid_contours[0]) / frame_area
                if area_ratio < self.large_body_threshold:
                    body = self._create_body_dict(valid_contours[0], frame, diff_frame)
                    return [body] if body else []
            
            # Increase threshold and try again
            threshold += self.temp_increment
        
        # Fallback: return largest contour
        if len(contours) > 0:
            largest = max(contours, key=cv2.contourArea)
            body = self._create_body_dict(largest, frame, diff_frame)
            return [body] if body else []
        
        return []
    
    def _get_contours(self, diff_frame, threshold):
        """
        Get contours from difference frame with threshold
        
        Args:
            diff_frame: Difference from background
            threshold: Temperature threshold
            
        Returns:
            tuple: (binary_mask, contours)
        """
        # Create binary mask
        binary_mask = (diff_frame >= threshold).astype(np.uint8) * 255
        
        # Find contours
        contours, _ = cv2.findContours(
            binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        return binary_mask, contours
    
    def _create_body_dict(self, contour, frame, diff_frame):
        """
        Create body dictionary with features
        
        Args:
            contour: Body contour
            frame: Current frame
            diff_frame: Difference frame
            
        Returns:
            dict: Body features
        """
        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)
        
        # Calculate center
        M = cv2.moments(contour)
        if M["m00"] == 0:
            return None
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        # Get location (horizontal position for tracking)
        location = self._get_body_location(diff_frame, contour)
        
        # Calculate average temperature
        mask = np.zeros(frame.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], 0, 1, -1)
        avg_temp = np.mean(frame[mask == 1])
        
        # Calculate max temperature
        max_temp = np.max(frame[mask == 1])
        
        body = {
            'contour': contour,
            'bounding_box': (x, y, w, h),
            'center': (cx, cy),
            'location': location,
            'avg_temp': avg_temp,
            'max_temp': max_temp,
            'area': cv2.contourArea(contour)
        }
        
        return body
    
    def _get_body_location(self, diff_frame, contour):
        """
        Get horizontal location of body (for tracking)
        
        Args:
            diff_frame: Difference frame
            contour: Body contour
            
        Returns:
            float: Normalized horizontal position (0-1)
        """
        # Create mask for this body
        mask = np.zeros(diff_frame.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], 0, 1, -1)
        
        # Calculate column sums
        col_sums = np.sum(mask, axis=0)
        
        # Find center of mass
        if np.sum(col_sums) == 0:
            return 0.5
        
        weighted_sum = np.sum(col_sums * np.arange(len(col_sums)))
        location = weighted_sum / np.sum(col_sums)
        
        # Normalize to 0-1
        normalized_location = location / diff_frame.shape[1]
        
        return normalized_location
    
    def find_body_locations(self, bodies, frame_width):
        """
        Find precise locations of bodies using column analysis
        
        Args:
            bodies: List of body dictionaries
            frame_width: Width of frame
            
        Returns:
            list: Updated body dictionaries with refined locations
        """
        for body in bodies:
            # Location already calculated in _create_body_dict
            pass
        
        return bodies