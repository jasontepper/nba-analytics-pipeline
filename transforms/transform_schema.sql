-- Per-player, per-game rolling metrics (last-5 and last-10 game windows)
CREATE TABLE IF NOT EXISTS player_rolling_stats (
    player_id        BIGINT,
    game_date        DATE,
    points           INTEGER,
    rebounds         INTEGER,
    assists          INTEGER,
    pts_roll5        REAL,
    reb_roll5        REAL,
    ast_roll5        REAL,
    pts_roll10       REAL,
    reb_roll10       REAL,
    ast_roll10       REAL,
    PRIMARY KEY (player_id, game_date)
);

-- Per-player season summary: averages, consistency, games played
CREATE TABLE IF NOT EXISTS player_season_summary (
    player_id        BIGINT PRIMARY KEY,
    games_played     INTEGER,
    pts_avg          REAL,
    reb_avg          REAL,
    ast_avg          REAL,
    pts_std          REAL,
    pts_consistency  REAL,  -- coefficient of variation (std/mean); lower = more consistent
    min_avg          REAL
);