from pathlib import Path
from google.cloud import bigquery
import pandas as pd
import datetime as dt

DEFAULT_COUNTRY = "Argentina"

def get_sql(first, last, kw:dict, media, include_goldstein: bool = False):
    """
    Genera un SQL estilo Baker y Bloom (BBD) compatible con BigQuery (RE2),
    con agrupación por medio y por fecha, incluyendo V2Tone y opcionalmente GoldsteinScale.
    """

    def group_pattern(words):
        return "(" + "|".join([r"\b" + w.replace(' ', r'\s+') + r"\b" for w in words]) + ")"

    # Construir los patrones de los grupos E, P, U y S si fuera sub-categoría
    re_e = group_pattern(kw["E"])
    re_p = group_pattern(kw["P"])
    re_u = group_pattern(kw["U"])
    if "S" in kw.keys():
        re_s = group_pattern(kw["S"])
        is_sub_category = True
    else:
        re_s = ""  # No se usará en el SQL, pero lo definimos para mantener la estructura
        is_sub_category = False

    # Armar el CASE para los medios
    case_statements = []
    for m in media:
        domain = m.replace('.', r'\.')
        name = m.split('.')[0].capitalize()
        case_statements.append("WHEN REGEXP_CONTAINS(DocumentIdentifier, r'\\." + domain + "/') THEN '" + name + "'")
    case_sql = "\n    ".join(case_statements)

    # Armar el filtro WHERE para los medios
    media_rex = "|".join([r"\." + m.replace('.', r'\.') + "/" for m in media])

    # Construir el SQL completo
    if is_sub_category:
      base_sql = f"""
      SELECT
        DATE(_PARTITIONTIME) AS fecha,
        CASE
          {case_sql}
        END AS medio,
        COUNTIF(
          REGEXP_CONTAINS(V2Themes, r'{re_e}')
          AND REGEXP_CONTAINS(V2Themes, r'{re_p}')
          AND REGEXP_CONTAINS(V2Themes, r'{re_u}')
          AND REGEXP_CONTAINS(V2Themes, r'{re_s}')
        ) AS matches,
        COUNT(*) AS total,
        V2Tone AS tono
      FROM
        `gdelt-bq.gdeltv2.gkg_partitioned`
      WHERE
        _PARTITIONDATE BETWEEN '{first.isoformat()}' AND '{last.isoformat()}'
        AND REGEXP_CONTAINS(DocumentIdentifier, r'{media_rex}')
      GROUP BY fecha, medio, V2Tone
      ORDER BY fecha, medio
      """
    else:
        base_sql = f"""
        SELECT
          DATE(_PARTITIONTIME) AS fecha,
          CASE
            {case_sql}
          END AS medio,
          COUNTIF(
            REGEXP_CONTAINS(V2Themes, r'{re_e}')
            AND REGEXP_CONTAINS(V2Themes, r'{re_p}')
            AND REGEXP_CONTAINS(V2Themes, r'{re_u}')
          ) AS matches,
          COUNT(*) AS total,
          V2Tone AS tono
        FROM
          `gdelt-bq.gdeltv2.gkg_partitioned`
        WHERE
          _PARTITIONDATE BETWEEN '{first.isoformat()}' AND '{last.isoformat()}'
          AND REGEXP_CONTAINS(DocumentIdentifier, r'{media_rex}')
        GROUP BY fecha, medio, V2Tone
        ORDER BY fecha, medio
        """

    if include_goldstein:
      sql = __include_goldstein_scale(media_rex, base_sql)
    else:
      sql = base_sql

    return sql.strip()

def get_data_from_big_query(sql: str, client: bigquery.Client) -> pd.DataFrame:
  """
  Ejecuta un SQL sobre GDELT, calcula el índice EPU por día según Baker, Bloom & Davis,
  y lo normaliza a base 100 tomando como referencia el promedio del período base.
  
  Parameters:
      sql: query SQL con cálculo de matches y total por medio y día
      client: instancia de BigQuery Client
      base_start: inicio del período base para normalización
      base_end: fin del período base para normalización
      
  Returns:
      pd.DataFrame con datos raw
  """
  df = client.query(sql).to_dataframe()
  df['fecha'] = pd.to_datetime(df['fecha'])
  df.set_index('fecha', inplace=True)
  return df

def guardar_df(df: pd.DataFrame, filename: str, folder: Path) -> None:
    """
    Guarda el DataFrame en un archivo CSV.
    """

    full_path = folder / filename

    # 🔥 Ensure full path directories exist (including subfolders)
    full_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(full_path, index=True)
    print(f"DataFrame guardado en {full_path}")
    
def get_query_estimated_price(client, SQL):
    job_cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    dry = client.query(SQL, job_config=job_cfg)

    bytes_processed = dry.total_bytes_processed
    tb_scanned = bytes_processed / 1e12           
    unit_price = 5.00                             
    estimated_cost = tb_scanned * unit_price

    print(f"Bytes a escanear: {bytes_processed:,}")
    print(f"Estimación de costo: ${estimated_cost:.2f} USD (@ ${unit_price:.2f}/TB)")

    MAX_COST_USD = 5.00
    if estimated_cost > MAX_COST_USD:
      raise ValueError(
          f"Query abortada: costo estimado ${estimated_cost:.2f} USD supera el límite de ${MAX_COST_USD:.2f} USD."
      )

    return bytes_processed

def set_epu_files_names(kw_file: str, medios: list[str], base_dir: Path, country: str, is_sub_category: bool) -> tuple[str, Path]:
    
    store_dir = Path()
    if "src" in str(base_dir):
        store_dir = base_dir.parent
    else:
        store_dir = base_dir

    if is_sub_category:
        store_dir = store_dir / "data" / "subcategories"
    else:
        store_dir = store_dir / "data"

    if country != DEFAULT_COUNTRY:
        store_dir = store_dir / "countries"

    country = country.lower()
    base_name = kw_file.split('.')[0]

    epu_file_name = f"epu_{country}_{base_name}_all_media.csv"
    
    return epu_file_name, store_dir

def get_raw_given_historical_data_from_db(store_dir: Path, epu_file_name: str, is_sub_category: bool = False) -> pd.DataFrame:
    """
    Lee el archivo CSV guardado y devuelve la fecha del último registro + 1 día.
    Si el archivo no existe, devuelve una fecha por defecto (2015-02-19).
    """

    csv_file = store_dir / epu_file_name

    if not csv_file.exists():
      return pd.DataFrame()
    
    df = pd.read_csv(csv_file)
    df['fecha'] = pd.to_datetime(df['fecha'])
    df.set_index('fecha', inplace=True)

    return df

def concat_raw_with_updated_dfs(df_raw: pd.DataFrame, df_new: pd.DataFrame) -> pd.DataFrame:
    if not df_new.empty:
        df_updated = pd.concat([df_raw, df_new])
        df_updated.sort_index(inplace=True)
        return df_updated
    else:
        return df_raw
  
def __include_goldstein_scale(media_rex, base_sql):

    sql = f"""
    SELECT
      g.fecha,
      g.medio,
      g.matches,
      g.total,
      g.tono,
      AVG(e.GoldsteinScale) AS goldsteinscale
    FROM ({base_sql}) g
    JOIN `gdelt-bq.gdeltv2.events` e
    ON DATE(PARSE_DATE('%Y%m%d', CAST(e.SQLDATE AS STRING))) = g.fecha
    WHERE REGEXP_CONTAINS(e.Actor1Code, r'{media_rex}')
    GROUP BY g.fecha, g.medio, g.matches, g.total, g.tono
    ORDER BY g.fecha, g.medio
        """

    return sql