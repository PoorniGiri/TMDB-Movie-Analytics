import os
import pandas as pd
import sqlite3

def run_data_cleaning():
    print("Starting Data Cleaning Pipeline...")
    
    data_dir = 'data'
    db_path = os.path.join(data_dir, 'tmdb_movies.db')
    
    if not os.path.exists(data_dir):
        print(f"Directory '{data_dir}' not found. Checking root directory...")
        if os.path.exists('movies.csv'):
            data_dir = '.'
            db_path = 'tmdb_movies.db'
    
    print(f"Reading CSV files from '{data_dir}'...")
    movies_df = pd.read_csv(os.path.join(data_dir, 'movies.csv'))
    genres_df = pd.read_csv(os.path.join(data_dir, 'genres.csv'))
    movie_genres_df = pd.read_csv(os.path.join(data_dir, 'movie_genres.csv'))
    cast_df = pd.read_csv(os.path.join(data_dir, 'cast.csv'))
    crew_df = pd.read_csv(os.path.join(data_dir, 'crew.csv'))
    movie_keywords_df = pd.read_csv(os.path.join(data_dir, 'movie_keywords.csv'))
    
    # 1. Type Casting & Sanitization
    print("Cleaning and casting data types...")
    # Convert release_date to string format YYYY-MM-DD for SQLite compatibility
    dt_series = pd.to_datetime(movies_df['release_date'], errors='coerce')
    movies_df['release_date'] = dt_series.dt.strftime('%Y-%m-%d')
    movies_df['movie_id'] = movies_df['movie_id'].astype(int)
    
    # Flag valid financial records
    movies_df['has_valid_financials'] = (movies_df['budget'] > 0) & (movies_df['revenue'] > 0)
    
    # Deduplicate
    movies_df = movies_df.drop_duplicates(subset=['movie_id'])
    genres_df = genres_df.drop_duplicates(subset=['genre_id'])
    
    # 2. Orphan Removal in Junction Tables
    valid_movie_ids = set(movies_df['movie_id'])
    movie_genres_df = movie_genres_df[movie_genres_df['movie_id'].isin(valid_movie_ids)]
    cast_df = cast_df[cast_df['movie_id'].isin(valid_movie_ids)]
    crew_df = crew_df[crew_df['movie_id'].isin(valid_movie_ids)]
    movie_keywords_df = movie_keywords_df[movie_keywords_df['movie_id'].isin(valid_movie_ids)]
    
    # 3. Create SQLite Database
    print(f"Creating SQLite Database at '{db_path}'...")
    conn = sqlite3.connect(db_path)
    
    movies_df.to_sql('movies', conn, if_exists='replace', index=False)
    genres_df.to_sql('genres', conn, if_exists='replace', index=False)
    movie_genres_df.to_sql('movie_genres', conn, if_exists='replace', index=False)
    cast_df.to_sql('cast', conn, if_exists='replace', index=False)
    crew_df.to_sql('crew', conn, if_exists='replace', index=False)
    movie_keywords_df.to_sql('movie_keywords', conn, if_exists='replace', index=False)
    
    conn.close()
    print("Data Cleaning & Database Build Complete!")
    print(f"Database successfully created at: {os.path.abspath(db_path)}")

if __name__ == '__main__':
    run_data_cleaning()
