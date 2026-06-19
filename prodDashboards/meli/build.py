"""Build self-contained HTML for the AMBA Explorer dashboard.

Reads the latest snapshot of Ventas/Alquileres CSVs at three geographic
levels (Agrupacion, CABA-barrio, GBA-municipio) via the existing
`amba_dashboard` package and produces a single HTML file with all data,
styles and scripts inlined. Output is ready to be served by any static
HTTP server (e.g. for ngrok).

Usage:
    python build.py                       # ES → amba_explorer.html
    python build.py --lang en             # EN → amba_explorer_en.html
    python build.py --lang es --output X  # explicit output path

Contrato con el pipeline R upstream
-----------------------------------
Las bases de los índices que aparecen como label en la UI
(`Oferta: base 2018 = 1`, `Demanda: base 2019 = 1`) VIENEN
CALCULADAS desde los CSVs del pipeline R. Este build NO recalcula bases:
solo pasa los valores crudos al front y declara el label que el dashboard
muestra. Si el Centro cambia las bases upstream, hay que actualizar las
strings en `lib/amba_dashboard/i18n.py` (claves `saleMetrics.demanda.*`,
`saleMetrics.oferta.*`, `rentMetrics.demanda.*`, `rentMetrics.oferta.*`)
Y este comentario. Verificado contra los CSVs del snapshot 202604 y
202605: la base es uniforme por inmueble y por geografía (no depende de
Casa vs Departamento ni de aglomerado vs barrio vs municipio).
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

# El paquete auxiliar `amba_dashboard` esta en lib/ — autocontenido.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))

from amba_dashboard.data_store import DatasetBundle  # noqa: E402
from amba_dashboard.utils import safe_float  # noqa: E402
from amba_dashboard.catalogs import (  # noqa: E402
    COLORS,
    INMUEBLES,
    LEVELS,
    REGIONS_BY_LEVEL,
)
from amba_dashboard.metrics import (  # noqa: E402
    build_rent_metric_info,
    build_sale_metric_info,
)
from amba_dashboard.i18n import get_lang  # noqa: E402


# ---------------------------------------------------------------------------
# Carga y armado de series
# ---------------------------------------------------------------------------

_warned_missing_columns: set[tuple[str, str]] = set()


def _snapshot_month_label(snapshot_id: str) -> str:
    """'202603' → '2026-03' (formato del campo Mes en los CSVs)."""
    return f"{snapshot_id[:4]}-{snapshot_id[4:6]}"


def _warn_missing(table: str, field: str) -> None:
    """Avisa a stderr UNA sola vez por (tabla, columna) faltante.

    Si el pipeline R cambia el nombre de una columna sin avisar, hoy el
    dashboard mostraría la serie vacía silenciosamente. Esto convierte
    ese fallo silencioso en un warning visible en consola.
    """
    key = (table, field)
    if key in _warned_missing_columns:
        return
    _warned_missing_columns.add(key)
    print(
        f"[WARN] columna '{field}' no encontrada en la tabla '{table}'. "
        f"La serie correspondiente quedará vacía en el dashboard.",
        file=sys.stderr,
    )


def _series_for(
    bundle: DatasetBundle,
    table: str,
    region: str,
    inmueble: str,
    field: str,
    *,
    skip_month: str | None = None,
    skip_zero: bool = False,
) -> list[dict]:
    """Lee una serie del bundle aplicando filtros de calidad del Centro.

    - `skip_month`: si está seteado, omite la fila cuyo `Mes` coincide. Se
      usa para Demanda y Oferta: el último mes del snapshot está incompleto
      (contactos siguen entrando, publicaciones siguen abriéndose). Es la
      misma regla del pipeline R (`Graficos_AMBA.R`, `data$mes <= end_month`).
    - `skip_zero`: si True, omite valores == 0. Aplica a Contactos, cuya
      serie inicial (2018-01) puede valer 0 por inicialización.
    - Si `field` no existe en ninguna fila de la serie, emite warning a
      stderr UNA vez por (tabla, columna).
    """
    rows = bundle.get_series(table, region, inmueble)
    if not rows:
        return []
    if field not in rows[0]:
        _warn_missing(table, field)
        return []
    points: list[dict] = []
    for row in rows:
        mes = str(row["Mes"])
        if skip_month is not None and mes == skip_month:
            continue
        value = safe_float(row.get(field))
        if value is None:
            continue
        if skip_zero and value == 0:
            continue
        points.append({"x": mes, "y": value})
    return points


def _populate_precio(bundle, table, regions, inmueble, fields) -> dict:
    """Empaqueta precio bajo {universo: {region: series}}.

    Precio NO excluye el último mes (la mediana del stock activo ya es
    final una vez cerrado el mes).
    """
    out: dict = {}
    if "precio_stock" in fields:
        stock_field = fields["precio_stock"]
        stock_data = {}
        for region in regions:
            points = _series_for(bundle, table, region, inmueble, stock_field)
            if points:
                stock_data[region] = points
        if stock_data:
            out["stock"] = stock_data
    if "precio_flujo" in fields:
        flujo_field = fields["precio_flujo"]
        flujo_data = {}
        for region in regions:
            points = _series_for(bundle, table, region, inmueble, flujo_field)
            if points:
                flujo_data[region] = points
        if flujo_data:
            out["flujo"] = flujo_data
    return out


def _populate_flat(
    bundle, table, regions, inmueble, field, *, skip_month=None, skip_zero=False
) -> dict:
    """Empaqueta demanda/oferta como {region: series}.

    Acepta filtros de calidad (último mes incompleto + valores cero).
    """
    out: dict = {}
    for region in regions:
        points = _series_for(
            bundle, table, region, inmueble, field,
            skip_month=skip_month, skip_zero=skip_zero,
        )
        if points:
            out[region] = points
    return out


def _populate_side(bundle: DatasetBundle, level_spec: dict, side: str) -> dict:
    """Devuelve {inmueble: {precio: {...}, demanda: {...}, oferta: {...}}}."""
    table = level_spec[f"{side}_table"]
    regions = level_spec["regions"]
    fields = level_spec[side]

    # Regla del Centro (ver Graficos_AMBA.R + Indices_AMBA.Rmd):
    # Demanda y Oferta del último mes del snapshot son parciales. Se
    # excluyen del gráfico. Precio NO se filtra (el stock cerró).
    last_mes = _snapshot_month_label(bundle.snapshot_id)

    out: dict = {}
    for inmueble in INMUEBLES:
        per_inmueble: dict = {}
        if side == "rent":
            # Alquiler: un solo campo de precio ("corrientes"), expuesto como
            # universo virtual "stock" para que el front no requiera ramas.
            corrientes_field = fields["precio_corrientes"]
            data = {}
            for region in regions:
                points = _series_for(bundle, table, region, inmueble, corrientes_field)
                if points:
                    data[region] = points
            per_inmueble["precio"] = {"stock": data} if data else {}
        else:
            # Venta: stock y (cuando aplica) flujo.
            per_inmueble["precio"] = _populate_precio(
                bundle, table, regions, inmueble, fields
            )
        # Demanda: excluye último mes + valores cero (índice mal inicializado
        # en los primeros meses de 2018 vale 0 → genera división por cero
        # en modo "índice base 100" e induce a error en nivel).
        per_inmueble["demanda"] = _populate_flat(
            bundle, table, regions, inmueble, fields["demanda"],
            skip_month=last_mes, skip_zero=True,
        )
        # Oferta: excluye último mes. No filtra por cero (Oferta no llega a 0).
        per_inmueble["oferta"] = _populate_flat(
            bundle, table, regions, inmueble, fields["oferta"],
            skip_month=last_mes,
        )
        out[inmueble] = per_inmueble
    return out


def build_data(bundle: DatasetBundle) -> dict:
    """Build the nested data structure consumed by the front-end.

    Shape:
        data["sale" | "rent"][level][inmueble]["precio"][universo][region] = [{x,y}, ...]
        data["sale" | "rent"][level][inmueble]["demanda" | "oferta"][region] = [{x,y}, ...]

    `universo` para alquiler siempre es "stock" (no hay flujo).
    `universo` para venta CABA siempre es "stock" (no hay flujo a nivel barrio).
    `universo` para venta aglomerado/municipio puede ser "stock" o "flujo".
    """
    data: dict = {"sale": {}, "rent": {}}
    for level_name, level_spec in LEVELS.items():
        data["sale"][level_name] = _populate_side(bundle, level_spec, "sale")
        data["rent"][level_name] = _populate_side(bundle, level_spec, "rent")
    return data


def _logo_data_uri(path: Path) -> str | None:
    if not path.exists():
        return None
    raw = path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    suffix = path.suffix.lower().lstrip(".")
    mime = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "svg": "image/svg+xml",
    }.get(suffix, "application/octet-stream")
    return f"data:{mime};base64,{encoded}"


def build_html(bundle: DatasetBundle, source_dir: Path, lang_code: str) -> str:
    template = (source_dir / "template.html").read_text(encoding="utf-8")
    css = (source_dir / "explorer.css").read_text(encoding="utf-8")
    js = (source_dir / "explorer.js").read_text(encoding="utf-8")

    lang = get_lang(lang_code)

    branding_dir = HERE / "lib" / "amba_dashboard" / "assets" / "branding"
    logos = {
        "udesa": _logo_data_uri(branding_dir / "udesa-logo.jpg"),
        "meli": _logo_data_uri(branding_dir / "mercado-libre-logo.webp"),
    }

    bootstrap = {
        "data": build_data(bundle),
        "saleMetrics": build_sale_metric_info(lang),
        "rentMetrics": build_rent_metric_info(lang),
        "regions": REGIONS_BY_LEVEL,
        "inmuebles": INMUEBLES,
        "colors": COLORS,
        "snapshotId": bundle.snapshot_id,
        "logos": logos,
        "lang": lang,
    }

    bootstrap_json = json.dumps(bootstrap, ensure_ascii=False, separators=(",", ":"))
    return (
        template.replace("__HTML_LANG__", str(lang["htmlLang"]))
        .replace("__PAGE_TITLE__", str(lang["title"]))
        .replace("__BOOT_LOADING__", str(lang["bootLoading"]))
        .replace("__CSS__", css)
        .replace("__JS__", js)
        .replace("__BOOTSTRAP__", bootstrap_json)
    )


def _default_output_for(lang_code: str) -> Path:
    """ES → amba_explorer.html (compatibilidad), EN → amba_explorer_en.html."""
    name = "amba_explorer.html" if lang_code == "es" else f"amba_explorer_{lang_code}.html"
    return HERE / name


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Construye el HTML autocontenido del explorador AMBA.",
    )
    parser.add_argument(
        "--lang",
        choices=("es", "en"),
        default="es",
        help="Idioma del dashboard (default: es).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Ruta del HTML autocontenido a generar. "
            "Default: amba_explorer.html (ES) o amba_explorer_en.html (EN)."
        ),
    )
    parser.add_argument(
        "--source-dir",
        default=str(HERE / "source"),
        help="Carpeta con template.html / explorer.css / explorer.js.",
    )
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else _default_output_for(args.lang)

    bundle = DatasetBundle.discover(HERE)
    html = build_html(bundle, Path(args.source_dir), args.lang)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    size_kb = output_path.stat().st_size / 1024
    print(f"Explorer generado en: {output_path}  ({size_kb:.0f} KB)")
    print(f"Idioma:               {args.lang}")
    print(f"Snapshot de datos:    {bundle.snapshot_id}")


if __name__ == "__main__":
    main()
