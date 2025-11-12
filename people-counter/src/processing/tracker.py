"""
People Tracker Module
Tracks people across frames and determines direction of movement
"""

import numpy as np
import logging
from collections import deque
import time


class Person:
    """
    Represents a tracked person
    """
    
    def __init__(self, person_id, body, timestamp):
        """
        Initialize person tracker
        
        Args:
            person_id: Unique identifier
            body: Body dictionary
            timestamp: Time of first detection
        """
        self.id = person_id
        self.locations = deque(maxlen=20)
        self.temperatures = deque(maxlen=20)
        self.timestamps = deque(maxlen=20)
        self.frames_tracked = 0
        
        # Add initial data
        self.update(body, timestamp)
        
        self.direction = None  # 'entrance' or 'exit'
        self.direction_determined = False
    
    def update(self, body, timestamp):
        """
        Update person with new observation
        
        Args:
            body: Body dictionary
            timestamp: Current timestamp
        """
        self.locations.append(body['location'])
        self.temperatures.append(body['avg_temp'])
        self.timestamps.append(timestamp)
        self.frames_tracked += 1
    
    def determine_direction(self, min_frames=3):
        """
        Determine direction of movement
        
        Args:
            min_frames: Minimum frames before determining direction
            
        Returns:
            str: 'entrance', 'exit', or None
        """
        if self.frames_tracked < min_frames:
            return None
        
        if self.direction_determined:
            return self.direction
        
        # Analyze location trajectory
        locations = list(self.locations)
        
        # Calculate movement direction
        start_location = np.mean(locations[:2])
        end_location = np.mean(locations[-2:])
        
        movement = end_location - start_location
        
        # Threshold for determining direction
        threshold = 0.15
        
        if movement > threshold:
            self.direction = 'entrance'  # Moving right (entering)
            self.direction_determined = True
        elif movement < -threshold:
            self.direction = 'exit'  # Moving left (exiting)
            self.direction_determined = True
        
        return self.direction
    
    def is_stale(self, current_time, max_age=2.0):
        """
        Check if person tracking is stale
        
        Args:
            current_time: Current timestamp
            max_age: Maximum age in seconds
            
        Returns:
            bool: True if stale
        """
        if len(self.timestamps) == 0:
            return True
        
        last_seen = self.timestamps[-1]
        age = current_time - last_seen
        
        return age > max_age
    
    def get_avg_temperature(self):
        """Get average temperature across observations"""
        if len(self.temperatures) == 0:
            return 0
        return np.mean(self.temperatures)


class PeopleTracker:
    """
    Tracks multiple people across frames
    """
    
    def __init__(self, config):
        """
        Initialize people tracker
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Tracking parameters
        self.spatial_threshold = config['tracking']['spatial_distance_threshold']
        self.temp_threshold = config['tracking']['temperature_distance_threshold']
        self.temporal_threshold = config['tracking']['temporal_distance_threshold']
        self.min_tracking_frames = config['tracking']['min_tracking_frames']
        
        # Active persons being tracked
        self.active_persons = []
        self.next_person_id = 1
        
        # Completed tracks (crossed the door)
        self.completed_entrances = []
        self.completed_exits = []
        
        # Statistics
        self.total_entrances = 0
        self.total_exits = 0
        self.current_occupancy = 0
    
    def update(self, bodies, timestamp):
        """
        Update tracker with new bodies
        
        Args:
            bodies: List of body dictionaries
            timestamp: Current timestamp
            
        Returns:
            dict: Tracking results
        """
        # Match bodies to existing persons
        matched_persons = []
        unmatched_bodies = []
        
        for body in bodies:
            matched = False
            
            for person in self.active_persons:
                if self._is_match(person, body, timestamp):
                    person.update(body, timestamp)
                    matched_persons.append(person)
                    matched = True
                    break
            
            if not matched:
                unmatched_bodies.append(body)
        
        # Create new persons for unmatched bodies
        for body in unmatched_bodies:
            new_person = Person(self.next_person_id, body, timestamp)
            self.next_person_id += 1
            self.active_persons.append(new_person)
            matched_persons.append(new_person)
        
        # Update active persons list
        self.active_persons = matched_persons
        
        # Check for completed tracks
        self._check_completed_tracks(timestamp)
        
        # Remove stale persons
        self._remove_stale_persons(timestamp)
        
        # Return current status
        return self._get_status()
    
    def _is_match(self, person, body, timestamp):
        """
        Check if body matches person
        
        Args:
            person: Person object
            body: Body dictionary
            timestamp: Current timestamp
            
        Returns:
            bool: True if match
        """
        # Spatial distance check
        last_location = person.locations[-1]
        spatial_distance = abs(body['location'] - last_location)
        
        if spatial_distance > self.spatial_threshold:
            return False
        
        # Temperature distance check
        last_temp = person.temperatures[-1]
        temp_distance = abs(body['avg_temp'] - last_temp)
        
        if temp_distance > self.temp_threshold:
            return False
        
        # Temporal distance check
        last_timestamp = person.timestamps[-1]
        time_diff = timestamp - last_timestamp
        frame_diff = time_diff * 10  # Assuming 10 FPS
        
        if frame_diff > self.temporal_threshold:
            return False
        
        return True
    
    def _check_completed_tracks(self, current_time):
        """
        Check if any persons have completed their tracks
        
        Args:
            current_time: Current timestamp
        """
        completed = []
        
        for person in self.active_persons:
            # Determine direction
            direction = person.determine_direction(self.min_tracking_frames)
            
            if direction and person.frames_tracked >= self.min_tracking_frames:
                # Check if person has moved significantly
                locations = list(person.locations)
                
                # Check if person has crossed threshold (0.3 or 0.7 normalized position)
                if direction == 'entrance':
                    if locations[-1] > 0.7:  # Crossed entrance threshold
                        completed.append(person)
                        self.completed_entrances.append(person)
                        self.total_entrances += 1
                        self.current_occupancy += 1
                        self.logger.info(f"Person {person.id} entered. Occupancy: {self.current_occupancy}")
                
                elif direction == 'exit':
                    if locations[-1] < 0.3:  # Crossed exit threshold
                        completed.append(person)
                        self.completed_exits.append(person)
                        self.total_exits += 1
                        self.current_occupancy = max(0, self.current_occupancy - 1)
                        self.logger.info(f"Person {person.id} exited. Occupancy: {self.current_occupancy}")
        
        # Remove completed persons
        for person in completed:
            self.active_persons.remove(person)
    
    def _remove_stale_persons(self, current_time):
        """
        Remove persons that haven't been seen recently
        
        Args:
            current_time: Current timestamp
        """
        stale_persons = []
        
        for person in self.active_persons:
            if person.is_stale(current_time):
                stale_persons.append(person)
                self.logger.debug(f"Removing stale person {person.id}")
        
        for person in stale_persons:
            self.active_persons.remove(person)
    
    def _get_status(self):
        """
        Get current tracking status
        
        Returns:
            dict: Status dictionary
        """
        return {
            'active_persons': len(self.active_persons),
            'total_entrances': self.total_entrances,
            'total_exits': self.total_exits,
            'current_occupancy': self.current_occupancy,
            'persons': [
                {
                    'id': p.id,
                    'location': p.locations[-1] if p.locations else 0,
                    'direction': p.direction,
                    'frames_tracked': p.frames_tracked
                }
                for p in self.active_persons
            ]
        }
    
    def reset_counts(self):
        """Reset entrance and exit counts"""
        self.total_entrances = 0
        self.total_exits = 0
        self.current_occupancy = 0
        self.completed_entrances = []
        self.completed_exits = []
        self.logger.info("Counts reset")
    
    def get_occupancy(self):
        """
        Get current occupancy count
        
        Returns:
            int: Number of people in room
        """
        return self.current_occupancy