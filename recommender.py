import pandas as pd
import sqlite3
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

class AnimeRecommender:
    def __init__(self, db_path='anime_app.db'):
        # Handle path relative to this file if needed, or absolute
        if not os.path.isabs(db_path):
             base_dir = os.path.dirname(os.path.abspath(__file__))
             db_path = os.path.join(base_dir, db_path)
             
        self.db_path = db_path
        self.df = None
        self.tfidf = None
        self.tfidf_matrix = None
        self.indices = None
        self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT anime_id, name, genres, synopsis FROM anime"
            self.df = pd.read_sql_query(query, conn)
            conn.close()
        except Exception as e:
            print(f"Error loading data: {e}")
            return

        # Fill NaN
        self.df['genres'] = self.df['genres'].fillna('')
        self.df['synopsis'] = self.df['synopsis'].fillna('')
        
        # Create content string
        self.df['content'] = self.df['genres'] + " " + self.df['synopsis']
        
        # Initialize TF-IDF
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.tfidf.fit_transform(self.df['content'])
        
        # Map anime_id to index
        self.indices = pd.Series(self.df.index, index=self.df['anime_id']).drop_duplicates()

    def get_recommendations(self, anime_id, n=10):
        if self.df is None or self.indices is None:
            return []
            
        if anime_id not in self.indices:
            return []
            
        idx = self.indices[anime_id]
        
        # Compute cosine similarity between this anime and all others
        # linear_kernel is equivalent to cosine_similarity for normalized vectors (TF-IDF is normalized)
        cosine_sim = linear_kernel(self.tfidf_matrix[idx], self.tfidf_matrix)
        
        # Get scores
        sim_scores = list(enumerate(cosine_sim[0]))
        
        # Sort
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get top n (excluding self)
        sim_scores = sim_scores[1:n+1]
        
        # Get indices
        anime_indices = [i[0] for i in sim_scores]
        
        # Return anime_ids
        return self.df['anime_id'].iloc[anime_indices].tolist()

# Global instance
recommender = AnimeRecommender()
