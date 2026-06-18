"""
Servidor estático mínimo para servir el explorador AMBA por HTTP.

Pensado para usar con ngrok:
    1) python build.py
    2) python serve.py          (default port 8000)
    3) ngrok http 8000          (en otra terminal)

Acepta --port y --host. No requiere dependencias externas.
"""

from __future__ import annotations

import argparse
import http.server
import socketserver
from functools import partial
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000, help="Puerto HTTP (default 8000).")
    parser.add_argument("--host", default="0.0.0.0", help="Host bind (default 0.0.0.0).")
    parser.add_argument(
        "--directory",
        default=str(Path(__file__).resolve().parent),
        help="Directorio raíz a servir (default: carpeta del script).",
    )
    args = parser.parse_args()

    handler = partial(http.server.SimpleHTTPRequestHandler, directory=args.directory)

    # Permite reusar el puerto inmediatamente después de Ctrl+C.
    class Reusable(socketserver.TCPServer):
        allow_reuse_address = True

    with Reusable((args.host, args.port), handler) as httpd:
        print(f"Sirviendo {args.directory} en http://{args.host}:{args.port}")
        print("Abrí http://localhost:{0}/amba_explorer.html en el navegador.".format(args.port))
        print("Para exponer por ngrok:  ngrok http {0}".format(args.port))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")


if __name__ == "__main__":
    main()
