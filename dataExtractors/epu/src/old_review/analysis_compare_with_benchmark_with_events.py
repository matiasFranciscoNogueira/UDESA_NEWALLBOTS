import json
from matplotlib import pyplot as plt
import pandas as pd
from pathlib import Path
import pandas as pd
from adjustText import adjust_text
import textwrap
from Helpers.analisys_helpers import sentiment_indicator, get_epu_and_resample_from_daily_selector


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    events_file = "events_eng_jp.json"  # events file
    events_path = BASE_DIR.parent / "src" / "Events_news" / events_file

    with open(events_path, 'r', encoding='utf-8') as f:
        events = json.load(f)


    list_of_csv = [
        "epu_argentina_key_words_gdelt_maped_jp_trade_maped_all_media_with_sentiment.csv",
    ]

    media_exclude_list = ["Tn", "Diariouno"]

    data_paths = [BASE_DIR.parent / "data" / "subcategories" / csv for csv in list_of_csv]

    renorm = "M"
    span = 30  # Ventana de suavizado para la media móvil, 30 días para consistencia con benchmarks
    tone_standarize = True  # Cambia a False si no querés estandarizar el tono
    tone_adjust_is_simple = False  # Cambia a False si querés usar el ajuste por percentiles
    proces_tone_montly = False
    epus_monthly = pd.DataFrame()
    tono_float = pd.DataFrame()

    tone_threshold = 1.0

    for path in data_paths:
        df_raw = pd.read_csv(path, index_col=0)
        df_raw.index = pd.to_datetime(df_raw.index, errors="coerce")
        df_monthly = get_epu_and_resample_from_daily_selector(df_raw, renorm, media_exclude_list, tone_standarize=tone_standarize, tone_adjust_is_simple=tone_adjust_is_simple, process_tone_monthly=proces_tone_montly, tone_threshold=tone_threshold)
        epus_monthly = pd.concat([epus_monthly, df_monthly[["epu_index", "epu_index_tone_adjusted"]]], axis=1)

        df_monthly_exclude_none = get_epu_and_resample_from_daily_selector(df_raw, renorm, [], tone_standarize=tone_standarize, tone_adjust_is_simple=tone_adjust_is_simple, process_tone_monthly=proces_tone_montly, tone_threshold=tone_threshold)
        df_monthly_exclude_none["Exclude none"] = df_monthly_exclude_none["epu_index"]
        epus_monthly = pd.concat([epus_monthly, df_monthly_exclude_none[["epu_index", "epu_index_tone_adjusted"]]], axis=1)

        tono_float = pd.concat([tono_float, df_monthly[["tono_float"]]], axis=1)

    base_names = [x.replace("epu_argentina_key_words_", "").split(".")[0] for x in list_of_csv]
    tono_float.columns = [x.replace("epu_argentina_key_words_", "Tone_").split(".")[0] for x in list_of_csv]

    columns = []
    for name in base_names:
        columns.append(name)
        columns.append(f"{name}_adjusted")

    columns.extend(["Exclude none", "Exclude none adj by tone"])

    epus_monthly.columns = columns

    ghirelli_bench = BASE_DIR.parent / "data" / 'EPU_All_benchmark_ghirelli.xlsx'
    df = pd.read_excel(ghirelli_bench, sheet_name='data')
    df['datem'] = pd.to_datetime(df['datem'])
    df.set_index('datem', inplace=True)
    benchmark_epu_arg_ghirelli = df['EPU_ARG_local']

    sentiment_indicator_data = sentiment_indicator(tono_float, pd.DataFrame())

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(22, 12), gridspec_kw={'height_ratios': [3, 1]}, sharex=True)
    
    ax1.plot(benchmark_epu_arg_ghirelli.loc[epus_monthly.index[0]:], label='EPU Argentina Ghirelli Benchmark', color='black', linewidth=2, linestyle='--')

    ax1.plot(epus_monthly.index, epus_monthly.iloc[:, 0], label=f'EPU GDELT Exclude {media_exclude_list}', linewidth=2, linestyle='-', color='steelblue')
    ax1.plot(epus_monthly.index, epus_monthly.iloc[:, 1], label='EPU GDELT Exclude Adj', linewidth=2, linestyle='-', color='red')
    ax1.plot(epus_monthly.index, epus_monthly.iloc[:, 2], label=f'EPU GDELT Exclude None', linewidth=2, linestyle='-', color='steelblue', alpha=0.5)
    ax1.plot(epus_monthly.index, epus_monthly.iloc[:, 3], label='EPU GDELT Exclude None Adj', linewidth=2, linestyle='-', color='red', alpha=0.5)

    texts = []
    for fecha_str, datos in events.items():
        fecha = pd.to_datetime(fecha_str + "-01")
        if fecha in epus_monthly.index:
            valor = epus_monthly.loc[fecha].max()
            evento_wrap = "\n".join(textwrap.wrap(datos["event"], width=40))  # multilínea
            texts.append(
                ax1.text(
                    fecha, valor, evento_wrap,
                    fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", lw=0.6, alpha=0.9)
                )
            )
            ax1.plot(fecha, valor, 'ko', markersize=3)

    adjust_text(
        texts,
        ax=ax1,
        expand_points=(1.1, 1.5),
        expand_text=(1.5, 2),
        arrowprops=dict(
            arrowstyle="->",
            color="gray",
            lw=0.8,
            connectionstyle="angle3,angleA=0,angleB=90"
        ),
        only_move={'points': 'y', 'text': 'xy'}
    )

    ax1.set_title("EPU Argentina (GDELT) - Eventos Relevantes", fontsize=16)
    ax1.set_ylabel("EPU BBD", fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.4)
    ax1.legend(loc='upper left', fontsize=11)

    ax2.bar(tono_float.index, tono_float[tono_float.columns[0]].values, color='lightblue', edgecolor='black', alpha=1, width=20)
    ax2.plot(tono_float.expanding().mean(), color='orange', linewidth=2, alpha=0.4)
    ax2.set_xlabel("Fecha", fontsize=12)
    ax2.set_ylabel("Tono", fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.4)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(22, 10))
    ax = plt.gca()
    x = sentiment_indicator_data.index
    y = sentiment_indicator_data.iloc[:, 0].values

    ax.plot(x, y, label='Tone Indicator', color='#800080', linewidth=2.5)

    ax.fill_between(x, -100, -33, color='red', alpha=0.3, label='Bad')
    ax.fill_between(x, -33, 33, color='yellow', alpha=0.3, label='Regular')
    ax.fill_between(x, 33, 100, color='green', alpha=0.3, label='Good')

    ax.set_title("Tone Indicator (news sentiment)", fontsize=18, pad=15, fontweight='bold')
    ax.set_xlabel("Fecha", fontsize=14, labelpad=10)
    ax.set_ylabel("News Sentiment", fontsize=14, labelpad=10)

    ax.grid(True, linestyle='--', alpha=0.2, linewidth=0.5)
    ax.tick_params(axis='x', rotation=45, labelsize=12)
    ax.tick_params(axis='y', labelsize=12)

    ax.legend(fontsize=12, loc='upper right', frameon=True, facecolor='white', edgecolor='gray')
    plt.tight_layout()

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('gray')
    ax.spines['bottom'].set_color('gray')
    plt.show()