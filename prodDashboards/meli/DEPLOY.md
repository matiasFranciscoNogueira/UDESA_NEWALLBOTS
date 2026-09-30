# DEPLOY — cómo se actualiza el dashboard MELI en vivo

Documento operativo para la carpeta que corre en el server. Complementa
`ACTUALIZAR_DATOS.md` (que cubre solo la generación del HTML) y sigue el
patrón del manual del Centro *"Actualización y Restore Nowcast"* (mayo
2026), que describe el mismo entorno. Arquitectura verificada desde afuera
el 2026-09-17.

---

## 1. Entorno (según el manual del Nowcast + verificación externa)

- Server Windows, operado desde **PowerShell**.
- Proyecto **Docker Compose** en **`C:\REPOS`** (nombre de proyecto `repos`;
  contenedores `repos-<servicio>-1`). Las apps viven en
  `C:\REPOS\prodDashboards\<app>\` (Nowcast en `...\prodDashboards\nowcast\`;
  MELI es la carpeta hermana).
- Servicios nombrados `<app>-<idioma>-<entorno>` (`nowcast-es-prod`,
  `nowcast-en-dev`, ...). Reverse proxy **nginx** (`nginx:alpine`, contenedor
  `nginx`, :80) y túnel **ngrok** (contenedor `ngrok-prod`) con **dominio
  reservado estático** `https://finley-unwhispered-ching.ngrok-free.dev`,
  que sobrevive a `docker compose build/up/down/restart`.
- Verificado para MELI: `udesa.edu.ar/indices-mercado-libre` embebe un
  `<iframe>` a `.../prod/meli/es/`; nginx rutea `/prod/meli/{es,en}/` y
  `/dev/meli/{es,en}/` (versión de prueba) a contenedores que sirven
  `amba_explorer.html` / `amba_explorer_en.html` con `serve.py`
  (`Server: nginx/1.29.6`; los 404 bajo esos paths son los de `http.server`
  de Python, o sea nginx proxya y reescribe la URL).

```
udesa.edu.ar/indices-mercado-libre
  └─ iframe → https://finley-unwhispered-ching.ngrok-free.dev/prod/meli/es/   (ngrok reservado)
                └─ nginx :80
                     ├─ /prod/meli/es/ , /prod/meli/en/  → servicio(s) meli-*-prod
                     └─ /dev/meli/es/  , /dev/meli/en/   → servicio(s) meli-*-dev
                            └─ imagen de `dockerfile`: python:3.13-slim, COPY . ., CMD python serve.py
```

**Diferencia clave con Nowcast.** El contenedor de Nowcast corre la app
(`python src/main.py`) y lee el Excel al arrancar: alcanza con reemplazar
el archivo y reconstruir. El de MELI **solo sirve dos HTML estáticos**: el
`dockerfile` no ejecuta `build.py`. Por eso el HTML tiene que generarse
**antes** de `docker compose build`, o venir ya generado en la carpeta.

**Aviso del manual (mayo 2026):** *"Los entornos DEV se están migrando a
otro esquema, por favor no modificarlos"* y *"No ejecutar comandos de
Docker salvo indicación explícita"*. `/dev/meli/` existe y hoy sirve lo
mismo que prod, así que probablemente ya quedó dentro del esquema nuevo,
pero conviene confirmarlo con quien administra `C:\REPOS` antes de usar
dev como banco de pruebas.

## 2. Lo único que falta saber (un comando)

Los nombres exactos de los servicios MELI y si el compose les agrega algo
(volumen, `command:` que corra `build.py` al arrancar):

```powershell
cd C:\REPOS
docker compose config --services | Select-String meli
docker compose config | Select-String -Pattern "meli" -Context 0, 25
```

Con eso se completan los `<...>` de abajo. Para un inventario completo de
solo lectura: `powershell -ExecutionPolicy Bypass -File .\discover_server.ps1 > discovery.txt`
desde la carpeta de MELI.

## 3. Procedimiento — primero DEV, después PROD

### Paso 0 — Estado del entorno (igual que el manual del Nowcast)

```powershell
cd C:\REPOS
docker ps
```

Todo `Up`, `nginx` y `ngrok-prod` incluidos; nada en `Restarting`/`Exited`.

### Paso 1 — Backup y datos nuevos (convención de esta carpeta: `data/older/`)

En la carpeta de MELI (`C:\REPOS\prodDashboards\meli` o la que use el
servicio dev — la muestra `build.context` en `docker compose config`):

```powershell
cd C:\REPOS\prodDashboards\meli
Copy-Item .\amba_explorer.html    .\data\older\amba_explorer_202607.html      # backup del HTML vigente
Copy-Item .\amba_explorer_en.html .\data\older\amba_explorer_en_202607.html
Move-Item .\data\*_202607*.csv .\data\older\                                 # snapshot que sale
Copy-Item <origen>\*_202608*.csv .\data\                                     # 14 CSVs del snapshot nuevo
(Get-ChildItem .\data\*.csv).Count                                           # tiene que dar 14
```

(Si se sube la carpeta ya preparada — CSVs 202608 en `data/`, 202607 en
`data/older/`, HTML 202608 generados — este paso y el 2 ya están hechos;
verificar con `MANIFEST_202608.txt` y `Get-FileHash`.)

### Paso 2 — Generar los dos HTML

En un contenedor efímero (mismo Python que la imagen, no depende de que el
host tenga Python; produce finales de línea LF como el HTML actual):

```powershell
docker run --rm -v "${PWD}:/app" -w /app python:3.13-slim python build.py
docker run --rm -v "${PWD}:/app" -w /app python:3.13-slim python build.py --lang en
```

(Alternativa con Python 3.10+ del host: `python build.py` y
`python build.py --lang en`.) Salida esperada en ambos:

```
Explorer generado en: /app/amba_explorer.html  (~5300 KB)
Idioma:               es
Snapshot de datos:    202608
```

**Sin ninguna línea `[WARN]`.** Un `[WARN] columna ... no encontrada`
significa serie vacía en el dashboard: no seguir (ver apéndice de
`ACTUALIZAR_DATOS.md`; el fix de alias de columnas ya está aplicado en
`build.py` y `lib/dashboard/catalogs.py`).

### Paso 3 — Verificar el HTML antes de reconstruir

```powershell
Select-String -Path .\amba_explorer.html, .\amba_explorer_en.html -Pattern '"snapshotId":"(\d{6})"' | ForEach-Object { "$($_.Filename): $($_.Matches[0].Value)" }
# esperado: "snapshotId":"202608" en los dos
Select-String -Path .\amba_explorer.html -Pattern '"PALERMO":\[\{"x":"2018-01","y":3400' -Quiet
# esperado: True  (precio de barrios CABA presente: la celda que se rompia con el rename de columna)
```

La regresión completa contra el HTML anterior se corre en la PC local con
`new_version/intern/verification/verify_snapshot.py --old <html viejo> --new <html nuevo>`
(esperado: `Series perdidas: 0`, `Valores distintos en meses cerrados: 0`).

### Paso 4 — Reconstruir y recrear SOLO los servicios dev de MELI

Mismo par de comandos que el manual del Nowcast, con los servicios de MELI:

```powershell
cd C:\REPOS
docker compose build <meli-es-dev> <meli-en-dev>
docker compose up -d <meli-es-dev> <meli-en-dev>
docker compose ps
```

(Si el compose define un solo servicio dev para MELI, va uno solo. Si
`docker compose config` mostró un volumen de la carpeta en `/app`, el
`build` es redundante pero inofensivo.) nginx y ngrok no se tocan; el
dominio reservado persiste.

### Paso 5 — Probar DEV por el túnel real

```powershell
$h = @{ "ngrok-skip-browser-warning" = "1" }
$r = Invoke-WebRequest "https://finley-unwhispered-ching.ngrok-free.dev/dev/meli/es/" -Headers $h -UseBasicParsing -TimeoutSec 120
"servido: $($r.RawContentStream.Length) bytes   generado: $((Get-Item C:\REPOS\prodDashboards\meli\amba_explorer.html).Length) bytes"
# esperado: los dos numeros iguales (si el servido es menor, la descarga se corto: repetir)
[System.Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray()) -match '"snapshotId":"(\d{6})"' | Out-Null; $Matches[1]
# esperado: 202608
```

Y a ojo en el browser: `https://finley-unwhispered-ching.ngrok-free.dev/dev/meli/es/`
→ footer "Agosto 2026"; Buenos Aires → Barrio (CABA) → Precio mediano
muestra curvas (no panel vacío); Córdoba y Rosario cargan; `/dev/meli/en/`
en inglés.

### Paso 6 — PROD

Si prod construye desde la misma carpeta, repetir solo el paso 4 con
`<meli-es-prod> <meli-en-prod>`. Si prod tiene su propia carpeta, repetir
pasos 1-3 ahí. Comprobar `/prod/meli/es/` con el mismo chequeo del paso 5
y abrir `https://udesa.edu.ar/indices-mercado-libre` (Ctrl+F5: el iframe
puede quedar cacheado).

### Rollback

Restaurar los HTML del backup (`data/older/amba_explorer*_202607.html`
→ raíz de la carpeta), volver a poner los CSVs 202607 en `data/` y repetir
el paso 4. Copia adicional de los HTML de julio en
`new_version/intern/archive/` (PC local).

## 4. Notas

- `lib/amba_dashboard/` es el paquete de `version_final`; nada lo importa
  (`build.py` usa `lib/dashboard`). Código muerto que viaja en la imagen.
- `COPY . .` mete en la imagen `data/older/` (crece ~25 MB por snapshot),
  ambos `lib/`, `source/` y los CSVs; para servir solo hacen falta
  `serve.py` y los dos HTML. Opcional: `.dockerignore` con `data/`, `lib/`,
  `source/`, `__pycache__/`, `*.md` reduce la imagen a ~11 MB sin cambiar
  el comportamiento (decisión de quien administra `C:\REPOS`).
- Fix de alias de columnas (2026-09-17): `build.py::_resolve_field` +
  `catalogs._SALE_FIELDS_CABA` como tupla `("Mediana Stock", "Mediana.Stock")`.
  Con la tupla pero el `build.py` viejo, el build "termina bien" y deja
  vacías las 62 series de precio de barrios CABA. Tests:
  `new_version/intern/verification/test_field_aliases.py` (12).
- Verificado el 2026-09-17: prod y dev servían exactamente los mismos
  bytes (5.396.805, snapshot 202607) que el `amba_explorer.html` recibido.
