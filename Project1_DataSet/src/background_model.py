import numpy as np

def build_background_model(df):
    if df is None or df.empty:
        raise ValueError("Background data is empty or invalid.")
    frames = np.stack(df['gridEye_array'])
    background = np.median(frames, axis=0)  # Robust to outliers
    print(f"[INFO] Background model created successfully from {frames.shape[0]} frames.")
    return background
