# src/main.py

import os
import sys
import numpy as np
import shutil # Import the shutil library for directory operations

#  Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src import config
from src import utils
from src import data_loader
from src import people_counter
from src import visualization

def main():
    """Main function to orchestrate the people counting process."""
    
    # Automatically delete and recreate the outputs folder ---
    if os.path.exists(config.OUTPUTS_DIR):
        print(f"Removing existing outputs directory: {config.OUTPUTS_DIR}")
        shutil.rmtree(config.OUTPUTS_DIR)
    
    # Ensure the main output directory exists
    utils.ensure_dir_exists(config.OUTPUTS_DIR)
    
    print("Calculating initial background temperature...")
    df_0_person = data_loader.load_data(config.FILE_0_PERSON)
    background_profile = people_counter.calculate_initial_background(df_0_person)

    if background_profile is None:
        print("Could not calculate background. Exiting.")
        return

    print("Initial background calculation complete.")
    print("-" * 30)

    datasets_to_process = [
        (config.FILE_1_PERSON, 1),
        (config.FILE_2_PERSON, 2)
    ]

    for filepath, actual_count in datasets_to_process:
        filename = os.path.basename(filepath)
        print(f"Processing file: {filename} (Actual Count: {actual_count})")
        
        df = data_loader.load_data(filepath)
        if df is None:
            continue

        output_subdir = os.path.join(config.OUTPUTS_DIR, os.path.splitext(filename)[0])
        utils.ensure_dir_exists(output_subdir)
        
        eligible_frames = df.iloc[config.START_FRAME:]
        
        if len(eligible_frames) < config.NUM_RANDOM_SAMPLES:
            print(f"  -> Skipping {filename}, not enough frames ({len(eligible_frames)}) to sample {config.NUM_RANDOM_SAMPLES} random cases.")
            continue
        
        df_to_process = eligible_frames.sample(n=config.NUM_RANDOM_SAMPLES)
        print(f"  -> Processing {config.NUM_RANDOM_SAMPLES} random frames (from frame {config.START_FRAME} onwards)...")

        for index, row in df_to_process.iterrows():
            frame = row['gridEye_array']
            timestamp = row['timestamp']
            
            est_count, raw_frame, fg, final_blobs = people_counter.count_people(frame, background_profile)

            if est_count == 0:
                background_profile = (1 - config.ADAPTIVE_BG_RATE) * background_profile + (config.ADAPTIVE_BG_RATE * frame)

            visualization.save_visualization(
                output_dir=output_subdir,
                frame_number=index,
                frame=raw_frame,
                foreground=fg,
                final_blobs=final_blobs,
                est_count=est_count,
                actual_count=actual_count,
                timestamp=timestamp
            )
            
        print(f"  -> Finished processing. {config.NUM_RANDOM_SAMPLES} visualizations saved in: {output_subdir}")
        print("-" * 30)

if __name__ == '__main__':
    main()