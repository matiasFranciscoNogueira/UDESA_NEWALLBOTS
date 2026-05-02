#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NOWCAST HISTORY (Plotly) con leyenda custom tipo "checkbox" (tick verde)
------------------------------------------------------------------------
- Leyenda innovadora y profesional: panel flotante con:
  * Checkboxes por serie (tick si está activa)
  * Grupos (Series / Confidence bands) con checkbox de grupo (incluye estado mixto)
  * Buscador
  * Botones rápidos: Show all, Hide all, Only Nowcast
  * Doble click en una serie: aislar (doble click otra vez: restaurar)
  * Doble click en un grupo: aislar el grupo (doble click otra vez: restaurar)

Genera un HTML autocontenido (inline) o liviano (cdn).
"""

import argparse
from pathlib import Path
import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


# ============================================================
# DASHBOARD-LIKE SETTINGS
# ============================================================
START_TQ = pd.Timestamp("2024-06-30")  # 2024:Q2 end (arranque nowcast/bandas desde Q2)


# -----------------------------
# Helpers
# -----------------------------
def to_dt(s: pd.Series) -> pd.Series:
    """Coerce to naive datetime (no tz), day precision."""
    out = pd.to_datetime(s, errors="coerce")
    try:
        out = out.dt.tz_localize(None)
    except Exception:
        pass
    return out.dt.floor("D")


def as_py_datetimes(dt_series: pd.Series) -> list:
    """Plotly-friendly python datetimes."""
    dt_series = pd.to_datetime(dt_series, errors="coerce").dropna()
    return [pd.Timestamp(x).to_pydatetime() for x in dt_series]


def add_band(fig: go.Figure, x, lo, hi, name: str, fillcolor: str, legendrank: int) -> None:
    """Add a filled band (polygon) similar to Matlab fill([x;flip(x)],[lo;flip(hi)])."""
    x = pd.to_datetime(x, errors="coerce")
    lo = pd.to_numeric(lo, errors="coerce").to_numpy()
    hi = pd.to_numeric(hi, errors="coerce").to_numpy()

    mask = x.notna().to_numpy() & np.isfinite(lo) & np.isfinite(hi)
    x = x[mask]
    lo = lo[mask]
    hi = hi[mask]

    if len(x) == 0:
        return

    order = np.argsort(x.values)
    x = x.iloc[order]
    lo = lo[order]
    hi = hi[order]

    xx = np.concatenate([x.values, x.values[::-1]])
    yy = np.concatenate([lo, hi[::-1]])

    fig.add_trace(
        go.Scatter(
            x=xx,
            y=yy,
            mode="lines",
            line=dict(width=0),
            fill="toself",
            fillcolor=fillcolor,
            name=name,
            hoverinfo="skip",
            showlegend=True,
            legendrank=legendrank,
        )
    )


# -----------------------------
# Read Excel bundle
# -----------------------------
def read_nowcast_excel(xlsx_path: Path) -> dict:
    xlsx_path = Path(xlsx_path)
    xl = pd.ExcelFile(xlsx_path)
    sheets = set(xl.sheet_names)

    required = {
        "all_nowcast_bands",
        "plot_full_history_indec",
        "plot_full_history_rem",
        "plot_full_history_ticks",
        "plot_full_history_meta",
    }
    missing = sorted(list(required - sheets))
    if missing:
        raise ValueError(
            "El Excel no tiene todas las hojas necesarias.\n"
            f"Faltan: {missing}\n"
            f"Sheets disponibles: {sorted(list(sheets))}"
        )

    # all nowcast + bands
    df = pd.read_excel(xlsx_path, sheet_name="all_nowcast_bands")
    df["Date"] = to_dt(df["Date"])
    if "TargetQuarter" in df.columns:
        df["TargetQuarter"] = to_dt(df["TargetQuarter"])
    df = df.sort_values("Date").reset_index(drop=True)

    # meta
    meta_df = pd.read_excel(xlsx_path, sheet_name="plot_full_history_meta")
    meta = meta_df.iloc[0].to_dict() if len(meta_df) else {}
    meta["Unit"] = str(meta.get("Unit", ""))
    meta["YLabel"] = str(meta.get("YLabel", "Value"))
    meta["AnchorQuarterEnd"] = pd.to_datetime(meta.get("AnchorQuarterEnd"), errors="coerce")
    meta["AnchorDate"] = pd.to_datetime(meta.get("AnchorDate"), errors="coerce")
    meta["PadLeftDays"] = int(meta.get("PadLeftDays", 7))
    meta["PadRightDays"] = int(meta.get("PadRightDays", 7))

    if pd.isna(meta["AnchorDate"]):
        raise ValueError("plot_full_history_meta.AnchorDate es NaT o inválido.")
    anchor_date = pd.Timestamp(meta["AnchorDate"]).floor("D")

    anchor_qend = (
        pd.Timestamp(meta["AnchorQuarterEnd"]).floor("D")
        if not pd.isna(meta["AnchorQuarterEnd"])
        else pd.Timestamp("2024-03-31")
    )

    # indec
    indec = pd.read_excel(xlsx_path, sheet_name="plot_full_history_indec")
    for c in ["QuarterEnd", "PubProxyDate", "PlotDate"]:
        if c in indec.columns:
            indec[c] = to_dt(indec[c])
    indec = indec.sort_values("PlotDate")

    # rem
    rem = pd.read_excel(xlsx_path, sheet_name="plot_full_history_rem")
    for c in ["REM_Month", "REM_PubProxy", "PlotDate"]:
        if c in rem.columns:
            rem[c] = to_dt(rem[c])
    rem = rem.sort_values("PlotDate")

    # ticks
    ticks = pd.read_excel(xlsx_path, sheet_name="plot_full_history_ticks")
    for c in ["QuarterEnd", "TickDate"]:
        if c in ticks.columns:
            ticks[c] = to_dt(ticks[c])
    ticks = (
        ticks.dropna(subset=["TickDate"])
        .sort_values("TickDate")
        .drop_duplicates(subset=["TickDate"], keep="first")
    )

    return {
        "bands": df,
        "indec": indec,
        "rem": rem,
        "ticks": ticks,
        "meta": meta,
        "anchor_date": anchor_date,
        "anchor_qend": anchor_qend,
        "sheets": sheets,
    }


# -----------------------------
# Build figure (Matlab-like) + professional touches
# -----------------------------
def build_nowcast_figure(bundle: dict) -> go.Figure:
    df_all = bundle["bands"].copy()
    indec_all = bundle["indec"].copy()
    rem_all = bundle["rem"].copy()
    ticks_all = bundle["ticks"].copy()

    meta = bundle["meta"]
    anchor_date = bundle["anchor_date"]
    anchor_qend = bundle["anchor_qend"]

    # Filter dashboard
    if "TargetQuarter" in df_all.columns:
        df = df_all[df_all["TargetQuarter"].notna() & (df_all["TargetQuarter"] >= START_TQ)].copy()
        if df.empty:
            df = df_all.copy()
    else:
        df = df_all.copy()

    indec = indec_all.copy()
    if "QuarterEnd" in indec.columns:
        indec = indec[(indec["QuarterEnd"] == anchor_qend) | (indec["QuarterEnd"] >= START_TQ)].copy()

    rem = rem_all.copy()
    if "PlotDate" in rem.columns:
        rem = rem[rem["PlotDate"].notna() & (rem["PlotDate"] >= anchor_date)].copy()

    ticks = ticks_all.copy()
    if "QuarterEnd" in ticks.columns:
        ticks = ticks[(ticks["QuarterEnd"] == anchor_qend) | (ticks["QuarterEnd"] >= START_TQ)].copy()

    # X range
    padL = int(meta.get("PadLeftDays", 7))
    padR = int(meta.get("PadRightDays", 7))
    xmin = anchor_date - pd.Timedelta(days=padL)

    allx_parts = [df["Date"].dropna()]
    if "PlotDate" in indec.columns:
        allx_parts.append(indec["PlotDate"].dropna())
    if "PlotDate" in rem.columns:
        allx_parts.append(rem["PlotDate"].dropna())
    allx = pd.to_datetime(pd.concat(allx_parts), errors="coerce").dropna()
    xmax = allx.max() + pd.Timedelta(days=padR)

    if "TickDate" in ticks.columns:
        ticks = ticks[(ticks["TickDate"] >= xmin) & (ticks["TickDate"] <= xmax)].copy()
        ticks = (
            ticks.dropna(subset=["TickDate"])
            .sort_values("TickDate")
            .drop_duplicates(subset=["TickDate"], keep="first")
        )

    # Colors (Matlab-like)
    col80 = "rgba(230,240,255,1.0)"
    col70 = "rgba(209,224,250,1.0)"
    col60 = "rgba(189,209,247,1.0)"
    col50 = "rgba(168,194,245,1.0)"

    indec_line = "rgb(217,89,0)"
    indec_fill = "rgb(255,140,26)"
    rem_gray = "rgb(89,89,89)"

    fig = go.Figure()

    # Bands (behind)
    add_band(fig, df["Date"], df["p10"], df["p90"], "80%", col80, legendrank=140)
    add_band(fig, df["Date"], df["p15"], df["p85"], "70%", col70, legendrank=130)
    add_band(fig, df["Date"], df["p20"], df["p80"], "60%", col60, legendrank=120)
    add_band(fig, df["Date"], df["p25"], df["p75"], "50%", col50, legendrank=110)

    # Nowcast
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=pd.to_numeric(df["Nowcast"], errors="coerce"),
            mode="lines",
            name="Nowcast",
            line=dict(width=2.4, color="black"),
            legendrank=10,
            hovertemplate="%{x|%Y-%m-%d}<br><b>Nowcast</b>: %{y:.2f}<extra></extra>",
        )
    )

    # INDEC published
    ip = indec.dropna(subset=["PlotDate"]).copy()
    ip["INDEC_Published"] = pd.to_numeric(ip.get("INDEC_Published", np.nan), errors="coerce")
    ip = ip[np.isfinite(ip["INDEC_Published"])].sort_values("PlotDate")
    if not ip.empty:
        fig.add_trace(
            go.Scatter(
                x=ip["PlotDate"],
                y=ip["INDEC_Published"],
                mode="lines+markers",
                name="INDEC (Published)",
                line=dict(width=1.7, color=indec_line),
                marker=dict(symbol="square", size=8, color=indec_fill, line=dict(width=1.1, color=indec_line)),
                legendrank=20,
                hovertemplate="%{x|%Y-%m-%d}<br><b>INDEC (Published)</b>: %{y:.2f}<extra></extra>",
            )
        )

    # INDEC revised
    ir = indec.dropna(subset=["PlotDate"]).copy()
    if "INDEC_Revised" in ir.columns:
        ir["INDEC_Revised"] = pd.to_numeric(ir["INDEC_Revised"], errors="coerce")
        ir = ir[np.isfinite(ir["INDEC_Revised"])].sort_values("PlotDate")
        if not ir.empty:
            fig.add_trace(
                go.Scatter(
                    x=ir["PlotDate"],
                    y=ir["INDEC_Revised"],
                    mode="markers",
                    name="INDEC (Revised)",
                    marker=dict(symbol="diamond", size=9, color="rgba(0,0,0,0)", line=dict(width=2, color=indec_line)),
                    legendrank=30,
                    hovertemplate="%{x|%Y-%m-%d}<br><b>INDEC (Revised)</b>: %{y:.2f}<extra></extra>",
                )
            )

    # REM
    rr = rem.dropna(subset=["PlotDate"]).copy()
    rr["REM"] = pd.to_numeric(rr.get("REM", np.nan), errors="coerce")
    rr = rr[np.isfinite(rr["REM"])].sort_values("PlotDate")
    if not rr.empty:
        fig.add_trace(
            go.Scatter(
                x=rr["PlotDate"],
                y=rr["REM"],
                mode="lines+markers",
                name="REM",
                line=dict(width=1.2, color=rem_gray, dash="dash"),
                marker=dict(symbol="circle", size=6, color=rem_gray, line=dict(width=1, color=rem_gray)),
                legendrank=40,
                hovertemplate="%{x|%Y-%m-%d}<br><b>REM</b>: %{y:.2f}<extra></extra>",
            )
        )

    # Ticks
    tickvals = as_py_datetimes(ticks["TickDate"]) if ("TickDate" in ticks.columns and len(ticks)) else []
    ticktext = ticks["TickLabel"].astype(str).tolist() if ("TickLabel" in ticks.columns and len(ticks)) else []

    # Professional layout
    unit = meta.get("Unit", "").strip()
    ylabel = str(meta.get("YLabel", "Value"))
    #subtitle = (f"Unit: {unit}" if unit else "").strip()

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=70, r=20, t=20, b=70),
        font=dict(family="Helvetica, Arial, sans-serif", size=14, color="black"),
        showlegend=True,  # se apaga en export (para custom legend). acá lo dejamos para debug si querés.
        xaxis=dict(
            title=None,
            range=[xmin, xmax],
            tickmode="auto",
            tickformat="%b %Y",
            nticks=20,
            tickangle=-45,
            showgrid=False,
            zeroline=False,
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikedash="solid",
            spikecolor="rgba(0,0,0,0.25)",
            spikethickness=1,
        ),
        yaxis=dict(
            title=None,
            showgrid=True,
            gridcolor="rgba(0,0,0,0.10)",
            zeroline=False,
        ),
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(0,0,0,0.15)",
            font=dict(size=13, family="Helvetica, Arial, sans-serif", color="black"),
        ),
    )

    # if subtitle:
    #     fig.add_annotation(
    #         xref="paper",
    #         yref="paper",
    #         x=0.01,
    #         y=1.06,
    #         xanchor="left",
    #         yanchor="top",
    #         text=subtitle,
    #         showarrow=False,
    #         font=dict(size=12, color="rgba(0,0,0,0.55)"),
    #     )

    # Anchor vertical line
    # fig.add_vline(
    #     x=anchor_date,
    #     line_width=1,
    #     line_dash="dot",
    #     line_color="rgba(0,0,0,0.25)",
    # )
    # fig.add_annotation(
    #     x=anchor_date,
    #     yref="paper",
    #     y=1.02,
    #     text=f"Anchor: {anchor_date.strftime('%Y-%m-%d')}",
    #     showarrow=False,
    #     font=dict(size=11, color="rgba(0,0,0,0.55)"),
    #     xanchor="left",
    #     yanchor="bottom",
    #     bgcolor="rgba(255,255,255,0.6)",
    #     bordercolor="rgba(0,0,0,0.10)",
    #     borderwidth=1,
    #     borderpad=3,
    # )

    # Tip (lo movemos a panel custom también, pero lo dejamos como guía visual)
    # fig.add_annotation(
    #     xref="paper",
    #     yref="paper",
    #     x=0.01,
    #     y=0.99,
    #     xanchor="left",
    #     yanchor="top",
    #     text="Tip: usá el panel de series (checkbox) para mostrar u ocultar. Doble click para aislar.",
    #     showarrow=False,
    #     font=dict(size=12, color="rgba(0,0,0,0.55)"),
    #     bgcolor="rgba(255,255,255,0.65)",
    #     bordercolor="rgba(0,0,0,0.10)",
    #     borderwidth=1,
    #     borderpad=4,
    # )

    fig.update_xaxes(showline=False)
    fig.update_yaxes(showline=False)

    return fig


# -----------------------------
# Build custom legend items (Python side)
# -----------------------------
def build_legend_items(fig: go.Figure) -> list:
    band_names = {"50%", "60%", "70%", "80%"}
    items = []

    for idx, tr in enumerate(fig.data):
        # showlegend default True if None
        show = True if getattr(tr, "showlegend", None) is None else bool(getattr(tr, "showlegend"))
        name = getattr(tr, "name", None)
        if (not show) or (not name):
            continue

        name = str(name)
        group = "Confidence bands" if name in band_names else "Series"

        # swatch color
        color = None
        if getattr(tr, "fillcolor", None):
            color = tr.fillcolor
        elif getattr(getattr(tr, "line", None), "color", None):
            color = tr.line.color
        elif getattr(getattr(tr, "marker", None), "color", None):
            color = tr.marker.color
        elif getattr(getattr(getattr(tr, "marker", None), "line", None), "color", None):
            color = tr.marker.line.color
        else:
            color = "rgba(120,120,120,1)"

        rank = getattr(tr, "legendrank", None)
        if rank is None:
            rank = 1000 + idx

        items.append(
            {
                "i": int(idx),
                "name": name,
                "group": group,
                "color": str(color),
                "rank": float(rank),
            }
        )

    # Order: group first, then rank, then name
    group_order = {"Series": 0, "Confidence bands": 1}
    items.sort(key=lambda d: (group_order.get(d["group"], 9), d["rank"], d["name"]))
    return items


# -----------------------------
# JS post_script (checkbox legend)
# -----------------------------
def make_post_script(items: list) -> str:
    items_json = json.dumps(items, ensure_ascii=False)

    post_script = r"""
(function(){
  var gd = document.getElementById('{plot_id}');
  if(!gd) return;

  var ITEMS = __ITEMS_JSON__;
  var doc = gd.ownerDocument;

  function safeKey(s){ return String(s).replace(/[^a-z0-9_-]/gi,'_'); }

  function el(tag, attrs, html){
    var x = doc.createElement(tag);
    if(attrs){
      Object.keys(attrs).forEach(function(k){
        if(k === 'style') x.setAttribute('style', attrs[k]);
        else x.setAttribute(k, attrs[k]);
      });
    }
    if(html !== undefined) x.innerHTML = html;
    return x;
  }

  function isVisible(idx){
    var v = gd.data[idx].visible;
    return (v === undefined || v === true);
  }

  function setVisible(idx, on){
    var newVis = on ? true : 'legendonly';
    return Plotly.restyle(gd, {visible: newVis}, [idx]);
  }

  function setMany(indices, on){
    if(!indices.length) return Promise.resolve();
    var upd = {visible: []};
    indices.forEach(function(_){ upd.visible.push(on ? true : 'legendonly'); });
    return Plotly.restyle(gd, upd, indices);
  }

  // Aislar / restaurar (trace o grupo)
  var isolateState = {active:false, saved:null, key:null};

  function snapshotVisible(){
    return gd.data.map(function(t){
      return (t.visible === undefined) ? true : t.visible;
    });
  }

  function restoreVisible(saved){
    var indices = [];
    var update = {visible: []};
    for(var k=0; k<gd.data.length; k++){
      indices.push(k);
      update.visible.push(saved[k]);
    }
    return Plotly.restyle(gd, update, indices);
  }

  function isolate(indices, key){
    if(isolateState.active && isolateState.key === key){
      var saved = isolateState.saved;
      isolateState.active = false;
      isolateState.saved = null;
      isolateState.key = null;
      return restoreVisible(saved);
    }

    isolateState.active = true;
    isolateState.saved = snapshotVisible();
    isolateState.key = key;

    var all = [];
    var upd = {visible: []};
    for(var j=0; j<gd.data.length; j++){
      all.push(j);
      upd.visible.push(indices.indexOf(j) >= 0 ? true : 'legendonly');
    }
    return Plotly.restyle(gd, upd, all);
  }

  // Insertar panel DENTRO del gráfico (overlay)
  // aseguramos que el contenedor sea "position: relative"
  if(!gd.style.position || gd.style.position === 'static'){
    gd.style.position = 'relative';
  }

  // CSS compacto + overlay + scroll interno
  if(!doc.getElementById('cb-legend-style')){
    var st = el('style', {id:'cb-legend-style'});
    st.textContent = `
      .cb-panel{
        position: absolute;
        top: 10px;
        left: 443px;
        z-index: 50;
        width: 230px;
        max-width: calc(100% - 20px);
        background: rgba(255,255,255,0.90);
        border: 1px solid rgba(0,0,0,0.14);
        box-shadow: 0 8px 20px rgba(0,0,0,0.10);
        border-radius: 12px;
        padding: 8px;
        font-family: Helvetica, Arial, sans-serif;
        color: #111;
        user-select: none;
      }
      .cb-grip{font-size:18px;color:#aaa;cursor:move;padding:0 4px;flex-shrink:0;line-height:1;user-select:none;}
      .cb-header{
        display:flex;
        align-items:center;
        gap:6px;
        margin-bottom: 0;
        cursor: move;
      }
      .cb-editbtn{
        font-size: 12px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,0.14);
        background: rgba(255,255,255,0.85);
        cursor: pointer;
        flex: 1;
      }
      .cb-editbtn:hover{ background: rgba(255,255,255,1); }
      .cb-body{ margin-top: 8px; }
      .cb-actions{
        display:flex;
        gap:6px;
        flex-wrap: wrap;
        margin: 6px 0 8px 0;
      }
      .cb-btn{
        font-size: 10px;
        padding: 5px 7px;
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,0.12);
        background: rgba(255,255,255,0.85);
        cursor:pointer;
      }
      .cb-btn:hover{
        background: rgba(255,255,255,1);
        border-color: rgba(0,0,0,0.18);
      }
      .cb-search{
        width: 100%;
        box-sizing: border-box;
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,0.12);
        padding: 6px 8px;
        font-size: 11px;
        outline: none;
        background: rgba(255,255,255,0.90);
      }
      .cb-groups{
        margin-top: 8px;
        display:flex;
        flex-direction: column;
        gap: 8px;
        max-height: 170px;      /* <<< scroll dentro del panel */
        overflow: auto;
        padding-right: 4px;
      }
      .cb-group{
        display:flex;
        flex-direction: column;
        gap: 5px;
      }
      .cb-group-head{
        display:flex;
        align-items:center;
        justify-content: space-between;
        gap: 8px;
        padding: 6px 8px;
        border-radius: 12px;
        border: 1px solid rgba(0,0,0,0.08);
        background: rgba(0,0,0,0.03);
        cursor:pointer;
      }
      .cb-group-name{
        font-size: 11px;
        font-weight: 700;
      }
      .cb-item{
        display:flex;
        align-items:center;
        gap: 8px;
        padding: 6px 8px;
        border-radius: 12px;
        cursor: pointer;
        border: 1px solid rgba(0,0,0,0.06);
        background: rgba(255,255,255,0.60);
      }
      .cb-item:hover{
        background: rgba(255,255,255,0.95);
        border-color: rgba(0,0,0,0.10);
      }
      .cb-item.off{
        opacity: 0.55;
      }
      .cb-box{
        width: 15px;
        height: 15px;
        border-radius: 5px;
        border: 1px solid rgba(0,0,0,0.35);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        line-height: 1;
        color: white;
        background: transparent;
        flex: 0 0 auto;
      }
      .cb-box.on{
        background: rgba(16,185,129,0.95);
        border-color: rgba(16,185,129,1);
      }
      .cb-box.mix{
        background: rgba(59,130,246,0.95);
        border-color: rgba(59,130,246,1);
      }
      .cb-swatch{
        width: 11px;
        height: 11px;
        border-radius: 4px;
        border: 1px solid rgba(0,0,0,0.15);
        flex: 0 0 auto;
      }
      .cb-label{
        font-size: 12px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    `;
    doc.head.appendChild(st);
  }

  // Remove previous panel if any
  var prev = doc.getElementById('cb-panel');
  if(prev) prev.remove();

  // Panel DOM
  var panel = el('div', {id:'cb-panel', class:'cb-panel'});

  // Header (drag handle) con botón Editar
  var header = el('div', {class:'cb-header'});
  var grip = el('span', {class:'cb-grip'}, '⠿');
  var editBtn = el('button', {class:'cb-editbtn', type:'button'}, 'Editar Indicadores');
  header.appendChild(grip);
  editBtn.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
  editBtn.addEventListener('click', function(){
    var body = panel.querySelector('.cb-body');
    body.style.display = body.style.display === 'none' ? '' : 'none';
  });
  header.appendChild(editBtn);
  panel.appendChild(header);

  // Cuerpo colapsable (empieza oculto)
  var body = el('div', {class:'cb-body', style:'display:none;'});

  var search = el('input', {class:'cb-search', type:'text', placeholder:'Buscar...'});
  body.appendChild(search);

  var actions = el('div', {class:'cb-actions'});
  var btnAllOn = el('button', {class:'cb-btn', type:'button'}, 'All on');
  var btnAllOff = el('button', {class:'cb-btn', type:'button'}, 'All off');
  var btnOnlyNow = el('button', {class:'cb-btn', type:'button'}, 'Only now');
  actions.appendChild(btnAllOn);
  actions.appendChild(btnAllOff);
  actions.appendChild(btnOnlyNow);
  body.appendChild(actions);

  var groupsBox = el('div', {class:'cb-groups'});
  body.appendChild(groupsBox);

  panel.appendChild(body);

  // Append INSIDE the plot div (overlay within chart)
  gd.appendChild(panel);

  // ---- Date picker overlay (same height as Edit panel, to its right) ----
  var dpDiv = el('div', {style:
    'position:absolute; top:10px; left:78px; display:flex; align-items:center; ' +
    'background:rgba(255,255,255,0.88); border-radius:6px; padding:4px 8px; z-index:10; ' +
    'font-family:Helvetica,Arial,sans-serif;'});
  var fromSpan = el('span', {style:'font-size:13px; color:#555; margin-right:4px;'}, 'From:');
  var fromInput = el('input', {type:'date',
    style:'font-size:13px; border:1px solid rgba(0,0,0,0.15); border-radius:4px; padding:2px 4px;'});
  var toSpan = el('span', {style:'font-size:13px; color:#555; margin:0 4px 0 10px;'}, 'To:');
  var toInput = el('input', {type:'date',
    style:'font-size:13px; border:1px solid rgba(0,0,0,0.15); border-radius:4px; padding:2px 4px;'});
  dpDiv.appendChild(fromSpan);
  dpDiv.appendChild(fromInput);
  dpDiv.appendChild(toSpan);
  dpDiv.appendChild(toInput);
  gd.appendChild(dpDiv);

  var initRange = ((gd.layout || {}).xaxis || {}).range || [];
  var xDataMin = initRange[0] ? String(initRange[0]).split('T')[0] : null;
  var xDataMax = initRange[1] ? String(initRange[1]).split('T')[0] : null;

  function applyDateRange(){
    var from = fromInput.value;
    var to = toInput.value;
    Plotly.relayout(gd, {
      'xaxis.range[0]': from || xDataMin,
      'xaxis.range[1]': to || xDataMax,
    });
  }

  fromInput.addEventListener('change', applyDateRange);
  toInput.addEventListener('change', applyDateRange);

  // Group map
  var groups = {};
  ITEMS.forEach(function(it){
    if(!groups[it.group]) groups[it.group] = [];
    groups[it.group].push(it);
  });

  var groupNames = Object.keys(groups);
  groupNames.sort(function(a,b){
    var o = {'Series':0,'Confidence bands':1};
    return (o[a]||9) - (o[b]||9);
  });

  function setBoxState(boxEl, state){
    boxEl.classList.remove('on');
    boxEl.classList.remove('mix');
    boxEl.textContent = '';
    if(state === 'on'){
      boxEl.classList.add('on');
      boxEl.textContent = '✓';
    } else if(state === 'mix'){
      boxEl.classList.add('mix');
      boxEl.textContent = '−';
    }
  }

  function rowState(rowEl, on){
    var box = rowEl.querySelector('.cb-box');
    if(on){
      setBoxState(box, 'on');
      rowEl.classList.remove('off');
    } else {
      setBoxState(box, 'off');
      rowEl.classList.add('off');
    }
  }

  function groupState(groupItems){
    var onCount = 0;
    groupItems.forEach(function(it){
      if(isVisible(it.i)) onCount += 1;
    });
    if(onCount === 0) return 'off';
    if(onCount === groupItems.length) return 'on';
    return 'mix';
  }

  function syncAll(){
    // rows
    ITEMS.forEach(function(it){
      var row = doc.getElementById('cb-item-' + it.i);
      if(!row) return;
      rowState(row, isVisible(it.i));
    });
    // groups
    groupNames.forEach(function(g){
      var gkey = safeKey(g);
      var headBox = doc.getElementById('cb-group-box-' + gkey);
      if(!headBox) return;
      setBoxState(headBox, groupState(groups[g]));
    });
  }

  function applyFilter(){
    var q = (search.value || '').trim().toLowerCase();
    groupNames.forEach(function(g){
      var gkey = safeKey(g);
      var anyShown = false;
      groups[g].forEach(function(it){
        var row = doc.getElementById('cb-item-' + it.i);
        if(!row) return;
        var ok = (!q) || (it.name.toLowerCase().indexOf(q) >= 0);
        row.style.display = ok ? '' : 'none';
        if(ok) anyShown = true;
      });
      var gWrap = doc.getElementById('cb-group-wrap-' + gkey);
      if(gWrap) gWrap.style.display = anyShown ? '' : 'none';
    });
  }

  // Build UI per group
  groupNames.forEach(function(g){
    var gkey = safeKey(g);
    var wrap = el('div', {class:'cb-group', id:'cb-group-wrap-' + gkey});

    var head = el('div', {class:'cb-group-head'});
    var left = el('div', {style:'display:flex; align-items:center; gap:8px;'});
    var gbox = el('span', {class:'cb-box', id:'cb-group-box-' + gkey});
    var gname = el('span', {class:'cb-group-name'}, g);
    left.appendChild(gbox);
    left.appendChild(gname);
    head.appendChild(left);
    head.appendChild(el('div', {style:'font-size:10px; color: rgba(0,0,0,0.50);'}, 'group'));
    wrap.appendChild(head);

    groups[g].forEach(function(it){
      var row = el('div', {class:'cb-item', id:'cb-item-' + it.i});
      var box = el('span', {class:'cb-box'});
      var swatch = el('span', {class:'cb-swatch', style:'background:' + (it.color||'rgba(120,120,120,1)') + ';'});
      var label = el('span', {class:'cb-label'});
      label.textContent = it.name;

      row.appendChild(box);
      row.appendChild(swatch);
      row.appendChild(label);

      // click vs dblclick
      var timer = null;
      row.addEventListener('click', function(){
        if(timer) return;
        timer = setTimeout(function(){
          var on = isVisible(it.i);
          setVisible(it.i, !on).then(syncAll);
          timer = null;
        }, 220);
      });
      row.addEventListener('dblclick', function(){
        if(timer){ clearTimeout(timer); timer = null; }
        isolate([it.i], 'trace:' + it.i).then(syncAll);
      });

      wrap.appendChild(row);
    });

    // group click vs dblclick
    var gTimer = null;
    head.addEventListener('click', function(){
      if(gTimer) return;
      gTimer = setTimeout(function(){
        var st = groupState(groups[g]);
        var indices = groups[g].map(function(it){ return it.i; });
        var turnOn = (st === 'off' || st === 'mix');
        setMany(indices, turnOn).then(syncAll);
        gTimer = null;
      }, 220);
    });
    head.addEventListener('dblclick', function(){
      if(gTimer){ clearTimeout(gTimer); gTimer = null; }
      var indices = groups[g].map(function(it){ return it.i; });
      isolate(indices, 'group:' + gkey).then(syncAll);
    });

    groupsBox.appendChild(wrap);
  });

  // Actions
  btnAllOn.addEventListener('click', function(){
    var idx = ITEMS.map(function(it){ return it.i; });
    setMany(idx, true).then(syncAll);
  });
  btnAllOff.addEventListener('click', function(){
    var idx = ITEMS.map(function(it){ return it.i; });
    setMany(idx, false).then(syncAll);
  });
  btnOnlyNow.addEventListener('click', function(){
    var now = ITEMS.filter(function(it){ return it.name.toLowerCase() === 'nowcast'; }).map(function(it){ return it.i; });
    var keep = {};
    now.forEach(function(i){ keep[i] = true; });

    var all = [];
    var upd = {visible: []};
    for(var k=0; k<gd.data.length; k++){
      all.push(k);
      upd.visible.push(keep[k] ? true : 'legendonly');
    }
    Plotly.restyle(gd, upd, all).then(syncAll);
  });

  // Search
  search.addEventListener('input', function(){ applyFilter(); });

  // Initial
  syncAll();
  applyFilter();

  // Keep in sync if plot changes
  if(gd.on){
    gd.on('plotly_restyle', function(){ syncAll(); });
    gd.on('plotly_redraw', function(){ syncAll(); });
  }

  // -----------------------------
  // DRAG dentro del gráfico (bounded)
  // -----------------------------
  function clampPos(left, top){
    var rectG = gd.getBoundingClientRect();
    var rectP = panel.getBoundingClientRect();
    var pad = 6;

    var maxLeft = rectG.width - rectP.width - pad;
    var maxTop  = rectG.height - rectP.height - pad;

    var L = Math.max(pad, Math.min(left, maxLeft));
    var T = Math.max(pad, Math.min(top,  maxTop));
    return {L:L, T:T};
  }

  var dragging = false;
  var offX = 0, offY = 0;

  header.addEventListener('pointerdown', function(e){
    // para que el drag no seleccione texto
    e.preventDefault();
    dragging = true;

    // Pasar a posicionamiento por left/top
    var rectG = gd.getBoundingClientRect();
    var rectP = panel.getBoundingClientRect();
    var curLeft = rectP.left - rectG.left;
    var curTop  = rectP.top  - rectG.top;

    panel.style.right = 'auto';
    panel.style.bottom = 'auto';
    panel.style.left = curLeft + 'px';
    panel.style.top  = curTop  + 'px';

    offX = e.clientX - rectP.left;
    offY = e.clientY - rectP.top;

    header.setPointerCapture(e.pointerId);
  });

  header.addEventListener('pointermove', function(e){
    if(!dragging) return;
    var rectG = gd.getBoundingClientRect();
    var left = (e.clientX - rectG.left) - offX;
    var top  = (e.clientY - rectG.top)  - offY;
    var c = clampPos(left, top);
    panel.style.left = c.L + 'px';
    panel.style.top  = c.T + 'px';
  });

  header.addEventListener('pointerup', function(e){
    dragging = false;
    try{ header.releasePointerCapture(e.pointerId); } catch(_){}
  });

})();
""".replace("__ITEMS_JSON__", items_json)

    return post_script


# -----------------------------
# CLI
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path al Excel exportado (nowcast_estimations_base_with_bands.xlsx)")
    ap.add_argument("--output", required=True, help="Path del HTML de salida (ej: nowcast_history.html)")
    ap.add_argument(
        "--include-js",
        choices=["inline", "cdn"],
        default="inline",
        help="inline: HTML autocontenido; cdn: más liviano pero requiere internet. Default inline.",
    )
    args = ap.parse_args()

    xlsx_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bundle = read_nowcast_excel(xlsx_path)
    fig = build_nowcast_figure(bundle)

    # Config Plotly
    config = {
        "displaylogo": False,
        "responsive": True,
        "modeBarButtonsToRemove": ["select2d", "lasso2d"],
    }

    # Apagar la leyenda nativa (usamos panel custom)
    fig.update_layout(showlegend=False)

    # Panel custom
    items = build_legend_items(fig)
    post_script = make_post_script(items)

    # Export HTML con post_script
    pio.write_html(
        fig,
        str(out_path),
        full_html=True,
        include_plotlyjs=args.include_js,
        config=config,
        post_script=post_script,
    )

    print(f"[OK] HTML generado: {out_path.resolve()}")
    print(f"     Sheets detectados: {sorted(list(bundle['sheets']))}")


import sys

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv += [
            "--input", "nowcast_estimations_base_with_bands.xlsx",
            "--output", "nowcast_history.html",
        ]
    main()