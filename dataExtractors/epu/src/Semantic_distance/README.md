# Semantic Theme Selection

Este módulo permite seleccionar los *GDELT themes* más relevantes para un conjunto de palabras clave (keywords) de un diccionario temático (por ejemplo, EPU, incertidumbre, política, economía, etc.), utilizando embeddings y modelos de similitud semántica.

## Estructura general

- Los archivos fuente están en `src/Semantic_distance/`.
- Los resultados se escriben como `.csv` en `data/mapped/`.

## Estrategias disponibles (`select_best_themes`)

Se pueden aplicar diferentes estrategias para seleccionar los mejores themes por cada keyword:

### 1. `best_per_model`
Selecciona los mejores `top_n` themes por modelo para cada keyword según la similitud semántica. Si no alcanza el mínimo de similitud (`min_similarity`), rellena con los mejores disponibles si `fill_if_missing=True`.

### 2. `mean_similarity`
Agrupa por combinación `keyword-theme` y calcula la media de similitud entre modelos. Devuelve los `top_n` themes con mayor similitud promedio por keyword. También puede rellenar si no alcanza el mínimo.

### 3. `consensus`
Agrupa por `keyword-theme` y selecciona los themes más consensuados entre modelos (más apariciones) ponderado por similitud promedio.

## Formato de salida

Todos los `.csv` generados contienen las siguientes columnas:

- `keyword`: palabra clave del diccionario.
- `theme`: theme de GDELT seleccionado.
- `similarity`: valor de similitud semántica.
- `model`: nombre del modelo (o "Mean"/"Consensus").
- `match_rank`: ranking del match (menor es mejor; `-1` en estrategias agregadas).
- `group`: categoría temática del keyword (ej. E, P, U).
- `filled`: indica si el theme fue agregado por relleno al no alcanzar el umbral mínimo.

## Ejemplo de uso

```bash
python src/Semantic_distance/best_theme_chooser.py
```

Este script aplica todas las estrategias y guarda los resultados como CSV.
