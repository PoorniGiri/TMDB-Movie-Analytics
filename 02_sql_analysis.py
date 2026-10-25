import os
import sqlite3
import pandas as pd

def run_sql_analysis():
    db_path = os.path.join('data', 'tmdb_movies.db')
    if not os.path.exists(db_path):
        if os.path.exists('tmdb_movies.db'):
            db_path = 'tmdb_movies.db'
        else:
            print("Error: tmdb_movies.db not found. Please run 01_data_cleaning.py first.")
            return
            
    conn = sqlite3.connect(db_path)
    
    queries = {
        "Q1: Action Movies Released After 2015": """
            SELECT m.movie_id, m.title, m.release_date, m.vote_average 
            FROM movies m 
            JOIN movie_genres mg ON m.movie_id = mg.movie_id 
            JOIN genres g ON mg.genre_id = g.genre_id 
            WHERE g.genre_name = 'Action' AND strftime('%Y', m.release_date) > '2015' 
            ORDER BY m.release_date DESC LIMIT 10;
        """,
        "Q2: Top 10 Highest Grossing Movies & Genres": """
            SELECT m.title, m.revenue, GROUP_CONCAT(g.genre_name, ', ') AS genres 
            FROM movies m 
            JOIN movie_genres mg ON m.movie_id = mg.movie_id 
            JOIN genres g ON mg.genre_id = g.genre_id 
            WHERE m.revenue > 0 
            GROUP BY m.movie_id 
            ORDER BY m.revenue DESC LIMIT 10;
        """,
        "Q3: Average Budget & Revenue by Genre": """
            SELECT g.genre_name, ROUND(AVG(m.budget), 2) AS avg_budget, ROUND(AVG(m.revenue), 2) AS avg_revenue 
            FROM genres g 
            JOIN movie_genres mg ON g.genre_id = mg.genre_id 
            JOIN movies m ON mg.movie_id = m.movie_id 
            WHERE m.budget > 0 AND m.revenue > 0 
            GROUP BY g.genre_name 
            ORDER BY avg_revenue DESC;
        """,
        "Q4: Top 10 Most Prolific Cast Members": """
            SELECT c.actor_name, COUNT(DISTINCT c.movie_id) AS movie_count 
            FROM cast c 
            GROUP BY c.actor_name 
            ORDER BY movie_count DESC LIMIT 10;
        """,
        "Q5: Directors with > 3 Directed Movies": """
            SELECT cr.person_name AS director_name, COUNT(DISTINCT cr.movie_id) AS directed_count 
            FROM crew cr 
            WHERE cr.job = 'Director' 
            GROUP BY cr.person_name 
            HAVING directed_count > 3 
            ORDER BY directed_count DESC;
        """,
        "Q6: Top 10 Most Frequent Keywords": """
            SELECT mk.keyword_name, COUNT(mk.movie_id) AS frequency 
            FROM movie_keywords mk 
            GROUP BY mk.keyword_name 
            ORDER BY frequency DESC LIMIT 10;
        """,
        "Q7: Above Avg Budget but Below Avg Revenue": """
            SELECT title, budget, revenue, (budget - revenue) AS loss_amount 
            FROM movies 
            WHERE budget > (SELECT AVG(budget) FROM movies WHERE budget > 0) 
              AND revenue < (SELECT AVG(revenue) FROM movies WHERE revenue > 0) 
              AND revenue > 0 
            ORDER BY loss_amount DESC LIMIT 10;
        """,
        "Q8: Cast in Christopher Nolan Films": """
            SELECT DISTINCT c.actor_name, m.title AS movie_title 
            FROM cast c 
            JOIN movies m ON c.movie_id = m.movie_id 
            JOIN crew cr ON m.movie_id = cr.movie_id 
            WHERE cr.job = 'Director' AND cr.person_name LIKE '%Christopher Nolan%' 
            ORDER BY c.actor_name LIMIT 10;
        """,
        "Q9: Highest-Rated Genre (>= 20 Movies)": """
            SELECT g.genre_name, COUNT(m.movie_id) AS movie_count, ROUND(AVG(m.vote_average), 2) AS avg_rating 
            FROM genres g 
            JOIN movie_genres mg ON g.genre_id = mg.genre_id 
            JOIN movies m ON mg.movie_id = m.movie_id 
            GROUP BY g.genre_name 
            HAVING movie_count >= 20 
            ORDER BY avg_rating DESC LIMIT 1;
        """,
        "Q10: Top 10 Movies with Most Tagged Keywords": """
            SELECT m.title, COUNT(mk.keyword_id) AS keyword_count 
            FROM movies m 
            JOIN movie_keywords mk ON m.movie_id = mk.movie_id 
            GROUP BY m.movie_id 
            ORDER BY keyword_count DESC LIMIT 10;
        """
    }
    
    print("--- Executing 10 SQL Queries ---")
    for title, q in queries.items():
        print(f"\n=== {title} ===")
        df = pd.read_sql_query(q, conn)
        print(df.head())
        
    conn.close()
    print("\nSQL Analysis Complete!")

if __name__ == '__main__':
    run_sql_analysis()
