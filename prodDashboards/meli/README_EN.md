# AMBA Dashboard — Real Estate Market

> **Status:** production · snapshot **May 2026 (202605)** · audit 8/8 PASS against `Indices_AMBA.html`
> **Languages:** Spanish · English

Interactive, self-contained dashboard for the real estate market of the
Buenos Aires Metropolitan Area (AMBA — *Área Metropolitana de Buenos
Aires*). Produced by the **Center for Quantitative Business Studies
(CECN)** at Universidad de San Andrés, using data from Mercado Libre.

[Versión en castellano → README.md](README.md)

---

## What this is

- A single HTML file (`amba_explorer_en.html` for English,
  `amba_explorer.html` for Spanish) with **all data, styles, and JS
  embedded**. No external dependencies: no CDN calls, no application
  server required.
- Works on any static host (Apache, nginx, GitHub Pages, ngrok) or can
  be opened directly in a browser (double-click → it just works).
- Built with **Python ≥ 3.10 standard library only** — no third-party
  packages.

---

## Quickstart (from zero)

### 1. Prerequisites

- **Python 3.10 or higher.** Check with:

  ```bash
  python --version
  ```

  If missing, install from [python.org/downloads](https://www.python.org/downloads/).

### 2. Setup

From a terminal in the project folder (`version_final/`):

```bash
# Create and activate a virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (macOS / Linux)
source .venv/bin/activate

# Install dependencies (empty for now — the project uses stdlib only —
# but the file is here for future-proofing)
pip install -r requirements.txt
```

### 3. Build the dashboard

```bash
# English → amba_explorer_en.html
python build.py --lang en

# Spanish (default) → amba_explorer.html
python build.py
```

Expected output:

```
Explorer generado en: .../amba_explorer_en.html  (~4075 KB)
Idioma:               en
Snapshot de datos:    202605
```

(The build script's stdout is in Spanish — the dashboard contents are in
the chosen language. This is intentional: the script is for operators,
the dashboard is for end users.)

### 4. Serve locally

```bash
python serve.py --port 8000
```

Open in your browser:

- `http://localhost:8000/amba_explorer_en.html` (EN)
- `http://localhost:8000/amba_explorer.html` (ES, if you also built it)

---

## Monthly data refresh

Each time a new snapshot arrives from the R pipeline: see
**[ACTUALIZAR_DATOS.md](ACTUALIZAR_DATOS.md)** (Spanish only — operator
manual).

TL;DR: drop the 6 CSVs for the new month into `data/`, run
`python build.py`, verify 4 headline figures against the official report.

---

## Public exposure with ngrok

> Make sure ngrok is authenticated: first time, run `ngrok config
> add-authtoken <TOKEN>` with a token from
> [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken).

### English only (default use case)

```bash
# Terminal 1: static server
cd version_final/
python build.py --lang en
python serve.py --port 8000

# Terminal 2: public tunnel
ngrok http 8000
```

Share `https://<random>.ngrok-free.app/amba_explorer_en.html`.

### Both languages simultaneously (one port, two files)

```bash
# Terminal 1: build both
python build.py --lang es
python build.py --lang en

# Terminal 2: server
python serve.py --port 8000

# Terminal 3: tunnel
ngrok http 8000
```

Public URLs:

- `https://<random>.ngrok-free.app/amba_explorer.html` (ES)
- `https://<random>.ngrok-free.app/amba_explorer_en.html` (EN)

### ngrok notes

- On the free plan the URL **changes every time** the tunnel restarts.
  For a stable URL you need a paid plan or a reserved domain.
- `serve.py` sets `allow_reuse_address`: after Ctrl-C you can restart
  immediately with no waiting.
- If port 8000 is busy: `python serve.py --port 8080`.

---

## Project structure

```
version_final/
├── .gitignore                  ← ignores __pycache__, .venv, etc.
├── README.md                   ← Spanish documentation
├── README_EN.md                ← this file
├── ACTUALIZAR_DATOS.md         ← monthly refresh runbook (Spanish)
├── requirements.txt            ← (empty — Python stdlib only)
├── build.py                    ← generates amba_explorer*.html
├── serve.py                    ← minimal local HTTP server
├── amba_explorer.html          ← OUTPUT in Spanish (~4 MB)
├── amba_explorer_en.html       ← OUTPUT in English (~4 MB)
├── data/                       ← CSV snapshots from R pipeline
│   ├── VentasAgrupacion_202605.csv
│   ├── AlquileresAgrupacion_202605.csv
│   ├── VentasCABA_202605.csv
│   ├── AlquileresCABA_202605.csv
│   ├── VentasMunicipios_202605.csv
│   └── AlquileresMunicipios_202605.csv
├── lib/amba_dashboard/         ← self-contained Python package
│   ├── __init__.py
│   ├── data_store.py           ← snapshot discovery and loading
│   ├── utils.py                ← safe_float
│   ├── catalogs.py             ← regions, neighborhoods, municipalities, colors, LEVELS
│   ├── metrics.py              ← metric structure + per-language factory
│   ├── i18n.py                 ← LANG_ES / LANG_EN (all UI strings)
│   └── assets/branding/        ← UdeSA + Mercado Libre logos
├── source/
│   ├── template.html           ← HTML shell with __X__ placeholders
│   ├── explorer.css            ← styles (UdeSA institutional palette)
│   └── explorer.js             ← front-end logic (~50 KB, no frameworks)
└── intern/                     ← EVERYTHING non-essential to run/deliver
    ├── README_intern.md        ← what lives here and why
    ├── AUDITORIA_INTEGRAL.md   ← QA report (2026-05-21)
    ├── Indices_AMBA.html       ← official CECN report (reference)
    ├── Indices_AMBA_files/     ← reference report assets
    ├── _pycache_root/          ← stale bytecode (autogenerated)
    ├── _pycache_lib/           ← idem
    └── legacy_code/            ← deprecated package functions
```

---

## Data: contract with the R pipeline

The 6 CSVs in `data/` are produced by the **CECN R pipeline** (folder
`Index_AMBA/` on the Center's Drive). The dashboard consumes them as-is,
recomputing nothing beyond cosmetic transformations.

### Expected CSV schema

| Typical column | Type | Example |
|---|---|---|
| `Mes` (Month) | string `YYYY-MM` | `2026-05` |
| `Aglomerado` / `Barrio` / `Municipio` | string | `CABA` / `PALERMO` / `Tigre` |
| `Inmueble` (property type) | string | `Casa` (house), `Departamento` (apartment) |
| `Mediana Stock` / `Mediana Flujo` (median, stock / flow) | float (USD/m²) | `2632.94` |
| `Mediana por m2 a precios corrientes` (nominal median per m²) | float (ARS/m²) | `8430.12` |
| `Contactos` (contacts) | float (index) | `1.43` |
| `Oferta` (supply) | float (index) | `1.07` |

> **Note:** `VentasCABA_*.csv` uses `Mediana.Stock` (with a dot) because
> the R pipeline exports it via `write.csv`, which replaces spaces. The
> other tables use spaces. The code handles both variants.

### Index base contract

The `Contactos` (demand) and `Oferta` (supply) indices are **already
normalized in the R pipeline**; they are not recomputed here:

- **Supply (Oferta)**: base `January 2018 = 1`
- **Demand (Contactos)**: base `January 2019 = 1` (contact capture
  starts a year later than active-listings capture)

Verified against snapshots 202604 and 202605: the base is uniform across
property types and geographies. If the Center changes the base upstream,
update the strings in `lib/amba_dashboard/i18n.py` (keys
`saleMetrics.{demanda,oferta}` and `rentMetrics.{demanda,oferta}`).

### Partial-month rule

**Demand** and **supply** series for the last snapshot month are
incomplete (contacts keep coming in, listings keep opening after the
cutoff). The build excludes them, replicating the official report's
rule. **Price** is not filtered: median stock prices are final once the
month closes.

---

## Filters and controls

| Filter | Options | Notes |
|---|---|---|
| **Geographic level** | Region · Neighborhood (CABA) · Municipality (AMBA) | Changes the region catalog |
| **Region / Neighborhood / Municipality** | Multi-select | Default: AMBA + CABA |
| **Property type** | House · Apartment | Deliberate scope: Office not exposed |
| **Metric** | Price · Demand · Supply | Each in its natural unit |
| **Period (chips)** | 12 m · 24 m · 60 m · Full history | Default: full history |
| **Reset button** ↺ | Restores all filters |  |
| **Download buttons** ⬇ | Export panel as PNG |  |

### Presentation conventions

- **Capitalization**: each segment after `·` starts capitalized
  (`Houses · CABA neighborhoods`). Month names are also capitalized
  (`January 2026`).
- **Palette**: UdeSA institutional (navy blue `#0F3E7D` for sales, steel
  blue `#4A8CC1` for rentals). Green/red badges in stat cards are kept
  because they carry universal semantics (up/down), not brand.
- **Number locale**:
  - EN: `1,234.56` (comma thousands, decimal point)
  - ES: `1.234,56` (dot thousands, decimal comma)

---

## Bilingual support (ES / EN)

### Choosing the language

By flag at build time:

```bash
python build.py --lang en   # → amba_explorer_en.html
python build.py --lang es   # → amba_explorer.html       (default)
```

Each HTML is **self-contained**: the embedded JS reads UI strings from
the `lang` dictionary that `build.py` injects into the bootstrap.
**There is no runtime toggle** — opening `amba_explorer_en.html` shows
everything in English without any user action.

### Where the strings live

All UI strings live in `lib/amba_dashboard/i18n.py`, in two flat dicts
(`LANG_ES`, `LANG_EN`) with identical keys. The module includes an
`assert` that fails the build if the keys go out of sync — it works as a
translation linter when you add new strings.

### Adding / changing a string

1. Edit `lib/amba_dashboard/i18n.py`, adding or modifying the key in
   **both** dicts.
2. If new, reference it in `source/explorer.js` as `lang.myNewKey`.
3. Re-run `python build.py --lang es` and `python build.py --lang en`.

### What is not translated

- **Proper geographic names**: CABA, AMBA, PALERMO, Tigre, etc., are
  proper nouns of the region — they stay in Spanish in both languages.
- **Download filenames**: PNG exports use
  `cecn_amba_sale_precio_departamento_all.png` even in English, so
  filenames are stable across languages.

---

## Integrity verification

The dashboard was audited against the Center's official report
`Indices_AMBA.html` (snapshot 202605). All 8 published YoY values (4
sale + 4 rental, CABA and AMBA × House and Apartment) match the
dashboard within 0.00 pp. Full detail in
[`intern/AUDITORIA_INTEGRAL.md`](intern/AUDITORIA_INTEGRAL.md), which
includes a copy-paste Python script for re-running the verification each
month.

### Deliberate scope differences vs. the official report

| Aspect | Official `Indices_AMBA.html` | Dashboard | Reason |
|---|---|---|---|
| Property types | House + Apartment + Office | House + Apartment | Office adds no explanatory value for the general public |
| Rentals in constant prices | Yes | No (nominal only) | Editorial decision by CECN |
| Demand / supply aggregated YoY | Not published | Not exposed | Consistent with source |
| Tonicity / Profitability | Not published | Not exposed | Consistent with source |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Snapshot: 202604` (when you expected 202605) | A CSV for the new snapshot is missing in `data/` | Verify all 6 `*_202605.csv` files are present |
| `FileNotFoundError: No se encontró un snapshot común` | `data/` lacks the 6 CSVs for the same month | Check the exact prefix names |
| `UnicodeDecodeError` | CSV in an unusual encoding | `data_store.py` already tries utf-8-sig, latin-1, iso-8859-15. If all fail, re-export the CSV as UTF-8. |
| `[WARN] columna 'X' no encontrada en la tabla 'Y'` | The R pipeline renamed a column | Update the mapping in `lib/amba_dashboard/catalogs.py` (dict `LEVELS`) |
| Dashboard loads but the panel is empty | Incomplete snapshot or new column name | Check the WARN in build stderr |
| `Port 8000 already in use` | A previous `serve.py` is still running | `python serve.py --port 8080` or kill the old process |
| ngrok returns `ERR_NGROK_*` | Invalid or expired token | `ngrok config add-authtoken <TOKEN>` with the current one |

---

## Credits

- **Data**: Mercado Libre.
- **Analysis and curation**: Center for Quantitative Business Studies
  (CECN), Universidad de San Andrés.
- **Upstream R pipeline**: Abigail (CECN).
