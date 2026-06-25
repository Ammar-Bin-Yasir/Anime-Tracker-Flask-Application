import pandas as pd
import numpy as np
import os
import sys

# Set encoding to utf-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = 'data'
CLEAN_DIR = os.path.join(DATA_DIR, 'cleaned')
os.makedirs(CLEAN_DIR, exist_ok=True)

FILES = {
    'anime': 'anime-dataset-2023.csv',
    'users': 'users-details-2023.csv',
    'scores': 'users-score-2023.csv'
}

def clean_anime(df):
    print("Cleaning Anime Data...")
    initial_rows = len(df)
    
    # 1. Replace 'UNKNOWN' with NaN
    df = df.replace('UNKNOWN', np.nan)
    
    # 2. Drop duplicates
    if 'anime_id' in df.columns:
        df = df.drop_duplicates(subset=['anime_id'])
    
    # 3. Convert 'episodes' to numeric, coercing errors (e.g. 'Unknown') to NaN
    if 'Episodes' in df.columns:
        df['Episodes'] = pd.to_numeric(df['Episodes'], errors='coerce')
        
    # 4. Fill critical missing values or drop if essential
    # For synopsis, fill with empty string
    if 'Synopsis' in df.columns:
        df['Synopsis'] = df['Synopsis'].fillna('')
    
    print(f"Dropped {initial_rows - len(df)} duplicate rows.")
    return df

def clean_users(df):
    print("Cleaning User Data...")
    
    # 1. Fill missing gender/location
    if 'Gender' in df.columns:
        df['Gender'] = df['Gender'].fillna('Non-Specified')
    if 'Location' in df.columns:
        df['Location'] = df['Location'].fillna('Unknown')
        
    return df

def clean_scores(df):
    print("Cleaning Scores Data...")
    initial_rows = len(df)
    
    # 1. Drop rows with missing Username
    if 'Username' in df.columns:
        df = df.dropna(subset=['Username'])
        
    # 2. Ensure rating is valid (1-10)
    # Some datasets might have 0 or -1 for "plan to watch" but usually scores are 1-10
    if 'rating' in df.columns:
        # Keep only valid ratings if strictly analyzing scores
        # But if -1 represents something else, we might want to keep it.
        # Assuming 1-10 based on analysis.
        pass 
        
    print(f"Dropped {initial_rows - len(df)} rows with missing user info.")
    return df

def process_file(name, filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        try:
            df = pd.read_csv(path)
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding='latin1')
            
        if name == 'anime':
            df = clean_anime(df)
        elif name == 'users':
            # df = clean_users(df)
            print("Skipping users (already cleaned)")
            return
        elif name == 'scores':
            # df = clean_scores(df)
            print("Skipping scores (already cleaned)")
            return
            
        # Save to cleaned directory
        output_path = os.path.join(CLEAN_DIR, filename)
        df.to_csv(output_path, index=False)
        print(f"Saved cleaned file to {output_path}")
        
    except Exception as e:
        print(f"Error cleaning {filename}: {e}")

if __name__ == "__main__":
    for name, filename in FILES.items():
        process_file(name, filename)
