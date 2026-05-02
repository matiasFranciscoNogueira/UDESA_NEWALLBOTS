import sqlite3
from pathlib import Path
import pandas as pd
import os

DATA_PATH = Path(os.getenv("DATA_PATH", "/app/data/epu"))
DEFAULT_DB = DATA_PATH / "database.sqlite"


def get_db_path(db_path: str | Path | None = None) -> Path:
    if db_path:
        return Path(db_path)
    return DEFAULT_DB


def initialize_db_if_missing():
    """Create SQLite DB from CSV if it doesn't exist."""
    db_path = get_db_path()

    if db_path.exists():
        return

    print("⚠️ DB not found → initializing from CSV")

    csv_path = DATA_PATH / "epu_argentina_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV source not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # 🔥 write directly WITHOUT triggering recursion
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql("epu_main", conn, if_exists="replace", index=False)
    finally:
        conn.close()

    print(f"✅ DB initialized at {db_path}")


def read_table(table_name: str, db_path: str | Path | None = None) -> pd.DataFrame:
    """Read an entire table from the sqlite DB and return a DataFrame."""
    path = get_db_path(db_path)

    # 🔥 ensure DB exists (ONLY here)
    initialize_db_if_missing()

    if not path.exists():
        raise FileNotFoundError(f"Database file not found: {path}")

    conn = sqlite3.connect(path)
    try:
        df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
    finally:
        conn.close()

    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'])

    return df


def write_table(
    df: pd.DataFrame,
    table_name: str,
    db_path: str | Path | None = None,
    if_exists: str = 'replace'
) -> None:
    """Write DataFrame to sqlite table."""
    path = get_db_path(db_path)

    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    try:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    finally:
        conn.close()