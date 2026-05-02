import numpy as np
import pandas as pd


def get_epu_and_resample_from_daily_selector(df_input: pd.DataFrame, freq: str = "ME", exclude_medios: list[str] = [], tone_standarize: bool = False, tone_adjust_is_simple: bool = False, process_tone_monthly: bool = True, tone_threshold: float = 1.0) -> pd.DataFrame:
    if process_tone_monthly:
        return __get_epu_and_resample_from_daily_montlhy_tone_process(df_input, freq, exclude_medios, tone_standarize, tone_adjust_is_simple, process_tone_monthly)
    else:
        return __get_epu_and_resample_from_daily_tone_process(df_input, freq, exclude_medios, tone_threshold)

def __get_epu_and_resample_from_daily_montlhy_tone_process(df_input: pd.DataFrame, freq: str = "ME", exclude_medios: list[str] = [], tone_standarize: bool = False, tone_adjust_is_simple: bool = False) -> pd.DataFrame:
    """
    Calcula el índice EPU mensual siguiendo la metodología Baker, Bloom y Davis.
    - Calcula epu_raw diario por medio.
    - Agrega matches y total por medio y mes.
    - Calcula epu_raw mensual por medio.
    - Estandariza por medio.
    - Promedia entre medios (excluyendo los especificados en exclude_medios).
    - Normaliza a media 100 en periodo base completo.
    - Ajusta el EPU usando el tono promedio de la columna 'tono_float'.
    
    Parameters:
        df_input: DataFrame con columnas ['fecha', 'medio', 'matches', 'total', 'tono_float']
        freq: Frecuencia de resampleo (default 'ME' para fin de mes).
        exclude_medios: Lista de medios a excluir (default vacía).
        
    Returns:
        DataFrame con índice fecha y columnas: ['epu_index', 'epu_index_tone_adjusted', 'tono_float'].
    """
    df = df_input.copy()

    tone_data = df['tono'].apply(process_tone)
    tone_data = pd.DataFrame(tone_data.tolist(), index=df.index, columns=[
        'Tone', 'Positive Score', 'Negative Score', 'Polarity',
        'Activity Reference Density', 'Self/Group Reference Density'
    ])

    df['tono_float'] = tone_data['Tone'] 
    df['epu_raw'] = df['matches'] / df['total']
    
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
    df['month'] = df.index.to_period(freq)

    if len(exclude_medios) > 0:
        df = df[~df['medio'].isin(exclude_medios)]

    monthly = df.groupby(['medio', 'month']).agg({'matches': 'sum', 'total': 'sum', 'tono_float': 'mean'}).reset_index()
    monthly['epu_raw'] = monthly['matches'] / monthly['total']

    monthly['epu_std'] = monthly.groupby('medio')['epu_raw'].transform(__standardize_to_BBD)

    monthly_mean = monthly.groupby('month').agg({'epu_std': 'mean', 'tono_float': 'mean'}).reset_index() #Agrego por mes y calculo la media de epu_std y tono_float

    base_mean = monthly_mean['epu_std'].mean()

    monthly_mean['epu_index'] = (monthly_mean['epu_std'] / base_mean) * 100

    monthly_mean['epu_index_tone_adjusted'] = __adjust_by_tone(monthly_mean['epu_std'], monthly_mean['tono_float'], base_mean, tone_standarize, tone_adjust_is_simple)

    monthly_mean['fecha'] = monthly_mean['month'].dt.to_timestamp()
    monthly_mean.set_index('fecha', inplace=True)

    return monthly_mean[['epu_index', 'epu_index_tone_adjusted', 'tono_float']]

def __get_epu_and_resample_from_daily_tone_process(df_input: pd.DataFrame, freq: str = "ME", exclude_medios: list[str] = [], tone_threshold: float = 1.0) -> pd.DataFrame:

    df = df_input.copy()

    tone_data = df['tono'].apply(process_tone)
    tone_data = pd.DataFrame(tone_data.tolist(), index=df.index, columns=[
        'Tone', 'Positive Score', 'Negative Score', 'Polarity',
        'Activity Reference Density', 'Self/Group Reference Density'
    ])

    df['tono_float'] = tone_data['Tone'] 

    df['epu_raw'] = df['matches'] / df['total']
    
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
    df['month'] = df.index.to_period(freq)

    if len(exclude_medios) > 0:
        df = df[~df['medio'].isin(exclude_medios)]

    positive_proportion = df.groupby('month').apply(lambda x: (x['tono_float'] > tone_threshold).mean()).reset_index(name='positive_proportion')
    negative_proportion = df.groupby('month').apply(lambda x: (x['tono_float'] < -tone_threshold).mean()).reset_index(name='negative_proportion')
    neutral_proportion = df.groupby('month').apply(lambda x: (abs(x['tono_float']) <= tone_threshold).mean()).reset_index(name='neutral_proportion')

    monthly = df.groupby(['medio', 'month']).agg({'matches': 'sum', 'total': 'sum', 'tono_float': 'mean'}).reset_index()
    monthly['epu_raw'] = monthly['matches'] / monthly['total']

    monthly['epu_std'] = monthly.groupby('medio')['epu_raw'].transform(__standardize_to_BBD)

    monthly_mean = monthly.groupby('month').agg({'epu_std': 'mean', 'tono_float': 'mean'}).reset_index() #Agrego por mes y calculo la media de epu_std y tono_float

    base_mean = monthly_mean['epu_std'].mean()

    monthly_mean['epu_index'] = (monthly_mean['epu_std'] / base_mean) * 100

    monthly_mean['fecha'] = monthly_mean['month'].dt.to_timestamp()
    monthly_mean.set_index('fecha', inplace=True)

    positive_proportion.set_index(monthly_mean.index, inplace = True)
    negative_proportion.set_index(monthly_mean.index, inplace = True)
    neutral_proportion.set_index(monthly_mean.index, inplace = True)

    monthly_mean['positive_proportion'] = positive_proportion['positive_proportion']
    monthly_mean['negative_proportion'] = negative_proportion['negative_proportion']
    monthly_mean['neutral_proportion'] = neutral_proportion['neutral_proportion']

    monthly_mean.drop(columns=['month', 'epu_std'], inplace=True)
    monthly_mean.rename(columns={'epu_index': 'EPU UdeSA'}, inplace=True)

    counts = get_counts(df, freq) # Para medir la proporción de subcategorías
    counts.index = monthly_mean.index
    monthly_mean = monthly_mean.join(counts)
    monthly_mean.rename(columns={'epu_std': 'EPU Counts'}, inplace=True) 
    return monthly_mean


def get_counts(df_input:pd.DataFrame, freq:str='M') ->pd.DataFrame:
    df = df_input.copy() # Evito modificar el df original por referencia
    df['epu_raw'] = df['matches'] / df['total']

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
    df['month'] = df.index.to_period(freq)

    monthly = df.groupby(['medio', 'month']).agg({'matches': 'sum', 'total': 'sum'}).reset_index()
    monthly['epu_raw'] = monthly['matches'] / monthly['total']
    monthly['epu_std'] = monthly.groupby('medio')['epu_raw'].transform(lambda x: x / x.std()) # Estandarizo los medios para evitar sesgos

    monthly_mean = monthly.groupby('month').agg({'epu_std': 'sum'}).reset_index() # Sumo los medios
    monthly_mean.set_index('month', inplace=True)
    return pd.DataFrame(monthly_mean['epu_std'])


def get_epu_by_media_and_resample_from_daily(df_input: pd.DataFrame, freq: str = "ME") -> pd.DataFrame:
    
    """
    Calcula el índice EPU mensual por medio siguiendo la metodología Baker, Bloom y Davis.
    - Calcula epu_raw diario por medio.
    - Agrega matches y total por medio y mes.
    - Calcula epu_raw mensual por medio.
    - Estandariza por medio.
    - Normaliza a media 100 en periodo base completo por medio.
    - Devuelve un DataFrame con columnas epu_index_media_name.
    """

    df = df_input.copy()
    df['epu_raw'] = df['matches'] / df['total']
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
    df['month'] = df.index.to_period(freq)

    monthly = df.groupby(['medio', 'month']).agg({'matches': 'sum', 'total': 'sum'}).reset_index()
    monthly['epu_raw'] = monthly['matches'] / monthly['total']

    result = pd.DataFrame()
    for medio in monthly['medio'].unique():
        medio_data = monthly[monthly['medio'] == medio].copy()
        if not medio_data.empty:
            medio_data['epu_std'] = __standardize_to_BBD(medio_data['epu_raw'])
            base_mean = medio_data['epu_std'].mean()
            medio_data['epu_index'] = (medio_data['epu_std'] / base_mean) * 100
            result[f'epu_index_{medio}'] = medio_data.set_index('month')['epu_index']

    result.index = result.index.to_timestamp()
    result.index.name = 'fecha'
    return result

def sentiment_indicator(tono_float:pd.DataFrame, polarity: pd.DataFrame) -> pd.DataFrame:
    '''
    Calcula un indicador de sentimiento basado en la columna 'tono_float'.
    - Normaliza el tono a base 100.
    '''
    tone_indicator = (tono_float - tono_float.expanding().mean()) / tono_float.expanding().std(ddof=0)
    #tone_indicator = tone_indicator.mul( 1+ polarity/100, axis = 0)
    tone_indicator = (tone_indicator / tone_indicator.abs().max()) * 100
    return pd.DataFrame(tone_indicator) #quiero que el sentimiento sea positivo cuando es negativo, por lo que multiplico por -1

def process_tone(tone_str: str) -> list[float]:
    if pd.isna(tone_str) or not isinstance(tone_str, str):
        return np.nan
    
    tone_list = tone_str.split(',')
    if not tone_list or len(tone_list) < 2: 
        return [np.nan]*6
    
    tones = []
    for x in tone_list[:-1]: 
        cleaned = x.replace('.', '').replace('-', '')
        if cleaned.isdigit() or (cleaned.lstrip('0').isdigit() and x.startswith('-')):
            tones.append(float(x))
    
    return tones

def __standardize_to_BBD(x):
    return x / x.std(ddof=0)  # Notar que sólo divido por la desviación estándar, no resto la media por que sino dan valores de epu negativos

def __adjust_by_tone(epu_std_adjusted: pd.Series, tone_flat: pd.Series, epu_historical_mean: float | None = None, tone_standarize: bool = False, is_simple: bool = False) -> pd.Series:
    if is_simple:
        return __adjust_by_tone_simple(epu_std_adjusted, tone_flat, epu_historical_mean, tone_standarize)
    else:
        return __adjust_by_tone_by_percentile(epu_std_adjusted, tone_flat, epu_historical_mean, tone_standarize)

def __adjust_by_tone_by_percentile(epu_std_adjusted: pd.Series, tone_flat: pd.Series, epu_historical_mean: float | None = None, tone_standarize: bool = False) -> pd.Series:

    if tone_standarize:
        tone_flat = (tone_flat - tone_flat.expanding().mean()) / tone_flat.expanding(5).std(ddof=0) #expanding con ventana de 5 para suavizar el tono

    if epu_historical_mean is None:
        epu_historical_mean = epu_std_adjusted.mean()

    epu_tone_adjusted = 100 * (epu_std_adjusted / epu_historical_mean) * (1 - (tone_flat.apply(__adjust_by_value)))

    return epu_tone_adjusted

def __adjust_by_tone_simple(epu_std_adjusted: pd.Series, tone_flat: pd.Series, epu_historical_mean: float | None = None, tone_standarize: bool = False) -> pd.Series:

    if tone_standarize:
        tone_flat = (tone_flat - tone_flat.expanding().mean()) / tone_flat.expanding(5).std(ddof=0) #expanding con ventana de 5 para suavizar el tono

    if epu_historical_mean is None:
        epu_historical_mean = epu_std_adjusted.mean()

    epu_tone_adjusted = (epu_std_adjusted / epu_historical_mean) * (1 + tone_flat)

    return epu_tone_adjusted

def __adjust_by_value(value):
    threshold = 1 # This threshold can be adjusted based on the desired sensitivity. Not implemented yet.
    return 0
    # if value > threshold:
    #     return 0
    # else:
    #     return 1

def __get_tone_side(value: float, threshold:float = 1.0):

    if abs(value) <= threshold:
        return 0.0
    elif value > threshold:
        return 1.0
    elif value < -threshold:
        return -1.0    
