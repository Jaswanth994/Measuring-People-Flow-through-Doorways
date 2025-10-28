# src/utils.py

import os

def ensure_dir_exists(directory_path):
    """Checks if a directory exists, and if not, creates it."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Created directory: {directory_path}")