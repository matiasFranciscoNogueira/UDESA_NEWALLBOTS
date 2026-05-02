from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import os
import sys

# Ensure project root is on sys.path so `import src` works when running `python src/main.py`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.db import read_table

url_prefix = os.environ.get("URL_PREFIX", "/")
app = Dash(__name__, assets_folder=str(ROOT / "assets"), url_base_pathname=url_prefix)

FROM_DOCKER = os.environ.get("FROM_DOCKER", "false").lower() == "true"

if FROM_DOCKER:
    RESULTS_DB = Path("/app/data/epu/data/database.sqlite")
else:
    RESULTS_DB = (Path(__file__).parent.parent / "data" / "database.sqlite").resolve()

if not RESULTS_DB.exists():
    print(f"WARNING: Database not found at {RESULTS_DB}. Run scripts/import_excel_to_sqlite.py to create it.")


app.layout = html.Div([
    dcc.Graph(id="epu-graph", style={"height": "100%"}),
    dcc.Interval(id="interval", interval=120_000, n_intervals=0)
], style={"height": "100%"})

@app.callback(
    Output("epu-graph", "figure"),
    Input("interval", "n_intervals"),
)
def update_graph(_):
    # Read tables from sqlite database
    df = read_table('data', RESULTS_DB)
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'])
        df = df.set_index('fecha')

    ghirelli = read_table('benchmark', RESULTS_DB)
    if 'fecha' in ghirelli.columns:
        ghirelli['fecha'] = pd.to_datetime(ghirelli['fecha'])
        ghirelli = ghirelli.set_index('fecha').reindex(df.index).ffill()
    ghirelli_values = ghirelli.iloc[:, 0]

    TAB20 = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
        '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5'
    ]

    fig = go.Figure()

    for i, col in enumerate(df.columns):
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df[col],
            mode='lines',
            name=col,
            line=dict(color=TAB20[i % len(TAB20)], width=2.2),
            hovertemplate='<b>%{text}</b><br>' +
                          'Fecha: %{x|%Y-%m}<br>' +
                          'EPU: %{y:.2f}<extra></extra>',
            text=[col] * len(df)
        ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=ghirelli_values,
        mode='lines',
        name='Ghirelli (benchmark)',
        line=dict(color='black', width=3.5, dash='dash'),
        hovertemplate='<b>Ghirelli (benchmark)</b><br>' +
                      'Fecha: %{x|%Y-%m}<br>' +
                      'EPU: %{y:.2f}<extra></extra>'
    ))

    fig.update_layout(
        template="plotly_white",
        height=None,
        width=None,
        title=None,
        hovermode="x unified",
        showlegend=False,
        uirevision="constant",
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(0,0,0,0.15)",
            font=dict(size=13, family="Helvetica, Arial, sans-serif", color="black"),
        ),
        font=dict(family="Helvetica, Arial, sans-serif", size=14, color="black"),
        margin=dict(l=70, r=20, t=20, b=70),
    )

    fig.update_xaxes(
        title=None,
        tickangle=-45,
        tickformat="%b %Y",
        tickmode='auto',
        nticks=20,
        showgrid=False,
        zeroline=False,
        showline=False,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="solid",
        spikecolor="rgba(0,0,0,0.25)",
        spikethickness=1,
        rangeselector=dict(
            buttons=list([
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(step="all", label="All")
            ])
        ),
        rangeslider=dict(visible=False),
        type="date",
        range=[df.index.min().strftime("%Y-%m-%d"), df.index.max().strftime("%Y-%m-%d")],
    )

    fig.update_yaxes(
        title=None,
        showgrid=True,
        gridcolor="rgba(0,0,0,0.10)",
        gridwidth=1,
        zeroline=False,
        showline=False,
    )

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
    )

    return fig

if __name__ == "__main__":
    if FROM_DOCKER:
        app.run(debug=False, host="0.0.0.0", port=8050)
    else:
        app.run(debug=False, port=8050)
