import time
import pandas as pd
from sqlalchemy import text
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players as nba_players
from db import engine

SEASON = "2024-25"
REQUEST_DELAY = 0.6  # seconds between API calls to respect rate limits
MAX_RETRIES = 3

# Maps the API's column names to our table's column names
COLUMN_MAP = {
    "Game_ID": "game_id",
    "Player_ID": "player_id",
    "GAME_DATE": "game_date",
    "MATCHUP": "matchup",
    "WL": "win_loss",
    "MIN": "minutes",
    "PTS": "points",
    "REB": "rebounds",
    "AST": "assists",
    "STL": "steals",
    "BLK": "blocks",
    "TOV": "turnovers",
    "FGM": "field_goals_made",
    "FGA": "field_goals_att",
    "FG3M": "three_pointers_made",
    "FG3A": "three_pointers_att",
    "FTM": "free_throws_made",
    "FTA": "free_throws_att",
    "PLUS_MINUS": "plus_minus",
}

UPSERT_SQL = """
INSERT INTO game_logs (
    game_id, player_id, team_id, game_date, matchup, win_loss, minutes,
    points, rebounds, assists, steals, blocks, turnovers,
    field_goals_made, field_goals_att, three_pointers_made,
    three_pointers_att, free_throws_made, free_throws_att, plus_minus
) VALUES (
    :game_id, :player_id, :team_id, :game_date, :matchup, :win_loss, :minutes,
    :points, :rebounds, :assists, :steals, :blocks, :turnovers,
    :field_goals_made, :field_goals_att, :three_pointers_made,
    :three_pointers_att, :free_throws_made, :free_throws_att, :plus_minus
)
ON CONFLICT (game_id, player_id) DO UPDATE SET
    points = EXCLUDED.points,
    rebounds = EXCLUDED.rebounds,
    assists = EXCLUDED.assists,
    minutes = EXCLUDED.minutes,
    plus_minus = EXCLUDED.plus_minus;
"""


def get_active_player_ids():
    """Return list of (player_id, team_id) for active players."""
    active = [p for p in nba_players.get_players() if p["is_active"]]
    return [p["id"] for p in active]


def fetch_player_game_log(player_id):
    """Fetch one player's game log for the season, with retries."""
    for attempt in range(MAX_RETRIES):
        try:
            gl = playergamelog.PlayerGameLog(
                player_id=player_id,
                season=SEASON,
                timeout=30
            )
            return gl.get_data_frames()[0]
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)  # back off before retry
            else:
                print(f"  Failed player {player_id} after {MAX_RETRIES} tries: {e}")
                return None


def transform(df):
    """Map API columns to our schema and clean types."""
    df = df.rename(columns=COLUMN_MAP)

    # team_id isn't in the game log directly — derive from matchup later if needed.
    # For now we pull it from a separate column the API provides.
    keep = list(COLUMN_MAP.values())
    df = df[[c for c in keep if c in df.columns]]

    # Parse game_date (API format like 'OCT 22, 2024')
    df["game_date"] = pd.to_datetime(df["game_date"], format="%b %d, %Y").dt.date

    # Convert minutes to numeric
    df["minutes"] = pd.to_numeric(df["minutes"], errors="coerce")

    return df


def load_game_logs():
    player_ids = get_active_player_ids()
    print(f"Fetching game logs for {len(player_ids)} active players, season {SEASON}...")

    total_rows = 0
    for i, player_id in enumerate(player_ids, 1):
        df = fetch_player_game_log(player_id)
        time.sleep(REQUEST_DELAY)

        if df is None or df.empty:
            continue

        df = transform(df)
        df["team_id"] = None  # placeholder; we'll backfill team_id below

        records = df.to_dict(orient="records")
        with engine.begin() as conn:
            for rec in records:
                conn.execute(text(UPSERT_SQL), rec)

        total_rows += len(records)
        if i % 25 == 0:
            print(f"  {i}/{len(player_ids)} players done, {total_rows} rows so far")

    print(f"Done. Loaded {total_rows} game log rows.")


if __name__ == "__main__":
    load_game_logs()