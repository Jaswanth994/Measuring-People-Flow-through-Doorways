"""
Visualization Module
Displays thermal heatmaps and tracking information
"""

import numpy as np
import cv2
import logging


class Visualizer:
    """
    Handles visualization of thermal data and tracking
    """
    
    def __init__(self, config):
        """
        Initialize visualizer
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.enabled = config['visualization']['enable']
        self.interpolation_size = tuple(config['visualization']['interpolation_size'])
        self.colormap = getattr(cv2, f"COLORMAP_{config['visualization']['colormap'].upper()}")
        self.display_fps = config['visualization']['display_fps']
        
        self.fps_values = []
        self.last_time = None
    
    def visualize_frame(self, frame, bodies=None, tracking_status=None, 
                       background=None, diff_frame=None):
        """
        Create visualization of current frame
        
        Args:
            frame: Current thermal frame
            bodies: List of detected bodies
            tracking_status: Tracking status dictionary
            background: Background frame (optional)
            diff_frame: Difference frame (optional)
            
        Returns:
            numpy.ndarray: Visualization image
        """
        if not self.enabled:
            return None
        
        # Interpolate to larger size for better visualization
        frame_interp = cv2.resize(frame, self.interpolation_size, 
                                 interpolation=cv2.INTER_LINEAR)
        
        # Normalize to 0-255
        frame_norm = cv2.normalize(frame_interp, None, 0, 255, cv2.NORM_MINMAX)
        frame_norm = frame_norm.astype(np.uint8)
        
        # Apply colormap
        frame_color = cv2.applyColorMap(frame_norm, self.colormap)
        # --- START OF NEW CODE ---
        # Get min/max temperatures from the raw frame
        min_temp = np.min(frame)
        max_temp = np.max(frame)
        
        # Create text labels
        min_text = f"Min: {min_temp:.1f}C"
        max_text = f"Max: {max_temp:.1f}C"
        
        # Draw text on the image (bottom-left corner)
        # Using interpolation_size[1] for the y-axis ensures it's at the bottom
        cv2.putText(frame_color, min_text, 
                   (10, self.interpolation_size[1] - 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        cv2.putText(frame_color, max_text, 
                   (10, self.interpolation_size[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        # --- END OF NEW CODE ---
        # Draw bodies if provided
        if bodies:
            frame_color = self._draw_bodies(frame_color, bodies, frame.shape)
        
        # Draw tracking info if provided
        if tracking_status:
            frame_color = self._draw_tracking_info(frame_color, tracking_status)
        
        # Draw FPS if enabled
        if self.display_fps:
            frame_color = self._draw_fps(frame_color)
        
        # Create additional views if requested
        if diff_frame is not None:
            combined = self._create_multi_view(frame_color, diff_frame)
            return combined
        
        return frame_color
    
    def _draw_bodies(self, image, bodies, original_shape):
        """
        Draw detected bodies on image
        
        Args:
            image: Visualization image
            bodies: List of body dictionaries
            original_shape: Shape of original thermal frame
            
        Returns:
            numpy.ndarray: Image with bodies drawn
        """
        # Calculate scaling factors
        scale_x = self.interpolation_size[0] / original_shape[1]
        scale_y = self.interpolation_size[1] / original_shape[0]
        
        for idx, body in enumerate(bodies):
            # Scale bounding box
            x, y, w, h = body['bounding_box']
            x_scaled = int(x * scale_x)
            y_scaled = int(y * scale_y)
            w_scaled = int(w * scale_x)
            h_scaled = int(h * scale_y)
            
            # Draw rectangle
            cv2.rectangle(image, (x_scaled, y_scaled), 
                         (x_scaled + w_scaled, y_scaled + h_scaled),
                         (0, 255, 0), 2)
            
            # Draw center point
            cx, cy = body['center']
            cx_scaled = int(cx * scale_x)
            cy_scaled = int(cy * scale_y)
            cv2.circle(image, (cx_scaled, cy_scaled), 5, (0, 255, 255), -1)
            
            # Draw temperature
            temp_text = f"{body['avg_temp']:.1f}C"
            cv2.putText(image, temp_text, (x_scaled, y_scaled - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return image
    
    def _draw_tracking_info(self, image, tracking_status):
        """
        Draw tracking information overlay
        
        Args:
            image: Visualization image
            tracking_status: Tracking status dictionary
            
        Returns:
            numpy.ndarray: Image with tracking info
        """
        # Draw semi-transparent overlay
        overlay = image.copy()
        
        # Info panel
        panel_height = 120
        cv2.rectangle(overlay, (0, 0), (image.shape[1], panel_height), 
                     (0, 0, 0), -1)
        
        # Blend
        alpha = 0.6
        image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
        
        # Text info
        y_offset = 25
        line_height = 25
        
        texts = [
            f"Entrances: {tracking_status['total_entrances']}",
            f"Exits: {tracking_status['total_exits']}",
            f"Current Occupancy: {tracking_status['current_occupancy']}",
            f"Active Tracks: {tracking_status['active_persons']}"
        ]
        
        for i, text in enumerate(texts):
            y_pos = y_offset + i * line_height
            cv2.putText(image, text, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw active persons
        for person in tracking_status['persons']:
            # Draw direction arrow
            location = person['location']
            x_pos = int(location * image.shape[1])
            y_pos = panel_height + 30
            
            color = (0, 255, 0) if person['direction'] == 'entrance' else (0, 0, 255)
            
            cv2.circle(image, (x_pos, y_pos), 8, color, -1)
            
            # Draw ID
            id_text = f"#{person['id']}"
            cv2.putText(image, id_text, (x_pos - 10, y_pos - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return image
    
    def _draw_fps(self, image):
        """
        Draw FPS counter
        
        Args:
            image: Visualization image
            
        Returns:
            numpy.ndarray: Image with FPS
        """
        import time
        
        current_time = time.time()
        
        if self.last_time is not None:
            fps = 1.0 / (current_time - self.last_time)
            self.fps_values.append(fps)
            
            # Keep last 30 values
            if len(self.fps_values) > 30:
                self.fps_values.pop(0)
            
            avg_fps = np.mean(self.fps_values)
            
            # Draw FPS
            fps_text = f"FPS: {avg_fps:.1f}"
            cv2.putText(image, fps_text, 
                       (image.shape[1] - 120, image.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        self.last_time = current_time
        
        return image
    
    def _create_multi_view(self, frame_color, diff_frame):
        """
        Create multi-view visualization
        
        Args:
            frame_color: Colored frame
            diff_frame: Difference frame
            
        Returns:
            numpy.ndarray: Combined view
        """
        # Interpolate difference frame
        diff_interp = cv2.resize(diff_frame, self.interpolation_size,
                                interpolation=cv2.INTER_LINEAR)
        
        # Normalize and colorize
        diff_norm = cv2.normalize(diff_interp, None, 0, 255, cv2.NORM_MINMAX)
        diff_norm = diff_norm.astype(np.uint8)
        diff_color = cv2.applyColorMap(diff_norm, cv2.COLORMAP_HOT)
        
        # Stack horizontally
        combined = np.hstack([frame_color, diff_color])
        
        # Add labels
        cv2.putText(combined, "Current Frame", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(combined, "Difference", 
                   (self.interpolation_size[0] + 10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return combined
    
    def show(self, image, window_name="People Counter"):
        """
        Display image in window
        
        Args:
            image: Image to display
            window_name: Window title
        """
        if not self.enabled or image is None:
            return
        
        cv2.imshow(window_name, image)
    
    def save_frame(self, image, filename):
        """
        Save frame to file
        
        Args:
            image: Image to save
            filename: Output filename
        """
        if image is not None:
            cv2.imwrite(filename, image)
            self.logger.info(f"Frame saved to {filename}")


