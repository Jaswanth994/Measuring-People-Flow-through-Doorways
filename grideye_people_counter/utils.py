# utils.py
import numpy as np

def smooth_background(bg, frame, rate=0.001):
    return (1 - rate) * bg + rate * frame
