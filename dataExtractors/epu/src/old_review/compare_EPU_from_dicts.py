from pathlib import Path
import pandas as pd
from Helpers.analisys_helpers import __get_epu_and_resample_from_daily_montlhy_tone_process
#from Helpers.gdelt_request_helpers import normalizar_epu_v2

from Helpers.plot_helpers import plot_epu_interactive

if __name__ == "__main__":

    BASE_DIR = Path(__file__).resolve().parent
    DATA_PATH_1 = BASE_DIR.parent / "data" / "epu_argentina_key_words_gdelt_maped_all_media.csv"
    DATA_PATH_2 = BASE_DIR.parent / "data" / "epu_argentina_key_words_paper_ghirelli_maped_all_media.csv"

    BENCHMARK_PATH = BASE_DIR.parent / "data" / "All_Country_monthly_Data_benchmark.xlsx"

    data_paths = [DATA_PATH_1, DATA_PATH_2]
    columns = [x.__str__().split('\\')[-1].split('.')[0] for x in data_paths]


    renorm = "M"
    span = 30  # Ventana de suavizado para la media móvil, 30 días para consistencia con benchmarks

    dfs = pd.DataFrame()
    dfs_monthly = pd.DataFrame()
    for path in data_paths:
        df_raw = pd.read_csv(path, index_col=0)
        df_raw.index = pd.to_datetime(df_raw.index, errors="coerce")
        df = pd.DataFrame()#normalizar_epu_v2(df_raw) Esto se borró
        dfs = pd.concat([dfs, pd.DataFrame(df['epu_index'])], axis = 1)
        df_monthly = __get_epu_and_resample_from_daily_montlhy_tone_process(df_raw, renorm)
        dfs_monthly = pd.concat([dfs_monthly, pd.DataFrame(df_monthly["epu_index"])], axis = 1)

    dfs_monthly.columns = columns

    benchmark = pd.read_excel(BENCHMARK_PATH)
    benchmark['Date'] = pd.to_datetime(benchmark[['Year', 'Month']].assign(DAY=1))
    benchmark.drop(columns=['Year', 'Month'], inplace=True)
    benchmark.set_index('Date', inplace=True)
    benchmark = benchmark.loc[dfs_monthly.index[0]:dfs_monthly.index[-1]]

    region = ["Brazil", "Chile", "Spain"]

    fig = plot_epu_interactive(benchmark, region, dfs_monthly, renorm, dfs, span)
    fig.show()