import requests, io, pandas as pd
import matplotlib.pyplot as plt

# ---------------- CONFIGURACIÓN ----------------
BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
# Palabras clave EPU (sin tildes; * = comodín para stemming)
keywords = [
    "econom*", "incertidumbre", "politic*", "impuesto*", "reglamentacion",
    "regulacion", "decreto", "crisis", "default", "inflacion"
]

key_word_clause = "(" + " OR ".join(keywords) + ")"

params = {
    "query": f"sourcecountry:ar AND {key_word_clause}",
    "mode": "TimelineVolRaw",   # columnas Date/Series/Value
    "timespan": "90days",
    "maxpoints": "250",
    "format": "CSV"
}

# ---------------- DESCARGA ----------------
r = requests.get(BASE, params=params, timeout=30)
r.raise_for_status()

# ---------------- LECTURA ----------------
df_raw = pd.read_csv(io.StringIO(r.text))
# limpieza de cabeceras
df_raw.columns = [c.strip().lstrip('\ufeff') for c in df_raw.columns]
print("\nPrimeras filas (formato crudo):")
print(df_raw.head())

# Verifica columnas esperadas
expected_cols = {'Date', 'Series', 'Value'}
if not expected_cols.issubset(df_raw.columns):
    raise ValueError(f"Columns missing. Got {list(df_raw.columns)}, expected at least {expected_cols}")

# Pivot a forma ancha: una fila por día
pivot = (df_raw
         .pivot(index='Date', columns='Series', values='Value')
         .reset_index()
         .rename_axis(None, axis=1))

# Renombra columnas estándar si existen
col_match = next((c for c in pivot.columns if 'article count' in c.lower()), None)
col_total = next((c for c in pivot.columns if 'total monitored articles' in c.lower()), None)
if col_match is None or col_total is None:
    raise ValueError("No se encontraron columnas 'Article Count' / 'Total Monitored Articles' tras pivotear. Columnas: " + ", ".join(pivot.columns))

pivot = pivot.rename(columns={col_match: 'matches', col_total: 'total'})
pivot['date'] = pd.to_datetime(pivot['Date'], errors='coerce')

for c in ['matches', 'total']:
    pivot[c] = (pivot[c].astype(str)
                         .str.replace(',', '', regex=False)
                         .str.replace(' ', '', regex=False))
    pivot[c] = pd.to_numeric(pivot[c], errors='coerce')

pivot = pivot[pivot['total'] > 0].copy()
pivot['EPU'] = 100 * pivot['total'] / pivot['matches']

if (pivot['matches'] == 0).all():
    print("Advertencia: Ningún artículo coincidió con las keywords actuales en los últimos 90 días.\n"
          "Revisá la lista de palabras o amplía el rango de búsqueda (timespan) para captar más artículos.")

pivot = pivot.sort_values('date').reset_index(drop=True)
print("\nHead tras cálculo de EPU:")
print(pivot[['date', 'matches', 'total', 'EPU']].head())

plt.figure()
plt.plot(pivot['date'], pivot['EPU'])
plt.title('Argentina EPU (últimos 90 días, GDELT)')
plt.xlabel('Fecha')
plt.ylabel('EPU (por 100 artículos)')
plt.tight_layout()
plt.show()
