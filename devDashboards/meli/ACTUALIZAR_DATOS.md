# Actualizar el snapshot mensual

Protocolo paso a paso para regenerar el dashboard cuando el pipeline R
del Centro publica un snapshot nuevo. Cubre los tres mercados (Buenos
Aires, Cordoba, Rosario) y ambos idiomas.

---

## Pre-requisitos

- Python 3.10 o superior (sin paquetes externos).
- Los 14 CSVs del nuevo snapshot generados por el pipeline R.

---

## Paso 1 — Verificar que el snapshot esta completo

El nuevo snapshot debe traer **14 archivos**, todos con el mismo
sufijo `_YYYYMM` (por ejemplo `_202607`):

### Buenos Aires (6 archivos)
- `VentasAgrupacion_YYYYMM.csv`
- `AlquileresAgrupacion_YYYYMM.csv`
- `VentasCABA_YYYYMM.csv`
- `AlquileresCABA_YYYYMM.csv`
- `VentasMunicipios_YYYYMM.csv`
- `AlquileresMunicipios_YYYYMM.csv`

### Interior — agregados (4 archivos)
- `VentasAgrupacion_YYYYMM_interior.csv`
- `AlquileresAgrupacion_YYYYMM_interior.csv`
- `VentasMunicipios_YYYYMM_interior.csv`
- `AlquileresMunicipios_YYYYMM_interior.csv`

### Interior — barrios (4 archivos)
- `VentasCordoba_YYYYMM.csv`
- `AlquileresCordoba_YYYYMM.csv`
- `VentasRosario_YYYYMM.csv`
- `AlquileresRosario_YYYYMM.csv`

Si falta uno de los 14, `DatasetBundle.discover()` lanza un error claro
listando los que faltan. **No empieces el build si falta uno.**

---

## Paso 2 — Copiar al folder `data/`

```bash
# Copiar los 14 archivos nuevos a new_version/data/
cp <fuente>/Ventas*_YYYYMM*.csv      new_version/data/
cp <fuente>/Alquileres*_YYYYMM*.csv  new_version/data/
```

Los archivos del snapshot anterior pueden quedar en `data/` — el
descubrimiento toma el snapshot mas reciente comun a las 14 tablas.
Si queres limpiar para evitar confusion, borra los archivos con el
sufijo anterior despues de verificar que el build pasa.

---

## Paso 3 — Build (ambos idiomas)

```bash
cd new_version
python build.py                # → amba_explorer.html
python build.py --lang en      # → amba_explorer_en.html
```

Output esperado:

```
Explorer generado en: .../amba_explorer.html  (~5100 KB)
Idioma:               es
Snapshot de datos:    202607
```

### Errores comunes en build

- **"No hay un snapshot YYYYMM comun a las 14 tablas"**: alguna tabla
  no esta al dia. Verificar con `ls data/Ventas*` y `ls data/Alquileres*`.
- **`[WARN] Tabla 'X' tiene snapshot mas nuevo`**: una o varias tablas
  estan adelantadas respecto a otras. El build elige el snapshot comun
  mas reciente. Si vos esperabas el snapshot mas nuevo: verifica el
  pipeline R para esa tabla.
- **`[WARN] columna 'X' no encontrada`**: el pipeline R cambio un
  nombre de columna. Actualizar el mapeo en `lib/dashboard/catalogs.py`
  (`_SALE_FIELDS_STD`, `_SALE_FIELDS_CABA`, `_RENT_FIELDS_STD`).

---

## Paso 4 — Verificacion numerica

Antes de publicar, correr los dos scripts de QA.

### 4a — Paridad con el dashboard anterior

Compara contra `version_final/amba_explorer.html` (regenerado al vuelo
o leido de baseline). Aplica solo a Buenos Aires.

```bash
# Regenerar baseline (solo si los CSVs de version_final tambien cambian)
cd ../version_final
python build.py --output ../new_version/intern/verification/baseline_es.html

# Comparar
cd ../new_version
python intern/verification/verify_baseline.py
```

Output esperado: `Match bit-a-bit: 453 / 646` con `Mismatches: 193`. Las
193 son todas de **oferta** y crecen exactamente 1 punto (fix intencional
del último mes parcial, ver `intern/CHANGELOG.md`). Precio y demanda quedan
bit-idénticos. Cualquier **otro** tipo de mismatch = investigar antes de
publicar.

### 4b — Spot checks contra los informes del Centro

Si los informes del nuevo snapshot ya estan publicados:

1. Abrir `Cordoba_InformeYYYYMM.docx` y `Rosario_InformeYYYYMM.docx`.
2. Copiar los porcentajes destacados (intermensual e interanual) en la
   lista `CASES` de `intern/verification/verify_informes.py`. Cada entrada es
   una tupla con (label, side, market, level, inmueble, region,
   mes_actual, mes_referencia, esperado_pct, fuente).
3. Ejecutar:
   ```bash
   python intern/verification/verify_informes.py
   ```
4. El reporte queda en `intern/verification/spot_checks.md`. Esperado:
   `PASS: 22/22` (o el numero total de casos definidos).

Tolerancia: 0.06 pp (precision implicita de informes redondeados a
1 decimal + ruido float).

---

## Paso 5 — Publicar

Una vez verificados los dos HTMLs:

```bash
# Servir localmente para revisar visualmente
python serve.py
# Abrir http://localhost:8000/amba_explorer.html
# Cambiar entre mercados, niveles, inmuebles — verificar a ojo
```

Si todo se ve bien, los archivos a entregar son:

- `amba_explorer.html` (~5 MB, autocontenido)
- `amba_explorer_en.html` (~5 MB, autocontenido)

Ambos son standalone: no requieren conexion al servidor original, ni
acceso a `data/`, ni a `lib/`. Una vez generados se pueden enviar por
mail, subir a un drive, exponer por ngrok, o publicar en GitHub Pages.

---

## Paso 6 — Backup

Antes de sobreescribir los HTMLs publicados del mes anterior, guardar
copia con sufijo `_YYYYMM` en un folder de archivo. Esto permite
verificar retroactivamente si una pregunta del usuario referencia un
snapshot viejo.

---

## Apendice — Cambios en los CSVs que rompen el build

Si el pipeline R cambia algo aguas arriba (formato de columnas, nombre
de aglomerado nuevo, etc.), el build puede fallar silenciosamente (las
series quedan vacias) o ruidosamente (un error).

**Sintomas y donde mirar:**

| Sintoma | Donde mirar |
|---|---|
| Una serie aparece vacia en el dashboard pero la dropdown la lista | `[WARN]` en stderr del build sobre columna faltante |
| Una zona/barrio nuevo no aparece en el dropdown | Lista en `lib/dashboard/catalogs.py` (constantes `AGLOMERADOS_BA`, `BARRIOS_CORDOBA`, etc.) |
| Mas mercados en el CSV pero el dashboard solo tiene 3 | Registry `MARKETS` en `lib/dashboard/catalogs.py` |
| Encoding raro / acentos rotos | Cadena de fallback en `load_csv()` — UTF-8 → Latin-1 → ISO-8859-15 |
| Base de indice cambia | `i18n.py` strings de `saleMetrics`/`rentMetrics` + comentario de contrato en `build.py` |
| Cambia el orden o nombre de zonas del interior | Listas `ZONAS_CORDOBA` / `ZONAS_ROSARIO` en `catalogs.py` |

Todos los cambios estructurales deberian ir acompañados de:
1. Update del README y este documento.
2. Si afecta visibilidad: actualizar `intern/docs/DECISIONES.md`.
3. Verificacion numerica (Paso 4) que confirme que el build sigue
   produciendo los valores correctos.
