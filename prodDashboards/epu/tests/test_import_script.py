"""Tests for scripts/import_excel_to_sqlite.py."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.import_excel_to_sqlite import main
from src.db import read_table, write_table

REAL_EXCEL = Path(__file__).parent.parent / "data" / "all_subcategories_compare.xlsx"


# ---------------------------------------------------------------------------
# main() with the real Excel file
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not REAL_EXCEL.exists(), reason="real Excel fixture not present")
class TestImportWithRealExcel:
    def test_creates_data_table(self, tmp_path):
        db = tmp_path / "db.sqlite"
        main(excel_path=REAL_EXCEL, db_path=db)
        df = read_table("data", db_path=db)
        assert len(df) > 0

    def test_creates_benchmark_table(self, tmp_path):
        db = tmp_path / "db.sqlite"
        main(excel_path=REAL_EXCEL, db_path=db)
        df = read_table("benchmark", db_path=db)
        assert len(df) > 0

    def test_data_table_has_fecha_column(self, tmp_path):
        db = tmp_path / "db.sqlite"
        main(excel_path=REAL_EXCEL, db_path=db)
        df = read_table("data", db_path=db)
        assert "fecha" in df.columns

    def test_fecha_is_parsed_as_datetime(self, tmp_path):
        db = tmp_path / "db.sqlite"
        main(excel_path=REAL_EXCEL, db_path=db)
        df = read_table("data", db_path=db)
        assert pd.api.types.is_datetime64_any_dtype(df["fecha"])

    def test_data_table_has_epu_udesa_column(self, tmp_path):
        db = tmp_path / "db.sqlite"
        main(excel_path=REAL_EXCEL, db_path=db)
        df = read_table("data", db_path=db)
        assert "EPU UdeSA" in df.columns


# ---------------------------------------------------------------------------
# main() error handling
# ---------------------------------------------------------------------------

class TestImportErrors:
    def test_missing_excel_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            main(excel_path=tmp_path / "nonexistent.xlsx")

    def test_is_idempotent(self, tmp_path):
        """Running main twice on the same DB replaces the tables cleanly."""
        if not REAL_EXCEL.exists():
            pytest.skip("real Excel fixture not present")
        db = tmp_path / "db.sqlite"
        main(excel_path=REAL_EXCEL, db_path=db)
        main(excel_path=REAL_EXCEL, db_path=db)  # second run — should not raise
        df = read_table("data", db_path=db)
        assert len(df) > 0
