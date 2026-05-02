#!/usr/bin/env python3
"""Import `data/all_subcategories_compare.xlsx` into a sqlite database.

Creates two tables: `data` and `benchmark` in `data/database.sqlite`.
"""
from pathlib import Path
import sys
import pandas as pd

# Ensure project root is on sys.path so `import src` works when running this script directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db import write_table, get_db_path


ROOT = Path(__file__).parent.parent
EXCEL = ROOT / 'data' / 'all_subcategories_compare.xlsx'
DB = ROOT / 'data' / 'database.sqlite'


def main(excel_path: Path = EXCEL, db_path: Path | None = None):
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_path}")

    print(f"Reading Excel: {excel_path}")
    data_df = pd.read_excel(excel_path, sheet_name='Data')
    benchmark_df = pd.read_excel(excel_path, sheet_name='benchmark')

    # Ensure fecha column is ISO-serializable
    if 'fecha' in data_df.columns:
        data_df['fecha'] = pd.to_datetime(data_df['fecha']).dt.strftime('%Y-%m-%d')
    if 'fecha' in benchmark_df.columns:
        benchmark_df['fecha'] = pd.to_datetime(benchmark_df['fecha']).dt.strftime('%Y-%m-%d')

    print(f"Writing to DB: {db_path or DB}")
    write_table(data_df, 'data', db_path=db_path or DB, if_exists='replace')
    write_table(benchmark_df, 'benchmark', db_path=db_path or DB, if_exists='replace')

    print("Import finished.")


if __name__ == '__main__':
    main()
