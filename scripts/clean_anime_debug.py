import pandas as pd
import numpy as np
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = 'data'
CLEAN_DIR = os.path.join(DATA_DIR, 'cleaned')
os.makedirs(CLEAN_DIR, exist_ok=True)
FILENAME = 'anime-dataset-2023.csv'

def clean_anime(df):
    print("Cleaning Anime Data...")
    initial_rows = len(df)
    df = df.replace('UNKNOWN', np.nan)
    if 'anime_id' in df.columns:
        df = df.drop_duplicates(subset=['anime_id'])
    if 'episodes' in df.columns:
        df['episodes'] = pd.to_numeric(df['episodes'], errors='coerce')
    df['synopsis'] = df['synopsis'].fillna('')
    print(f"Dropped {initial_rows - len(df)} duplicate rows.")
    return df

def process():
    path = os.path.join(DATA_DIR, FILENAME)
    print(f"Reading {path}...")
    try:
        try:
            df = pd.read_csv(path)
        except UnicodeDecodeError:
            print("Unicode error, trying latin1")
            df = pd.read_csv(path, encoding='latin1')
        except Exception as e:
            print(f"Read error: {e}")
            return

        print(f"Read {len(df)} rows. Cleaning...")
        df = clean_anime(df)
        
        output_path = os.path.join(CLEAN_DIR, FILENAME)
        df.to_csv(output_path, index=False)
        print(f"Saved cleaned file to {output_path}")
        
    except Exception as e:
        print(f"Error cleaning {FILENAME}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process()
