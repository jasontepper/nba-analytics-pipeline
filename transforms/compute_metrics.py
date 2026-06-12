import sys
sys.path.insert(0, "../ingestion")

import pandas as pd
from sqlalchemy import text
from db import engine


def load_game_logs():
    """Pull all game logs into a DataFrame, sorted for rolling windows."""
    df = pd.read_sql("SELECT * FROM game_logs", engine)
    # Critical: sort by player then date so rolling windows are chronological per player
    df = df.sort_values(["player_id", "game_date"]).reset_index(drop=True)
    return df


def compute_rolling(df):
    """Compute last-5 and last-10 game rolling averages, per player."""
    out = df[["player_id", "game_date", "points", "rebounds", "assists"]].copy()

    grouped = df.groupby("player_id")
    for stat, col in [("points", "pts"), ("rebounds", "reb"), ("assists", "ast")]:
        # rolling(5) over each player's chronological games; min_periods=1 so early games still get a value
        out[f"{col}_roll5"] = (
            grouped[stat].rolling(window=5, min_periods=1).mean().reset_index(level=0, drop=True)
        )
        out[f"{col}_roll10"] = (
            grouped[stat].rolling(window=10, min_periods=1).mean().reset_index(level=0, drop=True)
        )

    # Round for cleanliness
    roll_cols = [c for c in out.columns if "roll" in c]
    out[roll_cols] = out[roll_cols].round(2)
    return out


def compute_season_summary(df):
    """Compute per-player season averages and consistency."""
    agg = df.groupby("player_id").agg(
        games_played=("points", "count"),
        pts_avg=("points", "mean"),
        reb_avg=("rebounds", "mean"),
        ast_avg=("assists", "mean"),
        pts_std=("points", "std"),
        min_avg=("minutes", "mean"),
    ).reset_index()

    # Coefficient of variation: std/mean. Lower = more consistent scorer.
    # Guard against divide-by-zero for players averaging 0 points.
    agg["pts_consistency"] = (agg["pts_std"] / agg["pts_avg"]).where(agg["pts_avg"] > 0, None)

    # Round everything
    for col in ["pts_avg", "reb_avg", "ast_avg", "pts_std", "pts_consistency", "min_avg"]:
        agg[col] = agg[col].round(3)

    return agg


def write_table(df, table_name):
    """Truncate and reload a derived table."""
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {table_name}"))
    df.to_sql(table_name, engine, if_exists="append", index=False)
    print(f"Wrote {len(df)} rows to {table_name}")


def main():
    print("Loading game logs...")
    df = load_game_logs()
    print(f"  {len(df)} rows loaded")

    print("Computing rolling stats...")
    rolling = compute_rolling(df)
    write_table(rolling, "player_rolling_stats")

    print("Computing season summary...")
    summary = compute_season_summary(df)
    write_table(summary, "player_season_summary")

    print("Done.")


if __name__ == "__main__":
    main()