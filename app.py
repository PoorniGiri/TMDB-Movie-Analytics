import os
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Reel Insights: TMDB Movie Analytics Hub",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Cinematic Theme with Glowing Metric Cards)
st.markdown("""
    <style>
    /* Dark Theme Base Colors */
    .stApp {
        background-color: #0b0e14;
        color: #e0e6ed;
    }
    
    /* Header Banners */
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #01b4e4, #90aea1, #d29034);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #8b9bb4;
        margin-bottom: 1.5rem;
    }
    
    /* Metric Cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #161b26 0%, #1f2636 100%);
        border: 1px solid #2a3447;
        border-radius: 10px;
        padding: 15px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetric"] label {
        color: #8b9bb4 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #01b4e4 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #111622;
        border-right: 1px solid #2a3447;
    }
    
    /* Filter Badge */
    .filter-badge {
        background-color: #1f2636;
        border: 1px solid #01b4e4;
        color: #01b4e4;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 8px;
        margin-bottom: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# Database & Data Loading Helper
@st.cache_resource
def get_db_connection():
    db_path = os.path.join('data', 'tmdb_movies.db')
    if not os.path.exists(db_path):
        if os.path.exists('tmdb_movies.db'):
            db_path = 'tmdb_movies.db'
        else:
            return None
    return sqlite3.connect(db_path, check_same_thread=False)

conn = get_db_connection()

@st.cache_data
def load_and_prep_catalog():
    data_dir = 'data'
    movies_csv = os.path.join(data_dir, 'movies.csv')
    genres_csv = os.path.join(data_dir, 'genres.csv')
    movie_genres_csv = os.path.join(data_dir, 'movie_genres.csv')
    
    if not os.path.exists(movies_csv):
        movies_csv = 'movies.csv'
        genres_csv = 'genres.csv'
        movie_genres_csv = 'movie_genres.csv'
        
    if os.path.exists(movies_csv):
        movies = pd.read_csv(movies_csv)
    elif conn is not None:
        movies = pd.read_sql_query("SELECT * FROM movies", conn)
    else:
        # Fallback empty dataframe structure
        movies = pd.DataFrame(columns=['movie_id', 'title', 'budget', 'revenue', 'vote_average', 'vote_count', 'runtime', 'popularity', 'release_date', 'original_language'])

    if os.path.exists(genres_csv) and os.path.exists(movie_genres_csv):
        genres = pd.read_csv(genres_csv)
        movie_genres = pd.read_csv(movie_genres_csv)
    elif conn is not None:
        try:
            genres = pd.read_sql_query("SELECT * FROM genres", conn)
            movie_genres = pd.read_sql_query("SELECT * FROM movie_genres", conn)
        except Exception:
            genres = pd.DataFrame({'genre_id': [], 'genre_name': []})
            movie_genres = pd.DataFrame({'movie_id': [], 'genre_id': []})
    else:
        genres = pd.DataFrame({'genre_id': [], 'genre_name': []})
        movie_genres = pd.DataFrame({'movie_id': [], 'genre_id': []})

    # Standardize release dates and years
    movies['release_date_dt'] = pd.to_datetime(movies['release_date'], errors='coerce')
    movies['release_year'] = movies['release_date_dt'].dt.year

    # Map genres to each movie
    if not genres.empty and not movie_genres.empty:
        mg = movie_genres.merge(genres, on='genre_id')
        genre_map = mg.groupby('movie_id')['genre_name'].apply(list).to_dict()
        genre_str_map = mg.groupby('movie_id')['genre_name'].apply(lambda x: ', '.join(x)).to_dict()
    else:
        genre_map = {}
        genre_str_map = {}

    movies['genres_list'] = movies['movie_id'].map(lambda x: genre_map.get(x, []))
    movies['genres_display'] = movies['movie_id'].map(lambda x: genre_str_map.get(x, 'N/A'))
    
    all_genres_list = sorted(genres['genre_name'].dropna().unique().tolist()) if not genres.empty else ['Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Drama', 'Family', 'Fantasy', 'History', 'Horror', 'Music', 'Mystery', 'Romance', 'Science Fiction', 'Thriller']
    
    return movies, all_genres_list

catalog_df, available_genres = load_and_prep_catalog()

# ----------------------------------------------------
# SIDEBAR FILTERS (GLOBAL CONTROLS)
# ----------------------------------------------------
st.sidebar.title("🎬 Global Filters")
st.sidebar.caption("Filter all dashboard metrics & visuals in real-time.")

# 1. Genre Multiselect
selected_genres = st.sidebar.multiselect(
    "Select Genre(s)",
    options=available_genres,
    default=[],
    help="Filter films that match ANY of the selected genres."
)

# 2. Release Year Range Slider
min_dataset_year = int(catalog_df['release_year'].min()) if not catalog_df['release_year'].dropna().empty else 1920
max_dataset_year = int(catalog_df['release_year'].max()) if not catalog_df['release_year'].dropna().empty else 2025

year_range = st.sidebar.slider(
    "Release Year Range",
    min_value=min_dataset_year,
    max_value=max_dataset_year,
    value=(min_dataset_year, max_dataset_year),
    step=1
)

# 3. Minimum Rating Slider
rating_threshold = st.sidebar.slider(
    "Minimum User Rating (0 - 10)",
    min_value=0.0,
    max_value=10.0,
    value=0.0,
    step=0.5
)

# 4. Original Language Selectbox
available_languages = ['All'] + sorted([str(lang) for lang in catalog_df['original_language'].dropna().unique().tolist()])
selected_language = st.sidebar.selectbox("Original Language", options=available_languages)

# Reset Button
if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    st.rerun()

# ----------------------------------------------------
# REAL-TIME FILTERING LOGIC
# ----------------------------------------------------
filtered_df = catalog_df.copy()

# Apply Genre Filter
if selected_genres:
    filtered_df = filtered_df[filtered_df['genres_list'].apply(lambda g_list: any(g in g_list for g in selected_genres))]

# Apply Year Range Filter
filtered_df = filtered_df[
    (filtered_df['release_year'] >= year_range[0]) & 
    (filtered_df['release_year'] <= year_range[1])
]

# Apply Rating Threshold
filtered_df = filtered_df[filtered_df['vote_average'] >= rating_threshold]

# Apply Language Filter
if selected_language != 'All':
    filtered_df = filtered_df[filtered_df['original_language'] == selected_language]

# Sidebar Status Summary
st.sidebar.markdown("---")
st.sidebar.metric("Matching Movies", f"{len(filtered_df):,} / {len(catalog_df):,}")

# ----------------------------------------------------
# MAIN CONTENT HEADER & NAVIGATION TABS
# ----------------------------------------------------
st.markdown("<div class='main-header'>Reel Insights: TMDB Movie Analytics</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Interactive Relational Database Dashboard & Business Intelligence Platform</div>", unsafe_allow_html=True)

# Display Active Filter Pills so user sees exactly what filters are currently applied
filter_pills = []
if selected_genres:
    filter_pills.append(f"Genres: {', '.join(selected_genres)}")
if year_range != (min_dataset_year, max_dataset_year):
    filter_pills.append(f"Years: {year_range[0]} - {year_range[1]}")
if rating_threshold > 0:
    filter_pills.append(f"Rating ≥ {rating_threshold}⭐")
if selected_language != 'All':
    filter_pills.append(f"Language: {selected_language}")

if filter_pills:
    st.markdown("**Active Filters:** " + " ".join([f"<span class='filter-badge'>{pill}</span>" for pill in filter_pills]), unsafe_allow_html=True)
else:
    st.markdown("<span class='filter-badge'>Showing Full Catalog (All Filters Active)</span>", unsafe_allow_html=True)

nav_tabs = st.tabs(["📊 Executive Dashboard", "🔍 SQL Query Explorer", "🧹 Data Pipeline & Schema"])

# ----------------------------------------------------
# TAB 1: EXECUTIVE DASHBOARD
# ----------------------------------------------------
with nav_tabs[0]:
    st.subheader("📊 Key Performance Indicators", divider='rainbow')
    
    total_count = len(filtered_df)
    avg_score = filtered_df['vote_average'].mean() if total_count > 0 else 0.0
    
    valid_rev = filtered_df[filtered_df['revenue'] > 0]['revenue']
    total_revenue = valid_rev.sum() if not valid_rev.empty else 0
    
    valid_bud = filtered_df[filtered_df['budget'] > 0]['budget']
    avg_budget = valid_bud.mean() if not valid_bud.empty else 0
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Matching Movies", f"{total_count:,}")
    m2.metric("Average User Rating", f"{avg_score:.2f} / 10 ⭐")
    m3.metric("Total Gross Revenue", f"${total_revenue / 1e9:.2f} Billion")
    m4.metric("Avg Production Budget", f"${avg_budget / 1e6:.1f} Million")
    
    st.markdown("---")
    st.subheader("📈 Dynamic Analytics & Box-Office Trends", divider='rainbow')
    
    if total_count == 0:
        st.warning("⚠️ No movies match the current sidebar filter selection. Please broaden your criteria in the left sidebar.")
    else:
        c1, c2 = st.columns(2)
        
        # Chart 1: Top 10 Movies by Revenue
        with c1:
            st.markdown("##### 🏆 Top 10 Highest Grossing Movies")
            top_revenue_movies = filtered_df[filtered_df['revenue'] > 0].sort_values(by='revenue', ascending=False).head(10)
            if not top_revenue_movies.empty:
                fig_bar = px.bar(
                    top_revenue_movies,
                    x='revenue',
                    y='title',
                    orientation='h',
                    color='revenue',
                    color_continuous_scale='tealgrn',
                    labels={'revenue': 'Revenue ($)', 'title': 'Movie Title'},
                    text_auto='.2s',
                    template='plotly_dark'
                )
                fig_bar.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    height=380,
                    margin=dict(l=10, r=10, t=30, b=30)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No box-office revenue data available for current selection.")

        # Chart 2: Budget vs Revenue Dynamics
        with c2:
            st.markdown("##### 💰 Budget vs Revenue Box Office Dynamics")
            valid_financials = filtered_df[(filtered_df['budget'] > 0) & (filtered_df['revenue'] > 0)]
            if not valid_financials.empty:
                fig_scatter = px.scatter(
                    valid_financials,
                    x='budget',
                    y='revenue',
                    size='vote_count',
                    hover_name='title',
                    color='vote_average',
                    color_continuous_scale='Blues',
                    labels={'budget': 'Budget ($)', 'revenue': 'Revenue ($)', 'vote_average': 'Rating'},
                    template='plotly_dark'
                )
                fig_scatter.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=30))
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("No valid budget & revenue records available for current selection.")

        c3, c4 = st.columns(2)
        
        # Chart 3: Rating Distribution
        with c3:
            st.markdown("##### ⭐ User Rating Score Distribution")
            fig_hist = px.histogram(
                filtered_df,
                x='vote_average',
                nbins=20,
                color_discrete_sequence=['#01b4e4'],
                labels={'vote_average': 'User Rating (0 - 10)'},
                template='plotly_dark'
            )
            fig_hist.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=30))
            st.plotly_chart(fig_hist, use_container_width=True)

        # Chart 4: Annual Release Output
        with c4:
            st.markdown("##### 📅 Annual Release Output Productivity")
            yearly_output = filtered_df.groupby('release_year')['movie_id'].count().reset_index()
            if not yearly_output.empty:
                fig_line = px.area(
                    yearly_output,
                    x='release_year',
                    y='movie_id',
                    labels={'release_year': 'Year', 'movie_id': 'Movies Released'},
                    color_discrete_sequence=['#90aea1'],
                    template='plotly_dark'
                )
                fig_line.update_layout(height=350, margin=dict(l=10, r=10, t=30, b=30))
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No release date data available for current selection.")

        # Interactive Data Table of Filtered Results
        st.markdown("---")
        st.markdown("### 📋 Filtered Movie Catalog Explorer")
        st.caption("Inspect, sort, and search all movies matching your active sidebar criteria.")
        
        display_cols = ['title', 'genres_display', 'release_year', 'vote_average', 'vote_count', 'budget', 'revenue', 'original_language']
        existing_display_cols = [col for col in display_cols if col in filtered_df.columns]
        
        data_preview = filtered_df[existing_display_cols].rename(columns={
            'title': 'Movie Title',
            'genres_display': 'Genres',
            'release_year': 'Release Year',
            'vote_average': 'Rating',
            'vote_count': 'Vote Count',
            'budget': 'Budget ($)',
            'revenue': 'Revenue ($)',
            'original_language': 'Language'
        })
        
        st.dataframe(data_preview.sort_values(by='Rating', ascending=False), use_container_width=True, height=300)

# ----------------------------------------------------
# TAB 2: SQL QUERY EXPLORER
# ----------------------------------------------------
with nav_tabs[1]:
    st.subheader("🔍 Relational SQL Query Explorer", divider='rainbow')
    st.write("Execute all 10 project SQL queries directly against `tmdb_movies.db`.")
    
    query_dict = {
        "Query 1: Action Movies Released After 2015": {
            "sql": "SELECT m.movie_id, m.title, m.release_date, m.popularity, m.vote_average FROM movies m JOIN movie_genres mg ON m.movie_id = mg.movie_id JOIN genres g ON mg.genre_id = g.genre_id WHERE g.genre_name = 'Action' AND strftime('%Y', m.release_date) > '2015' ORDER BY m.release_date DESC;",
            "insight": "Highlights modern action release cadence and audience popularity trends."
        },
        "Query 2: Top 10 Highest Grossing Movies & Genres": {
            "sql": "SELECT m.title, m.release_date, m.budget, m.revenue, GROUP_CONCAT(g.genre_name, ', ') AS genres FROM movies m JOIN movie_genres mg ON m.movie_id = mg.movie_id JOIN genres g ON mg.genre_id = g.genre_id WHERE m.revenue > 0 GROUP BY m.movie_id ORDER BY m.revenue DESC LIMIT 10;",
            "insight": "Demonstrates the commercial dominance of multi-genre blockbuster franchises."
        },
        "Query 3: Average Budget & Revenue by Genre": {
            "sql": "SELECT g.genre_name, COUNT(DISTINCT m.movie_id) AS total_movies, ROUND(AVG(m.budget), 2) AS avg_budget, ROUND(AVG(m.revenue), 2) AS avg_revenue FROM genres g JOIN movie_genres mg ON g.genre_id = mg.genre_id JOIN movies m ON mg.movie_id = m.movie_id WHERE m.budget > 0 AND m.revenue > 0 GROUP BY g.genre_name ORDER BY avg_revenue DESC;",
            "insight": "Compares capital investment efficiency and return ratios across film categories."
        },
        "Query 4: Top 10 Most Prolific Cast Members": {
            "sql": "SELECT c.actor_name, COUNT(DISTINCT c.movie_id) AS total_appearances, ROUND(AVG(m.vote_average), 2) AS avg_rating FROM cast c JOIN movies m ON c.movie_id = m.movie_id GROUP BY c.actor_name ORDER BY total_appearances DESC LIMIT 10;",
            "insight": "Identifies high-frequency actors and their audience review track record."
        },
        "Query 5: Directors with > 3 Directed Movies": {
            "sql": "SELECT cr.person_name AS director_name, COUNT(DISTINCT cr.movie_id) AS directed_count, ROUND(AVG(m.vote_average), 2) AS avg_rating, SUM(m.revenue) AS total_revenue FROM crew cr JOIN movies m ON cr.movie_id = m.movie_id WHERE cr.job = 'Director' GROUP BY cr.person_name HAVING directed_count > 3 ORDER BY total_revenue DESC;",
            "insight": "Evaluates commercial track records for veteran studio directors."
        },
        "Query 6: Top 10 Most Frequent Keywords": {
            "sql": "SELECT mk.keyword_name, COUNT(mk.movie_id) AS keyword_frequency FROM movie_keywords mk GROUP BY mk.keyword_name ORDER BY keyword_frequency DESC LIMIT 10;",
            "insight": "Reveals core thematic tags driving content recommendation logic."
        },
        "Query 7: Above Avg Budget but Below Avg Revenue": {
            "sql": "SELECT title, release_date, budget, revenue, (budget - revenue) AS loss_amount FROM movies WHERE budget > (SELECT AVG(budget) FROM movies WHERE budget > 0) AND revenue < (SELECT AVG(revenue) FROM movies WHERE revenue > 0) AND revenue > 0 ORDER BY loss_amount DESC LIMIT 10;",
            "insight": "Pinpoints high-budget box office underperformers for financial auditing."
        },
        "Query 8: Cast in Christopher Nolan Films": {
            "sql": "SELECT DISTINCT c.actor_name, c.character_name, m.title AS movie_title, m.release_date FROM cast c JOIN movies m ON c.movie_id = m.movie_id JOIN crew cr ON m.movie_id = cr.movie_id WHERE cr.job = 'Director' AND cr.person_name LIKE '%Christopher Nolan%' ORDER BY m.release_date DESC;",
            "insight": "Illustrates director casting preferences and recurring talent collaborators."
        },
        "Query 9: Highest-Rated Genre (>= 20 Movies)": {
            "sql": "SELECT g.genre_name, COUNT(m.movie_id) AS movie_count, ROUND(AVG(m.vote_average), 2) AS avg_genre_rating FROM genres g JOIN movie_genres mg ON g.genre_id = mg.genre_id JOIN movies m ON mg.movie_id = m.movie_id GROUP BY g.genre_name HAVING movie_count >= 20 ORDER BY avg_genre_rating DESC LIMIT 1;",
            "insight": "Surfaces top-rated specialized genres with sustained catalog volume."
        },
        "Query 10: Top 10 Movies with Most Tagged Keywords": {
            "sql": "SELECT m.title, m.release_date, COUNT(mk.keyword_id) AS keyword_count FROM movies m JOIN movie_keywords mk ON m.movie_id = mk.movie_id GROUP BY m.movie_id ORDER BY keyword_count DESC LIMIT 10;",
            "insight": "Shows highly complex IP films with heavy thematic tagging."
        }
    }
    
    selected_query_key = st.selectbox("Select SQL Query Question", options=list(query_dict.keys()))
    q_info = query_dict[selected_query_key]
    
    with st.expander("📄 View Executable SQL Code", expanded=True):
        st.code(q_info['sql'], language='sql')
        
    if conn is not None:
        try:
            sql_res = pd.read_sql_query(q_info['sql'], conn)
            st.markdown("##### Query Output Table")
            st.dataframe(sql_res, use_container_width=True)
        except Exception as e:
            st.warning(f"Database note: {e}")
    else:
        st.info("Database file `data/tmdb_movies.db` will populate SQL query tables when connected.")
        
    st.success(f"💡 **Business Insight**: {q_info['insight']}")

# ----------------------------------------------------
# TAB 3: DATA PIPELINE & SCHEMA
# ----------------------------------------------------
with nav_tabs[2]:
    st.subheader("🧹 Data Pipeline & Relational Schema Topology", divider='rainbow')
    
    if conn is not None:
        table_names = ['movies', 'genres', 'movie_genres', 'cast', 'crew', 'movie_keywords']
        stats = []
        for tbl in table_names:
            try:
                c = pd.read_sql_query(f"SELECT COUNT(*) as cnt FROM {tbl}", conn)['cnt'].values[0]
                stats.append({'Table Name': tbl, 'Record Count': f"{c:,}"})
            except Exception:
                pass
                
        if stats:
            st.table(pd.DataFrame(stats))
            
            st.markdown("---")
            st.markdown("### 🔍 Raw Table Sample Inspector")
            selected_table = st.selectbox("Select Table to Inspect", options=table_names)
            sample_df = pd.read_sql_query(f"SELECT * FROM {selected_table} LIMIT 15", conn)
            st.dataframe(sample_df, use_container_width=True)
