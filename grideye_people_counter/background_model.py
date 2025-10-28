# background_model.py
import numpy as np
from config import BG_FRAMES
from sensor_interface import GridEyeSensor

def build_background():
    sensor = GridEyeSensor()
    frames = []
    print("[INFO] Building background model...")
    for _ in range(BG_FRAMES):
        frames.append(sensor.read_frame())
    bg = np.mean(frames, axis=0)
    print("[INFO] Background model built successfully.")
    return bg
