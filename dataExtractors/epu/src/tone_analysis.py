import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from Helpers.analisys_helpers import process_tone, sentiment_indicator


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent

    list_of_csv = [
        "epu_argentina_key_words_gdelt_maped_jp_all_media_with_sentiment.csv",
    ]

    data_paths = [BASE_DIR.parent / "data" / csv for csv in list_of_csv]
    tono_float = pd.DataFrame()

    df_raw = pd.read_csv(data_paths[0], index_col=0)
    df_raw.index = pd.to_datetime(df_raw.index, errors="coerce")
    tono = df_raw['tono'].apply(process_tone)

    tono_df = pd.DataFrame(tono.to_list(), index=tono.index)
    tono_df = tono_df.reset_index()

    tono_df.columns = ['fecha', 'tone', 'positive', 'negative', 'polarity', 'activity ref density', 'group ref density']

    describe_columns = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
    desc_stats = tono_df.describe()
    desc_df = pd.DataFrame(desc_stats).T
    desc_df = desc_df[describe_columns]
    desc_df = desc_df.iloc[1:]

    df_melted = pd.melt(desc_df.reset_index(), id_vars=['index'], value_vars=desc_df.columns, var_name='metric', value_name='value')
    df_melted = df_melted[~(df_melted['metric'] == 'count')]
    df_melted = df_melted.rename(columns={'index': 'statistic'})

    sentiment = sentiment_indicator(tono_df['tone'], tono_df['polarity'])
    sentiment = pd.DataFrame(sentiment.values, index=tono_df['fecha'])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=False)
    bar_width = 0.1
    index = range(len(df_melted['metric'].unique()))

    for i, stat in enumerate(df_melted['statistic'].unique()):
        subset = df_melted[df_melted['statistic'] == stat]
        ax1.bar([x + i * bar_width for x in index], subset['value'], bar_width, label=stat)

    ax1.set_xlabel('Métrica')
    ax1.set_ylabel('Valores')
    ax1.set_title('Estadísticas Descriptivas Agrupadas por Métrica')
    ax1.set_yticks(np.arange(-40, 60, 5))
    ax1.set_xticks([x + bar_width * 2.5 for x in index])
    ax1.set_xticklabels(df_melted['metric'].unique(), rotation=45, ha='right')
    ax1.legend(title='Estadística')
    ax1.grid(True, alpha=0.3)

    ax2.hist(tono_df['tone'], bins=80, edgecolor='black', color='#1f77b4', label='Tone', alpha=0.7)
    ax2.hist(tono_df['polarity'], bins=80, edgecolor='black', color='#ff7f0e', label='Polarity', alpha=0.7)
    ax2.set_xticks(np.arange(-20, 21, 1))
    ax2.set_xlim(-20, 20)
    ax2.legend()
    ax2.set_xlabel('Valores de Tono/Polaridad')
    ax2.set_ylabel('Frecuencia')
    ax2.set_title('Histograma de tono y polaridad en artículos')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


plt.figure(figsize=(12, 6))
plt.plot(sentiment.index, sentiment, label='Sentiment', color='purple', linewidth=2)
plt.axhline(0, color='black', linewidth=1, linestyle='--')
plt.fill_between(sentiment.index, -100, -33, color='red', alpha=0.1, label='Negativo')
plt.fill_between(sentiment.index, -33, 33, color='yellow', alpha=0.1, label='Neutro')
plt.fill_between(sentiment.index, 33, 100, color='green', alpha=0.1, label='Positivo')
plt.title('Sentiment Diario', fontsize=16, fontweight='bold')
plt.xlabel('Fecha', fontsize=12)
plt.ylabel('Sentiment', fontsize=12)

plt.legend(frameon=True, loc='upper left', fontsize=10)
plt.grid(True, linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show()

