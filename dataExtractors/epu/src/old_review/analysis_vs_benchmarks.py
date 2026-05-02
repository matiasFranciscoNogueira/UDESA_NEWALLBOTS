from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from Helpers.analisys_helpers import __get_epu_and_resample_from_daily_montlhy_tone_process
from Helpers.gdelt_request_helpers import normalizar_epu_v2

if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parent
    DATA_PATH = BASE_DIR.parent / "data" / "epu_argentina_key_words_paper_ghirelli_maped.csv"
    BENCHMARK_PATH = BASE_DIR.parent / "data" / "All_Country_monthly_Data_benchmark.xlsx"

    df_raw = pd.read_csv(DATA_PATH, index_col=0)
    df_raw.index = pd.to_datetime(df_raw.index, errors="coerce")
    df = normalizar_epu_v2(df_raw) 

    renorm = "M"
    span = 30  # Ventana de suavizado para la media móvil, 30 días para consistencia con benchmarks
    df_monthly = __get_epu_and_resample_from_daily_montlhy_tone_process(df_raw, renorm)

    benchmark = pd.read_excel(BENCHMARK_PATH)
    benchmark['Date'] = pd.to_datetime(benchmark[['Year', 'Month']].assign(DAY=1))
    benchmark.drop(columns=['Year', 'Month'], inplace=True)
    benchmark.set_index('Date', inplace=True)
    benchmark = benchmark.loc[df.index[0]:df.index[-1]]

    region = ["Brazil", "Chile", "Spain"]

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=False)
    axes[0].plot(benchmark.index, benchmark[region])
    axes[0].plot(df_monthly.index, df_monthly["epu_index"], label=f"Argentina renormalizado a {renorm}", color='blue', linewidth=2)
    axes[0].set_title("EPU Argentina vs Benchmarks (GDELT)")
    axes[0].grid(True)
    axes[0].legend([*region, "Argentina"], loc='upper left')  
    axes[1].plot(df.index, df["epu_index"], label="Argentina Daily", color='black', linewidth=1, linestyle='--', alpha=0.7)
    axes[1].plot(df.index, df["epu_index"].ewm(span).mean(), label="media móvil exponencial", linewidth=2)
    axes[1].set_title("EPU Argentina daily (GDELT)")
    axes[1].legend()
    axes[1].grid(True)
    plt.tight_layout()
    plt.show()

