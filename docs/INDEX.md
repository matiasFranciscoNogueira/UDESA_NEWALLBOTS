# UDESA Projects Index

## Project 1: EPU-ARG-NEW
Economic Policy Uncertainty index calculator for Argentina using GDELT Global Knowledge Graph data from Google BigQuery. Processes Argentine news media articles (.ar domains) and calculates monthly EPU indices for 5 categories based on keyword analysis.

Key files:
- Main pipeline: `EPU-ARG-NEW/src/epu_bot_workflow.py`
- BigQuery fetcher: `EPU-ARG-NEW/src/epu_historical_GDELT_big_query.py`
- Documentation: `EPU-ARG-NEW/README.md`

## Project 2: MINIMAL_DOCKER_PLOT
Interactive Dash/Plotly dashboard for visualizing EPU index data. Accessible at http://localhost:8050. Embebible en iframe.

Key files:
- Main application: `MINIMAL_DOCKER_PLOT/src/main.py`
- Custom legend: `MINIMAL_DOCKER_PLOT/assets/legend.js`
- Iframe CSS fix: `MINIMAL_DOCKER_PLOT/assets/iframe.css`
- Documentation: `MINIMAL_DOCKER_PLOT/README.md`

## Project 3: nowcast-dashboard
Static HTML dashboard that visualizes EMAE nowcast estimations with confidence bands. Accessible at http://localhost:8060. Embebible en iframe.

Key files:
- HTML generator: `nowcast-dashboard/src/make_nowcast_history_html.py`
- Server: `nowcast-dashboard/src/main.py`
- Data: `nowcast-dashboard/src/data/nowcast_estimations_base_with_bands.xlsx`
- Documentation: `nowcast-dashboard/README.md`

## Infra
- `docker-compose.yml` — orquesta los tres servicios + nginx + ngrok
- `README.md` — guía completa de deploy, arquitectura y uso en iframe
