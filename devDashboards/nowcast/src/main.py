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

    pio.write_html(
        fig,
        str(HTML_OUT),
        full_html=True,
        include_plotlyjs="inline",
        config=config,
        post_script=post_script,
    )
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