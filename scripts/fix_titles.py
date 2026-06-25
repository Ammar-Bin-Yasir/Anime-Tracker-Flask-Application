import sqlite3
import re

def fix_titles():
    conn = sqlite3.connect('anime_app.db')
    cursor = conn.cursor()
    
    print("Fixing titles...")
    
    # 1. Fetch all anime
    cursor.execute("SELECT anime_id, name, english_name FROM anime")
    anime_list = cursor.fetchall()
    
    count = 0
    for anime_id, name, english_name in anime_list:
        new_name = name
        new_english = english_name
        
        # Clean 'name'
        if name:
            if name == 'UNKNOWN':
                new_name = None
            else:
                # Remove wrapping quotes
                if name.startswith('"') and name.endswith('"'):
                    new_name = name[1:-1]
                # Fix "Star"t -> "Start" (scikit-learn cleaning artifact?)
                if '"' in new_name:
                    # Specific fix for "Star"t -> Star"t -> Start? 
                    # If user saw "Star"t it means it wasn't stripped.
                    # Let's replace " with empty if it looks weird?
                    # Or just strip again.
                    pass
                
        # Clean 'english_name'
        if english_name:
            if english_name == 'UNKNOWN':
                new_english = None 
            else:
                if english_name.startswith('"') and english_name.endswith('"'):
                    new_english = english_name[1:-1]
        
        # Update if changed
        if new_name != name or new_english != english_name:
            # print(f"Updating {anime_id}: {name} -> {new_name} | {english_name} -> {new_english}")
            cursor.execute("UPDATE anime SET name = ?, english_name = ? WHERE anime_id = ?", (new_name, new_english, anime_id))
            count += 1
            
    # HARD FIX for specific known issues from screenshots/logs
    # "Star"t -> Start
    cursor.execute("UPDATE anime SET name = 'Start', english_name = 'Start' WHERE name LIKE '%\"Star\"t%' OR english_name LIKE '%\"Star\"t%'")
    
    # Fix # if it's rank artifact? 
    # User said: "titles also have "" # in them"
    # Maybe Remove # if it's just #
    
    conn.commit()
    print(f"Updated {count} titles.")
    conn.close()

if __name__ == "__main__":
    fix_titles()
