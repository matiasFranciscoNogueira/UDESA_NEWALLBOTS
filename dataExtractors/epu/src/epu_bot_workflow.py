import os
from pathlib import Path
import pandas as pd
import sqlite3

from epu_historical_GDELT_big_query import run_query_and_update_data
from analysis_compare_with_benchmarks_with_events_save_to_file import (
    compute_and_save_EPU_results,
    join_and_save_subcategories_compare
)
from Helpers.epu_categories_type import EPUCategoriesType
import Helpers.gdelt_request_helpers as Helpers


# -------------------------
# 🔥 NEW: BUILD SQLITE FROM EXCEL
# -------------------------
def build_sqlite_from_excel(store_dir_path: Path):
    excel_path = store_dir_path / "all_subcategories_compare.xlsx"
    db_path = store_dir_path / "database.sqlite"

    if not excel_path.exists():
        print("⚠️ Excel not found → skipping DB creation")
        return

    print(f"💾 Building SQLite DB from {excel_path}")

    data_df = pd.read_excel(excel_path, sheet_name='Data')
    benchmark_df = pd.read_excel(excel_path, sheet_name='benchmark')

    # Normalize fecha
    if 'fecha' in data_df.columns:
        data_df['fecha'] = pd.to_datetime(data_df['fecha']).dt.strftime('%Y-%m-%d')

    if 'fecha' in benchmark_df.columns:
        benchmark_df['fecha'] = pd.to_datetime(benchmark_df['fecha']).dt.strftime('%Y-%m-%d')

    conn = sqlite3.connect(db_path)

    data_df.to_sql("epu_main", conn, if_exists="replace", index=False)
    benchmark_df.to_sql("benchmark", conn, if_exists="replace", index=False)

    conn.close()

    print(f"✅ SQLite DB created at {db_path}")


if __name__ == "__main__":

    country = "Argentina"

    # 🔥 aligned with docker shared volume
    shared_data = os.environ.get("SHARED_DATA_PATH", "/app/data/epu")
    store_dir_path = Path(shared_data)
    store_dir_path.mkdir(parents=True, exist_ok=True)

    for sub_category in EPUCategoriesType:
        print(f"Ejecutando workflow para categoría: {sub_category.value}")

        # -------------------------
        # Step 1: Extract
        # -------------------------
        run_query_and_update_data(country=country, sub_category=sub_category)

        # -------------------------
        # Step 2: Resolve expected file dynamically
        # -------------------------
        kw_file = "key_words_gdelt_maped_jp.json"
        is_sub_category = sub_category != EPUCategoriesType.NONE

        if country == "Argentina":
            medios = [
                "clarin.com", "lanacion.com.ar", "infobae.com",
                "ambito.com", "pagina12.com.ar", "perfil.com",
                "tn.com.ar", "cronista.com", "lavoz.com.ar",
                "minutouno.com", "diariopopular.com.ar", "diariouno.com.ar"
            ]
        else:
            medios = []

        epu_file_name, _ = Helpers.set_epu_files_names(
            kw_file,
            medios=medios,
            base_dir=Path(__file__).resolve().parent,
            country=country,
            is_sub_category=is_sub_category
        )

        expected_file = store_dir_path / epu_file_name.replace(".csv", "_with_sentiment.csv")

        # -------------------------
        # Step 3: Safe analysis
        # -------------------------
        if expected_file.exists():
            print(f"📊 Running analysis for {sub_category.value}")
            compute_and_save_EPU_results(country=country, sub_category=sub_category)
        else:
            print(f"⚠️ Missing sentiment file → skipping analysis for {sub_category.value}")

    # -------------------------
    # Step 4: Join results + BUILD DB
    # -------------------------
    results_file = store_dir_path / "results" / "epu_analysis_results_udesa_jp.xlsx"

    if results_file.exists():
        print("📊 Joining subcategory results...")

        output_path = store_dir_path / "all_subcategories_compare.xlsx"
        join_and_save_subcategories_compare(country=country, output_path=output_path)

        # 🔥 NEW: create SQLite DB
        build_sqlite_from_excel(store_dir_path)

    else:
        print("⚠️ No analysis results found → skipping join + DB creation")