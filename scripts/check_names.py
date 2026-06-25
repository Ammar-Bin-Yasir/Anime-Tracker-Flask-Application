import sqlite3
import pandas as pd

def check_names():
    conn = sqlite3.connect('anime_app.db')
    df = pd.read_sql_query("SELECT name, english_name FROM anime LIMIT 20", conn)
    conn.close()
    print(df)

if __name__ == "__main__":
    check_names()
