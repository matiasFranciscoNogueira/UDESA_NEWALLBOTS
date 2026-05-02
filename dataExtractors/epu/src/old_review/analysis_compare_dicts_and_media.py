from matplotlib import pyplot as plt
import pandas as pd
from pathlib import Path
import seaborn as sns

from Helpers.analisys_helpers import __get_epu_and_resample_from_daily_montlhy_tone_process
from Helpers.gdelt_request_helpers import normalizar_epu_v2


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent

    list_of_csv = [
        "epu_argentina_key_words_gdelt_maped_jp_all_media.csv",
    ]

    data_paths = [BASE_DIR.parent / "data" / csv for csv in list_of_csv]

    renorm = "M"
    span = 30  # Ventana de suavizado para la media móvil, 30 días para consistencia con benchmarks
    epus_monthly = pd.DataFrame()

    for path in data_paths:
        df_raw = pd.read_csv(path, index_col=0)
        df_raw.index = pd.to_datetime(df_raw.index, errors="coerce")
        df = normalizar_epu_v2(df_raw) 
        df_monthly = __get_epu_and_resample_from_daily_montlhy_tone_process(df_raw, renorm)
        epus_monthly = pd.concat([epus_monthly, df_monthly["epu_index"]], axis=1)

    columns = [x.replace("epu_argentina_key_words_", "").split(".")[0] for x in list_of_csv]
    epus_monthly.columns = columns


    ghirelli_bench = BASE_DIR.parent / "data" / 'EPU_All_benchmark_ghirelli.xlsx'
    df = pd.read_excel(ghirelli_bench, sheet_name='data')
    df['datem'] = pd.to_datetime(df['datem'])
    df.set_index('datem', inplace=True)
    benchmark_epu_arg_ghirelli = df['EPU_ARG_local']

    corrs = epus_monthly.corrwith(benchmark_epu_arg_ghirelli, axis=0)

    no_cor_plot = True
    if no_cor_plot:

        plt.figure(figsize=(18, 8))
        plt.plot(epus_monthly.index, epus_monthly, linewidth=2, linestyle='-', alpha=0.7)
        plt.plot(benchmark_epu_arg_ghirelli.loc[epus_monthly.index[0]:], label='EPU Argentina Ghirelli Benchmark', color='black', linewidth=2, linestyle='--')
        plt.title("EPU Argentina (GDELT) - Comparación de diferentes keywords")
        plt.xlabel("Fecha")
        plt.ylabel("EPU BBD")
        plt.grid(True)
        plt.legend(epus_monthly.columns, loc='upper left')
        plt.tight_layout()
        plt.show()
        
    else:
        fig, axes = plt.subplots(1, 2, figsize=(18, 8), gridspec_kw={'width_ratios': [4, 1]})

        axes[0].plot(epus_monthly.index, epus_monthly, linewidth=2, linestyle='-', alpha=0.7)
        axes[0].plot(benchmark_epu_arg_ghirelli.loc[epus_monthly.index[0]:], label='EPU Argentina Ghirelli Benchmark', color='black', linewidth=2, linestyle='--')
        axes[0].set_title("EPU Argentina (GDELT) - Comparación de diferentes keywords")
        axes[0].set_xlabel("Fecha")
        axes[0].set_ylabel("EPU BBD")
        axes[0].grid(True)
        axes[0].legend(epus_monthly.columns, loc='upper left')

        sns.barplot(x=corrs.values, y=corrs.index, ax=axes[1], palette='coolwarm', hue='y', legend=False, orient='h')
        axes[1].set_title("Correlación con Benchmark")
        axes[1].set_xlim(-1, 1)

        plt.tight_layout()
        plt.show()