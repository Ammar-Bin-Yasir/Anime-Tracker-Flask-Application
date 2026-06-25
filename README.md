# Anime Tracker

A full-stack web app for tracking your anime watchlist, discovering new shows, and getting personalized recommendations — built with Flask and a content-based recommendation engine using TF-IDF and cosine similarity.

![Anime Tracker Demo](demo.gif)
<!-- Screen-record yourself browsing, searching, and viewing a recommendation -->

## Features

- **Accounts & auth** — registration and login with hashed passwords (`werkzeug.security`), session-based auth, and a `login_required` decorator protecting personal pages
- **Personalized recommendations** — a content-based recommender that suggests anime similar to what you've watched, based on genre + synopsis text
- **"Similar anime"** — every anime's detail page surfaces similar titles using the same recommendation engine
- **Watchlist management** — track anime as Watching / Completed / Plan to Watch / Dropped / On Hold, with per-entry episode progress and your own rating
- **Search** — full search with live autocomplete suggestions as you type
- **Browse & filter** — paginated catalog with filtering by genre (multi-select), type, age rating, and minimum score, plus sorting by name, score, or popularity
- **Profile dashboard** — at-a-glance stats on how many anime you've watched, are watching, or have planned

## Dataset

Anime metadata comes from the [**Anime Dataset 2023**](https://www.kaggle.com/datasets/dbdmobile/myanimelist-dataset) on Kaggle, sourced from MyAnimeList — one of the largest community-maintained anime databases. The dataset spans 86 columns of metadata per title (score, genres, synopsis, studios, episode counts, popularity rank, and more); this app loads a focused subset of those fields into `anime_app.db` via the `scripts/` folder.

![Genre and score distribution](genre_score_distribution.png)

## Architecture

![Architecture diagram](architecture.png)

The Flask app is the single entry point for the browser. It delegates two different jobs to two different places: persistent data (users, the anime catalog, watchlists, ratings) lives in SQLite, while similarity search is handled entirely in memory by the recommender, which loads the anime table once at startup rather than hitting the database on every request — recomputing TF-IDF vectors per request would be wasteful since the underlying anime metadata doesn't change at runtime.

## How the recommendation engine works

![TF-IDF and cosine similarity concept](tfidf_concept.png)

The recommender (`recommender.py`) treats each anime's **genres + synopsis** as a single block of text, then uses **TF-IDF (Term Frequency–Inverse Document Frequency)** to turn that text into a numeric vector — weighting words that are distinctive to that anime's description higher than common words that appear everywhere (English stopwords are filtered out entirely).

Once every anime is represented as a vector, finding "similar anime" becomes a geometry problem: compute the **cosine similarity** between vectors — how close their *direction* is in that high-dimensional space, regardless of magnitude. Since TF-IDF vectors are already normalized, this is computed efficiently with `linear_kernel` rather than a full cosine-similarity routine.

This single engine powers two features:
1. **`/recommendations`** — pulls your 3 most recently updated "watching"/"completed" entries and finds similar anime for each, filtering out anything you've already added to your watchlist
2. **Anime detail pages** — show similar titles for whatever you're currently looking at

This is the same family of technique ("content-based filtering") used as a baseline recommendation approach in real production systems, before layering on collaborative filtering or user-behavior signals.

## Tech stack

- **Backend:** Flask, SQLite3
- **Recommendation engine:** pandas, scikit-learn (`TfidfVectorizer`, `linear_kernel`)
- **Auth:** Werkzeug security (password hashing), Flask sessions
- **Frontend:** HTML/Jinja2 templates, CSS

## Database schema

Four tables: `users` (credentials, login history), `anime` (title, genres, synopsis, score, episodes, studios, and other metadata), `watchlist` (per-user status, rating, episode progress), and `user_ratings` (standalone reviews/ratings, separate from watchlist status).

## Running it locally

```bash
git clone https://github.com/Ammar-Bin-Yasir/Anime-Tracker-Flask-Application.git
cd Anime-Tracker-Flask-Application
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`. The database initializes automatically on first run.

## Project structure

```
app.py             # routes, auth, watchlist logic, search/browse/filter
recommender.py      # TF-IDF + cosine similarity recommendation engine
templates/          # Jinja2 HTML templates
static/             # CSS, JS, images
scripts/            # data loading/setup scripts
```

## Known limitations / future improvements

- `anime_app.db` is currently committed to the repo and `SECRET_KEY` is hardcoded — both should move out before any real deployment (`.gitignore` the database, load the secret from an environment variable)
- The recommender is purely content-based (genre/synopsis text) — it doesn't yet learn from collaborative signals like "users who watched X also liked Y"
- No password reset flow yet (`/forgot_password` exists as a stub page)
- No pagination on the recommendations page itself

## Regenerating the dataset chart

The genre/score distribution chart above is generated from real queries against `anime_app.db`, not estimated. To regenerate it after the dataset changes:

```sql
SELECT
  CASE
    WHEN score < 5 THEN '< 5' WHEN score < 6 THEN '5-6' WHEN score < 7 THEN '6-7'
    WHEN score < 8 THEN '7-8' WHEN score < 9 THEN '8-9' ELSE '9-10'
  END AS bucket, COUNT(*) FROM anime WHERE score IS NOT NULL GROUP BY bucket;
```

and a short Python script counting comma-separated `genres` values with `collections.Counter`.

## Background

Originally built as a final project for [CS50's Introduction to Programming with Python](https://cs50.harvard.edu/python/).
