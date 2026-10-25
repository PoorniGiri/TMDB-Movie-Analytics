import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def run_visualizations():
    data_dir = 'data'
    if not os.path.exists(os.path.join(data_dir, 'movies.csv')):
        if os.path.exists('movies.csv'):
            data_dir = '.'
        else:
            print("Error: CSV files not found.")
            return

    movies_df = pd.read_csv(os.path.join(data_dir, 'movies.csv'))
    movies_df['release_date'] = pd.to_datetime(movies_df['release_date'], errors='coerce')

    print("Generating charts...")
    
    # Chart 1: Correlation Heatmap
    num_cols = movies_df.select_dtypes(include="number").columns.drop("movie_id", errors='ignore').tolist()
    if len(num_cols) > 1:
        plt.figure(figsize=(8, 6))
        sns.heatmap(movies_df[num_cols].corr(), annot=True, fmt=".2f", cmap="coolwarm")
        plt.title("Numerical Attributes Correlation Heatmap")
        plt.tight_layout()
        plt.savefig('correlation_heatmap.png')
        plt.close()
        print("Saved correlation_heatmap.png")

    # Chart 2: Movies per year
    plt.figure(figsize=(8, 5))
    movies_per_year = movies_df.groupby(movies_df["release_date"].dt.year).size()
    plt.plot(movies_per_year.index, movies_per_year.values, marker='o', color='#1E88E5')
    plt.title("Movies Released per Year")
    plt.xlabel("Year")
    plt.ylabel("Movie Count")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig('movies_per_year.png')
    plt.close()
    print("Saved movies_per_year.png")

    print("Visualization Pipeline Complete!")

if __name__ == '__main__':
    run_visualizations()
