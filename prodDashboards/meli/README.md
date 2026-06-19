# Dashboard AMBA — Mercado Inmobiliario

> **Estado:** producción · snapshot **mayo 2026 (202605)** · auditoría 8/8 PASS contra `Indices_AMBA.html`
> **Idiomas:** español · inglés (ver `README_EN.md`)

Dashboard interactivo y autocontenido del mercado inmobiliario del Área
Metropolitana de Buenos Aires (AMBA). Generado por el Centro de Estudios
Cuantitativos en Negocios de la Universidad de San Andrés, con datos de
Mercado Libre.

[English version → README_EN.md](README_EN.md)

---

## ¿Qué es esto?

- Un único archivo HTML (`amba_explorer.html` o `amba_explorer_en.html`)
  con **toda la data, los estilos y el código JS embebidos**. No tiene
  dependencias externas: no carga CDN, no necesita servidor de aplicación.
- Sirve para cualquier servidor estático (Apache, nginx, GitHub Pages,
  ngrok) o se puede abrir local doble-click → navegador.
- El build se hace con Python ≥ 3.10 estándar (sin librerías externas).

---

## Quickstart (primera vez, desde cero)

### 1. Pre-requisitos

- **Python 3.10 o superior.** Verificá con:

  ```bash
  python --version
  ```

  Si no lo tenés, descargá desde [python.org/downloads](https://www.python.org/downloads/).

### 2. Setup

Desde una terminal en la carpeta del proyecto (`version_final/`):

```bash
# Crear y activar entorno virtual
python -m venv .venv

# Activar (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activar (macOS / Linux)
source .venv/bin/activate

# Instalar dependencias (el proyecto no tiene externas, pero queda preparado)
pip install -r requirements.txt
```

### 3. Generar el dashboard

```bash
# Español (default) → amba_explorer.html
python build.py

# Inglés → amba_explorer_en.html
python build.py --lang en
```

Output esperado:

```
Explorer generado en: .../amba_explorer.html  (~4075 KB)
Idioma:               es
Snapshot de datos:    202605
```

### 4. Servir local

```bash
python serve.py --port 8000
```

Abrí en el navegador:

- `http://localhost:8000/amba_explorer.html` (ES)
- `http://localhost:8000/amba_explorer_en.html` (EN, si lo generaste)

---

## Actualización mensual

Cada vez que llega un snapshot nuevo del pipeline R: ver
**[ACTUALIZAR_DATOS.md](ACTUALIZAR_DATOS.md)**.

TL;DR: pegar los 6 CSVs del mes nuevo en `data/`, correr `python build.py`,
verificar 4 cifras core contra el informe oficial.

---

## Exponer al público con ngrok

> ngrok ya autenticado: si es la primera vez, correr `ngrok config add-authtoken <TOKEN>`
> con un token de [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken).

### Solo español (caso default)

```bash
# Terminal 1: servidor estático
cd version_final/
python serve.py --port 8000

# Terminal 2: túnel público
ngrok http 8000
```

Compartir la URL `https://<random>.ngrok-free.app/amba_explorer.html`.

### Español y inglés simultáneo (un puerto, dos archivos)

Si generaste ambos HTMLs en la misma carpeta, **un solo `serve.py` y un
solo `ngrok` exponen los dos**:

```bash
# Terminal 1: builds (una sola vez por snapshot)
python build.py --lang es
python build.py --lang en

# Terminal 2: servidor
python serve.py --port 8000

# Terminal 3: túnel
ngrok http 8000
```

Las URLs públicas quedan:

- `https://<random>.ngrok-free.app/amba_explorer.html` (ES)
- `https://<random>.ngrok-free.app/amba_explorer_en.html` (EN)

### Notas sobre ngrok

- En plan gratuito la URL **cambia cada vez** que reiniciás el túnel.
  Para una URL estable hace falta plan paid o un dominio reservado.
- `serve.py` ya tiene `allow_reuse_address` activado: si reiniciás el
  servidor con Ctrl-C, podés volver a correr inmediatamente sin esperar.
- Si el puerto 8000 está ocupado, usá otro: `python serve.py --port 8080`.

---

## Estructura del proyecto

```
version_final/
├── .gitignore                  ← ignora __pycache__, .venv, etc.
├── README.md                   ← este archivo (español)
├── README_EN.md                ← versión inglesa
├── ACTUALIZAR_DATOS.md         ← runbook mensual para refrescar datos
├── requirements.txt            ← (vacío — sólo Python estándar)
├── build.py                    ← genera amba_explorer*.html
├── serve.py                    ← servidor HTTP local mínimo
├── amba_explorer.html          ← OUTPUT español (~4 MB)
├── amba_explorer_en.html       ← OUTPUT inglés (~4 MB, sólo si corriste --lang en)
├── data/                       ← CSVs del pipeline R (snapshots)
│   ├── VentasAgrupacion_202605.csv
│   ├── AlquileresAgrupacion_202605.csv
│   ├── VentasCABA_202605.csv
│   ├── AlquileresCABA_202605.csv
│   ├── VentasMunicipios_202605.csv
│   └── AlquileresMunicipios_202605.csv
├── lib/amba_dashboard/         ← paquete Python autocontenido
│   ├── __init__.py
│   ├── data_store.py           ← descubrimiento y carga de snapshots
│   ├── utils.py                ← safe_float
│   ├── catalogs.py             ← aglomerados, barrios, municipios, colores, LEVELS
│   ├── metrics.py              ← estructura de métricas + factory por idioma
│   ├── i18n.py                 ← LANG_ES / LANG_EN (todas las strings UI)
│   └── assets/branding/        ← logos UdeSA + Mercado Libre
├── source/
│   ├── template.html           ← shell HTML con placeholders __X__
│   ├── explorer.css            ← estilos (paleta institucional UdeSA)
│   └── explorer.js             ← lógica del front (~50 KB, sin frameworks)
└── intern/                     ← TODO LO NO ESENCIAL para correr o entregar
    ├── README_intern.md        ← qué hay acá y por qué
    ├── AUDITORIA_INTEGRAL.md   ← reporte QA point-in-time (2026-05-21)
    ├── Indices_AMBA.html       ← informe oficial del Centro (referencia)
    ├── Indices_AMBA_files/     ← assets del HTML de referencia
    ├── _pycache_root/          ← bytecode antiguo (autogenerado)
    ├── _pycache_lib/           ← idem
    └── legacy_code/            ← funciones del paquete amba_dashboard ya no usadas
```

---

## Datos: contrato con el pipeline R

Los 6 CSVs en `data/` son producidos por el **pipeline R del Centro**
(carpeta `Index_AMBA/` en el Drive). El dashboard los consume tal cual,
sin recalcular nada que no sea estrictamente cosmético.

### Estructura esperada de cada CSV

| Columna típica | Tipo | Ejemplo |
|---|---|---|
| `Mes` | string `YYYY-MM` | `2026-05` |
| `Aglomerado` / `Barrio` / `Municipio` | string | `CABA` / `PALERMO` / `Tigre` |
| `Inmueble` | string | `Casa`, `Departamento` |
| `Mediana Stock` / `Mediana Flujo` | float (USD/m²) | `2632.94` |
| `Mediana por m2 a precios corrientes` | float (ARS/m²) | `8430.12` |
| `Contactos` | float (índice) | `1.43` |
| `Oferta` | float (índice) | `1.07` |

> **Nota:** `VentasCABA_*.csv` usa `Mediana.Stock` (con punto) porque el
> pipeline R lo exporta con `write.csv` que reemplaza espacios. El resto
> usa espacios. El código contempla ambas variantes.

### Contrato sobre las bases de los índices

Los índices `Contactos` (Demanda) y `Oferta` **vienen ya normalizados
desde R**, no se recalculan acá:

- **Oferta**: base `enero 2018 = 1`
- **Contactos** (Demanda): base `enero 2019 = 1` (la captura empieza un
  año más tarde que la de publicaciones activas)

Verificado contra los snapshots 202604 y 202605: la base es uniforme
por inmueble y por geografía. Si el Centro cambiara la base upstream,
hay que actualizar las strings en `lib/amba_dashboard/i18n.py` (claves
`saleMetrics.{demanda,oferta}` y `rentMetrics.{demanda,oferta}`).

### Regla del último mes parcial

Las series de **Demanda** y **Oferta** del último mes del snapshot están
incompletas (siguen entrando contactos y abriendo publicaciones después
del corte). El build las excluye del gráfico, replicando la regla del
informe oficial. **Precio** no se filtra: la mediana del stock activo ya
es final una vez cerrado el mes.

---

## Filtros y controles

| Filtro | Opciones | Notas |
|---|---|---|
| **Nivel geográfico** | Aglomerado · Barrio (CABA) · Municipio (AMBA) | Cambia el catálogo de regiones |
| **Aglomerado / Barrio / Municipio** | Multi-select | Default: AMBA + CABA |
| **Tipo de propiedad** | Casa · Departamento | Scope deliberado: Oficina no se expone |
| **Métrica** | Precio · Demanda · Oferta | Cada una en su unidad natural |
| **Período (chips)** | 12 m · 24 m · 60 m · Histórico | Default: histórico completo |
| **Botón ↺** | Restablece todos los filtros |  |
| **Botón ⬇ Venta / Alquiler** | Exporta el panel como PNG |  |

### Convenciones de presentación

- **Capitalización**: cada segmento después de `·` arranca con mayúscula
  (`Casas · Barrios CABA`, no `casas · barrios CABA`). Los nombres de
  meses también van capitalizados (`Enero 2026`, no `enero 2026`).
- **Paleta**: institucional UdeSA (azul navy `#0F3E7D` para venta, azul
  acero `#4A8CC1` para alquiler). El verde/rojo de las cajas de
  variación se mantienen porque tienen semántica universal
  (subió/bajó), no marca.
- **Locale numérico**:
  - ES: `1.234,56` (puntos como separador de miles, coma decimal)
  - EN: `1,234.56` (comas como separador de miles, punto decimal)

---

## Soporte bilingue (ES / EN)

### Cómo se elige el idioma

Por flag al momento del build:

```bash
python build.py --lang es   # → amba_explorer.html      (default)
python build.py --lang en   # → amba_explorer_en.html
```

Cada HTML es **autocontenido**: el JS embebido lee las strings desde el
diccionario `lang` que `build.py` inyecta en el bootstrap. **No hay
toggle en runtime**: el usuario que abre `amba_explorer_en.html` ve todo
en inglés sin tocar nada.

### Dónde viven las strings

Todas las strings de UI están en `lib/amba_dashboard/i18n.py`, en dos
diccionarios planos (`LANG_ES` y `LANG_EN`) con las mismas claves. El
módulo tiene un `assert` que falla el build si las claves se
desincronizan — sirve como linter de traducción cuando agregás strings
nuevas.

### Para agregar / cambiar una string

1. Editá `lib/amba_dashboard/i18n.py` agregando/modificando la clave en
   **ambos** diccionarios.
2. Si es nueva, usala en `source/explorer.js` como `lang.miNuevaClave`.
3. Re-correr `python build.py --lang es` y `python build.py --lang en`.

### Lo que no se traduce

- **Nombres propios de geografías**: CABA, AMBA, PALERMO, Tigre, etc.
  son proper nouns de la región — quedan en castellano en ambos idiomas.
- **Identificadores en filenames de descarga**: el PNG exportado usa
  `cecn_amba_sale_precio_departamento_all.png` aún en EN, para que el
  filename sea estable entre idiomas.

---

## Verificación de integridad

El dashboard se auditó contra el informe oficial `Indices_AMBA.html` del
Centro (snapshot 202605). Los 8 valores YoY publicados (4 venta + 4
alquiler, CABA y AMBA × Casa y Departamento) coinciden al 0.00 pp con
los del dashboard. Detalle completo en
[`intern/AUDITORIA_INTEGRAL.md`](intern/AUDITORIA_INTEGRAL.md), que
incluye un script Python copy-paste para re-correr la verificación cada
mes.

### Diferencias de scope deliberadas con el informe oficial

| Aspecto | Informe `Indices_AMBA.html` | Dashboard | Razón |
|---|---|---|---|
| Inmuebles | Casa + Departamento + Oficina | Casa + Departamento | Oficina no aporta valor explicativo para el público general |
| Alquiler precios constantes | Sí | No (sólo corrientes) | Decisión editorial del Centro |
| Demanda / Oferta YoY agregado | No publicado | No expuesto | Coherente con la fuente |
| Tonicidad / Rentabilidad | No publicado | No expuesto | Coherente con la fuente |

---

## Troubleshooting

| Síntoma | Causa probable | Fix |
|---|---|---|
| `Explorer generado en: ... Snapshot: 202604` (cuando esperabas 202605) | Falta algún CSV del snapshot nuevo en `data/` | Verificar que los 6 archivos `*_202605.csv` estén presentes |
| `FileNotFoundError: No se encontró un snapshot común` | `data/` no tiene los 6 CSVs del mismo mes | Revisar nombres y prefijos exactos |
| `UnicodeDecodeError` | CSV en encoding raro | `data_store.py` ya prueba utf-8-sig, latin-1 e iso-8859-15. Si falla todo, reexportar el CSV en UTF-8. |
| `[WARN] columna 'X' no encontrada en la tabla 'Y'` | El pipeline R renombró una columna | Actualizar el mapeo en `lib/amba_dashboard/catalogs.py` (dict `LEVELS`) |
| Dashboard abre pero el panel se ve vacío | Snapshot incompleto o nombre de columna nuevo | Mirar el WARN en stderr del build |
| `Port 8000 already in use` | Algún `serve.py` viejo sigue activo | `python serve.py --port 8080` o matar el proceso anterior |
| ngrok devuelve `ERR_NGROK_*` | Token inválido o vencido | `ngrok config add-authtoken <TOKEN>` con el actual |

---

## Créditos

- **Datos**: Mercado Libre.
- **Análisis y curaduría**: Centro de Estudios Cuantitativos en Negocios
  (CECN), Universidad de San Andrés.
- **Pipeline R upstream**: Abigail (CECN).
