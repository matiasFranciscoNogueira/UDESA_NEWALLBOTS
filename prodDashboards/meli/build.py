"""Construye el HTML autocontenido del explorador inmobiliario multi-mercado.

Lee los CSVs del pipeline R (14 archivos: 6 de AMBA / CABA / GBA mas 8
del interior con Cordoba y Rosario) via el paquete ``dashboard`` y
produce un unico HTML con todos los datos, estilos y scripts inlineados.
Output listo para servirse con cualquier server HTTP estatico (ngrok,
SimpleHTTPRequestHandler, GitHub Pages).

Uso
---
::

    python build.py                         # ES -> amba_explorer.html
    python build.py --lang en               # EN -> amba_explorer_en.html
    python build.py --lang es --output X    # ruta de salida explicita

Contrato con el pipeline R upstream
-----------------------------------
Las bases de los indices que el dashboard muestra como label
(``Oferta: base enero 2018 = 1``, ``Demanda: base enero 2019 = 1``)
VIENEN CALCULADAS desde los CSVs del pipeline R. Este build NO recalcula
bases: solo pasa los valores crudos al front y declara el label. Si el
Centro cambia las bases upstream, hay que actualizar las strings en
``lib/dashboard/i18n.py`` (claves ``saleMetrics.*`` y ``rentMetrics.*``)
Y este comentario. Verificado contra los CSVs de los snapshots 202605,
202606 y 202608: la base es uniforme por inmueble, geografia y mercado.

Los nombres de columna que lee cada tabla viven en ``catalogs.py``
(``_SALE_FIELDS_*`` / ``_RENT_FIELDS_*``). Un campo puede declararse como
tupla de alias; ``_resolve_field`` toma el primero presente en el CSV.

Forma del bootstrap del front
-----------------------------
::

    bootstrap = {
        "data":           {side: {market: {level: {inmueble: {metric: {...}}}}}}
        "markets":        metadata de mercados + niveles + regiones + hidden cells
        "saleMetrics":    info por metrica (label/unit/axisLabel) — ES o EN
        "rentMetrics":    idem
        "inmuebles":      ["Casa", "Departamento"]
        "colors":         paleta institucional por region (aglomerados/ciudades/zonas)
        "snapshotId":     "YYYYMM"
        "snapshotDiagnostics": dict | None  (warnings si tablas tienen snapshots distintos)
        "logos":          {udesa: data:URI, meli: data:URI}
        "lang":           dict de strings de UI por idioma
    }
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

# El paquete auxiliar ``dashboard`` esta en lib/ — autocontenido.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))

from dashboard.data_store import DatasetBundle  # noqa: E402
from dashboard.utils import safe_float  # noqa: E402
from dashboard.catalogs import (  # noqa: E402
    COLORS,
    INMUEBLES,
    MARKETS,
    HIDDEN_CELLS,
    cell_hidden_reason,
    skip_region,
)
from dashboard.metrics import (  # noqa: E402
    build_rent_metric_info,
    build_sale_metric_info,
)
from dashboard.i18n import get_lang  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers comunes
# ---------------------------------------------------------------------------

_warned_missing_columns: set[tuple[str, str]] = set()


def _snapshot_month_label(snapshot_id: str) -> str:
    """``'202603'`` -> ``'2026-03'`` (formato del campo Mes en los CSVs)."""
    return f"{snapshot_id[:4]}-{snapshot_id[4:6]}"


def _warn_missing(table: str, field: str) -> None:
    """Avisa a stderr UNA sola vez por (tabla, columna) faltante.

    Si el pipeline R cambia el nombre de una columna sin avisar, hoy el
    dashboard mostraria la serie vacia silenciosamente. Esto convierte
    ese fallo silencioso en un warning visible en consola.
    """
    key = (table, field)
    if key in _warned_missing_columns:
        return
    _warned_missing_columns.add(key)
    print(
        f"[WARN] columna '{field}' no encontrada en la tabla '{table}'. "
        f"La serie correspondiente quedara vacia en el dashboard.",
        file=sys.stderr,
    )


def _resolve_field(row: dict, field: str | tuple[str, ...]) -> str | None:
    """Devuelve el nombre de columna real a leer, o ``None`` si no hay ninguno.

    ``field`` puede ser un string o una tupla de alias en orden de
    preferencia. El pipeline R renombro columnas de ``VentasCABA`` en el
    snapshot 202608 (``Mediana.Stock`` -> ``Mediana Stock``); declarar
    ambos nombres en ``catalogs.py`` hace que el build tolere los dos
    formatos sin tocar codigo cuando el upstream cambie de nuevo.
    """
    candidates = (field,) if isinstance(field, str) else tuple(field)
    for name in candidates:
        if name in row:
            return name
    return None


def _series_for(
    bundle: DatasetBundle,
    table: str,
    region: str,
    inmueble: str,
    field: str | tuple[str, ...],
    *,
    skip_month: str | None = None,
    skip_zero: bool = False,
) -> list[dict]:
    """Lee una serie del bundle aplicando filtros de calidad del Centro.

    - ``field``: nombre de columna, o tupla de alias (ver ``_resolve_field``).
    - ``skip_month``: si esta seteado, omite la fila cuyo ``Mes`` coincide.
      Se usa para Demanda y Oferta: el ultimo mes del snapshot esta
      incompleto. Es la regla del pipeline R (``Indices_AMBA.Rmd``,
      ``Informe_Interior.R``: ``data$mes <= end_month``).
    - ``skip_zero``: omite valores == 0. Aplica a Contactos, cuya serie
      inicial (2018-01) puede valer 0 por inicializacion del indice.
    - Si ningun alias de ``field`` existe en la tabla, emite un ``[WARN]``
      a stderr una vez por ``(tabla, columna)``.
    """
    rows = bundle.get_series(table, region, inmueble)
    if not rows:
        return []
    column = _resolve_field(rows[0], field)
    if column is None:
        _warn_missing(table, field if isinstance(field, str) else " | ".join(field))
        return []
    points: list[dict] = []
    for row in rows:
        mes = str(row["Mes"])
        if skip_month is not None and mes == skip_month:
            continue
        value = safe_float(row.get(column))
        if value is None:
            continue
        if skip_zero and value == 0:
            continue
        points.append({"x": mes, "y": value})
    return points


# ---------------------------------------------------------------------------
# Poblado de un (market, level, side) en el data tree
# ---------------------------------------------------------------------------

def _populate_precio(
    bundle: DatasetBundle,
    table: str,
    regions: list[str],
    inmueble: str,
    fields: dict,
) -> dict:
    """Empaqueta precio de venta bajo ``{universo: {region: series}}``.

    Precio NO excluye el ultimo mes (la mediana del stock activo ya es
    final una vez cerrado el mes).
    """
    out: dict = {}
    if "precio_stock" in fields:
        stock_field = fields["precio_stock"]
        stock_data: dict[str, list[dict]] = {}
        for region in regions:
            points = _series_for(bundle, table, region, inmueble, stock_field)
            if points:
                stock_data[region] = points
        if stock_data:
            out["stock"] = stock_data
    if "precio_flujo" in fields:
        flujo_field = fields["precio_flujo"]
        flujo_data: dict[str, list[dict]] = {}
        for region in regions:
            points = _series_for(bundle, table, region, inmueble, flujo_field)
            if points:
                flujo_data[region] = points
        if flujo_data:
            out["flujo"] = flujo_data
    return out


def _populate_flat(
    bundle: DatasetBundle,
    table: str,
    regions: list[str],
    inmueble: str,
    field: str,
    *,
    skip_month: str | None = None,
    skip_zero: bool = False,
) -> dict:
    """Empaqueta demanda/oferta como ``{region: series}``."""
    out: dict = {}
    for region in regions:
        points = _series_for(
            bundle, table, region, inmueble, field,
            skip_month=skip_month, skip_zero=skip_zero,
        )
        if points:
            out[region] = points
    return out


def _populate_cell(
    bundle: DatasetBundle,
    market: str,
    level: str,
    side: str,
    inmueble: str,
    level_spec: dict,
    last_mes: str,
) -> dict | None:
    """Devuelve ``{precio: {...}, demanda: {...}, oferta: {...}}`` para una celda.

    Si la celda esta oculta editorialmente o no tiene tabla asignada,
    devuelve ``None`` (la celda no se incluye en el data tree).
    """
    if cell_hidden_reason(market, level, side, inmueble):
        return None

    table = level_spec[f"{side}_table"]
    fields = level_spec[f"{side}_fields"]
    if table is None or fields is None:
        return None

    # Filtrar regiones: las que el catalogo declara, menos las excluidas
    # explicitamente (e.g., ARGUELLO/Casa discontinuada en 2024-01).
    catalog_regions = level_spec["regions"]
    regions = [
        r for r in catalog_regions
        if not skip_region(market, level, side, inmueble, r)
    ]

    per_inmueble: dict = {}
    if side == "rent":
        # Alquiler: un solo campo de precio (``corrientes``). Se expone
        # como universo virtual ``stock`` para que el front no requiera
        # ramas adicionales.
        corrientes_field = fields["precio_corrientes"]
        data: dict[str, list[dict]] = {}
        for region in regions:
            points = _series_for(bundle, table, region, inmueble, corrientes_field)
            if points:
                data[region] = points
        per_inmueble["precio"] = {"stock": data} if data else {}
    else:
        per_inmueble["precio"] = _populate_precio(bundle, table, regions, inmueble, fields)

    per_inmueble["demanda"] = _populate_flat(
        bundle, table, regions, inmueble, fields["demanda"],
        skip_month=last_mes, skip_zero=True,
    )
    # Oferta es STOCK (no FLUJO): aunque el ultimo mes sea parcial captura la
    # mayoria del stock activo. Los informes 202605 calculan las variaciones de
    # oferta usando el mes parcial (e.g. AMBA depto alquiler +257.9% vs Nov 2023
    # = (3.64 / 1.016 - 1) usando el dato 2026-05). Para que el dashboard reproduzca
    # el informe, NO se excluye el ultimo mes en oferta.
    per_inmueble["oferta"] = _populate_flat(
        bundle, table, regions, inmueble, fields["oferta"],
    )

    # Si TODAS las metricas quedaron vacias, retornar None — la celda no
    # se incluye en el bootstrap.
    has_data = any([
        per_inmueble["precio"],
        per_inmueble["demanda"],
        per_inmueble["oferta"],
    ])
    return per_inmueble if has_data else None


# ---------------------------------------------------------------------------
# Construccion del data tree y la metadata de mercados
# ---------------------------------------------------------------------------

def _regions_with_data_in_cell(cell: dict | None) -> set[str]:
    """Conjunto de regiones presentes en cualquier metrica de la celda."""
    if cell is None:
        return set()
    seen: set[str] = set()
    precio = cell.get("precio") or {}
    if isinstance(precio, dict):
        # precio tiene forma {universo: {region: ...}}.
        for universo_data in precio.values():
            if isinstance(universo_data, dict):
                seen.update(universo_data.keys())
    for metric in ("demanda", "oferta"):
        metric_data = cell.get(metric) or {}
        if isinstance(metric_data, dict):
            seen.update(metric_data.keys())
    return seen


def build_data_and_markets(bundle: DatasetBundle, lang: dict) -> tuple[dict, dict]:
    """Construye el ``data`` tree y la ``markets`` metadata listos para el front.

    ``data["sale"|"rent"][market][level][inmueble]`` contiene los puntos por
    metrica. Celdas ocultas no se incluyen.

    ``markets[market_key]`` contiene la metadata de navegacion: labels
    localizados, niveles disponibles, defaultRegions, y por nivel un
    ``regionsByInmueble`` con la union de regiones donde HAY datos en al
    menos un lado, mas un dict ``hiddenCells`` con los mensajes
    editoriales para las celdas ocultas.
    """
    data: dict = {"sale": {}, "rent": {}}
    markets_meta: dict = {}
    last_mes = _snapshot_month_label(bundle.snapshot_id)

    market_display = lang.get("marketDisplay", {})

    for market_key, market_spec in MARKETS.items():
        data["sale"][market_key] = {}
        data["rent"][market_key] = {}

        market_meta = {
            "label": market_display.get(market_key, market_key),
            "defaultLevel": market_spec["default_level"],
            "levels": {},
        }

        for level_key, level_spec in market_spec["levels"].items():
            level_label = lang.get(level_spec["label_key"], level_key)
            region_label = lang.get(level_spec["region_label_key"], level_key)

            level_meta: dict = {
                "label": level_label,
                "regionLabel": region_label,
                "defaultRegions": list(level_spec["default_regions"]),
                "regionsByInmueble": {},
                "hiddenCells": {},
            }

            # Acumular regiones por inmueble: union de las que tienen datos
            # en cualquier side (sale o rent).
            regions_per_inmueble: dict[str, set[str]] = {
                inmueble: set() for inmueble in INMUEBLES
            }

            for side in ("sale", "rent"):
                data[side][market_key].setdefault(level_key, {})
                for inmueble in INMUEBLES:
                    reason = cell_hidden_reason(market_key, level_key, side, inmueble)
                    if reason is not None:
                        level_meta["hiddenCells"].setdefault(side, {})[inmueble] = reason
                        # No se incluye data para esta celda.
                        continue
                    cell = _populate_cell(
                        bundle, market_key, level_key, side, inmueble, level_spec, last_mes
                    )
                    if cell is None:
                        continue
                    data[side][market_key][level_key][inmueble] = cell
                    regions_per_inmueble[inmueble] |= _regions_with_data_in_cell(cell)

            # Pasar de sets a listas en el orden del catalogo (estabilidad).
            catalog_regions = level_spec["regions"]
            for inmueble in INMUEBLES:
                available = regions_per_inmueble[inmueble]
                level_meta["regionsByInmueble"][inmueble] = [
                    r for r in catalog_regions if r in available
                ]

            # Si no quedaron celdas con data ni hidden reasons para algun side,
            # limpiamos la rama del data tree para ahorrar bytes.
            for side in ("sale", "rent"):
                if not data[side][market_key][level_key]:
                    data[side][market_key].pop(level_key, None)

            market_meta["levels"][level_key] = level_meta

        markets_meta[market_key] = market_meta

    return data, markets_meta


# ---------------------------------------------------------------------------
# Encoding de logos a data URI (para HTML autocontenido)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Ensamble final del HTML
# ---------------------------------------------------------------------------

def build_html(bundle: DatasetBundle, source_dir: Path, lang_code: str) -> str:
    template = (source_dir / "template.html").read_text(encoding="utf-8")
    css = (source_dir / "explorer.css").read_text(encoding="utf-8")
    js = (source_dir / "explorer.js").read_text(encoding="utf-8")

    lang = get_lang(lang_code)

    branding_dir = HERE / "lib" / "dashboard" / "assets" / "branding"
    logos = {
        "udesa": _logo_data_uri(branding_dir / "udesa-logo.jpg"),
        "meli": _logo_data_uri(branding_dir / "mercado-libre-logo.webp"),
    }

    data, markets_meta = build_data_and_markets(bundle, lang)

    bootstrap = {
        "data": data,
        "markets": markets_meta,
        "saleMetrics": build_sale_metric_info(lang),
        "rentMetrics": build_rent_metric_info(lang),
        "inmuebles": INMUEBLES,
        "colors": COLORS,
        "snapshotId": bundle.snapshot_id,
        "snapshotDiagnostics": bundle.snapshot_diagnostics,
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
    """ES -> ``amba_explorer.html`` (backward-compat con version_final).
    EN -> ``amba_explorer_en.html``.

    Nota: el nombre `amba_explorer.html` se conserva para no romper URLs
    publicas (ngrok) ni scripts externos. El dashboard ya no es solo AMBA
    — incluye Cordoba y Rosario — pero el filename queda heredado.
    """
    if lang_code == "es":
        return HERE / "amba_explorer.html"
    return HERE / f"amba_explorer_{lang_code}.html"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Construye el HTML autocontenido del explorador inmobiliario multi-mercado."
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
    if bundle.snapshot_diagnostics:
        print(
            f"Snapshots divergentes: {len(bundle.snapshot_diagnostics)} tablas con "
            f"snapshot mas nuevo no usado. Ver warnings en stderr."
        )


if __name__ == "__main__":
    main()
