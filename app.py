from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore
from functools import wraps
import json
from recommender import recommender

# Database to keep user info and watchlists
def init_db():

    conn = sqlite3.connect('anime_app.db')

    # used to execute SQL commands
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')

    # Anime table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anime (
            anime_id INTEGER PRIMARY KEY,
            name TEXT,
            english_name TEXT,
            other_name TEXT,
            score REAL,
            genres TEXT,
            synopsis TEXT,
            type TEXT,
            episodes TEXT,
            aired TEXT,
            premiered TEXT,
            status TEXT,
            producers TEXT,
            licensors TEXT,
            studios TEXT,
            source TEXT,
            duration TEXT,
            rating TEXT,
            rank INTEGER,
            popularity INTEGER,
            favorites INTEGER,
            scored_by INTEGER,
            members INTEGER,
            image_url TEXT
        )
    ''')
    
    # Watchlist table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            anime_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'plan_to_watch',
            rating INTEGER,
            episodes_watched INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, anime_id)
        )
    ''')
    
    # User ratings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            anime_id INTEGER NOT NULL,
            rating REAL NOT NULL,
            review TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, anime_id)
        )
    ''')
    
    # confirm  
    conn.commit()
    
    conn.close()
    
# Use function to query the database
def get_db_connection():
    conn = sqlite3.connect('anime_app.db')

    # Return rows as dictionaries instead of just tuples
    conn.row_factory = sqlite3.Row
    
    return conn


# For 1 time login
def login_required(f):
    # special decorator that keeps the original name intact
    @wraps(f)

    # our addition to the function
    def decorated_function(*args, **kwargs):

        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        
        # if user passed the check, call the original function and return its result to decorated_function
        return f(*args, **kwargs)
    
    # return the new function
    return decorated_function

# Jinja filter to display timesince {{ some_date|timesince }}
def timesince(dt, default="just now"):
    if not dt:
        return default
        
    # if the time given is a string, parse it to datetime        
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return default

    # current time in UTC
    now = datetime.utcnow()

    diff = now - dt
    
    periods = (
        (diff.days // 365, "year", "years"),
        (diff.days // 30, "month", "months"),
        (diff.days // 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds // 3600, "hour", "hours"),
        (diff.seconds // 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )
    
    for period, singular, plural in periods:
        if period:
            return "%d %s" % (period, singular if period == 1 else plural)
    return default

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.jinja_env.globals.update(max=max, min=min)
app.jinja_env.filters['timesince'] = timesince

# Initialize database
init_db()

# Initialize recommender system
@app.route('/')
def index():
    conn = get_db_connection()
    
    # Get top rated anime for hero section (limit 5)
    hero_anime = conn.execute('''
        SELECT *, 
        COALESCE(NULLIF(english_name, 'UNKNOWN'), NULLIF(english_name, ''), name) as display_name 
        FROM anime 
        ORDER BY score DESC 
        LIMIT 5
    ''').fetchall()
    
    # Get trending (popularity)
    trending_anime = conn.execute('''
        SELECT *, 
        COALESCE(NULLIF(english_name, 'UNKNOWN'), NULLIF(english_name, ''), name) as display_name 
        FROM anime 
        ORDER BY popularity ASC 
        LIMIT 12
    ''').fetchall()
    
    # Get top rated (score)
    top_anime = conn.execute('''
        SELECT *, 
        COALESCE(NULLIF(english_name, 'UNKNOWN'), NULLIF(english_name, ''), name) as display_name 
        FROM anime 
        ORDER BY score DESC 
        LIMIT 12
    ''').fetchall()
    
    conn.close()

    return render_template("index.html", 
                           hero_anime=hero_anime, 
                           trending_anime=trending_anime,
                           top_anime=top_anime)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')

        if not username or not email or not password or not confirmation:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirmation:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')

        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                           (username, email, hashed_password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
            return render_template('register.html')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Please provide both username and password.', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            
            # Update last login
            conn = get_db_connection()
            conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
            conn.commit()
            conn.close()
            
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/recommendations')
@login_required
def recommendations():
    conn = get_db_connection()
    
    # Get user's last watched/liked anime
    user_anime = conn.execute('''
        SELECT anime_id FROM watchlist 
        WHERE user_id = ? AND (status = 'completed' OR status = 'watching')
        ORDER BY updated_at DESC LIMIT 3
    ''', (session['user_id'],)).fetchall()
    
    rec_ids = []
    seen_ids = set()
    
    # Add user's watched anime to seen set to avoid recommending what they already watched
    watched_ids = conn.execute('SELECT anime_id FROM watchlist WHERE user_id = ?', (session['user_id'],)).fetchall()
    for row in watched_ids:
        seen_ids.add(row['anime_id'])
    
    for item in user_anime:
        ids = recommender.get_recommendations(item['anime_id'], n=5)
        for rid in ids:
            if rid not in seen_ids:
                rec_ids.append(rid)
                seen_ids.add(rid)
    
    # Fetch details for recommendations
    rec_anime = []
    if rec_ids:
        placeholders = ','.join('?' for _ in rec_ids)
        rec_anime = conn.execute(f'''
            SELECT *,
            COALESCE(NULLIF(english_name, 'UNKNOWN'), NULLIF(english_name, ''), name) as display_name
            FROM anime WHERE anime_id IN ({placeholders})
        ''', rec_ids).fetchall()
        
    conn.close()
    return render_template('recommendations.html', recommendations=rec_anime)

@app.route('/api/search_suggestions')
def search_suggestions():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
        
    conn = get_db_connection()
    search_term = f'%{query}%'
    results = conn.execute('''
        SELECT anime_id, name, image_url, type, score,
        COALESCE(NULLIF(english_name, 'UNKNOWN'), NULLIF(english_name, ''), name) as display_name
        FROM anime 
        WHERE name LIKE ? OR english_name LIKE ? 
        LIMIT 5
    ''', (search_term, search_term)).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in results])

@app.route('/search', methods=['GET', 'POST'])
def search():
    query = request.args.get('q', '')
    genre = request.args.get('genre', '')
    
    conn = get_db_connection()
    
    if query:
        search_term = f'%{query}%'
        results = conn.execute('''
            SELECT *,
            COALESCE(NULLIF(english_name, 'UNKNOWN'), NULLIF(english_name, ''), name) as display_name 
            FROM anime 
            WHERE name LIKE ? OR english_name LIKE ? OR other_name LIKE ?
            LIMIT 50
        ''', (search_term, search_term, search_term)).fetchall()
    elif genre:
        search_term = f'%{genre}%'
        results = conn.execute('''
            SELECT *,
            COALESCE(NULLIF(english_name, 'UNKNOWN'), NULLIF(english_name, ''), name) as display_name 
            FROM anime 
            WHERE genres LIKE ?
            LIMIT 50
        ''', (search_term,)).fetchall()
    else:
        results = []
        
    conn.close()
    return render_template('search.html', results=results, query=query, genre=genre)

@app.route('/watchlist')
@login_required
def watchlist():
    conn = get_db_connection()
    
    watchlist_items = conn.execute('''
        SELECT w.*, a.name, a.english_name, a.image_url, a.score, a.episodes,
        COALESCE(NULLIF(a.english_name, 'UNKNOWN'), NULLIF(a.english_name, ''), a.name) as display_name
        FROM watchlist w
        JOIN anime a ON w.anime_id = a.anime_id
        WHERE w.user_id = ?
        ORDER BY w.updated_at DESC
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    # Group by status
    grouped_watchlist = {
        'watching': [],
        'completed': [],
        'plan_to_watch': [],
        'dropped': [],
        'on_hold': []
    }
    
    for item in watchlist_items:
        status = item['status']
        if status in grouped_watchlist:
            grouped_watchlist[status].append(item)
            
    return render_template('watchlist.html', watchlist=grouped_watchlist)

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Get stats
    watchlist_counts = conn.execute('''
        SELECT status, COUNT(*) as count 
        FROM watchlist 
        WHERE user_id = ? 
        GROUP BY status
    ''', (session['user_id'],)).fetchall()
    
    stats = {row['status']: row['count'] for row in watchlist_counts}
    
    conn.close()
    return render_template('profile.html', user=user, stats=stats)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/anime/<int:anime_id>')
def anime_detail(anime_id):
    conn = get_db_connection()
    anime = conn.execute('''
        SELECT *,
        COALESCE(NULLIF(english_name, 'UNKNOWN'), NULLIF(english_name, ''), name) as display_name
        FROM anime WHERE anime_id = ?
    ''', (anime_id,)).fetchone()
    
    in_watchlist = False
    watchlist_item = None
    
    if 'user_id' in session:
        watchlist_item = conn.execute('''
            SELECT * FROM watchlist WHERE user_id = ? AND anime_id = ?
        ''', (session['user_id'], anime_id)).fetchone()
        if watchlist_item:
            in_watchlist = True
            
    # Get similar anime
    similar_ids = recommender.get_recommendations(anime_id, n=6)
    similar_anime = []
    if similar_ids:
        placeholders = ','.join('?' for _ in similar_ids)
        similar_anime = conn.execute(f'''
            SELECT *,
            COALESCE(NULLIF(english_name, 'UNKNOWN'), NULLIF(english_name, ''), name) as display_name
            FROM anime WHERE anime_id IN ({placeholders})
        ''', similar_ids).fetchall()

    conn.close()
    
    if not anime:
        return "Anime not found", 404
        
    return render_template('anime_detail.html', anime=anime, in_watchlist=in_watchlist, watchlist_item=watchlist_item, similar_anime=similar_anime)

# API Routes for AJAX requests
@app.route('/api/watchlist/add/<int:anime_id>', methods=['POST'])
@login_required
def api_add_to_watchlist(anime_id):
    status = request.form.get('status', 'plan_to_watch')
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO watchlist (user_id, anime_id, status) 
            VALUES (?, ?, ?)
        ''', (session['user_id'], anime_id, status))
        conn.commit()
        return jsonify({'success': True, 'message': 'Added to watchlist successfully!'})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Anime already in watchlist'}), 400
    finally:
        conn.close()

@app.route('/api/watchlist/remove/<int:anime_id>', methods=['POST'])
@login_required
def api_remove_from_watchlist(anime_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM watchlist WHERE user_id = ? AND anime_id = ?', (session['user_id'], anime_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Removed from watchlist'})

@app.route('/api/watchlist/update/<int:anime_id>', methods=['POST'])
@login_required
def api_update_watchlist_status(anime_id):
    status = request.form.get('status')
    rating = request.form.get('rating')
    episodes_watched = request.form.get('episodes_watched')
    
    conn = get_db_connection()
    
    if status:
        conn.execute('UPDATE watchlist SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND anime_id = ?', 
                     (status, session['user_id'], anime_id))
    
    if rating:
        conn.execute('UPDATE watchlist SET rating = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND anime_id = ?', 
                     (rating, session['user_id'], anime_id))
                     
    if episodes_watched:
        conn.execute('UPDATE watchlist SET episodes_watched = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND anime_id = ?', 
                     (episodes_watched, session['user_id'], anime_id))
                     
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Watchlist updated'})



# Helper to get all genres (cached)
ALL_GENRES = None

def get_all_genres():
    global ALL_GENRES
    if ALL_GENRES is not None:
        return ALL_GENRES
        
    try:
        conn = get_db_connection()
        genres_data = conn.execute("SELECT DISTINCT genres FROM anime").fetchall()
        conn.close()
        
        unique_genres = set()
        for row in genres_data:
            if row['genres']:
                # Split comma-separated genres
                parts = [g.strip() for g in row['genres'].split(',')]
                unique_genres.update(parts)
        
        ALL_GENRES = sorted(list(unique_genres))
        # Filter out empty strings if any
        ALL_GENRES = [g for g in ALL_GENRES if g]
        return ALL_GENRES
    except Exception as e:
        print(f"Error fetching genres: {e}")
        return []

# Add this to your routes or context processor
@app.context_processor
def inject_genres():
    return dict(genres=get_all_genres())

@app.route('/browse')
def browse_all():
    page = request.args.get('page', 1, type=int)
    per_page = 24
    
    # Filters
    sort_by = request.args.get('sort', 'name') # name, score, popularity
    # genre_filter is now a list for multi-select
    genre_filters = request.args.getlist('genre')
    type_filter = request.args.get('type', '')
    rated_filter = request.args.get('rated', '')
    score_filter = request.args.get('score', 0, type=float)
    
    conn = get_db_connection()
    
    # Base query
    query = "SELECT *, COALESCE(NULLIF(english_name, 'UNKNOWN'), NULLIF(english_name, ''), name) as display_name FROM anime WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM anime WHERE 1=1"
    params = []
    
    # Apply Filters
    if genre_filters:
        # Filter out empty strings if any came through
        genre_filters = [g for g in genre_filters if g]
        for g in genre_filters:
            query += " AND genres LIKE ?"
            count_query += " AND genres LIKE ?"
            params.append(f'%{g}%')
        
    if type_filter:
        query += " AND type = ?"
        count_query += " AND type = ?"
        params.append(type_filter)
        
    if rated_filter:
        query += " AND rating = ?"
        count_query += " AND rating = ?"
        params.append(rated_filter)
        
    if score_filter > 0:
        query += " AND score >= ?"
        count_query += " AND score >= ?"
        params.append(score_filter)
        
    # Apply Sorting
    if sort_by == 'score':
        query += " ORDER BY score DESC, display_name ASC"
    elif sort_by == 'popularity':
        query += " ORDER BY popularity ASC" 
    else:
        query += " ORDER BY display_name ASC"
        
    # Pagination
    offset = (page - 1) * per_page
    query += " LIMIT ? OFFSET ?"
    query_params = params + [per_page, offset]
    
    # Execute
    total_anime = conn.execute(count_query, params).fetchone()[0]
    anime_list = conn.execute(query, query_params).fetchall()
    
    conn.close()
    
    total_pages = (total_anime + per_page - 1) // per_page
    
    return render_template('browse.html', 
                           anime_list=anime_list, 
                           page=page, 
                           total_pages=total_pages,
                           total_anime=total_anime,
                           current_sort=sort_by,
                           current_genres=genre_filters,
                           current_type=type_filter,
                           current_rated=rated_filter,
                           current_score=score_filter)
        
    # Pagination
    offset = (page - 1) * per_page
    query += " LIMIT ? OFFSET ?"
    query_params = params + [per_page, offset]
    
    # Execute
    total_anime = conn.execute(count_query, params).fetchone()[0]
    anime_list = conn.execute(query, query_params).fetchall()
    
    conn.close()
    
    total_pages = (total_anime + per_page - 1) // per_page
    
    return render_template('browse.html', 
                           anime_list=anime_list, 
                           page=page, 
                           total_pages=total_pages,
                           total_anime=total_anime,
                           current_sort=sort_by,
                           current_genre=genre_filter,
                           current_type=type_filter)

if __name__ == '__main__':
    app.run(debug=True)