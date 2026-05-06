#!/usr/bin/env python3
"""Import shared EPU Excel into sqlite DB for dashboards.

Creates:
- epu_main
- benchmark

Location:
- Excel: /app/data/epu/all_subcategories_compare.xlsx
- DB:    /app/data/epu/database.sqlite
"""
from pathlib import Path
import sys
import pandas as pd

# Ensure project root is on sys.path so `import src` works
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db import write_table


# -------------------------
# ✅ CORRECT SHARED PATHS
# -------------------------
DATA_ROOT = Path("/app/data/epu")

EXCEL = DATA_ROOT / "all_subcategories_compare.xlsx"
DB = DATA_ROOT / "database.sqlite"


def main(excel_path: Path = EXCEL, db_path: Path = DB):

    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    print(f"📥 Reading Excel: {excel_path}")

    data_df = pd.read_excel(excel_path, sheet_name='Data')
    benchmark_df = pd.read_excel(excel_path, sheet_name='benchmark')

    # -------------------------
    # Normalize date
    # -------------------------
    if 'fecha' in data_df.columns:
        data_df['fecha'] = pd.to_datetime(data_df['fecha']).dt.strftime('%Y-%m-%d')

    if 'fecha' in benchmark_df.columns:
        benchmark_df['fecha'] = pd.to_datetime(benchmark_df['fecha']).dt.strftime('%Y-%m-%d')

    print(f"💾 Writing DB: {db_path}")

    # -------------------------
    # ✅ CORRECT TABLE NAMES
    # -------------------------
    write_table(data_df, 'epu_main', db_path=db_path, if_exists='replace')
    write_table(benchmark_df, 'benchmark', db_path=db_path, if_exists='replace')

    print("✅ Import finished successfully.")


if __name__ == '__main__':
    main()