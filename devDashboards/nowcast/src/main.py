#!/usr/bin/env python3
"""
Genera nowcast_history_{lang}.html a partir del Excel y lo sirve con http.server.
Compatible con subrutas de Nginx y detección de idioma.
"""
import os
import http.server
from pathlib import Path
import sys

# -------------------------
# PATH SETUP (shared)
# -------------------------
sys.path.append("/shared")

# Importar el generador de HTML (mismo directorio)
sys.path.insert(0, str(Path(__file__).parent))

from make_nowcast_history_html import (
    read_nowcast_excel,
    build_nowcast_figure,
    build_legend_items,
    make_post_script
)

raw_lang = os.environ.get("LANG", "EN").upper()

from make_nowcast_history_html import t

if raw_lang.startswith("ES"):
    APP_LANG = "ES"
else:
    APP_LANG = "EN"
from make_nowcast_history_html import t

import plotly.io as pio

PORT = 8060
DATA_DIR = Path(__file__).parent / "data"
XLSX = DATA_DIR / "nowcast_estimations_base_with_bands.xlsx"

ENV = os.environ.get("ENV", "PROD").upper()

# Nombre del archivo dinámico
FILE_NAME = f"nowcast_history_{APP_LANG.lower()}.html"
HTML_OUT = DATA_DIR / FILE_NAME

# ============================================================
# 📊 GENERACIÓN DEL HTML
# ============================================================
def generate_html():
    print(f"[nowcast] CONFIG: LANG={APP_LANG} | ENV={ENV}")
    print(f"[nowcast] Generando HTML en: {HTML_OUT}")

    if not XLSX.exists():
        print(f"[error] No se encuentra el archivo Excel en {XLSX}")
        return

    bundle = read_nowcast_excel(XLSX)
    fig = build_nowcast_figure(bundle)

    config = {
        "displaylogo": False,
        "responsive": True,
        "modeBarButtonsToRemove": ["select2d", "lasso2d"],
    }

    fig.update_layout(showlegend=False)

    items = build_legend_items(fig)
    post_script = make_post_script(items)

    iframe_css = (
        "(function(){"
        "var s=document.createElement('style');"
        "s.textContent='html,body{height:100%;margin:0;overflow:hidden;}';"
        "document.head.appendChild(s);"
        "})();\n"
    )

    post_script = iframe_css + post_script

    inner_html = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs="inline",
        config=config,
        post_script=post_script,
    )
    outer_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Nowcast</title>

        <style>
            html, body {{
                margin: 0;
                height: 100%;
                overflow: hidden;
                font-family: Arial, sans-serif;
            }}

            #app-shell {{
                display: flex;
                flex-direction: column;
                height: 100%;
            }}

            #header {{
                height: 48px;
                background: #111;
                color: white;
                display: flex;
                align-items: center;
                padding: 0 16px;
                font-size: 14px;
                gap: 20px;
            }}

            #header-left {{
                font-weight: 600;
                white-space: nowrap;
            }}

            #header-controls {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-left: auto;
            }}

            #filter-panel {{
                display: none;
                background: white;
                border-bottom: 1px solid rgba(0,0,0,0.1);
                padding: 8px 12px;
            }}

            #filter-panel.open {{
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
            }}

            #filter-btn {{
                background: #333;
                color: white;
                border: none;
                padding: 6px 10px;
                border-radius: 4px;
                cursor: pointer;
            }}

            #filter-btn:hover {{
                background: #555;
            }}

            #content {{
                flex: 1;
                position: relative;
                display: flex;
                flex-direction: column;
                min-height: 0;
            }}

            #content > div {{
                flex: 1;
                min-height: 0;
            }}
        </style>
    </head>

    <body>

    <div id="app-shell">
        <div id="header">
            <div id="header-left">
                Nowcast ({APP_LANG})
            </div>

            <div id="header-controls">
                <button id="filter-btn">Filters</button>
            </div>
        </div>

        <div id="filter-panel"></div>
        
        <div id="content">
            {inner_html}
        </div>
    </div>

    </body>
    </html>
    """
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(outer_html)
    print(f"[nowcast] HTML generado exitosamente.")


# ============================================================
# 🌐 SERVIDOR HTTP
# ============================================================
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DATA_DIR), **kwargs)

    def do_GET(self):
        url_prefix = os.getenv('URL_PREFIX', '').rstrip('/')

        path_clean = self.path
        if url_prefix and path_clean.startswith(url_prefix):
            path_clean = path_clean[len(url_prefix):]

        # 🔥 FORCE correct file always (based on container LANG)
        self.path = f"/nowcast_history_{APP_LANG.lower()}.html"

        print(f"[http] Lang: {APP_LANG} | Serving: {self.path}")
        super().do_GET()

    def log_message(self, format, *args):
        pass


# ============================================================
# 🚀 RUN
# ============================================================
if __name__ == "__main__":
    generate_html()

    print(f"[nowcast] Servidor iniciado en http://0.0.0.0:{PORT}")
    with http.server.HTTPServer(("0.0.0.0", PORT), Handler) as httpd:
        httpd.serve_forever()