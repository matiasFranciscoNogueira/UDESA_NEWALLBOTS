# EPU-ARG — Economic Policy Uncertainty for Argentina

Builds a monthly EPU (Economic Policy Uncertainty) index for Argentina from the GDELT Global Knowledge Graph via Google BigQuery, following the Baker, Bloom & Davis (2016) methodology.

---

## How it works

1. Queries BigQuery for articles from 12 Argentine news outlets that mention **Economy + Policy + Uncertainty** keywords simultaneously
2. Normalizes article counts to a monthly EPU index (base 100)
3. Runs for 5 categories: the full index + 4 subcategories (Trade, Fiscal, Monetary Policy, Currency Crisis)
4. Saves results as Excel files and generates a combined file ready for the dashboard

**EPU formula:**
```
EPU = 100 × (articles matching E AND P AND U keywords) / (total articles from outlet)
```

**Tracked outlets (12):** Clarín, La Nación, Infobae, Ámbito, Página 12, Perfil, TN, Cronista, La Voz, Minuto Uno, Diario Popular, Diario Uno

---

## Prerequisites

### 1. Python & Poetry

Requires Python 3.12+. Install Poetry if you don't have it:

```bash
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
poetry --version
```

### 2. Google Cloud credentials

You need a Google Cloud service account with **BigQuery Editor** role:

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. IAM & Admin → Service Accounts → Create service account
3. Grant role: `BigQuery Editor`
4. Keys tab → Add Key → Create new key → JSON
5. Save the downloaded file as:

```
EPU-ARG-main/keys/epu-udesa-gdelt-reader-personal.json
```

---

## Setup

```bash
cd EPU-ARG-main
poetry install
```

---

## Running locally

### Full pipeline (recommended)

Runs all 5 categories end-to-end and generates the combined file for the dashboard:

```bash
cd EPU-ARG-main/src
poetry run python epu_bot_workflow.py
```

Three steps run automatically for each of the 5 EPU categories (`none`, `trade`, `fiscal`, `monetary_policy`, `currency_crisis`):

1. **Fetch** — queries BigQuery from the last saved date to today (incremental), saves raw CSV to `data/`
2. **Analyze** — normalizes to monthly EPU index, saves Excel to `data/results/`
3. **Join** — combines all 5 results into `../MINIMAL_DOCKER_PLOT-main/data/all_subcategories_compare.xlsx`

### Step by step (run parts separately)

```bash
cd EPU-ARG-main/src

# Step 1 only — fetch/update raw data from BigQuery
poetry run python epu_historical_GDELT_big_query.py

# Steps 2 + 3 — analyze existing CSVs and generate the combined dashboard file (no BigQuery needed)
poetry run python analysis_compare_with_benchmarks_with_events_save_to_file.py
```

### Legacy Matplotlib plots

```bash
cd EPU-ARG-main/src
MPLBACKEND=qtagg poetry run python old_review/analysis_compare_with_benchmark_by_media.py
MPLBACKEND=qtagg poetry run python old_review/analysis_compare_with_benchmark_with_events.py
MPLBACKEND=qtagg poetry run python old_review/analysis_vs_benchmarks.py
```

---

## Output

All outputs go to `EPU-ARG-main/data/`:

| Path | Contents |
|---|---|
| `data/epu_argentina_..._maped_all_media_with_sentiment.csv` | Raw daily data — main category |
| `data/subcategories/epu_argentina_..._<subcategory>_maped_all_media_with_sentiment.csv` | Raw daily data — per subcategory |
| `data/results/epu_analysis_results_udesa_jp.xlsx` | Monthly EPU results — main |
| `data/results/subcategories/epu_analysis_results_udesa_jp_<subcategory>.xlsx` | Monthly EPU results — per subcategory |
| `../MINIMAL_DOCKER_PLOT-main/data/all_subcategories_compare.xlsx` | Combined file for the dashboard |

---

## Running with Docker

The recommended way is to use the root-level `docker-compose.yml`, which handles both services and the shared volume automatically — see [../README.md](../README.md) for full instructions.

To run only the analysis container standalone (output goes to the dashboard's data directory):

```bash
# From the project root (newoctaproj/)
docker build -t epu-arg ./EPU-ARG-main

docker run --rm \
  -v "$(pwd)/EPU-ARG-main/keys:/app/keys:ro" \
  -v "$(pwd)/EPU-ARG-main/data:/app/data" \
  -v "$(pwd)/MINIMAL_DOCKER_PLOT-main/data:/app/dashboard-data" \
  -e SHARED_DATA_PATH=/app/dashboard-data \
  epu-arg
```

The `SHARED_DATA_PATH` env var controls where `all_subcategories_compare.xlsx` is written. When running via `docker compose` this is handled automatically by the shared named volume.

---

## BigQuery quotas

- Free tier: **1 TB/month** scanned
- The script always does a **dry-run cost estimate** before executing — check the output before confirming
- Monthly GKG slice ≈ 45 GB, so a full year run uses ~0.5 TB (~$2.50 if billed)
- Data is fetched **incrementally** — re-running only fetches what's new since the last saved date

---

## Configuration

Key parameters are at the top of `src/epu_historical_GDELT_big_query.py`:

```python
# Keyword dictionary (controls which GDELT themes count as E/P/U)
kw_file = "key_words_gdelt_maped_jp.json"

# Outlets to track
medios = ["clarin.com", "lanacion.com.ar", ...]
```

Subcategory keyword dictionaries are in `src/keywords_dicts/subcategories/`.

---

## Benchmark

The benchmark overlay in the dashboard comes from:

> Andres-Escayola, Ghirelli, Molina, Pérez & Vidal (2022) — *"Using newspapers for textual indicators: which and how many?"* — Bank of Spain Working Paper N. 2235

File: `data/EPU_All_benchmark_ghirelli.xlsx` — contains EPU for 12 Latin American countries. Column used: `EPU_ARG_local`.
