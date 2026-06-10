from sqlalchemy import create_engine, text

# Connection string: postgresql://user:password@host:port/database
# host is localhost because the container maps port 5432 to your Mac
DB_URL = "postgresql+psycopg2://nba_user:nba_password@localhost:5432/nba"

engine = create_engine(DB_URL)

if __name__ == "__main__":
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print("Connected to:", result.fetchone()[0])