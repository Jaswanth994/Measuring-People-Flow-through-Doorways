# src/people_counter.py

import numpy as np
from scipy.ndimage import label, binary_erosion, binary_dilation, generate_binary_structure
from . import config

def calculate_initial_background(df_no_person):
    """Calculates the initial background temperature from the 0-person data."""
    if df_no_person is None:
        return None
    return np.mean(np.stack(df_no_person['gridEye_array']), axis=0)

def count_people(frame, background):
    """Counts people in a single thermal frame using advanced techniques."""
    frame_grid = frame.reshape(8, 8)
    background_grid = background.reshape(8, 8)

    foreground = (frame_grid - background_grid) > config.TEMPERATURE_THRESHOLD

    struct = generate_binary_structure(2, 1)
    eroded = binary_erosion(foreground, structure=struct, iterations=config.EROSION_ITERATIONS)
    dilated = binary_dilation(eroded, structure=struct, iterations=config.DILATION_ITERATIONS)

    labeled_array, num_features = label(dilated)

    people_count = 0
    valid_labels = []
    for i in range(1, num_features + 1):
        blob_size = np.sum(labeled_array == i)
        if config.MIN_BLOB_SIZE <= blob_size <= config.MAX_BLOB_SIZE:
            people_count += 1
            valid_labels.append(i)
            
    final_blobs = np.isin(labeled_array, valid_labels)
    return people_count, frame_grid, foreground, final_blobs