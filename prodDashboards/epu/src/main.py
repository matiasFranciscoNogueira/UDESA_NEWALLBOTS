from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import os
import sqlite3

# -------------------------
# APP SETUP
# -------------------------
url_prefix = os.environ.get("URL_PREFIX", "/")

if not url_prefix.startswith("/"):
    url_prefix = "/" + url_prefix

if not url_prefix.endswith("/"):
    url_prefix = url_prefix + "/"

app = Dash(
    __name__,
    assets_folder=str(Path(__file__).resolve().parents[1] / "assets"),
    requests_pathname_prefix=url_prefix,
    routes_pathname_prefix=url_prefix
)

server = app.server
server.config["APPLICATION_ROOT"] = url_prefix

raw_lang = os.environ.get("LANG", "EN").upper()

if raw_lang.startswith("ES"):
    APP_LANG = "ES"
else:
    APP_LANG = "EN"

app.index_string = f"""
<!DOCTYPE html>
<html lang="{APP_LANG}">
<head>
    {{%metas%}}
    {{%css%}}
</head>
<body>
    {{%app_entry%}}
    <footer>
        {{%config%}}
        {{%scripts%}}
        {{%renderer%}}
    </footer>
</body>
</html>
"""

# -------------------------
# TRANSLATIONS
# -------------------------

TRANSLATIONS = {
    "EN": {
        "date": "Date",
        "epu": "EPU",
        "months": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],
        "currency_crisis": "Currency crisis",
        "monetary_policy": "Monetary policy",
        "trade": "Trade",
    },
    "ES": {
        "date": "Fecha",
        "epu": "EPU",
        "months": ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"],
        "currency_crisis": "Crisis cambiaria",
        "monetary_policy": "Politica monetaria",
        "trade": "Comercio",
    }
}

def t(key):
    return TRANSLATIONS.get(APP_LANG, {}).get(key, key)

# -------------------------
# DATABASE PATH
# -------------------------
RESULTS_DB = Path("/app/data/epu/db/database.sqlite")
if not RESULTS_DB.exists():
    raise RuntimeError(
        f"Database not found at {RESULTS_DB}. "
        "Ensure epu-arg extractor has run successfully."
    )
print("Using DB at:", RESULTS_DB)


# -------------------------
# LAYOUT
# -------------------------
app.layout = html.Div(
    [
        html.Div(
            [
                dcc.Graph(
                    id="epu-graph",
                    config={"responsive": True},
                    style={
                        "width": "100%",
                        "height": "100%",
                    },
                )
            ],
            style={
                "flex": "1",
                "minHeight": "0",  # 🔥 critical for flex + Plotly
            },
        ),
        dcc.Interval(id="interval", interval=120000, n_intervals=0),
    ],
    style={
        "display": "flex",
        "flexDirection": "column",
        "height": "100vh",
        "width": "100%",
        "overflow": "hidden",
    },
)

# -------------------------
# CALLBACK
# -------------------------
@app.callback(
    Output("epu-graph", "figure"),
    Input("interval", "n_intervals")
)
def update_graph(_):

    conn = sqlite3.connect(RESULTS_DB)

    df = pd.read_sql("SELECT * FROM data", conn)

    if df.empty:
        return go.Figure()

    df = df.rename(columns={"fecha": "date"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    ghirelli_values = None
    ghirelli_benchmark = False
    try:
        ghirelli = pd.read_sql("SELECT * FROM benchmark", conn)

        if not ghirelli.empty:
            ghirelli = ghirelli.rename(columns={"fecha": "date"})
            ghirelli["date"] = pd.to_datetime(ghirelli["date"])
            ghirelli = ghirelli.set_index("date").reindex(df.index).ffill()
            ghirelli_values = ghirelli.iloc[:, 0]

    except Exception:
        pass

    TAB20 = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
        '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5'
    ]

    fig = go.Figure()

    COLUMN_MAP = {
        "currency_crisis": "currency_crisis",
        "monetary_policy": "monetary_policy",
        "trade": "trade"
    }
    for i, col in enumerate(df.columns):
        normalized = col.lower().replace(" ", "_")

        if normalized in TRANSLATIONS[APP_LANG]:
            label = t(normalized)
        else:
            label = col

        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                mode="lines",
                name=label,
                line=dict(color=TAB20[i % len(TAB20)], width=2.2),
                hovertemplate="<b>%{text}</b><br>" +
                f"{t('date')}: %{{x|%Y-%m}}<br>" +
                f"{t('epu')}: %{{y:.2f}}<extra></extra>",
                text=[label] * len(df)
            )
        )

    if (ghirelli_values is not None) and ghirelli_benchmark:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=ghirelli_values,
                mode="lines",
                name="Ghirelli (benchmark)",
                line=dict(color="black", width=3.5, dash="dash"),
                hovertemplate="<b>Ghirelli (benchmark)</b><br>" +
                f"{t('date')}: %{{x|%Y-%m}}<br>" +
                f"{t('epu')}: %{{y:.2f}}<extra></extra>"
            )
        )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        showlegend=False,
        uirevision="constant",
        font=dict(family="Helvetica, Arial, sans-serif", size=14, color="black"),
        margin=dict(l=70, r=20, t=20, b=120),
        autosize=True
    )

    # Build translated monthly ticks
    dates = pd.to_datetime(df.index).sort_values()

    monthly_dates = pd.date_range(
        start=dates.min(),
        end=dates.max(),
        freq="MS"
    )

    months = t("months")

    total_months = len(monthly_dates)

    # 🎯 Adaptive step
    if total_months <= 24:
        step = 1        # every month
    elif total_months <= 60:
        step = 3        # quarterly
    else:
        step = 6        # semi-annual

    filtered_dates = monthly_dates[::step]

    tickvals = [d.to_pydatetime() for d in filtered_dates]
    ticktext = [f"{months[d.month-1]} {d.year}" for d in filtered_dates]

    fig.update_xaxes(
        tickangle=-45,
        tickmode="array",
        tickvals=tickvals,
        ticktext=ticktext,
        showgrid=False,
        zeroline=False,
        showline=False,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikedash="solid",
        spikecolor="rgba(0,0,0,0.25)",
        spikethickness=1,
        rangeslider=dict(visible=False),
        type="date",
        tickformat=None,
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(0,0,0,0.10)",
        gridwidth=1,
        zeroline=False,
        showline=False,
    )

    return fig


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)