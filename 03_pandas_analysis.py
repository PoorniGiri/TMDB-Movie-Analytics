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

    print("==================================================")
    print("  TMDB MOVIE ANALYTICS - PANDAS ANALYSIS (10/10)  ")
    print("==================================================\n")

    # Load Datasets
    movies_df = pd.read_csv(os.path.join(data_dir, 'movies.csv'))
    genres_df = pd.read_csv(os.path.join(data_dir, 'genres.csv'))
    movie_genres_df = pd.read_csv(os.path.join(data_dir, 'movie_genres.csv'))
    cast_df = pd.read_csv(os.path.join(data_dir, 'cast.csv'))
    crew_df = pd.read_csv(os.path.join(data_dir, 'crew.csv'))

    movies_df['release_date'] = pd.to_datetime(movies_df['release_date'], errors='coerce')

    # Question 1: Total Unique Counts
    print("--- 1. Unique Entity Counts Across Dataset ---")
    print(f"Movies: {movies_df['movie_id'].nunique():,}")
    print(f"Genres: {genres_df['genre_id'].nunique()}")
    print(f"Cast Members: {cast_df['person_id'].nunique():,}")
    print(f"Crew Members: {crew_df['person_id'].nunique():,}\n")

    # Question 2: Zero Financials Audit
    print("--- 2. Missing or $0 Financial Records Audit ---")
    zero_b = (movies_df['budget'] == 0).sum()
    zero_r = (movies_df['revenue'] == 0).sum()
    valid_fin = movies_df[(movies_df['budget'] > 0) & (movies_df['revenue'] > 0)].copy()
    print(f"$0 Budget Movies: {zero_b:,}")
    print(f"$0 Revenue Movies: {zero_r:,}")
    print(f"Valid Financial Records (Budget & Revenue > 0): {len(valid_fin):,}\n")

    # Question 3: Profit & ROI Calculation
    print("--- 3. Profit & ROI Calculation (Top 5 Sample) ---")
    valid_fin['profit'] = valid_fin['revenue'] - valid_fin['budget']
    valid_fin['roi_percent'] = (valid_fin['profit'] / valid_fin['budget']) * 100
    print(valid_fin[['title', 'budget', 'revenue', 'profit', 'roi_percent']].head().to_string(index=False))
    print("\n")

    # Question 4: Top 15 Movies by ROI (Budget >= $1 Million)
    print("--- 4. Top 15 Movies by ROI (Budget >= $1,000,000) ---")
    roi_1m = valid_fin[valid_fin['budget'] >= 1000000].sort_values(by='roi_percent', ascending=False).head(15)
    print(roi_1m[['title', 'release_date', 'budget', 'revenue', 'roi_percent']].to_string(index=False))
    print("\n")

    # Question 5: Annual Release Output & Peak Year
    print("--- 5. Annual Output Trends & Peak Release Year ---")
    movies_df['release_year'] = movies_df['release_date'].dt.year
    yearly = movies_df['release_year'].value_counts().sort_index()
    peak_year = int(yearly.idxmax())
    print(f"Peak Output Year: {peak_year} ({yearly.max()} movies released)\n")

    # Question 6: Runtime Outliers Identification (IQR Method)
    print("--- 6. Runtime Outliers Detection (IQR Method) ---")
    runtimes = movies_df[movies_df['runtime'] > 0]['runtime']
    Q1, Q3 = runtimes.quantile(0.25), runtimes.quantile(0.75)
    IQR = Q3 - Q1
    lower_b, upper_b = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
    outliers = movies_df[(movies_df['runtime'] < lower_b) | (movies_df['runtime'] > upper_b)]
    print(f"Q1: {Q1:.1f}m, Q3: {Q3:.1f}m, IQR: {IQR:.1f}m")
    print(f"Outlier Bounds: < {lower_b:.1f}m or > {upper_b:.1f}m")
    print(f"Total Runtime Outliers Detected: {len(outliers)}\n")

    # Question 7: Primary Genre Popularity Comparison
    print("--- 7. Primary Genre Average Popularity ---")
    merged_mg = movie_genres_df.merge(genres_df, on='genre_id')
    primary_g = merged_mg.groupby('movie_id').first().reset_index()
    genre_pop = movies_df.merge(primary_g[['movie_id', 'genre_name']], on='movie_id')
    avg_pop = genre_pop.groupby('genre_name')['popularity'].mean().sort_values(ascending=False)
    print(avg_pop.head(10).to_string())
    print("\n")

    # Question 8: Top 10 Most Prolific Cast Members & Ratings
    print("--- 8. Top 10 Most Prolific Actors & Avg Ratings ---")
    actor_m = cast_df.merge(movies_df, on='movie_id')
    prolific = actor_m.groupby('actor_name').agg(
        movie_count=('movie_id', 'nunique'),
        avg_rating=('vote_average', 'mean')
    ).reset_index().sort_values(by='movie_count', ascending=False).head(10)
    print(prolific.to_string(index=False))
    print("\n")

    # Question 9: Duplicate Titles & Remakes Checking
    print("--- 9. Duplicate Titles & Remakes Analysis ---")
    dup_counts = movies_df['title'].value_counts()
    reused_titles = dup_counts[dup_counts > 1].index
    print(f"Total Recurring Titles Found: {len(reused_titles)}")
    print(movies_df[movies_df['title'].isin(reused_titles)].sort_values(by='title')[['title', 'release_date', 'vote_average']].head(10).to_string(index=False))
    print("\n")

    # Question 10: Popularity vs. Vote Count Ratio Analysis
    print("--- 10. Popularity vs. Vote Count Ratio (Hype Index) ---")
    pop_v = movies_df[(movies_df['popularity'] > 0) & (movies_df['vote_count'] > 0)].copy()
    pop_v['pop_vote_ratio'] = pop_v['popularity'] / (pop_v['vote_count'] + 1)
    top_hype = pop_v.sort_values(by='pop_vote_ratio', ascending=False).head(10)
    print(top_hype[['title', 'popularity', 'vote_count', 'pop_vote_ratio']].to_string(index=False))
    print("\n")

    print("==================================================")
    print("  ALL 10 PANDAS ANALYSIS QUESTIONS COMPLETED!      ")
    print("==================================================")

if __name__ == '__main__':
    run_pandas_analysis()
