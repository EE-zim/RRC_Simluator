
"""
Utility helpers for loading JSON and CSV files.
"""
=======
import json
import os
import pandas as pd


def load_json_data(file_path):
    """Load JSON data from a file if it exists."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {file_path}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    else:
        print(f"Warning: File not found - {file_path}")
    return None


def load_csv_data(file_path):
    """Load CSV data from a file if it exists."""
    if os.path.exists(file_path):
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    else:
        print(f"Warning: File not found - {file_path}")
    return None
