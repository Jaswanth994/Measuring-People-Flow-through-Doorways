# src/data_loader.py

import pandas as pd
import numpy as np

def load_data(filename):
    """
    Loads and parses Grid-EYE sensor data from an XLSX file.
    Now only loads columns that are strictly necessary.
    """
    try:
        # We don't need 'current_people_count' anymore.
        df = pd.read_excel(filename, usecols=['gridEye_array', 'timestamp'])
        df['gridEye_array'] = df['gridEye_array'].apply(lambda x: np.array(eval(x))) #converts string to list
        return df
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
        return None
    except ValueError as e:
        print(f"Error reading {filename}: {e}. Ensure it contains the required columns.")
        return None