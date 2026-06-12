import sys
sys.path.insert(0, "../ingestion")

import pandas as pd
from sqlalchemy import text
from db import engine

HOT_THRESHOLD = 2.0
COLD_THRESHOLD = -2.0
MIN_GAMES = 10  # need enough games for a stable baseline


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS player_outliers (
    player_id       BIGINT PRIMARY KEY,
    games_played    INTEGER,
    pts_avg         REAL,
    pts_recent5     REAL,
    pts_zscore      REAL,
    status          VARCHAR(10)
);
"""


def main():
    with engine.begin() as conn:
        conn.execute(text(CREATE_TABLE_SQL))

    # Season baseline: mean + std per player
    summary = pd.read_sql(
        "SELECT player_id, games_played, pts_avg, pts_std FROM player_season_summary",
        engine,
    )

    # Most recent rolling-5 value per player = their current form.
    # We grab the latest game_date row for each player.
    recent = pd.read_sql("""
        SELECT DISTINCT ON (player_id) player_id, pts_roll5
        FROM player_rolling_stats
        ORDER BY player_id, game_date DESC
    """, engine)

    df = summary.merge(recent, on="player_id", how="inner")
    df = df[df["games_played"] >= MIN_GAMES].copy()

    # z-score of recent form vs season baseline
    # Standard error of a 5-game mean = season_std / sqrt(5).
    # The variance of an average shrinks with sample size, so we compare the
    # rolling-5 average against the *standard error*, not the raw single-game std.
    import numpy as np
    df["pts_zscore"] = (df["pts_roll5"] - df["pts_avg"]) / (df["pts_std"] / np.sqrt(5))

    def classify(z):
        if z >= HOT_THRESHOLD:
            return "hot"
        if z <= COLD_THRESHOLD:
            return "cold"
        return "normal"

    df["status"] = df["pts_zscore"].apply(classify)

    out = df.rename(columns={"pts_roll5": "pts_recent5"})[
        ["player_id", "games_played", "pts_avg", "pts_recent5", "pts_zscore", "status"]
    ]
    out["pts_zscore"] = out["pts_zscore"].round(3)
    out["pts_recent5"] = out["pts_recent5"].round(2)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE player_outliers"))
    out.to_sql("player_outliers", engine, if_exists="append", index=False)

    hot = (out["status"] == "hot").sum()
    cold = (out["status"] == "cold").sum()
    print(f"Wrote {len(out)} players. Hot: {hot}, Cold: {cold}")


if __name__ == "__main__":
    main()