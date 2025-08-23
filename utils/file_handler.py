# utils/file_handler.py

import os
import shutil
import pandas as pd

def save_uploaded_file(uploaded_file, save_dir="uploads"):
    """Save file uploaded via Streamlit uploader and return its path."""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def save_file(file_path, save_dir="uploads"):
    """Copy an existing local file to uploads folder and return new path."""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    dest_path = os.path.join(save_dir, os.path.basename(file_path))
    shutil.copy(file_path, dest_path)
    return dest_path


# def load_file(file_path):
#     """Load CSV file into a DataFrame (helper if needed)."""
#     return pd.read_csv(file_path)

def load_file(path):
    import pandas as pd
    try:
        df = pd.read_csv(path)

        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]

        # Expected schema
        expected_cols = ["date", "description", "category", "amount", "is_income"]

        # If CSV has fewer columns, add missing ones
        for col in expected_cols:
            if col not in df.columns:
                if col == "is_income":
                    df[col] = False
                elif col == "amount":
                    df[col] = 0.0
                else:
                    df[col] = ""

        # Reorder to match schema
        df = df[expected_cols]

        # Convert types
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

        return df

    except Exception as e:
        raise ValueError(f"Failed to process CSV: {e}")

