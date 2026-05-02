from pathlib import Path
from google.cloud import bigquery
from Helpers.epu_categories_type import EPUCategoriesType
import os
import datetime as dt
import json
import Helpers.gdelt_request_helpers as Helpers

def run_query_and_update_data(
    country: str = "Argentina",
    sub_category: EPUCategoriesType = EPUCategoriesType.NONE,
    run_query: bool = True
):
    BASE_DIR = Path(__file__).resolve().parent
    KEY_PATH = BASE_DIR.parent / "keys" / "project-60200dfd-09f6-41da-854-53a231b07325.json"
    client = bigquery.Client.from_service_account_json(str(KEY_PATH))

    # -------------------------
    # KEYWORDS
    # -------------------------
    if sub_category == EPUCategoriesType.NONE:
        kw_file = "key_words_gdelt_maped_jp.json"
        kw_path = BASE_DIR.parent / "src" / "keywords_dicts" / kw_file
    else:   
        kw_file = f"key_words_gdelt_maped_jp_{sub_category.value}.json"
        kw_path = BASE_DIR.parent / "src" / "keywords_dicts" / "subcategories" / kw_file
    
    with open(kw_path, 'r', encoding='utf-8') as f:
        kw = json.load(f)
        
    is_sub_category = "S" in kw.keys()

    # -------------------------
    # MEDIA
    # -------------------------
    if country == "Argentina":
        medios = [
            "clarin.com", "lanacion.com.ar", "infobae.com",
            "ambito.com", "pagina12.com.ar", "perfil.com",
            "tn.com.ar", "cronista.com", "lavoz.com.ar",
            "minutouno.com", "diariopopular.com.ar", "diariouno.com.ar"
        ]
    else:
        media_dict_file = "countries_media.json"
        media_path = BASE_DIR.parent / "src" / "Countries_Media" / media_dict_file
        with open(media_path, 'r', encoding='utf-8') as f:
            media_dict = json.load(f)
        medios = media_dict[country]
    
    # -------------------------
    # FILES + EXISTING DATA
    # -------------------------
    epu_file_name, _ = Helpers.set_epu_files_names(
        kw_file, medios, base_dir=BASE_DIR, country=country, is_sub_category=is_sub_category
    )

    # 🔥 FORCE centralized data path
    store_dir_path = Path(os.environ.get("SHARED_DATA_PATH", "/app/data/epu"))

    # ensure directory exists
    store_dir_path.mkdir(parents=True, exist_ok=True)
    
    df_raw = Helpers.get_raw_given_historical_data_from_db(
        store_dir_path, epu_file_name, is_sub_category
    )

    print("📂 CSV path:", store_dir_path / epu_file_name)
    print("📊 Rows loaded:", len(df_raw))

    # -------------------------
    # DATE LOGIC (FIXED)
    # -------------------------
    HISTORICAL_START = dt.date(2015, 2, 19)
    SAFE_LAG_DAYS = 3
    MAX_DAYS_QUERY = 31

    if df_raw.empty:
        last_csv_date = HISTORICAL_START
    else:
        last_csv_date = df_raw.index.max().date()

        # 🛑 Sanity check (anti corruption)
        if last_csv_date < dt.date(2016, 1, 1):
            print("⚠️ Suspicious CSV detected → fallback to safe start")
            last_csv_date = HISTORICAL_START

    # 🔁 Re-query window (handles GDELT lag)
    start = last_csv_date - dt.timedelta(days=SAFE_LAG_DAYS)

    if start < HISTORICAL_START:
        start = HISTORICAL_START

    today = dt.date.today()

    # 🛑 Limit query window (cost protection)
    delta_days = (today - start).days

    if delta_days > MAX_DAYS_QUERY:
        print(f"⚠️ Query too large ({delta_days} days) → limiting window")
        start = today - dt.timedelta(days=MAX_DAYS_QUERY)

    print("🔥 Script started")
    print("📅 Last CSV date:", last_csv_date)
    print("📅 Adjusted start date:", start)
    print("📅 Today:", today)

    if start >= today:
        print("No hay datos nuevos para actualizar.")
        return

    # -------------------------
    # BUILD SQL
    # -------------------------
    SQL = Helpers.get_sql(start, dt.date.today(), kw, medios)


    # -------------------------
    # 🔥 ALWAYS ESTIMATE FIRST
    # -------------------------
    MAX_COST_USD = 1.0

    print("🔍 Running cost estimation (dry run)...")
    estimated_bytes = Helpers.get_query_estimated_price(client, SQL)

    # Convert to human-readable
    estimated_gb = estimated_bytes / (1024**3)
    estimated_tb = estimated_bytes / (1024**4)
    estimated_cost = estimated_tb * 5  # BigQuery pricing

    print("📊 Estimated data to scan:")
    print(f"   → {estimated_bytes:,} bytes")
    print(f"   → {estimated_gb:.4f} GB")
    print(f"💰 Estimated cost: ${estimated_cost:.4f} USD")

    # -------------------------
    # 🛑 COST GUARDRAIL
    # -------------------------
    if estimated_cost > MAX_COST_USD:
        print("🚨 COST LIMIT EXCEEDED")
        print(f"   Max allowed: ${MAX_COST_USD}")
        print(f"   Estimated:  ${estimated_cost:.4f}")
        print("🛑 Query blocked to prevent high cost.")
        return

    print("✅ Cost within limit → allowed to run")

    # -------------------------
    # 🔒 SAFE MODE (DEFAULT)
    # -------------------------
    if not run_query:
        print("🛑 run_query=False → Dry run only (no execution)")
        return

    # -------------------------
    # 🚀 EXECUTION MODE
    # -------------------------
    print("🚀 run_query=True → Executing query...")

    df_new = Helpers.get_data_from_big_query(SQL, client)

    df_updated = Helpers.concat_raw_with_updated_dfs(df_raw, df_new)

    (store_dir_path / "subcategories").mkdir(exist_ok=True)
    (store_dir_path / "results").mkdir(exist_ok=True)
    Helpers.guardar_df(df_updated, epu_file_name, store_dir_path)

    print("✅ Data successfully updated.")


# 🔥 OUTSIDE function (IMPORTANT)
if __name__ == "__main__":
    run_query_and_update_data(
        country="Argentina",
        sub_category=EPUCategoriesType.NONE,
        run_query=True
    )