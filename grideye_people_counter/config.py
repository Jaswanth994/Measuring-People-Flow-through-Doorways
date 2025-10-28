# config.py
from collections import deque

# Sensor / Timing
FRAME_INTERVAL = 0.25     # seconds between frames
BG_FRAMES = 200           # frames to build initial background

# Thresholding
TEMP_THRESHOLD = 1.2      # degrees above background
MIN_BLOB_SIZE = 3
MAX_BLOB_SIZE = 50

# Tracking
FRAME_BUFFER_SIZE = 12
ENTRY_LINE_X = 4          # midline of 8x8 sensor (column index)
DIRECTION_SMOOTH = 4      # frames to confirm motion direction

# Debug / Logging
DEBUG = True
