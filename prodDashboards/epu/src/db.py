import sqlite3
from pathlib import Path
import pandas as pd


DEFAULT_DB = Path(__file__).parent.parent / "data" / "database.sqlite"


def get_db_path(db_path: str | Path | None = None) -> Path:
    if db_path:
        return Path(db_path)
    return DEFAULT_DB


def read_table(table_name: str, db_path: str | Path | None = None) -> pd.DataFrame:
    """Read an entire table from the sqlite DB and return a DataFrame.

    Expects a `fecha` column when present; parsing will attempt to convert it to datetime.
    """
    path = get_db_path(db_path)
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


def write_table(df: pd.DataFrame, table_name: str, db_path: str | Path | None = None, if_exists: str = 'replace') -> None:
    """Write DataFrame to sqlite table."""
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
    finally:
        conn.close()
