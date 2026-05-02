# Nowcast EMAE — Resumen técnico

## Qué es

Pipeline que estima en tiempo real la variación del EMAE (Estimador Mensual de Actividad Económica de INDEC) **antes de que se publique**, usando indicadores de alta frecuencia. El branch activo de desarrollo es `facu_changes_07072025`.

---

## Repositorios involucrados

| Repo | Qué hace | Estado |
|------|----------|--------|
| `nowcast-EMAE/` | Prototipo original — modelo simple PCA + bridge lineal. No conectado a la visualización. | Archivado |
| `nowcast-dashboard/` | Visualizador dockerizado. Genera HTML interactivo desde Excel y lo sirve en puerto 8060. | ✅ Activo |
| `make_nowcast_history_html/` | Carpeta suelta con el script generador de HTML (misma lógica que nowcast-dashboard). | Fuente de verdad del gráfico |

El flujo esperado (pendiente):
`nowcast-EMAE (branch facu_changes_07072025)` → produce `nowcast_estimations_base_with_bands.xlsx` → `nowcast-dashboard` lo visualiza.

Actualmente el Excel está hardcodeado en el repo `nowcast-dashboard` como dato estático.

---

## Arquitectura de nowcast-dashboard

```
nowcast-dashboard/
├── dockerfile                        # python:3.13-slim + pip, expone 8060
├── requirements.txt                  # numpy, pandas, plotly, openpyxl
├── src/
│   ├── main.py                       # arranca: genera HTML → sirve con http.server en 8060
│   ├── make_nowcast_history_html.py  # lógica del gráfico (copiado de make_nowcast_history_html/)
│   └── data/
│       └── nowcast_estimations_base_with_bands.xlsx  # datos hardcodeados
```

`main.py` al arrancar:
1. Llama a `read_nowcast_excel()` → parsea las 5 hojas del Excel
2. Llama a `build_nowcast_figure()` → construye figura Plotly
3. Llama a `build_legend_items()` + `make_post_script()` → leyenda JS custom
4. Exporta `nowcast_history.html` con `pio.write_html(..., post_script=...)`
5. Sirve `data/` con `http.server.HTTPServer` en `0.0.0.0:8060`

---

## Estructura del proyecto (branch `facu_changes_07072025`)

```
nowcast-EMAE/
├── main.py                          # Orquestador: corre paso 1 y 2 en secuencia
├── code/
│   ├── fetchers.py                  # Descarga y limpia cada fuente de datos
│   ├── run_fetchers.py              # Invoca todos los fetchers, guarda CSVs en src/data/dbs/
│   ├── load_and_combine_dbs.py      # Transforma y une todos los CSVs en db_combinada.csv
│   ├── preprocess_weekly_data.py    # Resamplea diario → semanal, genera features
│   ├── models_ml_final.py           # Entrena Ridge/Lasso con PCA, evalúa escenarios
│   └── old_code/                    # Código original del main branch (archivado)
└── src/
    └── data/
        ├── dbs/                     # CSVs por fuente (output de run_fetchers.py)
        ├── db_combinada.csv         # Base maestra diaria (output de load_and_combine_dbs.py)
        └── db_weekly_preprocessed.csv  # Base semanal con features (output de preprocess)
```

El branch `facu_changes_20250624` es una versión anterior sin los modelos ML ni el pipeline combinado. El branch `facu_changes` (sin fecha) es el prototipo inicial.

---

## Fuentes de datos

| Fuente | Variable | Frecuencia | Método |
|--------|----------|-----------|--------|
| CAMMESA | Demanda eléctrica por región | Diaria | ZIP → XLSX vía HTTP |
| SUBE | Transacciones de transporte público | Diaria | CSV anual (2020–2025), cachea 2020–2024, siempre rebaja 2025 |
| BCRA API v3.0 | Base monetaria (id=15) | Diaria | REST paginado (bloques de 1000) |
| BCRA API v3.0 | Depósitos a la vista privado (id=22) | Diaria | REST paginado |
| BCRA API v3.0 | Préstamos sector privado (id=26) | Diaria | REST paginado |
| CAC (Bolsa de Cereales Rosario) | Precio de soja | Diaria | Excel incremental (últimos 30 días) |
| MAGyP (SIOS) | Operaciones de granos (toneladas, contratos) | Diaria | Selenium headless → Excel |
| INDEC / datos.gob.ar | EMAE sectorial base 2004 | Mensual | CSV directo |
| INDEC / datos.gob.ar | EMAE total base 2004 | Mensual | CSV directo |

---

## Pipeline paso a paso

### Paso 1 — `run_fetchers.py`
Llama a cada método de `Fetchers`, guarda el DataFrame resultante como CSV en `src/data/dbs/`. Al final verifica cobertura de fechas (esperadas vs faltantes, diario y mensual).

### Paso 2 — `load_and_combine_dbs.py`
Usa un registry de funciones (`@register`) para transformar cada CSV antes de unirlos:
- **BCRA**: selecciona la columna relevante, la renombra
- **CAMMESA**: normaliza nombres de columnas, agrega prefijo `cammesa_`
- **SUBE**: agrupa por día-provincia, pivot ancho, prefijo `sube_`
- **Precio soja**: normaliza a un valor diario, renombra `precio_soja`
- **Granos**: agrupa por zona-puerto, pivot ancho, prefijo `granos_`
- **EMAE**: resamplea mensual → diario con forward-fill, prefijo `emae_`

Output: `db_combinada.csv` — todos los indicadores alineados a frecuencia diaria.

### Paso 3 — `preprocess_weekly_data.py`
- Resamplea a semanas (lunes–domingo)
- Aplica agregación diferenciada por tipo de variable:
  - Flujos (SUBE, CAMMESA, granos) → `sum`
  - Stocks monetarios (base, depósitos, préstamos) → `last`
  - Precio soja → `mean`
- Genera features: variación porcentual con lag 4 semanas (≈ mensual), y el lag de esas variaciones
- Maneja división por cero: si el denominador = 0, usa cambio absoluto

### Paso 4 — `models_ml_final.py` (análisis/investigación)
- Carga `db_weekly_preprocessed.csv`
- Target: `emae_total_emae_original`
- Elimina columnas `emae_*` de los predictores
- Aplica `VarianceThreshold` para descartar variables con varianza ~0
- Reduce dimensionalidad con **PCA por bloques** (cammesa, sube, granos) o **PCA global** (criterio: 90% varianza acumulada)
- Entrena 8 escenarios: combinaciones de con/sin CAMMESA, con/sin SUBE, PCA por bloques vs global
- Modelos: **RidgeCV** y **LassoCV** con CV=5, alphas en escala logarítmica
- Métricas: RMSE, MAE, MAPE en set de test (30%)
- Guarda comparativa en `output/model_comparison.csv` y predicciones en `output/nowcast_comparison_full.xlsx`

---

## Debilidades y cosas flojas

### Críticas (rompen producción)

1. **Token BCRA hardcodeado en el código fuente**
   - En `fetchers.py` el JWT aparece en el default argument de 3 funciones distintas
   - Expira en fecha fija, cuando venza falla silenciosamente con 401
   - Está commiteado al repo — credencial pública

2. **Selenium requiere Chrome + ChromeDriver instalados**
   - Sin Docker, sin pinning de versión de driver — si el host no tiene Chrome, `fetch_granos` explota
   - No hay fallback si falla el scraping (levanta `RuntimeError` but no hay retry)

3. **`main.py` solo corre pasos 1 y 2** — no llama a `preprocess_weekly_data.py` ni a `models_ml_final.py`. El pipeline está incompleto como orquestador.

4. **`models_ml_final.py` no es un script de producción** — tiene código `#%%` de celdas Jupyter, `plt.show()` bloqueante, prints de desarrollo. No puede correr desatendido.

5. **La fecha de corte está hardcodeada**: `df0 = df0.loc[:"2025-04-30"]` en `models_ml_final.py` — hay que actualizarla manualmente.

### Importantes (degradan calidad o mantenibilidad)

6. **SUBE descarga años anteriores completos si el CSV no existe localmente**
   - El CSV de 2025 se rebaja entero cada vez (cientos de miles de filas)
   - No hay descarga incremental por fecha para SUBE (a diferencia de soja y granos)

7. **`fetch_cammesa` descarga el ZIP completo (2017–2025) cada vez que corre**
   - ~1.8 MB por correr, sin caché incremental
   - El link tiene un `refresh=` hardcodeado que puede caducar

8. **Sin manejo de errores parciales en `run_fetchers.py`**
   - Si falla un fetcher, el script explota y no guarda los que ya corrieron
   - No hay `try/except` por fuente

9. **`load_and_combine_dbs.py` tiene `try/except` genérico que silencia errores de transform**
   - Si una transformación falla imprime "❌ TRANSFORM ERROR" y sigue — la base combinada queda incompleta sin avisar al pipeline

10. **Forward-fill del EMAE mensual a diario** introduce falsa precisión — el modelo ve el mismo valor del EMAE repetido 20-22 días como si fuera dato diario

### Menores (deuda técnica)

11. Sin tests de ningún tipo
12. `pyproject.toml` existe pero no hay `poetry.lock` commiteado — versiones de dependencias no reproducibles
13. Archivos de datos grandes commiteados en el repo (CSVs de SUBE, excels de granos) — el repo pesa cientos de MB
14. `preprocess_weekly_data.py` no está integrado al `main.py`
15. Los outputs de `models_ml_final.py` (`output/`) están en el repo — mezcla código con artefactos

---

## Cosas que faltan

- **Output final para el dashboard**: el pipeline produce `nowcast_comparison_full.xlsx` pero no genera el formato que consume `make_nowcast_history_html` (`nowcast_estimations_base_with_bands.xlsx` con bandas de confianza percentílicas). El puente entre ambos no está escrito.
- **Bandas de incertidumbre**: el modelo actual da una predicción puntual. El visualizador espera percentiles (p10, p15, p20, p25, p75, p80, p85, p90). No hay bootstrap ni intervalos de confianza implementados.
- **Dockerización**: a diferencia de EPU-ARG-NEW y MINIMAL_DOCKER_PLOT, este repo no tiene Dockerfile ni entrypoint.
- **Scheduling automático**: no hay cron ni mecanismo de actualización periódica.
- **Validación de datos entrantes**: si una API cambia su formato (pasó con SUBE y CAMMESA en el branch original), el pipeline falla sin mensaje útil.
- **Logging estructurado**: solo `print()`, nada que persista ni sea parseable.
- **El CCL fue eliminado** respecto al prototipo original (main branch) — puede ser una pérdida de señal relevante para el nowcast.
