#!/usr/bin/env python3
"""
Genera nowcast_history.html a partir del Excel y lo sirve con http.server.
Puerto: 8060
"""
import os
import shutil
import threading
import http.server
from pathlib import Path

# Importar el generador de HTML (mismo directorio)
import sys
sys.path.insert(0, str(Path(__file__).parent))
from make_nowcast_history_html import read_nowcast_excel, build_nowcast_figure, build_legend_items, make_post_script

import plotly.io as pio

PORT = 8060
DATA_DIR = Path(__file__).parent / "data"
XLSX = DATA_DIR / "nowcast_estimations_base_with_bands.xlsx"
HTML_OUT = DATA_DIR / "nowcast_history.html"


def generate_html():
    print(f"[nowcast] Generando HTML desde {XLSX} ...")
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

    # Evita doble scroll en iframe: body llena el alto disponible sin overflow.
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
    print(f"[nowcast] HTML generado: {HTML_OUT}")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DATA_DIR), **kwargs)

    def do_GET(self):
        # 1. Obtener el prefijo (ej: /prod/nowcast/)
        url_prefix = os.getenv('URL_PREFIX', '').rstrip('/')
        
        # 2. Limpiar la ruta de entrada
        # Si recibimos /prod/nowcast/ o /prod/nowcast/index.html, removemos el prefijo
        if url_prefix and self.path.startswith(url_prefix):
            self.path = self.path[len(url_prefix):]
        
        # 3. Asegurar que si la ruta queda vacía o es /, apunte al HTML generado
        if self.path == "" or self.path == "/":
            self.path = "/nowcast_history.html"

        print(f"[debug] Sirviendo path final: {self.path}")
        
        # 4. Llamar al método original con la ruta ya limpia
        super().do_GET()

    def log_message(self, format, *args):
        print(f"[http] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    generate_html()

    print(f"[nowcast] Servidor en http://0.0.0.0:{PORT}")
    with http.server.HTTPServer(("0.0.0.0", PORT), Handler) as httpd:
        httpd.serve_forever()
