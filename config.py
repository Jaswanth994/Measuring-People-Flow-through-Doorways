# config.py
import os

# --- Hardware Constants ---
GRID_SIZE = 8
TOTAL_PIXELS = GRID_SIZE * GRID_SIZE
FRAME_RATE = 10  # Hz [cite: 123]
FRAME_DELAY_MS = int(1000 / FRAME_RATE)

# --- Algorithm Constants (Based on Paper) ---
BACKGROUND_FRAMES = 250   # T_bg number of frames suggested for background calculation [cite: 235]
MIN_TEMP_FILTER = 0.25    # Min average frame temperature difference (in °C) for human presence [cite: 283]
OTSU_DIFF_THRESHOLD = 0.75 # Min class difference (in °C) for Otsu binarization validation [cite: 280]
MIN_PIXEL_AREA = 1        # Minimum pixels for a blob to be considered a body (practical value)
LARGE_BLOB_AREA = 0.3 * TOTAL_PIXELS  # 30% of frame area threshold for potential multi-person split [cite: 295]
SMALL_BODY_AREA = 0.1 * TOTAL_PIXELS  # 10% of frame area threshold for splitting logic [cite: 297, 298]

# --- Tracking Constraints (Based on Paper) ---
SPATIAL_THRESHOLD_COLS = 0.1 * GRID_SIZE  # 10% of frame width for spatial matching [cite: 310]
TEMP_THRESHOLD_DIFF = 1.0                 # Max temperature difference (in °C) for matching bodies [cite: 311]
TEMPORAL_THRESHOLD_FRAMES = 5             # Max frame difference for temporal matching (less than 5 frames) [cite: 312]

# --- File Paths ---
DATA_DIR = 'data'
BACKGROUND_FILE = os.path.join(DATA_DIR, "background.npy")
