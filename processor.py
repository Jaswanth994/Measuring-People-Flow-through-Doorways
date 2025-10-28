# processor.py
import numpy as np
import time
from config import *
from processor.noise_detector import check_for_human_presence
from processor.body_extractor import extract_bodies, find_body_location
from processor.tracker import track_and_count, Person

class PeopleCounter:
    """Orchestrates all processing algorithms."""
    def __init__(self, background_temp):
        self.background = background_temp
        self.occupancy_count = 0
        self.next_person_id = 1
        self.tracked_people = []
        self.diff_frame = None

    def _get_difference_frame(self, current_frame):
        """Calculates the pixel-wise difference frame (Current - Background)."""
        bg_reshaped = self.background.reshape((GRID_SIZE, GRID_SIZE))
        current_reshaped = current_frame.reshape((GRID_SIZE, GRID_SIZE))
        diff_frame = current_reshaped - bg_reshaped
        return diff_frame.astype(np.float32)

    def process_frame(self, current_frame):
        """Main frame processing pipeline."""
        
        # 1. Calculate Difference Frame
        self.diff_frame = self._get_difference_frame(current_frame)
        
        # 2. Noise Detection
        if check_for_human_presence(self.diff_frame):
            # 3. Extract Bodies
            bodies_data = extract_bodies(self.diff_frame)

            # 4. Find Body Location
            new_people_data = find_body_location(self.diff_frame, self.background, bodies_data)
            
            # 5. Tracking and Direction
            self.tracked_people, self.next_person_id, self.occupancy_count = \
                track_and_count(self.tracked_people, self.next_person_id, self.occupancy_count, new_people_data)
        else:
            # Still run tracking cleanup even if no human is detected in the current frame
            self.tracked_people, self.next_person_id, self.occupancy_count = \
                track_and_count(self.tracked_people, self.next_person_id, self.occupancy_count, [])