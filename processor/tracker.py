import numpy as np
import time
from config import SPATIAL_THRESHOLD_COLS, TEMP_THRESHOLD_DIFF, TEMPORAL_THRESHOLD_FRAMES, FRAME_DELAY_MS

class Person:
    """Represents a single tracked individual with history."""
    def __init__(self, location_col, max_temp, person_id):
        self.id = person_id
        self.location_col = float(location_col)
        self.max_temp = float(max_temp)
        self.last_seen = time.time()
        self.recent_locations = [int(location_col)]
        self.is_active = True
        self.counted = False  # Flag to prevent double counting a single Entrance/Exit

    def update_location(self, new_location, new_max_temp):
        """Updates location and history for sustained tracking."""
        self.location_col = float(new_location)
        self.max_temp = float(new_max_temp)
        self.last_seen = time.time()
        self.is_active = True
        
        self.recent_locations.append(int(new_location))
        # Keep recent history bounded by TEMPORAL_THRESHOLD_FRAMES
        if len(self.recent_locations) > TEMPORAL_THRESHOLD_FRAMES:
            self.recent_locations.pop(0)

def track_and_count(tracked_people, next_person_id, occupancy_count, new_people_data):
    """
    [cite_start]Matches new detections to tracked individuals and determines direction. [cite: 306-313]
    Returns updated tracked_people list, updated next_person_id, and updated occupancy_count.
    """
    newly_tracked = []
    
    # Mark all existing trackers as inactive; they will be re-activated if matched
    for p in tracked_people:
        p.is_active = False

    # For each new detection, try to find the best matching existing tracker
    for data in new_people_data:
        best_match = None
        min_distance = float('inf')
        
        for p in tracked_people:
            spatial_dist = abs(p.location_col - data['location_col'])
            temp_diff = abs(p.max_temp - data['max_temp'])
            
            # Match if within both spatial and temperature thresholds
            if spatial_dist < SPATIAL_THRESHOLD_COLS and temp_diff < TEMP_THRESHOLD_DIFF:
                distance = spatial_dist + temp_diff
                if distance < min_distance:
                    min_distance = distance
                    best_match = p
        
        if best_match:
            # Update matched person
            best_match.update_location(data['location_col'], data['max_temp'])
            newly_tracked.append(best_match)
            
            # Check for Direction and Counting (requires some movement history)
            if len(best_match.recent_locations) >= 3 and not best_match.counted:
                start_loc = best_match.recent_locations[0]
                end_loc = best_match.recent_locations[-1]
                
                # Entrance: Sustained move Left (Col < 2) to Right (Col > 5)
                if start_loc < 2 and end_loc > 5:
                    occupancy_count += 1
                    best_match.counted = True
                    print(f"[{best_match.id}] ENTRANCE Detected! Occupancy: {occupancy_count}")
                
                # Exit: Sustained move Right (Col > 5) to Left (Col < 2)
                elif start_loc > 5 and end_loc < 2:
                    occupancy_count -= 1
                    best_match.counted = True
                    print(f"[{best_match.id}] EXIT Detected! Occupancy: {occupancy_count}")
                    
        else:
            # New person: create tracker
            new_person = Person(data['location_col'], data['max_temp'], next_person_id)
            next_person_id += 1
            newly_tracked.append(new_person)
            
    # Cleanup: keep trackers that were newly_tracked and not stale
    current_time = time.time()
    stale_time_s = TEMPORAL_THRESHOLD_FRAMES * (FRAME_DELAY_MS / 1000.0)
    # Keep persons from newly_tracked that are active OR seen recently
    tracked_people = [p for p in newly_tracked if (p.is_active or (current_time - p.last_seen < stale_time_s))]

    return tracked_people, next_person_id, occupancy_count
