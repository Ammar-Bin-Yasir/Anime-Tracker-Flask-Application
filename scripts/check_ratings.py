import sqlite3

def check_ratings():
    try:
        conn = sqlite3.connect('anime_app.db')
        ratings = conn.execute("SELECT DISTINCT rating FROM anime").fetchall()
        print("--- Ratings ---")
        for r in ratings:
            print(r[0])
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ratings()
