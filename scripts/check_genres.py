import sqlite3

def check_genres():
    conn = sqlite3.connect('anime_app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT genres FROM anime")
    rows = cursor.fetchall()
    conn.close()
    
    all_genres = set()
    for row in rows:
        if row[0]:
            # genres are comma separated
            parts = [g.strip() for g in row[0].split(',')]
            all_genres.update(parts)
            
    sorted_genres = sorted(list(all_genres))
    print(f"Total Unique Genres: {len(sorted_genres)}")
    print("Example genres:", sorted_genres[:10])
    
if __name__ == "__main__":
    check_genres()
