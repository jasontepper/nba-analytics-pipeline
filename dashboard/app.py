import sys
sys.path.insert(0, "../ingestion")

import pandas as pd
import streamlit as st
from db import engine

st.set_page_config(page_title="NBA Analytics", layout="wide")


# ---------- Cached data loaders ----------
@st.cache_data
def load_leaderboard():
    return pd.read_sql("""
        SELECT p.full_name, s.games_played, s.pts_avg, s.reb_avg,
               s.ast_avg, s.pts_consistency
        FROM player_season_summary s
        JOIN players p ON s.player_id = p.player_id
        WHERE s.games_played >= 40
    """, engine)


@st.cache_data
def load_player_list():
    return pd.read_sql("""
        SELECT DISTINCT p.player_id, p.full_name
        FROM player_rolling_stats r
        JOIN players p ON r.player_id = p.player_id
        ORDER BY p.full_name
    """, engine)


@st.cache_data
def load_player_trend(player_id):
    return pd.read_sql(f"""
        SELECT game_date, points, pts_roll5, pts_roll10
        FROM player_rolling_stats
        WHERE player_id = {player_id}
        ORDER BY game_date
    """, engine)


@st.cache_data
def load_outliers():
    return pd.read_sql("""
        SELECT p.full_name, o.pts_avg, o.pts_recent5, o.pts_zscore, o.status
        FROM player_outliers o
        JOIN players p ON o.player_id = p.player_id
        WHERE o.status != 'normal'
        ORDER BY o.pts_zscore DESC
    """, engine)


@st.cache_data
def load_team_stats():
    return pd.read_sql("""
        SELECT t.full_name AS team,
               COUNT(DISTINCT g.player_id) AS players,
               ROUND(AVG(g.points), 1) AS avg_pts_per_player_game,
               SUM(g.points) AS total_points
        FROM game_logs g
        JOIN teams t ON g.team_id = t.team_id
        GROUP BY t.full_name
        ORDER BY total_points DESC
    """, engine)


# ---------- Header ----------
st.title("🏀 NBA Player Performance Analytics")
st.caption("2024-25 season · data from the NBA Stats API")

# ---------- Section 1: Leaderboards ----------
st.header("League Leaderboards")
lb = load_leaderboard()

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Top Scorers")
    st.dataframe(
        lb.nlargest(10, "pts_avg")[["full_name", "pts_avg"]].reset_index(drop=True),
        use_container_width=True, hide_index=True
    )
with col2:
    st.subheader("Top Rebounders")
    st.dataframe(
        lb.nlargest(10, "reb_avg")[["full_name", "reb_avg"]].reset_index(drop=True),
        use_container_width=True, hide_index=True
    )
with col3:
    st.subheader("Top Playmakers")
    st.dataframe(
        lb.nlargest(10, "ast_avg")[["full_name", "ast_avg"]].reset_index(drop=True),
        use_container_width=True, hide_index=True
    )

st.subheader("Most Consistent Scorers (min 40 games)")
consistent = lb[lb["pts_avg"] >= 15].nsmallest(10, "pts_consistency")
st.dataframe(
    consistent[["full_name", "pts_avg", "pts_consistency"]].reset_index(drop=True),
    use_container_width=True, hide_index=True
)

# ---------- Section 2: Player Deep-Dive ----------
st.header("Player Trend Explorer")
players = load_player_list()
selected_name = st.selectbox("Choose a player", players["full_name"])
selected_id = int(players[players["full_name"] == selected_name]["player_id"].iloc[0])

trend = load_player_trend(selected_id)
if not trend.empty:
    chart_data = trend.set_index("game_date")[["points", "pts_roll5", "pts_roll10"]]
    st.line_chart(chart_data)
    st.caption("Each line: actual points per game, 5-game rolling average, and 10-game rolling average")
else:
    st.info("No data for this player.")

# ---------- Section 3: Hot / Cold Tracker ----------
st.header("Hot & Cold Players")
st.caption("Players whose last-5-game scoring deviates 2+ standard errors from their season baseline")
outliers = load_outliers()

def color_status(row):
    color = "#1b5e20" if row["status"] == "hot" else "#7f1d1d"
    return [f"background-color: {color}"] * len(row)

if not outliers.empty:
    st.dataframe(
        outliers.style.apply(color_status, axis=1),
        use_container_width=True, hide_index=True
    )
else:
    st.info("No outliers detected.")

# ---------- Section 4: Team Comparison ----------
st.header("Team Comparison")
teams = load_team_stats()
if not teams.empty:
    st.bar_chart(teams.set_index("team")["total_points"])
    st.dataframe(teams, use_container_width=True, hide_index=True)
else:
    st.info("No team data available (team_id not populated in game logs).")