"""
Main People Counter Application
Integrates all modules for real-time people counting
"""

import cv2
import yaml
import logging
import time
import argparse
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sensor.grideye_reader import GridEyeReader
from src.processing.background import BackgroundEstimator
from src.processing.noise_filter import NoiseFilter
from src.processing.body_extractor import BodyExtractor
from src.processing.tracker import PeopleTracker
from src.utils.visualization import Visualizer


class PeopleCounter:
    """
    Main people counting system
    """
    
    def __init__(self, config_path='config/config.yaml'):
        """
        Initialize people counter system
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 50)
        self.logger.info("People Counter System Initializing")
        self.logger.info("=" * 50)
        
        # Initialize modules
        self.sensor_reader = GridEyeReader(self.config)
        self.background_estimator = BackgroundEstimator(self.config)
        self.noise_filter = NoiseFilter(self.config)
        self.body_extractor = BodyExtractor(self.config)
        self.tracker = PeopleTracker(self.config)
        self.visualizer = Visualizer(self.config)
        
        # System state
        self.running = False
        self.background_initialized = False
        
        self.logger.info("All modules initialized successfully")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config['logging']
        
        # Create log directory
        os.makedirs(os.path.dirname(log_config['log_file']), exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_config['log_level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config['log_file']),
                logging.StreamHandler()
            ]
        )
    
    def initialize_background(self, use_saved=True):
        """
        Initialize background
        
        Args:
            use_saved: Try to load saved background first
        """
        self.logger.info("Initializing background...")
        
        # Try to load saved background
        if use_saved and self.background_estimator.load_background():
            self.background_initialized = True
            return
        
        # Calculate new background
        self.logger.info("Please ensure the doorway is clear of people")
        self.logger.info("Background calculation starting in 3 seconds...")
        time.sleep(3)
        
        self.background_estimator.calculate_background(self.sensor_reader)
        self.background_initialized = True
        
        self.logger.info("Background initialization complete")
    
    def process_frame(self, frame_data):
        """
        Process a single frame
        
        Args:
            frame_data: Frame data dictionary
            
        Returns:
            dict: Processing results
        """
        frame = frame_data['frame']
        timestamp = frame_data['timestamp']
        
        # Get background
        background = self.background_estimator.get_background()
        background_temp = background.mean()
        
        # Calculate difference
        diff_frame = self.background_estimator.get_difference_frame(frame)
        
        # Check if frame contains human
        has_human = self.noise_filter.has_human(diff_frame, background_temp)
        
        bodies = []
        tracking_status = None
        
        if has_human:
            # Extract bodies
            bodies = self.body_extractor.extract_bodies(frame, background, diff_frame)
            
            # Update tracker
            tracking_status = self.tracker.update(bodies, timestamp)
        else:
            # Update tracker with no bodies
            tracking_status = self.tracker.update([], timestamp)
        
        return {
            'frame': frame,
            'diff_frame': diff_frame,
            'bodies': bodies,
            'tracking_status': tracking_status,
            'has_human': has_human
        }
    
    def run(self):
        """
        Main processing loop
        """
        if not self.background_initialized:
            self.logger.error("Background not initialized. Call initialize_background() first")
            return
        
        self.logger.info("=" * 50)
        self.logger.info("Starting People Counter")
        self.logger.info("Press 'q' to quit, 'r' to reset counts, 's' to save frame")
        self.logger.info("=" * 50)
        
        self.running = True
        frame_count = 0
        
        try:
            while self.running:
                # Read frame
                frame_data = self.sensor_reader.get_frame_sync()
                
                if frame_data is None:
                    time.sleep(0.01)
                    continue
                
                # Wrap in dict with timestamp
                frame_data = {
                    'frame': frame_data,
                    'timestamp': time.time()
                }
                
                # Process frame
                results = self.process_frame(frame_data)
                
                # Visualize
                vis_image = self.visualizer.visualize_frame(
                    results['frame'],
                    results['bodies'],
                    results['tracking_status'],
                    diff_frame=results['diff_frame']
                )
                
                if vis_image is not None:
                    self.visualizer.show(vis_image)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    self.logger.info("Quit requested")
                    self.running = False
                
                elif key == ord('r'):
                    self.logger.info("Resetting counts")
                    self.tracker.reset_counts()
                
                elif key == ord('s'):
                    filename = f"data/frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    self.visualizer.save_frame(vis_image, filename)
                
                frame_count += 1
                
                # Log status every 100 frames
                if frame_count % 100 == 0:
                    status = results['tracking_status']
                    self.logger.info(
                        f"Status - Occupancy: {status['current_occupancy']}, "
                        f"Entrances: {status['total_entrances']}, "
                        f"Exits: {status['total_exits']}"
                    )
        
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up...")
        cv2.destroyAllWindows()
        
        # Print final statistics
        occupancy = self.tracker.get_occupancy()
        self.logger.info("=" * 50)
        self.logger.info("Final Statistics:")
        self.logger.info(f"  Total Entrances: {self.tracker.total_entrances}")
        self.logger.info(f"  Total Exits: {self.tracker.total_exits}")
        self.logger.info(f"  Current Occupancy: {occupancy}")
        self.logger.info("=" * 50)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='People Counter System')
    parser.add_argument('--config', default='config/config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--no-saved-bg', action='store_true',
                       help='Do not use saved background')
    
    args = parser.parse_args()
    
    # Create people counter
    counter = PeopleCounter(args.config)
    
    # Initialize background
    counter.initialize_background(use_saved=not args.no_saved_bg)
    
    # Run
    counter.run()


if __name__ == '__main__':
    main()