import pandas as pd
import os
import sys

# Set encoding to utf-8 for console output
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = 'data'
FILES = {
    'anime': 'anime-dataset-2023.csv',
    'users': 'users-details-2023.csv',
    'scores': 'users-score-2023.csv'
}

def analyze_file(name, filename):
    path = os.path.join(DATA_DIR, filename)
    print(f"\n{'='*50}")
    print(f"Analyzing {name} ({filename})")
    print(f"{'='*50}")

    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    try:
        # Try reading with default encoding first, then fallback
        try:
            df = pd.read_csv(path)
        except UnicodeDecodeError:
            print("UTF-8 decode error, trying 'latin1'...")
            df = pd.read_csv(path, encoding='latin1')
            
        print(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
        print("\n--- Columns ---")
        print(df.columns.tolist())
        
        print("\n--- Missing Values ---")
        missing = df.isnull().sum()
        print(missing[missing > 0])
        
        print("\n--- Duplicates ---")
        duplicates = df.duplicated().sum()
        print(f"Total Duplicate Rows: {duplicates}")

        # Specific checks based on file type
        if name == 'anime':
            print("\n--- Anime Specific Checks ---")
            # Check for unique anime_id
            if 'anime_id' in df.columns:
                unique_ids = df['anime_id'].nunique()
                print(f"Unique Anime IDs: {unique_ids}")
                if unique_ids != df.shape[0]:
                    print(f"WARNING: Duplicate Anime IDs found! ({df.shape[0] - unique_ids})")
            
            # Check for 'UNKNOWN' values often used as placeholders
            unknown_check = (df == 'UNKNOWN').sum()
            print("\n'UNKNOWN' values count:")
            print(unknown_check[unknown_check > 0])

        elif name == 'users':
            print("\n--- Users Specific Checks ---")
            if 'user_id' in df.columns:
                unique_users = df['user_id'].nunique()
                print(f"Unique User IDs: {unique_users}")
                if unique_users != df.shape[0]:
                    print(f"WARNING: Duplicate User IDs found!")

        elif name == 'scores':
            print("\n--- Scores Specific Checks ---")
            if 'rating' in df.columns:
                print("\nRating Distribution:")
                print(df['rating'].value_counts().sort_index())
                
    except Exception as e:
        print(f"Error checking file {filename}: {e}")

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        print(f"Directory '{DATA_DIR}' not found.")
    else:
        for name, filename in FILES.items():
            analyze_file(name, filename)
