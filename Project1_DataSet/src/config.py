# src/config.py

import os

# --- File Paths ---
DATA_DIR = '../data'
FILE_0_PERSON = os.path.join(DATA_DIR, '0_Person_21.xlsx')
FILE_1_PERSON = os.path.join(DATA_DIR, '1_Person_21.xlsx')
FILE_2_PERSON = os.path.join(DATA_DIR, '2_Person_21.xlsx')

# --- Processing Control ---
OUTPUTS_DIR = '../outputs'
START_FRAME = 500          # We will only sample frames *after* this one.

# --- 💡 NEW: Random Sampling ---
NUM_RANDOM_SAMPLES = 10    # The number of random frames to select and process.

# --- People Counting Parameters ---
TEMPERATURE_THRESHOLD = 1.2
MIN_BLOB_SIZE = 3
MAX_BLOB_SIZE = 50

# --- Morphological Operations ---
EROSION_ITERATIONS = 1
DILATION_ITERATIONS = 1

# --- Adaptive Background ---
ADAPTIVE_BG_RATE = 0.001