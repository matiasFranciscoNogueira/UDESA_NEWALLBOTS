import json
import pandas as pd
from pathlib import Path
import pandas as pd
from Helpers.analisys_helpers import  get_epu_and_resample_from_daily_selector
from Helpers.epu_categories_type import EPUCategoriesType

_SUBCATEGORY_DISPLAY_NAMES = {
    EPUCategoriesType.TRADE: "Trade",
    EPUCategoriesType.MONETARY_POLICY: "Monetary Policy",
    EPUCategoriesType.FISCAL: "Fiscal",
    EPUCategoriesType.CURRENCY_CRISIS: "Currency crises",
}

    
def compute_and_save_EPU_results(country: str = "Argentina", sub_category: EPUCategoriesType = EPUCategoriesType.NONE):

    DEFAULT_COUNTRY = "argentina"
    BASE_DIR = Path(__file__).resolve().parent
    events_file = "events_eng_jp.json" 
    events_path = BASE_DIR.parent / "src" / "Events_news" / events_file

    with open(events_path, 'r', encoding='utf-8') as f:
        events = json.load(f)


    country = country.lower()
    save_results_dir = BASE_DIR.parent / "data" / "results"
    save_results_dir.mkdir(parents=True, exist_ok=True)

    if sub_category is EPUCategoriesType.NONE:
        list_of_csv = [f"epu_{country}_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv",]
        if country == DEFAULT_COUNTRY:
            results_file = save_results_dir / f"epu_analysis_results_udesa_jp.xlsx"
            data_paths = [BASE_DIR.parent / "data" / csv for csv in list_of_csv]
        else:
            results_file = save_results_dir / "countries" / f"epu_analysis_results_udesa_jp_{country}.xlsx"
            data_paths = [BASE_DIR.parent / "data" / "countries" / csv for csv in list_of_csv]

    else:
        sub_category_str = sub_category.value
        list_of_csv = [f"epu_{country}_key_words_gdelt_maped_jp_{sub_category_str}_maped_all_media_with_sentiment.csv",]
        if country == DEFAULT_COUNTRY:
            results_file = save_results_dir / "subcategories" / f"epu_analysis_results_udesa_jp_{sub_category_str}.xlsx"
            (save_results_dir / "subcategories").mkdir(parents=True, exist_ok=True)
            data_paths = [BASE_DIR.parent / "data" / "subcategories" / csv for csv in list_of_csv]
        else:
            results_file = save_results_dir / "subcategories" / "countries" / f"epu_analysis_results_udesa_jp_{sub_category_str}_{country}.xlsx"
            data_paths = [BASE_DIR.parent / "data" / "subcategories" / "countries" / csv for csv in list_of_csv]

    #Parámetros determinados en el desarrollo.--
    media_exclude_list = []#["Tn", "Diariouno"]
    renorm = "M"
    tone_standarize = True  # Cambia a False si no querés estandarizar el tono
    tone_adjust_is_simple = False  # Cambia a False si querés usar el ajuste por percentiles
    proces_tone_monthly = False
    tone_threshold = 1.0
    #-------------------------------------------
    
    df_monthly = pd.DataFrame()
    for path in data_paths:
        df_raw = pd.read_csv(path, index_col=0)
        df_raw.index = pd.to_datetime(df_raw.index, errors="coerce")

        df_monthly = get_epu_and_resample_from_daily_selector(df_raw, renorm, media_exclude_list, tone_standarize=tone_standarize, tone_adjust_is_simple=tone_adjust_is_simple, process_tone_monthly=proces_tone_monthly, tone_threshold=tone_threshold)

    ghirelli_bench = BASE_DIR.parent / "data" / 'EPU_All_benchmark_ghirelli.xlsx'
    df = pd.read_excel(ghirelli_bench, sheet_name='data')
    df['datem'] = pd.to_datetime(df['datem'])
    df.set_index('datem', inplace=True)
    benchmark_epu_arg_ghirelli = df['EPU_ARG_local']

    with pd.ExcelWriter(results_file) as writer:
        df_monthly.to_excel(writer, sheet_name='EPU_Monthly')
        benchmark_epu_arg_ghirelli.to_excel(writer, sheet_name='Benchmark_EPU')
            
            
def join_and_save_subcategories_compare(country: str = "Argentina", output_path: Path | None = None):
    """
    Joins the 'EPU UdeSA' column from each subcategory results file with the
    'Exclude none' column from the main results file, and writes the combined
    DataFrame to MINIMAL_DOCKER_PLOT-main/data/all_subcategories_compare.xlsx.

    Output sheets:
        'Data'      — monthly EPU per subcategory + main EPU, one column each, index=fecha
        'benchmark' — Ghirelli EPU_ARG_local series, index=fecha
    """
    DEFAULT_COUNTRY = "argentina"
    BASE_DIR = Path(__file__).resolve().parent
    results_dir = BASE_DIR.parent / "data" / "results"
    subcat_dir = results_dir / "subcategories"
    country_lower = country.lower()

    # --- main file (NONE category) ---
    if country_lower == DEFAULT_COUNTRY:
        main_file = results_dir / "epu_analysis_results_udesa_jp.xlsx"
    else:
        main_file = results_dir / "countries" / f"epu_analysis_results_udesa_jp_{country_lower}.xlsx"

    main_epu = pd.read_excel(main_file, sheet_name="EPU_Monthly", index_col=0)
    main_epu.index = pd.to_datetime(main_epu.index)
    combined = main_epu[["EPU UdeSA"]]

    # --- one subcategory file per category ---
    for sub_category, display_name in _SUBCATEGORY_DISPLAY_NAMES.items():
        sub_key = sub_category.value
        if country_lower == DEFAULT_COUNTRY:
            sub_file = subcat_dir / f"epu_analysis_results_udesa_jp_{sub_key}.xlsx"
        else:
            sub_file = subcat_dir / "countries" / f"epu_analysis_results_udesa_jp_{sub_key}_{country_lower}.xlsx"

        sub_df = pd.read_excel(sub_file, sheet_name="EPU_Monthly", index_col=0)
        sub_df.index = pd.to_datetime(sub_df.index)
        combined = combined.join(
            sub_df[["EPU UdeSA"]].rename(columns={"EPU UdeSA": display_name}),
            how="inner"
        )

    # subcategory columns first, main EPU last — matches the hand-made file layout
    subcategory_cols = list(_SUBCATEGORY_DISPLAY_NAMES.values())
    combined = combined[subcategory_cols + ["EPU UdeSA"]]

    # drop leading rows where all EPU values are 0 (no matches yet in early months)
    combined = combined.loc[(combined != 0).any(axis=1)]

    # --- benchmark (read from main file, rename index to 'fecha', drop NaN) ---
    benchmark = pd.read_excel(main_file, sheet_name="Benchmark_EPU", index_col=0)
    benchmark.index = pd.to_datetime(benchmark.index)
    benchmark.index.name = "fecha"
    benchmark = benchmark.dropna()

    # --- write output to the dashboard data directory ---
    if output_path is None:
        output_path = BASE_DIR.parent.parent / "MINIMAL_DOCKER_PLOT-main" / "data" / "all_subcategories_compare.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path) as writer:
        combined.to_excel(writer, sheet_name="Data")
        benchmark.to_excel(writer, sheet_name="benchmark")

    print(f"✓ Saved combined subcategories ({len(combined)} rows) to {output_path}")


if __name__ == "__main__":
    country = "Argentina"
    sub_category = EPUCategoriesType.NONE
    compute_and_save_EPU_results(country=country, sub_category=sub_category)
