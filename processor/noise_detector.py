# processor/noise_detector.py
import numpy as np
import cv2
from config import MIN_TEMP_FILTER, OTSU_DIFF_THRESHOLD

def check_for_human_presence(diff_frame):
    """
    [cite_start]Implements the combined Noise Removal Technique (Min T + Otsu) [cite: 279-284].
    Returns True if a human signature is detected, False otherwise.
    """
    # 1. Temperature Filter (Min T)
    avg_diff = np.mean(diff_frame)
    if avg_diff < MIN_TEMP_FILTER:
        return False

    # 2. Otsu's Binarization Check
    # Normalize the float difference image to 8-bit for Otsu
    diff_normalized = cv2.normalize(diff_frame, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    _, otsu_binary = cv2.threshold(diff_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    class1_temps = diff_frame[otsu_binary == 0]
    class2_temps = diff_frame[otsu_binary == 255]
    
    if len(class1_temps) == 0 or len(class2_temps) == 0:
         return False

    temp_class1_mean = np.mean(class1_temps)
    temp_class2_mean = np.mean(class2_temps)
    
    # Check if difference between class means is greater than 0.75C
    if np.abs(temp_class2_mean - temp_class1_mean) < OTSU_DIFF_THRESHOLD:
        return False
        
    return True