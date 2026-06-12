from pathlib import Path
from db import engine
from sqlalchemy import text

def init_schema():
    schema_path = Path(__file__).parent / "schema.sql"
    with open(schema_path) as f:
        schema_sql = f.read()

    with engine.begin() as conn:
        conn.execute(text(schema_sql))
    print("Schema created successfully.")

if __name__ == "__main__":
    init_schema()