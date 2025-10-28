# people_counter.py
import numpy as np
import cv2
from config import TEMP_THRESHOLD, MIN_BLOB_SIZE, MAX_BLOB_SIZE

def detect_people(frame, bg):
    diff = frame - bg
    mask = np.where(diff > TEMP_THRESHOLD, 255, 0).astype(np.uint8)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    blobs = []
    for c in contours:
        area = cv2.contourArea(c)
        if MIN_BLOB_SIZE <= area <= MAX_BLOB_SIZE:
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                blobs.append((cx, cy))
    return blobs, mask
