from matplotlib import pyplot as plt
import pandas as pd
from pathlib import Path
import pandas as pd

from Helpers.analisys_helpers import get_epu_by_media_and_resample_from_daily
from Helpers.gdelt_request_helpers import normalizar_epu_v2


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent

    list_of_csv = [
        "epu_argentina_key_words_gdelt_maped_jp_all_media.csv",
    ]

    data_paths = [BASE_DIR.parent / "data" / csv for csv in list_of_csv]

    renorm = "M"
    span = 30  # Ventana de suavizado para la media móvil, 30 días para consistencia con benchmarks


    df_raw = pd.read_csv(data_paths[0], index_col=0)
    df_raw.index = pd.to_datetime(df_raw.index, errors="coerce")
    df = normalizar_epu_v2(df_raw) 
    df_monthly = get_epu_by_media_and_resample_from_daily(df_raw, renorm)

    columns = [x.replace("epu_argentina_key_words_", "").split(".")[0] for x in list_of_csv]


    ghirelli_bench = BASE_DIR.parent / "data" / 'EPU_All_benchmark_ghirelli.xlsx'
    df = pd.read_excel(ghirelli_bench, sheet_name='data')
    df['datem'] = pd.to_datetime(df['datem'])
    df.set_index('datem', inplace=True)
    benchmark_epu_arg_ghirelli = df['EPU_ARG_local']

    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#C9CBCF', 
            '#66FF66', '#FF33CC', '#CC9900', '#3399FF', '#FF3333', '#33FF99', '#9933FF', 
            '#FF99CC', '#66CCCC', '#FFCC66', '#9999FF']

    plt.figure(figsize=(22, 10))
    for i, column in enumerate(df_monthly.columns):
        plt.plot(df_monthly.index, df_monthly[column], label=column, color=colors[i % len(colors)])
    plt.plot(benchmark_epu_arg_ghirelli.loc[df_monthly.index[0]:], label='EPU Argentina Ghirelli Benchmark', color='#000000', linewidth=2, linestyle='--')  # Black for benchmark
    plt.title("EPU Argentina (GDELT) - Eventos Relevantes", fontsize=16)
    plt.xlabel("Fecha", fontsize=12)
    plt.ylabel("EPU BBD", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.4)
    plt.legend(loc='upper left', fontsize=11)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
