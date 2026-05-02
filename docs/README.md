# UDESA — Pipelines de investigación económica

Tres proyectos independientes:

1. **EPU-ARG-NEW** — bot que consulta datos de noticias argentinas desde GDELT vía Google BigQuery y construye el índice mensual de Incertidumbre de Política Económica (EPU)
2. **MINIMAL_DOCKER_PLOT** — dashboard Dash/Plotly que visualiza los resultados EPU en http://localhost:8050
3. **nowcast-dashboard** — visualizador del Nowcast EMAE en http://localhost:8060 (HTML estático servido con Python http.server)

---

## Cómo funcionan los bots (modo automático)

Ambos contenedores corren **indefinidamente** con un cron interno (Linux, dentro del contenedor — funciona igual en Windows, Mac y Linux).

| Bot | Cuándo corre |
|-----|-------------|
| `epu-arg` | Al deployar + día 5 de cada mes a las 12:00 |
| `epu-dashboard` | Al deployar + día 6 de cada mes a las 12:00 |

El bot EPU corre el día 5 para asegurar que GDELT indexó por completo el mes anterior (tiene un lag de 1-3 días). El dashboard reimporta el Excel 24 hs después, cuando los datos ya están listos.

> **Importante:** hay tres mecanismos distintos:
> - **Auto-refresh 2 min**: actualiza el gráfico leyendo SQLite. No agrega datos nuevos.
> - **Watcher de archivo (cada 60 s)**: detecta cuando el bot EPU escribe un nuevo Excel y re-importa a SQLite automáticamente. Es el mecanismo principal.
> - **Cron día 6 a las 12:00**: re-importa como red de seguridad adicional.

---

## Deploy desde cero en una VM Windows (AnyDesk)

Esta es la guía completa para levantar todo desde cero en una máquina Windows limpia, con acceso público vía ngrok.

### 1. Instalar Docker Desktop

Descargá e instalá [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/).
Una vez instalado, abrilo y esperá a que el ícono de la ballena quede verde (Docker corriendo).

### 2. Copiar el proyecto

Copiá la carpeta `UDESA/` a la VM vía AnyDesk (arrastrar y soltar o usar el explorador de archivos compartido). Podés ponerla en cualquier lugar, por ejemplo `C:\Users\TuUsuario\Desktop\UDESA\`.

### 3. Colocar las credenciales

Copiá el archivo de clave de BigQuery a:
```
UDESA\EPU-ARG-NEW\keys\epu-udesa-gdelt-reader-personal.json
```

### 4. Configurar ngrok (acceso público)

1. Creá una cuenta gratuita en https://dashboard.ngrok.com
2. Copiá tu auth token desde https://dashboard.ngrok.com/get-started/your-authtoken
3. Creá el archivo `.env` en la raíz de `UDESA\` con el siguiente contenido:
   ```
   NGROK_AUTHTOKEN=tu_token_aqui
   ```

### 5. Levantar todo

Abrí PowerShell o CMD en la carpeta `UDESA\` y ejecutá:
```bash
docker compose up --build -d
```

Eso es todo. Docker construye las imágenes y levanta todos los servicios (EPU bot, dashboard EPU, dashboard Nowcast, nginx y ngrok). **No se necesita ningún paso adicional ni debug manual.**

### 6. Ver la URL pública

```bash
docker compose logs ngrok | findstr url
```

O abrí http://localhost:4040 en el browser de la VM.

| Ruta | Dashboard |
|------|-----------|
| `<url-ngrok>/epu/` | EPU (índice de incertidumbre) |
| `<url-ngrok>/nowcast/` | Nowcast EMAE |

> **Nota:** en el plan gratuito de ngrok la URL es fija por cuenta (no cambia entre reinicios).

### 7. Reinicio automático

Los contenedores tienen `restart: unless-stopped`, por lo que se levantan automáticamente si la VM se reinicia. No se necesita hacer nada manualmente.

### 8. Detener

```bash
docker compose down          # detiene (conserva datos)
docker compose down -v       # detiene y borra el volumen de datos EPU
```

---

## Actualizar la máquina de producción (AnyDesk)

Esta sección detalla cómo aplicar los cambios de código **y** los archivos de datos a la máquina Windows que corre el stack en producción.

### Paso 1 — Actualizar el código (git pull)

Conectarse vía AnyDesk, abrir PowerShell en la carpeta del proyecto y ejecutar:

```bash
git pull
```

Esto trae todos los fixes del pipeline EPU (exit→return, rutas duplicadas, etc.) y los cambios de UI (botón "Editar Indicadores", scroll iframe).

### Paso 2 — Transferir los archivos de datos

Los siguientes archivos **no están en git** (son demasiado grandes o son credenciales). Hay que transferirlos manualmente vía AnyDesk (arrastrar y soltar al explorador de archivos de la VM).

#### 2a. Clave de BigQuery

| Origen (esta máquina) | Destino en la VM |
|---|---|
| `EPU-ARG-NEW/keys/epu-udesa-gdelt-reader-personal.json` | `all-bots\EPU-ARG-NEW\keys\epu-udesa-gdelt-reader-personal.json` |

Crear la carpeta `keys\` si no existe.

#### 2b. Archivos de datos históricos

Estos archivos hay que copiarlos al **volumen Docker** de la VM, no a la carpeta del proyecto. Se hace igual que en esta máquina, desde PowerShell en la VM:

```powershell
# Primero detener el bot EPU para que no arranque antes de tiempo
docker compose stop epu-arg

# Crear subdirectorio de subcategorías en el volumen
docker run --rm -v all-bots_epu_data:/data alpine mkdir -p /data/subcategories

# Copiar cada archivo (correr uno por uno desde la carpeta donde están los archivos)
docker run --rm -v all-bots_epu_data:/data -v ${PWD}:/src alpine cp /src/epu_argentina_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv /data/epu_argentina_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv

docker run --rm -v all-bots_epu_data:/data -v ${PWD}:/src alpine cp /src/EPU_All_benchmark_ghirelli.xlsx /data/EPU_All_benchmark_ghirelli.xlsx
```

Si la VM nunca tuvo datos de subcategorías, repetir para cada CSV de subcategoría (trade, currency_crisis, fiscal, monetary_policy) — ver sección "Bootstrap del volumen" más abajo.

**Alternativa más simple:** copiar los archivos directo a `C:\Users\...\AppData\Local\Docker\wsl\data\` no funciona. La única forma es `docker run --rm -v` como se muestra arriba, o usar `docker cp` desde un container en ejecución:

```powershell
# Con el container epu-arg corriendo:
docker cp epu_argentina_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv all-bots-epu-arg-1:/app/data/
docker cp EPU_All_benchmark_ghirelli.xlsx all-bots-epu-arg-1:/app/data/
```

### Paso 3 — Rebuild y levantar

```bash
docker compose up --build -d
```

El `--build` es necesario para que los cambios de código Python se apliquen (no alcanza con pull solo).

### Paso 4 — Verificar

```bash
docker compose logs epu-arg -f
```

Debería ver:
```
=== Ejecución inicial del workflow EPU ===
Ejecutando workflow para categoría: none
No hay datos nuevos para actualizar.
...
✓ Saved combined subcategories (N rows) to /app/data/all_subcategories_compare.xlsx
=== Ejecución inicial completada ===
Cron activo — próxima ejecución: día 5 del mes a las 12:00
```

Si en cambio ve `Bytes a escanear: 2,174,xxx` con costo ~$10 por categoría, significa que los CSV históricos no llegaron bien al volumen — detener el container y repetir el paso 2.

---

## Bootstrap del volumen (primera vez en una máquina nueva)

En el primer deploy, el bot EPU no tiene historia y consulta BigQuery desde 2015 — eso cuesta ~$11 USD por categoría (~$55 total para las 5). Para evitarlo, hay que sembrar el volumen con los CSV históricos **antes** del primer arranque.

### Archivos necesarios

| Archivo | Descripción | Destino en el volumen |
|---|---|---|
| `epu_argentina_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv` | Raw data categoría principal (~440MB) | `/app/data/` |
| `epu_argentina_key_words_gdelt_maped_jp_trade_maped_all_media_with_sentiment.csv` | Raw data subcategoría trade | `/app/data/subcategories/` |
| `epu_argentina_key_words_gdelt_maped_jp_currency_crisis_maped_all_media_with_sentiment.csv` | Raw data subcategoría currency crisis | `/app/data/subcategories/` |
| `epu_argentina_key_words_gdelt_maped_jp_fiscal_maped_all_media_with_sentiment.csv` | Raw data subcategoría fiscal | `/app/data/subcategories/` |
| `epu_argentina_key_words_gdelt_maped_jp_monetary_policy_maped_all_media_with_sentiment.csv` | Raw data subcategoría monetary policy | `/app/data/subcategories/` |
| `EPU_All_benchmark_ghirelli.xlsx` | Benchmark Ghirelli (~138KB) | `/app/data/` |

Estos archivos son datos que no entran al repo (`.gitignore`). Pedírselos al equipo o exportarlos desde la máquina que ya tiene el volumen corriendo.

### Copiar al volumen

```bash
# Levantar el stack primero (crea el volumen)
docker compose up -d

# Detener solo el bot EPU para que no arranque antes de tiempo
docker compose stop epu-arg

# Copiar cada archivo al volumen (reemplazar <archivo> por la ruta local)
docker run --rm \
  -v all-bots_epu_data:/data \
  -v /ruta/local/<archivo>:/src/<archivo>:ro \
  alpine cp /src/<archivo> /data/<archivo>

# Para los de subcategorías, crear el subdirectorio primero:
docker run --rm -v all-bots_epu_data:/data alpine mkdir -p /data/subcategories

# Luego levantar el bot
docker compose up -d epu-arg
```

### Exportar los CSV desde una máquina que ya los tiene

```bash
# En la máquina origen, copiar desde el volumen al host:
docker run --rm \
  -v all-bots_epu_data:/data \
  -v $(pwd):/out \
  alpine cp /data/epu_argentina_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv /out/
```

---

## Deploy (modo bot continuo)

### Requisitos

- Docker y Docker Compose instalados
- Clave de servicio de Google Cloud con rol **BigQuery Editor**

### 1. Colocar la clave de BigQuery

```
EPU-ARG-NEW/keys/epu-udesa-gdelt-reader-personal.json
```

### 2. Levantar los bots

```bash
docker compose up --build -d
```

Esto construye las imágenes y arranca ambos bots. En el primer arranque:
- `epu-arg` corre el workflow completo inmediatamente (puede tardar 5-30 min según BigQuery)
- `epu-dashboard` intenta importar el Excel al volumen compartido. Si el bot EPU aún no terminó, el dashboard arranca sin datos y se actualiza en el próximo cron mensual

### 3. Ver logs

```bash
docker compose logs -f                    # logs de ambos servicios
docker exec epu-arg-1     tail -f /var/log/epu_cron.log      # log del cron EPU
docker exec epu-dashboard-1 tail -f /var/log/import_cron.log  # log del cron dashboard
```

### 4. Detener

```bash
docker compose down         # detiene y elimina contenedores (volumen de datos se conserva)
docker compose down -v      # también elimina el volumen compartido (borra datos)
```

---

## Demo rápida (sin clave BigQuery)

El repo incluye un Excel pre-generado. Para ver solo el dashboard:

```bash
docker build -t epu-dashboard ./MINIMAL_DOCKER_PLOT
docker run -d --name epu-dashboard \
  -p 8050:8050 \
  -e FROM_DOCKER=true \
  -v "$(pwd)/MINIMAL_DOCKER_PLOT/data:/app/data" \
  epu-dashboard
```

Abrí **http://localhost:8050**. Para detener: `docker stop epu-dashboard`.

---

## Ejecución local (sin Docker)

### Requisitos

- Python 3.12+ y Poetry ([guía de instalación](https://python-poetry.org/docs/#installation))
- Clave de Google Cloud en `EPU-ARG-NEW/keys/epu-udesa-gdelt-reader-personal.json`

### 1. Correr el pipeline EPU

```bash
cd EPU-ARG-NEW
poetry install
cd src
poetry run python epu_bot_workflow.py
```

Esto consulta BigQuery, construye los índices EPU para las 5 categorías y escribe `MINIMAL_DOCKER_PLOT/data/all_subcategories_compare.xlsx`.

### 2. Correr el dashboard

```bash
cd ../../MINIMAL_DOCKER_PLOT
poetry install
poetry run python scripts/import_excel_to_sqlite.py
poetry run python src/main.py
```

Abrí **http://localhost:8050**.

---

## Arquitectura

```
EPU-ARG-NEW/src/epu_bot_workflow.py
  Paso 1 (×5 categorías): BigQuery → CSV raw        →  EPU-ARG-NEW/data/
  Paso 2 (×5 categorías): CSV → índice EPU mensual  →  EPU-ARG-NEW/data/results/
  Paso 3:                 une las 5 categorías       →  [volumen compartido]/all_subcategories_compare.xlsx

MINIMAL_DOCKER_PLOT
  scripts/import_excel_to_sqlite.py  →  /app/data/database.sqlite  (cron día 6, o al deployar)
  src/main.py                        →  http://localhost:8050        (auto-refresh cada 2 min desde SQLite)
```

### Volumen compartido Docker

```
epu_data (named volume)
  ├── all_subcategories_compare.xlsx   ← escribe epu-arg, lee epu-dashboard
  ├── database.sqlite                  ← escribe y lee epu-dashboard
  └── [CSVs de datos raw]              ← escribe y lee epu-arg (incremental)
```

---

## Comandos útiles

```bash
docker compose up --build        # rebuild forzado (tras cambios de código)
docker compose up -d             # levantar en background
docker compose logs -f           # logs en tiempo real
docker compose down              # detener (conserva datos)
docker compose down -v           # detener y borrar volumen de datos
```

---

## Nowcast EMAE — Dashboard

El visualizador del nowcast es independiente del pipeline de datos. Genera un HTML interactivo a partir de un Excel y lo sirve en el puerto 8060.

```bash
cd nowcast-dashboard
docker build -t nowcast-dashboard .
docker run -d --name nowcast-dashboard -p 8060:8060 --restart unless-stopped nowcast-dashboard
```

Abrí **http://localhost:8060**. Para actualizar los datos sin reconstruir la imagen, montá el Excel como volumen:

```bash
docker run -d --name nowcast-dashboard -p 8060:8060 --restart unless-stopped \
  -v "$(pwd)/src/data:/app/src/data" \
  nowcast-dashboard
```

---

## Acceso externo vía ngrok

Los dashboards se exponen al exterior mediante **nginx** (reverse proxy) + **ngrok** (túnel HTTPS público).

| Ruta pública | Servicio |
|---|---|
| `/epu/` | EPU dashboard (puerto 8050) |
| `/nowcast/` | Nowcast dashboard (puerto 8060) |

### Configuración (una sola vez)

1. Crear cuenta gratuita en https://dashboard.ngrok.com
2. Copiar el auth token desde https://dashboard.ngrok.com/get-started/your-authtoken
3. Crear el archivo `.env` en la raíz del proyecto:
   ```
   NGROK_AUTHTOKEN=tu_token_aqui
   ```

### Levantar

```bash
docker compose up --build -d
```

### Ver la URL pública

```bash
docker compose logs ngrok | grep url
```

También disponible en http://localhost:4040 (dashboard web de ngrok).

> **Nota:** en el plan gratuito la URL cambia cada vez que se reinicia el contenedor ngrok. Para URL fija se requiere plan pago.

---

## Embeber dashboards en un iframe

Ambos dashboards están preparados para ser embebidos en una página externa mediante `<iframe>`.

### HTML mínimo recomendado

```html
<!-- EPU -->
<iframe
  src="https://<url-ngrok>/epu/"
  style="width:100%; height:700px; border:none;"
  scrolling="no"
  title="EPU Argentina">
</iframe>

<!-- Nowcast -->
<iframe
  src="https://<url-ngrok>/nowcast/"
  style="width:100%; height:700px; border:none;"
  scrolling="no"
  title="Nowcast EMAE">
</iframe>
```

### Tips para quien maneja la página que aplica el iframe

- **Altura fija en el iframe:** siempre definir un `height` explícito (px o vh). Si se deja `height:auto` el navegador no puede calcular el alto del contenido cross-origin y el gráfico aparece colapsado.
- **`scrolling="no"`:** los dashboards tienen `overflow:hidden` internamente para evitar doble scroll (scroll de la página padre + scroll interno del iframe). Agregar `scrolling="no"` en el tag como segunda línea de defensa para browsers más viejos.
- **`border:none`:** evita el borde gris por defecto del iframe.
- **Ancho:** usar `width:100%` para que sea responsivo al ancho del contenedor. El gráfico se adapta automáticamente.
- **URL base:** las rutas `/epu/` y `/nowcast/` incluyen la barra final. Omitirla puede causar redirect loops en nginx.
- **HTTPS:** ngrok expone HTTPS por defecto. Embeber un iframe HTTP dentro de una página HTTPS bloquea el contenido (mixed content). Siempre usar la URL `https://` que provee ngrok.
- **Plan gratuito de ngrok:** la URL cambia cada vez que el contenedor ngrok se reinicia. Si la página que embebe tiene la URL hardcodeada, hay que actualizarla tras cada reinicio. Para URL fija se requiere plan pago.

### Por qué no usar `position:fixed` en el gráfico

Alguna vez puede sugerirse agregar `position:fixed` al div del gráfico como solución rápida al doble scroll. **No hacerlo:** desconecta el gráfico del flujo del documento, rompe el detector de resize de Plotly y puede superponerse con otros elementos. El fix correcto ya está aplicado en el código (`overflow:hidden` en body + herencia de altura).

---

## Nota sobre Windows

El scheduling usa **cron de Linux dentro del contenedor Docker**, no el Task Scheduler de Windows. Funciona igual en cualquier sistema operativo con Docker Desktop instalado. No se necesita configurar nada en el host Windows.

Los scripts `.sh` tienen line endings forzados a LF via `.gitattributes`. Si se editan en Windows, no modificar los line endings.
