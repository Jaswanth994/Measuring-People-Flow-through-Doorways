# processor/body_extractor.py
import numpy as np
import cv2
from config import GRID_SIZE, TOTAL_PIXELS, MIN_TEMP_FILTER, LARGE_BLOB_AREA, SMALL_BODY_AREA, MIN_PIXEL_AREA

def _attempt_split_large_blob(diff_frame, original_mask):
    """Attempts to split a large blob into two smaller bodies via iterative thresholding. [cite: 295-300]"""
    split_bodies = []
    
    # Iteratively increase threshold: Background + 0.5C, 0.75C, 1.0C
    for delta in [0.5, 0.75, 1.0]: 
        current_thresh = MIN_TEMP_FILTER + delta
        
        # Apply new higher threshold to the original blob area
        temp_mask_float = np.where((diff_frame > current_thresh) & (original_mask == 1), 1, 0).astype(np.float32)
        temp_mask_8u = (temp_mask_float * 255).astype(np.uint8)
        
        n_labels_s, labels_s, stats_s, centroids_s = cv2.connectedComponentsWithStats(temp_mask_8u, connectivity=4)
        
        # Filter for two valid bodies (> 10% area)
        valid_bodies = [s for s in stats_s[1:] if s[cv2.CC_STAT_AREA] > SMALL_BODY_AREA]
        
        if len(valid_bodies) == 2:
            # Two bodies found!
            for j in range(1, n_labels_s):
                mask = (labels_s == j).astype(np.float32)
                if stats_s[j, cv2.CC_STAT_AREA] > SMALL_BODY_AREA:
                     split_bodies.append({
                        'mask': mask, 
                        'max_diff': np.max(diff_frame[labels_s == j]),
                    })
            return split_bodies
    
    return None # Failed to split

def extract_bodies(diff_frame):
    """
    Implements the Multi-Level Thresholding to extract and separate bodies.
    Returns a list of dictionaries with 'mask' and 'max_diff' for each body.
    """
    bodies_data = []

    # Find initial blobs using the base threshold (0.25C)
    min_thresholded_float = np.where(diff_frame > MIN_TEMP_FILTER, diff_frame, 0).astype(np.float32)
    _, min_thresholded_8u = cv2.threshold(min_thresholded_float, 0.01, 255, cv2.THRESH_BINARY)
    min_thresholded_8u = min_thresholded_8u.astype(np.uint8)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(min_thresholded_8u, connectivity=4)
    
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        
        if area >= MIN_PIXEL_AREA:
            mask = (labels == i).astype(np.float32)
            max_diff = np.max(diff_frame[labels == i])

            # Check for "large blob" scenario (possible two people)
            if area >= LARGE_BLOB_AREA: 
                split_bodies = _attempt_split_large_blob(diff_frame, mask)
                if split_bodies:
                    bodies_data.extend(split_bodies)
                    continue

            bodies_data.append({'mask': mask, 'max_diff': max_diff})
    
    return bodies_data

def find_body_location(diff_frame, background_temp, bodies_data):
    """Calculates the location of the body by analyzing column sums. [cite: 301-305]"""
    people = []
    bg_mean = np.mean(background_temp)

    for data in bodies_data:
        mask = data['mask']
        
        # Calculate column sum based on hot pixel values
        column_sum = np.sum(diff_frame * mask, axis=0)

        # Location is the column with the maximum sum
        location_col = np.argmax(column_sum) 
        
        # Max reported temp
        max_temp = data['max_diff'] + bg_mean 
        
        people.append({'location_col': location_col, 'max_temp': max_temp})
        
    return people