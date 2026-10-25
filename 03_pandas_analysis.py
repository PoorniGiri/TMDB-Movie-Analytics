import os
import pandas as pd
import numpy as np

def run_pandas_analysis():
    data_dir = 'data'
    if not os.path.exists(os.path.join(data_dir, 'movies.csv')):
        if os.path.exists('movies.csv'):
            data_dir = '.'
        else:
            print("Error: CSV files not found. Please ensure CSVs are in 'data/' subfolder.")
            return

    print("--- Loading Datasets for Pandas Analysis ---")
    movies_df = pd.read_csv(os.path.join(data_dir, 'movies.csv'))
    genres_df = pd.read_csv(os.path.join(data_dir, 'genres.csv'))
    movie_genres_df = pd.read_csv(os.path.join(data_dir, 'movie_genres.csv'))
    cast_df = pd.read_csv(os.path.join(data_dir, 'cast.csv'))
    crew_df = pd.read_csv(os.path.join(data_dir, 'crew.csv'))

    movies_df['release_date'] = pd.to_datetime(movies_df['release_date'], errors='coerce')

    print("\n1. Unique Entity Counts:")
    print(f"Movies: {movies_df['movie_id'].nunique()}, Genres: {genres_df['genre_id'].nunique()}, Cast: {cast_df['person_id'].nunique()}")

    print("\n2. $0 Financials Audit:")
    valid_fin = movies_df[(movies_df['budget'] > 0) & (movies_df['revenue'] > 0)].copy()
    print(f"Valid Financial Records: {len(valid_fin)} out of {len(movies_df)}")

    print("\n3. Profit & ROI Calculation:")
    valid_fin['profit'] = valid_fin['revenue'] - valid_fin['budget']
    valid_fin['roi'] = (valid_fin['profit'] / valid_fin['budget']) * 100
    print(valid_fin[['title', 'budget', 'revenue', 'profit', 'roi']].head())

    print("\n4. Top 5 Movies by ROI (Budget >= $1M):")
    top_roi = valid_fin[valid_fin['budget'] >= 1000000].sort_values(by='roi', ascending=False).head(5)
    print(top_roi[['title', 'budget', 'revenue', 'roi']])

    print("\n5. Peak Annual Releases:")
    yearly = movies_df.groupby(movies_df['release_date'].dt.year)['movie_id'].count()
    print(f"Peak Year: {yearly.idxmax()} with {yearly.max()} releases")

    print("\n6. Runtime Outliers (IQR Method):")
    Q1, Q3 = movies_df['runtime'].quantile(0.25), movies_df['runtime'].quantile(0.75)
    IQR = Q3 - Q1
    outliers = movies_df[(movies_df['runtime'] < (Q1 - 1.5*IQR)) | (movies_df['runtime'] > (Q3 + 1.5*IQR))]
    print(f"Detected {len(outliers)} runtime outliers")

    print("\n7. Duplicate Titles (Remakes/Reboots):")
    dupes = movies_df[movies_df.duplicated(subset=['title'], keep=False)]
    print(f"Found {dupes['title'].nunique()} recurring titles")

    print("\nPandas Analysis Complete!")

if __name__ == '__main__':
    run_pandas_analysis()
