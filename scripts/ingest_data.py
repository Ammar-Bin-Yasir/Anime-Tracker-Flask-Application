import pandas as pd
import sqlite3
import os

def ingest_anime_data():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, 'data', 'cleaned', 'anime-dataset-2023.csv')
    db_path = os.path.join(base_dir, 'anime_app.db')

    print(f"Reading CSV from: {csv_path}")
    
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print("Error: CSV file not found.")
        return

    # Rename columns to match DB schema
    # CSV headers: anime_id, Name, English name, Other name, Score, Genres, Synopsis, Type, Episodes, Aired, Premiered, Status, Producers, Licensors, Studios, Source, Duration, Rating, Rank, Popularity, Favorites, Scored By, Members, Image URL
    column_mapping = {
        'anime_id': 'anime_id',
        'Name': 'name',
        'English name': 'english_name',
        'Other name': 'other_name',
        'Score': 'score',
        'Genres': 'genres',
        'Synopsis': 'synopsis',
        'Type': 'type',
        'Episodes': 'episodes',
        'Aired': 'aired',
        'Premiered': 'premiered',
        'Status': 'status',
        'Producers': 'producers',
        'Licensors': 'licensors',
        'Studios': 'studios',
        'Source': 'source',
        'Duration': 'duration',
        'Rating': 'rating',
        'Rank': 'rank',
        'Popularity': 'popularity',
        'Favorites': 'favorites',
        'Scored By': 'scored_by',
        'Members': 'members',
        'Image URL': 'image_url'
    }
    
    # Select only columns that exist in mapping and rename them
    # Some CSVs might have 'UNKNOWN' or similar for missing numeric values, we need to handle that.
    # For now, we'll just rename and let sqlite handle type conversion or fail if strict.
    # Better to clean 'UNKNOWN' to None/NaN
    
    df = df.rename(columns=column_mapping)
    
    # Keep only columns that are in our schema
    expected_cols = list(column_mapping.values())
    # Filter df to only have these columns (if they exist in df)
    existing_cols = [col for col in expected_cols if col in df.columns]
    df = df[existing_cols]

    # Handle 'UNKNOWN' in numeric fields
    numeric_cols = ['score', 'rank', 'popularity', 'favorites', 'scored_by', 'members']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce') # Converts non-numeric to NaN

    print(f"Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    
    # We rely on app.py init_db to create the table, but we can also ensure it exists here or just append.
    # Since we updated app.py, we should probably run app.py's init_db logic or just assume it's there.
    # Actually, let's just use to_sql with if_exists='append' but we need to make sure the table exists.
    # Or we can use if_exists='replace' but that might wipe the schema definition if we aren't careful with types.
    # Best to append to the table created by app.py.
    
    # Let's clear the table first to avoid duplicates if re-running
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM anime")
        conn.commit()
        print("Cleared existing data from 'anime' table.")
    except sqlite3.OperationalError:
        print("Table 'anime' does not exist. Please run the app first to initialize the DB or create it manually.")
        # For this script, let's just rely on the table being there.
        # If it fails, we know we need to run app.py once.
        pass

    print("Inserting data...")
    df.to_sql('anime', conn, if_exists='append', index=False)
    
    print(f"Successfully inserted {len(df)} rows.")
    conn.close()

if __name__ == "__main__":
    ingest_anime_data()
