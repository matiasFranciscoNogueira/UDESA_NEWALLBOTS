# Real Estate Explorer · Multi-market

Interactive dashboard of the Argentine real estate market, covering
**Buenos Aires (AMBA + CABA + GBA)**, **Córdoba**, and **Rosario**.
Produced by the Center for Quantitative Business Studies at Universidad
de San Andrés, in collaboration with Mercado Libre.

**Version:** `new_version` (multi-market). Replaces `version_final` (AMBA-only).
**Bundled snapshot:** `202608` (August 2026). Server deployment: see `DEPLOY.md`.
**Languages:** Spanish (`amba_explorer.html`) and English (`amba_explorer_en.html`).
**Status:** verified against the previous dashboard (646 series bit-identical
for Buenos Aires) and against the official Córdoba and Rosario reports
(22/22 spot checks within report precision).

---

## Quickstart

```bash
# No external dependencies: pure Python 3.10+.
cd new_version

# Option 1 — use the pre-packaged HTML
python serve.py        # opens local server at http://localhost:8000

# Option 2 — rebuild the HTML from CSVs
python build.py                # → amba_explorer.html
python build.py --lang en      # → amba_explorer_en.html
python serve.py                # then serve
```

To expose publicly via ngrok:

```bash
python serve.py             # terminal 1
ngrok http 8000             # terminal 2 — grab the https://...ngrok-free.app URL
```

---

## Project structure

```
new_version/
├── README.md                   Spanish version
├── README_EN.md                this file
├── ACTUALIZAR_DATOS.md         monthly snapshot update runbook (Spanish)
├── build.py                    builds the self-contained HTML
├── serve.py                    local static HTTP server
├── requirements.txt            (empty: stdlib only)
├── amba_explorer.html          output: ES, ~5 MB, self-contained
├── amba_explorer_en.html       output: EN, ~5 MB, self-contained
├── data/                       14 CSVs from the R pipeline (current snapshot; older ones in data/older/)
├── lib/dashboard/              Python package
│   ├── catalogs.py             MARKETS registry + visibility rules
│   ├── data_store.py           snapshot discovery + CSV loading
│   ├── metrics.py              metric definitions
│   ├── i18n.py                 ES + EN strings + sync linter
│   ├── utils.py                safe_float
│   └── assets/branding/        UdeSA + Mercado Libre logos
├── source/                     frontend (template + CSS + JS)
│   ├── template.html
│   ├── explorer.css
│   └── explorer.js
└── intern/                     EVERYTHING NON-ESSENTIAL to run or deliver
    ├── README_intern.md        what lives here and why
    ├── CHANGELOG.md            differences vs version_final
    ├── docs/
    │   ├── ARQUITECTURA.md     Alternative C architecture (Spanish)
    │   └── DECISIONES.md       visibility decisions registry (Spanish)
    ├── verification/           QA artifacts (regenerable)
    │   ├── verify_baseline.py  compares new vs version_final
    │   ├── verify_informes.py  spot checks vs official reports
    │   ├── verify_full.py      75 claims from the 3 official reports
    │   ├── verification_report.md
    │   └── spot_checks.md
    ├── AMBA_Informe202605.docx      official AMBA report (source of truth)
    ├── Cordoba_Informe202605.docx   official Córdoba report
    ├── Rosario_Informe202605.docx   official Rosario report
    ├── Indices_AMBA.html            Centro's HTML report (reference)
    └── Indices_AMBA_files/          assets for the reference HTML report
```

---

## Coverage

Three markets, with heterogeneous geographic levels and data availability.

### Buenos Aires
- **Region** (Level 1): AMBA, CABA, GBA North / West / South.
- **CABA Neighborhood**: 43 neighborhoods.
- **GBA District**: 30 districts of the conurbano + Capital Federal.

### Córdoba
- **City**: Córdoba.
- **Zone**: Córdoba Center / East / North / West / South (5 zones).
- **Neighborhood**: 30 neighborhoods of Córdoba city (Sales only — see
  editorial decision below).

### Rosario
- **City**: Rosario.
- **Zone**: Rosario Center / North / West / South (4 zones, no East).
- **Neighborhood**: 14 neighborhoods of Rosario city (Sales only — see
  editorial decision below).

### What is NOT exposed (editorial decisions)

These cells exist in the CSVs but the dashboard does NOT display them
(documented in `intern/docs/DECISIONES.md`):

- **Córdoba Zones Rental — House**: only 2 of 5 zones have House data.
- **Córdoba Neighborhoods Rental**: only 4 neighborhoods, no House.
- **Rosario Zones Rental**: only Rosario Center has data.
- **Rosario Neighborhoods Rental**: only CENTRO has data.

In those combinations the panel shows an editorial message explaining
why there is no chart.

### Excluded series
- **ARGUELLO/House in Córdoba**: series discontinued in January 2024,
  excluded from the neighborhoods dropdown when House is selected.

---

## Metrics

Identical to the previous dashboard, aligned with the Centro reports:

| Side | Metric | Unit | Notes |
|---|---|---|---|
| Sales | Median price | USD/m² (stock + flow when applicable) | Does not exclude last month |
| Sales | Demand | Contacts index (base Jan 2019 = 1) | Excludes last month (partial) + initial zeros |
| Sales | Supply | Active-listings index (base Jan 2018 = 1) | Excludes last month |
| Rentals | Median price | ARS/m² nominal | Does not exclude last month |
| Rentals | Demand | Contacts index (base Jan 2019 = 1) | Excludes last month |
| Rentals | Supply | Active-listings index (base Jan 2018 = 1) | Excludes last month |

The index bases **come pre-computed from the R pipeline**. The dashboard
does not recompute bases.

---

## Property types in scope

Only `Casa` (House) and `Departamento` (Apartment). Offices, retail
spaces, and room-count subsets are out of scope (documented as deferral
in `intern/docs/DECISIONES.md`).

---

## Numeric verification

Two automated protocols, both pass at checkout:

### Buenos Aires vs version_final
- **646 series compared: 453 bit-for-bit identical + 193 with 1 extra
  point.** The 193 are all **oferta** (supply) series and grow by exactly
  1 point (May 2026): the intentional partial-last-month fix documented in
  `intern/CHANGELOG.md` ("Fix de oferta" section). **Price and demand stay
  100% bit-identical.** Any other kind of mismatch = investigate before
  publishing.
- Report: `intern/verification/verification_report.md`.
- Re-run: `python intern/verification/verify_baseline.py`.

### Córdoba + Rosario vs official reports
- **22 spot checks, 22 PASS** (tolerance 0.06 pp).
- Report: `intern/verification/spot_checks.md`.
- Re-run: `python intern/verification/verify_informes.py`.

The verified values are those literally cited in
`Cordoba_Informe202605.docx` and `Rosario_Informe202605.docx` (May 2026):
month-on-month and year-on-year variations by city, zones, and
neighborhoods.

---

## Available filters

| Filter | Options |
|---|---|
| Market | Buenos Aires · Córdoba · Rosario |
| Geographic level | Region/Neighborhood/District (BA) · City/Zone/Neighborhood (Cba, Ros) |
| Regions | Multi-select with search when more than 15 options |
| Property type | House · Apartment |
| Metric | Median price · Demand · Supply |
| Period | 12 m · 24 m · 60 m · Full history |

Dropdowns are **dynamic**: when changing market / level / property type,
options are filtered to those with available data per the visibility
matrix. The user cannot select a combination that the Centro does not
publish.

---

## Internationalization

Two separate HTMLs: `amba_explorer.html` (default) and `amba_explorer_en.html`.
The front-end consumes `bootstrap.lang` for all visible strings. Data
identifiers (market, level, region, property keys) are NOT translated —
only the display labels.

To add a new language:
1. Copy `LANG_ES` in `lib/dashboard/i18n.py`, rename and translate.
2. Add it to `_LANGS` and to the `--lang` choices.
3. The `_assert_keys_in_sync()` linter fails the build if any key is missing.

---

## Institutional palette

- **Buenos Aires**: original palette (AMBA blue, CABA coral, etc.).
- **Córdoba**: red-orange family.
- **Rosario**: green-blue family.
- **Sales**: top border navy UdeSA (`#0F3E7D`).
- **Rentals**: top border steel blue (`#4A8CC1`).

Defined in `lib/dashboard/catalogs.py` (constant `COLORS`).

---

## Monthly update

See `ACTUALIZAR_DATOS.md` (Spanish) for the step-by-step protocol.

Summary: the Centro's R pipeline generates 14 new CSVs each month with
a `_YYYYMM` suffix. Copy them to `data/` and run `python build.py` to
regenerate the HTML.

---

## Additional documentation

- `intern/docs/ARQUITECTURA.md` (Spanish) — "Market + dynamic levels" architecture
  (Alternative C). Explains the `MARKETS → availability → state machine` flow.
- `intern/docs/DECISIONES.md` (Spanish) — full registry of editorial decisions
  with justification: why each cell is hidden, why ARGUELLO is excluded,
  why Office is deferred.
- `intern/CHANGELOG.md` — concrete differences vs `version_final`.

---

## Support

- Internal issues / questions: contact the Centro de Estudios
  Cuantitativos en Negocios (UdeSA) team.
- For verification against new monthly reports: edit the ``CASES`` list
  in `intern/verification/verify_informes.py` with the highlighted values of
  the new report and run the script.
