"""Unit tests for src/db.py."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_db_path, read_table, write_table, DEFAULT_DB


# ---------------------------------------------------------------------------
# get_db_path
# ---------------------------------------------------------------------------

class TestGetDbPath:
    def test_none_returns_default(self):
        assert get_db_path(None) == DEFAULT_DB

    def test_no_arg_returns_default(self):
        assert get_db_path() == DEFAULT_DB

    def test_string_path_returns_path_object(self):
        result = get_db_path("/tmp/test.sqlite")
        assert isinstance(result, Path)
        assert str(result) == "/tmp/test.sqlite"

    def test_path_object_is_returned_as_path(self):
        p = Path("/tmp/other.sqlite")
        assert get_db_path(p) == p


# ---------------------------------------------------------------------------
# write_table / read_table round-trip
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_db(tmp_path):
    """A fresh SQLite DB path in a pytest temp directory."""
    return tmp_path / "test.sqlite"


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "fecha": ["2023-01-31", "2023-02-28", "2023-03-31"],
        "value_a": [100.0, 120.0, 110.0],
        "value_b": [80.0, 90.0, 85.0],
    })


class TestWriteReadRoundtrip:
    def test_write_then_read_returns_same_rows(self, tmp_db, sample_df):
        write_table(sample_df, "my_table", db_path=tmp_db)
        result = read_table("my_table", db_path=tmp_db)
        assert len(result) == len(sample_df)

    def test_write_then_read_preserves_columns(self, tmp_db, sample_df):
        write_table(sample_df, "my_table", db_path=tmp_db)
        result = read_table("my_table", db_path=tmp_db)
        assert set(result.columns) == set(sample_df.columns)

    def test_write_then_read_preserves_values(self, tmp_db, sample_df):
        write_table(sample_df, "my_table", db_path=tmp_db)
        result = read_table("my_table", db_path=tmp_db)
        assert list(result["value_a"]) == list(sample_df["value_a"])

    def test_replace_overwrites_previous_data(self, tmp_db, sample_df):
        write_table(sample_df, "my_table", db_path=tmp_db)
        smaller_df = sample_df.head(1)
        write_table(smaller_df, "my_table", db_path=tmp_db, if_exists="replace")
        result = read_table("my_table", db_path=tmp_db)
        assert len(result) == 1

    def test_creates_parent_directory_if_missing(self, tmp_path):
        nested_db = tmp_path / "nested" / "dir" / "test.sqlite"
        df = pd.DataFrame({"x": [1, 2]})
        write_table(df, "t", db_path=nested_db)
        assert nested_db.exists()


class TestReadTable:
    def test_missing_db_raises_file_not_found(self, tmp_path):
        missing = tmp_path / "nonexistent.sqlite"
        with pytest.raises(FileNotFoundError):
            read_table("any_table", db_path=missing)

    def test_fecha_column_parsed_as_datetime(self, tmp_db):
        df = pd.DataFrame({"fecha": ["2023-01-31", "2023-02-28"], "v": [1.0, 2.0]})
        write_table(df, "tbl", db_path=tmp_db)
        result = read_table("tbl", db_path=tmp_db)
        assert pd.api.types.is_datetime64_any_dtype(result["fecha"])

    def test_no_fecha_column_leaves_dtypes_unchanged(self, tmp_db):
        df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
        write_table(df, "tbl", db_path=tmp_db)
        result = read_table("tbl", db_path=tmp_db)
        # No exception, fecha parsing is skipped
        assert "fecha" not in result.columns
