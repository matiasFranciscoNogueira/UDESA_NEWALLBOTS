# Guía de actualización mensual

Este documento describe el flujo de trabajo para refrescar el dashboard
con los datos del mes nuevo.

---

## TL;DR (versión corta)

1. Pegar los **6 archivos nuevos del mes** (`*_YYYYMM.csv`) en `data/`.
2. Correr `python build.py`.
3. **Verificar** las 4 cifras core contra el informe del mes (ver más abajo).
4. Subir el `amba_explorer.html` resultante al servidor.

Listo. Si las 4 cifras del paso 3 coinciden al segundo decimal con el
informe oficial del Centro, el dashboard está sincronizado correctamente.

---

## Detalles

### Qué archivos necesitás cada mes

Del pipeline R (carpeta `Index_AMBA/` en el Drive del Centro) tenés que
copiar los **6 CSVs del mes nuevo** a `version_final/data/`:

| Archivo | Cubre |
|---|---|
| `VentasAgrupacion_YYYYMM.csv`     | 5 aglomerados, ventas |
| `AlquileresAgrupacion_YYYYMM.csv` | 5 aglomerados, alquileres |
| `VentasCABA_YYYYMM.csv`           | 42 barrios CABA, ventas |
| `AlquileresCABA_YYYYMM.csv`       | 42 barrios CABA, alquileres |
| `VentasMunicipios_YYYYMM.csv`     | 30 municipios AMBA, ventas |
| `AlquileresMunicipios_YYYYMM.csv` | 30 municipios AMBA, alquileres |

`YYYYMM` es el sufijo del mes nuevo (p. ej. `202604` para abril 2026).

### ¿Reemplazo los del mes anterior o los dejo al lado?

**Cualquiera de las dos opciones funciona.** El código (`DatasetBundle.discover`)
busca automáticamente el **snapshot común más reciente** entre los 6
prefijos. Si en `data/` hay archivos de marzo y abril, va a usar abril.

- **Si querés mantener historial de snapshots** (auditoría): dejá los
  archivos viejos al lado de los nuevos. La carpeta crece ~1.5 MB por mes.
- **Si preferís carpeta liviana**: borrá los 6 archivos del mes anterior
  y pegá los 6 del mes nuevo.

> ⚠️ **Importante:** cada CSV del mes nuevo ya contiene **toda la historia**
> hasta ese mes (desde 2018-01). No es incremental — un sólo archivo por
> tabla alcanza para reconstruir el histórico completo.

### Trampa común: snapshot incompleto

Si en `data/` están los 6 archivos de marzo y **sólo 5 de los 6 de abril**
(p. ej. olvidaste subir `AlquileresMunicipios_202604.csv`), el código va
a quedarse con el snapshot **completo más reciente**, que es marzo. El
dashboard saldría desactualizado sin que el script avise.

**Cómo evitarlo:** después de correr `python build.py`, verificá la
segunda línea del output:

```
Explorer generado en: .../amba_explorer.html  (~4075 KB)
Idioma:               es
Snapshot de datos:    202605        ← debe coincidir con el mes esperado
```

Si dice un mes anterior al que esperabas, falta algún CSV en `data/`.

### Correr el script

Desde la carpeta `version_final/`:

```bash
python build.py
```

Output esperado:

```
Explorer generado en: ...\version_final\amba_explorer.html  (~4075 KB)
Idioma:               es
Snapshot de datos:    202605
```

Tarda ~3-5 segundos. No hay dependencias externas: usa sólo Python
estándar (3.10+).

> Para generar la versión en inglés del dashboard, agregá `--lang en`:
> `python build.py --lang en` → `amba_explorer_en.html`.

### Verificación de integridad (recomendado)

Después de generar el HTML, comparar **4 cifras core** contra el informe
oficial del Centro (`Indices_AMBA.html`). Si coinciden al segundo decimal,
el dashboard está sincronizado:

1. **Venta stock MoM Casa AMBA** (mayor variación en categoría "Casa")
2. **Venta stock MoM Depto CABA** (mayor variación en categoría "Depto")
3. **Alquiler corrientes YoY Depto CABA**
4. **Alquiler corrientes YoY Casa GBA Sur**

Para correr la verificación automática, ver el script copy-paste en
`AUDITORIA_INTEGRAL.md` (sección "Cómo re-verificar al cargar un
snapshot nuevo"). Solo hay que cambiar `mes_t`, `mes_prev`, `mes_y1`
al snapshot nuevo.

### Servir y compartir

**Local (para probar):**

```bash
python serve.py
# Abrir http://localhost:8000/amba_explorer.html
```

**Producción:** subir `amba_explorer.html` (un solo archivo) al servidor
web del Centro. El HTML es autocontenido — no necesita CDN, librerías,
ni los CSVs.

### Embeber como iframe en la web del Centro

```html
<iframe
  src="https://tu-dominio/amba_explorer.html"
  width="100%" height="780"
  style="border:0; border-radius:18px;"
  loading="lazy"
  title="Explorador AMBA — CECN UdeSA">
</iframe>
```

---

## Qué hacer si algo cambia en el pipeline R

Si Abigail (o quien arme los CSVs) **cambia los nombres de columnas** o
**agrega un aglomerado/barrio/municipio nuevo**:

1. Verificar los headers nuevos:
   ```bash
   head -1 data/VentasAgrupacion_YYYYMM.csv
   ```
2. Si cambió un nombre de campo, ajustar el catálogo `LEVELS` en
   `lib/amba_dashboard/catalogs.py`.
3. Si hay un aglomerado/barrio/municipio nuevo, agregarlo a las listas
   `AGLOMERADOS`, `BARRIOS_CABA` o `MUNICIPIOS_GBA` (mismo archivo).
4. Si el build muestra `[WARN] columna 'X' no encontrada`, es exactamente
   este caso: el aviso indica qué columna falta y en qué tabla.

Para más detalle, ver `README.md`.
