import sqlite3
import pandas as pd

def inspect_titles():
    conn = sqlite3.connect('anime_app.db')
    
    print("--- Titles with Quotes ---")
    quotes = conn.execute("SELECT anime_id, name, english_name FROM anime WHERE name LIKE '%\"%' OR english_name LIKE '%\"%' LIMIT 20").fetchall()
    for row in quotes:
        print(row)
        
    print("\n--- Titles with # ---")
    hashes = conn.execute("SELECT anime_id, name, english_name FROM anime WHERE name LIKE '%#%' OR english_name LIKE '%#%' LIMIT 20").fetchall()
    for row in hashes:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    inspect_titles()
