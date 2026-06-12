import pandas as pd
from sqlalchemy import text
from nba_api.stats.static import teams as nba_teams
from nba_api.stats.static import players as nba_players
from db import engine

def load_teams():
    """Load all NBA teams into the teams table."""
    teams_list = nba_teams.get_teams()
    df = pd.DataFrame(teams_list)
    df = df.rename(columns={"id": "team_id"})
    df = df[["team_id", "abbreviation", "nickname", "city", "full_name"]]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE teams CASCADE"))
    df.to_sql("teams", engine, if_exists="append", index=False)
    print(f"Loaded {len(df)} teams")

def load_players():
    """Load all NBA players into the players table."""
    players_list = nba_players.get_players()
    df = pd.DataFrame(players_list)
    df = df.rename(columns={"id": "player_id"})
    df = df[["player_id", "full_name", "is_active"]]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE players CASCADE"))
    df.to_sql("players", engine, if_exists="append", index=False)
    print(f"Loaded {len(df)} players")

if __name__ == "__main__":
    load_teams()
    load_players()