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

PAGE_LANG = os.environ.get("LANG")

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
# TRANSLATION
# -------------------------
DATELABEL = "Date" if PAGE_LANG == "EN" else "Fecha"

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

    for i, col in enumerate(df.columns):
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col],
                mode="lines",
                name=col,
                line=dict(color=TAB20[i % len(TAB20)], width=2.2),
                hovertemplate="<b>%{text}</b><br>" +
                            DATELABEL + ": %{x|%Y-%m}<br>" +
                            "EPU: %{y:.2f}<extra></extra>",
                text=[col] * len(df)
            )
        )

    if ghirelli_values is not None:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=ghirelli_values,
                mode="lines",
                name="Ghirelli (benchmark)",
                line=dict(color="black", width=3.5, dash="dash"),
                hovertemplate="<b>Ghirelli (benchmark)</b><br>" +
                            DATELABEL + ": %{x|%Y-%m}<br>" +
                            "EPU: %{y:.2f}<extra></extra>"
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

    fig.update_xaxes(
        tickangle=-45,
        tickformat="%b %Y",
        dtick="M6",
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
        tickmode="linear",
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