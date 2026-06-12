-- Teams: one row per NBA team (essentially static reference data)
CREATE TABLE IF NOT EXISTS teams (
    team_id      BIGINT PRIMARY KEY,
    abbreviation VARCHAR(5),
    nickname     VARCHAR(50),
    city         VARCHAR(50),
    full_name    VARCHAR(100)
);

-- Players: one row per player (slowly-changing reference data)
CREATE TABLE IF NOT EXISTS players (
    player_id    BIGINT PRIMARY KEY,
    full_name    VARCHAR(100),
    is_active    BOOLEAN
);

-- Game logs: one row per player per game (the growing "fact" table)
CREATE TABLE IF NOT EXISTS game_logs (
    game_id         VARCHAR(20),
    player_id       BIGINT REFERENCES players(player_id),
    team_id         BIGINT REFERENCES teams(team_id),
    game_date       DATE,
    matchup         VARCHAR(20),
    win_loss        VARCHAR(1),
    minutes         REAL,
    points          INTEGER,
    rebounds        INTEGER,
    assists         INTEGER,
    steals          INTEGER,
    blocks          INTEGER,
    turnovers       INTEGER,
    field_goals_made    INTEGER,
    field_goals_att     INTEGER,
    three_pointers_made INTEGER,
    three_pointers_att  INTEGER,
    free_throws_made    INTEGER,
    free_throws_att     INTEGER,
    plus_minus      INTEGER,
    PRIMARY KEY (game_id, player_id)
);