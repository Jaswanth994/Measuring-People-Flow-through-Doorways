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
        
        # Filter for candidate bodies (ignore background label at index 0)
        valid_bodies = [s for s in stats_s[1:] if s[cv2.CC_STAT_AREA] > SMALL_BODY_AREA]
        
        if len(valid_bodies) == 2:
            # Two bodies found! Build masks and record max diffs
            for j in range(1, n_labels_s):
                area_j = stats_s[j, cv2.CC_STAT_AREA]
                if area_j > SMALL_BODY_AREA:
                    mask = (labels_s == j).astype(np.float32)
                    # guard against empty selection
                    if np.any(labels_s == j):
                        max_diff_value = float(np.max(diff_frame[labels_s == j]))
                    else:
                        max_diff_value = 0.0
                    split_bodies.append({
                        'mask': mask,
                        'max_diff': max_diff_value,
                    })
            return split_bodies
    
    return None  # Failed to split

def extract_bodies(diff_frame):
    """
    Implements the Multi-Level Thresholding to extract and separate bodies.
    Returns a list of dictionaries with 'mask' and 'max_diff' for each body.
    """
    bodies_data = []

    # Ensure diff_frame is 2D (GRID_SIZE x GRID_SIZE)
    diff_frame = diff_frame.reshape((GRID_SIZE, GRID_SIZE)) if diff_frame.size == TOTAL_PIXELS and diff_frame.ndim == 1 else diff_frame

    # Find initial blobs using the base threshold (MIN_TEMP_FILTER)
    min_thresholded_float = np.where(diff_frame > MIN_TEMP_FILTER, diff_frame, 0).astype(np.float32)
    # Convert to 8-bit binary for connected components (small positive values must be non-zero)
    _, min_thresholded_8u = cv2.threshold(min_thresholded_float, 0.01, 255, cv2.THRESH_BINARY)
    min_thresholded_8u = min_thresholded_8u.astype(np.uint8)

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(min_thresholded_8u, connectivity=4)
    
    for i in range(1, num_labels):
        area = int(stats[i, cv2.CC_STAT_AREA])
        
        if area >= MIN_PIXEL_AREA:
            mask = (labels == i).astype(np.float32)
            # Protect against empty selection (shouldn't happen if area >= 1)
            if np.any(labels == i):
                max_diff = float(np.max(diff_frame[labels == i]))
            else:
                max_diff = 0.0

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
    # background_temp might be 1D (TOTAL_PIXELS) or 2D; compute mean safely
    bg_mean = float(np.mean(background_temp))

    # Ensure diff_frame is 2D GRID_SIZE x GRID_SIZE
    diff_frame = diff_frame.reshape((GRID_SIZE, GRID_SIZE)) if diff_frame.size == TOTAL_PIXELS and diff_frame.ndim == 1 else diff_frame

    for data in bodies_data:
        mask = data['mask']
        # Ensure mask is 2D of same shape
        mask = mask.reshape((GRID_SIZE, GRID_SIZE)) if mask.size == TOTAL_PIXELS and mask.ndim == 1 else mask
        
        # Calculate column sum based on hot pixel values within the mask
        # multiplying diff_frame by mask zeros out non-body pixels
        column_sum = np.sum(diff_frame * mask, axis=0)

        # Location is the column index with the maximum sum (0..GRID_SIZE-1)
        location_col = int(np.argmax(column_sum))

        # Max reported temperature is peak diff + estimated background mean
        max_temp = float(data.get('max_diff', 0.0)) + bg_mean

        people.append({'location_col': location_col, 'max_temp': max_temp})
        
    return people
