import numpy as np
import cv2
from config import MIN_TEMP_FILTER, OTSU_DIFF_THRESHOLD

def check_for_human_presence(diff_frame):
    """
    [cite_start]Implements the combined Noise Removal Technique (Min T + Otsu) [cite: 279-284].
    Returns True if a human signature is detected, False otherwise.
    """
    # Ensure diff_frame is a numpy array
    diff_frame = np.asarray(diff_frame, dtype=np.float32)

    # 1. Temperature Filter (Min T) - average difference across frame
    avg_diff = float(np.mean(diff_frame))
    if avg_diff < MIN_TEMP_FILTER:
        return False

    # 2. Otsu's Binarization Check
    # Normalize the float difference image to 8-bit for Otsu
    diff_normalized = cv2.normalize(diff_frame, None, 0, 255, cv2.NORM_MINMAX)
    diff_normalized = diff_normalized.astype(np.uint8)
    _, otsu_binary = cv2.threshold(diff_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Separate the original diff_frame values by Otsu classes (0 and 255)
    class1_temps = diff_frame[otsu_binary == 0]
    class2_temps = diff_frame[otsu_binary == 255]
    
    # If any class is empty, Otsu can't be trusted -> treat as no presence
    if class1_temps.size == 0 or class2_temps.size == 0:
         return False

    temp_class1_mean = float(np.mean(class1_temps))
    temp_class2_mean = float(np.mean(class2_temps))
    
    # Check if difference between class means is greater than threshold (OTSU_DIFF_THRESHOLD)
    if np.abs(temp_class2_mean - temp_class1_mean) < OTSU_DIFF_THRESHOLD:
        return False
        
    return True
