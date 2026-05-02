# TODO

## ✅ Hecho en sesión 03/04/2026

- **Credenciales BigQuery** — service account key creada en Google Cloud (org policy override requerido). Archivo en `EPU-ARG-NEW/keys/epu-udesa-gdelt-reader-personal.json` (gitignoreado).
- **Seeding del volumen Docker** — CSV histórico (~440MB, datos hasta 2026-04-03) y `EPU_All_benchmark_ghirelli.xlsx` copiados al volumen `all-bots_epu_data` con `docker run --rm -v`.
- **Fix `exit()` → `return`** en `epu_historical_GDELT_big_query.py` — el proceso moría antes del paso 2 y 3 cuando no había datos nuevos.
- **Fix ruta duplicada `subcategories/subcategories/`** en `get_raw_given_historical_data_from_db` — hacía que el bot nunca encontrara los CSV de subcategorías y arrancara desde 2015 en cada restart (quemaba ~$10 por ciclo).
- **Fix `mkdir results/subcategories`** en `analysis_compare_with_benchmarks_with_events_save_to_file.py` — el directorio no existía y crasheaba el paso 2.
- **Fix columna `"Exclude none"` → `"EPU UdeSA"`** en `join_and_save_subcategories_compare` — nombre de columna incorrecto bloqueaba el paso 3.
- **Primera corrida completa exitosa** — las 5 categorías (none, trade, currency_crisis, fiscal, monetary_policy) corrieron de punta a punta. Excel `all_subcategories_compare.xlsx` generado con 125 filas. Cron activo.
- **Fix scroll iframe** — `overflow:hidden` en body + herencia de altura en EPU (assets/iframe.css) y Nowcast (post_script CSS injection).
- **UI**: label eje Y removido en Nowcast, botón "Edit" → "Editar Indicadores" en ambos dashboards.

---

## ✅ Hecho en sesión 22/03/2026 (tarde)

- **Fix `KeyError: 'Argentina'`** — `epu_historical_GDELT_big_query.py` línea 26: `"argentina"` → `"Argentina"`. El bot llevaba 7.685 reinicios desde el 13/03 sin hacer ninguna query (crash antes de llegar a BigQuery, costo $0).
- **`restart: on-failure:5`** en `epu-arg` (`docker-compose.yml`) — previene crash loops indefinidos. El resto de servicios mantiene `unless-stopped`.
- **Hard gate $5 USD** en `get_query_estimated_price` (`gdelt_request_helpers.py`) — si el dry-run estima más de $5, lanza `ValueError` antes de ejecutar la query real.
- **Fix EPU dashboard "Loading..." indefinido** — `MINIMAL_DOCKER_PLOT/src/main.py`: `requests_pathname_prefix` → `url_base_pathname`. En Dash 3.x estos parámetros son estrictamente independientes; usar solo `requests_pathname_prefix` dejaba las rutas Flask en `/` mientras el browser enviaba callbacks a `/epu/`, resultando en 405 y gráfico que nunca carga. Ver bitacora.md para diagnóstico completo.

---

## ✅ Hecho en sesión 22/03/2026

- Nuevo repo `all-bots` en GitHub (sin credenciales)
- Review de cambios del otro PC (JS date picker, armonización visual EPU ↔ Nowcast, nginx sin rewrite en /epu/)
- Confirmado: cambios de código OK, slowness era el PC viejo + ngrok free tier
- Containers corriendo localmente con la nueva versión del código (all-bots stack)
- Branch `hetzner-deploy` creada y pusheada con todos los archivos de deploy

---

## ✅ Hecho en sesión 06/04/2026 — Deploy prod (AnyDesk) + scripts de seed

- **Scripts de seed** — `scripts/export_seed_data.sh` (Linux) y `scripts/import_seed_data.ps1` + `.bat` (Windows) para transferir datos históricos del volumen Docker entre máquinas sin tocar BigQuery.
- **Fix CRLF Windows** — `EPU-ARG-NEW/Dockerfile` ahora instala `dos2unix` y lo aplica al `entrypoint.sh` en el build, igual que MINIMAL_DOCKER_PLOT. Sin esto, `git` en Windows convertía el script a CRLF y el container no arrancaba.
- **`.gitattributes`** — fuerza LF en archivos `.sh` y CRLF en `.ps1`/`.bat`. Previene el problema CRLF en futuros clones desde Windows.
- **Deploy prod verificado** — VM Windows actualizada. 5 categorías EPU corriendo sin queries a BigQuery (datos históricos sembrados desde volumen local). Output: `all_subcategories_compare.xlsx` con 125 filas. Cron activo.

---

## 🔲 PLAN COMPLETO — Deploy en Hetzner (próxima sesión)

### Contexto
Todo el trabajo de Hetzner está en el branch `hetzner-deploy`. Hacer checkout ahí antes de empezar:
```bash
git checkout hetzner-deploy
```

Los archivos ya listos en ese branch:
- `scripts/cloud-init.yml` — setup automático del servidor (Docker + clone del repo)
- `scripts/deploy.sh` — valida prereqs y levanta todo
- `scripts/logs.sh` — wrapper de logs
- `scripts/status.sh` — estado completo del stack
- `DEPLOY.md` — guía paso a paso para humanos
- `.env.example` — template del token ngrok

### Paso 1 — Completar el branch antes de mergear

Cosas que faltan en `hetzner-deploy` antes de mergear a main:

1. **Agregar logging a `docker-compose.yml`** — añadir el bloque `x-logging` con `json-file` (10MB × 5 archivos) a todos los servicios. Ya estaba escrito en esta sesión pero se perdió al hacer `git stash` + `git pull`. Ver el código que tenía:
   ```yaml
   x-logging: &default-logging
     driver: json-file
     options:
       max-size: "10m"
       max-file: "5"
   ```
   Agregar `logging: *default-logging` a cada servicio.

2. **Flag ngrok (profiles)** — agregar `profiles: ["ngrok"]` al servicio ngrok en `docker-compose.yml` y documentar en `.env.example`:
   ```yaml
   # docker-compose.yml
   ngrok:
     profiles: ["ngrok"]
     ...
   ```
   ```bash
   # .env
   COMPOSE_PROFILES=ngrok   # quitar esta línea para deshabilitar ngrok
   ```

3. **Mergear a main** y pushear.

### Paso 2 — Crear el servidor en Hetzner

1. Ir a https://console.hetzner.cloud → New project → "udesa"
2. Add server:
   - Location: Nuremberg o Helsinki
   - Image: **Ubuntu 24.04**
   - Type: Shared CPU → **CX22** (2 vCPU, 4 GB RAM, ~€4/mes)
   - SSH key: pegar la clave pública local (`~/.ssh/id_rsa.pub`)
   - **User data**: pegar el contenido de `scripts/cloud-init.yml`
3. Create & Buy → esperar ~2 min

### Paso 3 — Configuración manual post-servidor (única vez)

```bash
# Desde la máquina local:

# 1. Subir la clave BigQuery
scp /ruta/a/epu-udesa-gdelt-reader-personal.json \
  root@<SERVER-IP>:~/all-bots/EPU-ARG-NEW/keys/epu-udesa-gdelt-reader-personal.json

# 2. SSH al servidor
ssh root@<SERVER-IP>

# 3. Completar el .env con el token de ngrok
nano ~/all-bots/.env
# → reemplazar "your_ngrok_token_here" con el token real

# 4. Deploy
cd ~/all-bots && bash scripts/deploy.sh
```

### Paso 4 — Verificar

```bash
# Ver URL pública
bash scripts/status.sh

# Dashboards en:
# https://<ngrok-url>/epu/
# https://<ngrok-url>/nowcast/
```

### Paso 5 — Mantenimiento futuro

```bash
# Actualizar código
ssh root@<SERVER-IP>
cd ~/all-bots && git pull && docker compose up --build -d

# Ver logs
bash scripts/logs.sh            # todos
bash scripts/logs.sh epu-arg    # uno solo

# Estado
bash scripts/status.sh
```

---

## 🔲 Pendientes menores (post-Hetzner)

- **`process_tone_monthly=True` bug** en `EPU-ARG-NEW/src/Helpers/analisys_helpers.py` línea 7 — pasa 6 args a función de 5. No afecta producción (usa `False`).
- **Pixel offsets hardcodeados** en `legend.js` (`left:443px`, `left:78px`) — el ancho no es un problema en producción según el equipo, pero podría romperse en viewports muy angostos.
- **`--no-install-recommends`** al instalar `cron` en ambos Dockerfiles (ahorra ~93MB).
- **Seeding en Hetzner** — al deployar en Hetzner, recordar copiar el CSV histórico y el Ghirelli al volumen antes del primer arranque (ver sección "Bootstrap del volumen" en este README).
