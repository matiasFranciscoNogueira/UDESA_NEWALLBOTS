"""Carga de los CSVs del pipeline R y descubrimiento automatico de snapshot.

Catorce tablas en total (seis del proyecto AMBA original + ocho del
interior). Las tablas estan declaradas en ``TABLE_SPECS`` con su prefijo
y sufijo de archivo, su par de claves de serie y la codificacion sugerida.

API publica
-----------
- ``DatasetBundle.discover(root)``  — encuentra el snapshot mas reciente
  comun a todas las tablas requeridas y carga todo en memoria. Si las
  tablas tienen snapshots distintos (caso tipico en una operacion mensual
  con datos llegando en olas), elige el snapshot comun mas reciente y
  emite un ``[WARN]`` por cada tabla cuyo snapshot mas nuevo difiere.
- ``bundle.get_series(table, region, inmueble)`` — devuelve la serie
  temporal para una combinacion, ordenada por mes.
- ``bundle.tables[name]`` — acceso crudo al listado de filas.

Encoding
--------
``load_csv`` intenta ``utf-8-sig`` y, ante ``UnicodeDecodeError``, cae a
``latin-1`` e ``iso-8859-15``. Es robusto para los CSVs del Centro
(AMBA Municipios trae acentos en partidos como ``Lanús``, ``Morón``).
"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Catalogo de tablas
# ---------------------------------------------------------------------------
#
# Cada entrada define:
#   - folder:       carpeta relativa al root
#   - prefix:       prefijo del archivo (antes del snapshot id)
#   - suffix:       sufijo del archivo (despues del snapshot id, antes de .csv)
#   - series_keys:  par de columnas que definen una serie ((region, inmueble))
#
# El sufijo ``_interior`` distingue las tablas del interior (Cordoba +
# Rosario) de las de Buenos Aires que comparten prefijo (p. ej.
# ``VentasAgrupacion_202605.csv`` vs ``VentasAgrupacion_202605_interior.csv``).

TABLE_SPECS: dict[str, dict] = {
    # --- Buenos Aires ---
    "sale_group_ba": {
        "folder": "data",
        "prefix": "VentasAgrupacion_",
        "suffix": "",
        "series_keys": ("Aglomerado", "Inmueble"),
    },
    "rent_group_ba": {
        "folder": "data",
        "prefix": "AlquileresAgrupacion_",
        "suffix": "",
        "series_keys": ("Aglomerado", "Inmueble"),
    },
    "sale_caba": {
        "folder": "data",
        "prefix": "VentasCABA_",
        "suffix": "",
        "series_keys": ("Barrio", "Inmueble"),
    },
    "rent_caba": {
        "folder": "data",
        "prefix": "AlquileresCABA_",
        "suffix": "",
        "series_keys": ("Barrio", "Inmueble"),
    },
    "sale_muni_ba": {
        "folder": "data",
        "prefix": "VentasMunicipios_",
        "suffix": "",
        "series_keys": ("Municipio", "Inmueble"),
    },
    "rent_muni_ba": {
        "folder": "data",
        "prefix": "AlquileresMunicipios_",
        "suffix": "",
        "series_keys": ("Municipio", "Inmueble"),
    },
    # --- Interior (Cordoba + Rosario agregadas) ---
    "sale_group_interior": {
        "folder": "data",
        "prefix": "VentasAgrupacion_",
        "suffix": "_interior",
        "series_keys": ("Aglomerado", "Inmueble"),
    },
    "rent_group_interior": {
        "folder": "data",
        "prefix": "AlquileresAgrupacion_",
        "suffix": "_interior",
        "series_keys": ("Aglomerado", "Inmueble"),
    },
    "sale_muni_interior": {
        "folder": "data",
        "prefix": "VentasMunicipios_",
        "suffix": "_interior",
        "series_keys": ("Municipio", "Inmueble"),
    },
    "rent_muni_interior": {
        "folder": "data",
        "prefix": "AlquileresMunicipios_",
        "suffix": "_interior",
        "series_keys": ("Municipio", "Inmueble"),
    },
    # --- Barrios Cordoba + Rosario ---
    "sale_cordoba": {
        "folder": "data",
        "prefix": "VentasCordoba_",
        "suffix": "",
        "series_keys": ("Barrio", "Inmueble"),
    },
    "rent_cordoba": {
        "folder": "data",
        "prefix": "AlquileresCordoba_",
        "suffix": "",
        "series_keys": ("Barrio", "Inmueble"),
    },
    "sale_rosario": {
        "folder": "data",
        "prefix": "VentasRosario_",
        "suffix": "",
        "series_keys": ("Barrio", "Inmueble"),
    },
    "rent_rosario": {
        "folder": "data",
        "prefix": "AlquileresRosario_",
        "suffix": "",
        "series_keys": ("Barrio", "Inmueble"),
    },
}


_SNAPSHOT_RE = re.compile(r"^20\d{4}$")


# ---------------------------------------------------------------------------
# Carga de un CSV
# ---------------------------------------------------------------------------

def _coerce_value(key: str, value: str | None) -> object:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if key == "Mes":
        return text
    if text.upper() in {"NA", "NAN", "NULL"}:
        return None
    try:
        return float(text)
    except ValueError:
        return text


def _normalize_row(row: dict[str | None, str | None]) -> dict[str, object]:
    clean_row: dict[str, object] = {}
    for raw_key, raw_value in row.items():
        # Limpia BOM (zero-width no-break space U+FEFF) que algunos editores
        # pegan al primer encabezado en CSVs generados en Windows.
        key = (raw_key or "").replace("﻿", "").strip()
        if not key:
            continue
        clean_row[key] = _coerce_value(key, raw_value)
    return clean_row


def load_csv(path: Path) -> list[dict[str, object]]:
    """Lee un CSV probando UTF-8 → Latin-1 → ISO-8859-15.

    AMBA Municipios incluye partidos con acentos (Lanús, Morón); el
    interior es ASCII puro pero conviene mantener la cadena de fallback
    por compatibilidad con cualquier futuro snapshot.
    """
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "latin-1", "iso-8859-15"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                return [_normalize_row(row) for row in reader]
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise FileNotFoundError(path)


# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------

def _build_series(
    rows: list[dict[str, object]],
    keys: tuple[str, ...],
) -> dict[tuple[object, ...], list[dict[str, object]]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(tuple(row.get(key) for key in keys), []).append(row)
    for values in grouped.values():
        values.sort(key=lambda item: str(item.get("Mes", "")))
    return grouped


def _scan_snapshots(folder: Path, prefix: str, suffix: str) -> set[str]:
    """Lista todos los snapshot ids (YYYYMM) presentes para una tabla."""
    ids: set[str] = set()
    pattern = f"{prefix}*{suffix}.csv"
    for path in folder.glob(pattern):
        stem = path.stem
        if not stem.startswith(prefix):
            continue
        rest = stem[len(prefix):]
        if suffix and not rest.endswith(suffix):
            continue
        snap = rest[:-len(suffix)] if suffix else rest
        if _SNAPSHOT_RE.match(snap):
            ids.add(snap)
    return ids


@dataclass
class DatasetBundle:
    root: Path
    snapshot_id: str
    tables: dict[str, list[dict[str, object]]]
    snapshot_diagnostics: dict[str, str] | None = None

    def __post_init__(self) -> None:
        # Indices por (region, inmueble) para acceso O(1) a series.
        self.series = {
            name: _build_series(rows, TABLE_SPECS[name]["series_keys"])
            for name, rows in self.tables.items()
        }

    @classmethod
    def discover(cls, root: Path) -> "DatasetBundle":
        """Encuentra el snapshot mas reciente comun a las 14 tablas requeridas.

        Si las tablas tienen snapshots diferentes (p. ej. el snapshot mas
        nuevo de AMBA llego pero el de interior aun no), elige el comun mas
        reciente y avisa por stderr de cada divergencia. Es un guardrail
        contra "el dashboard se atraso silenciosamente porque una sola tabla
        no se actualizo".
        """
        per_table_snapshots: dict[str, set[str]] = {}
        for name, spec in TABLE_SPECS.items():
            folder = root / spec["folder"]
            per_table_snapshots[name] = _scan_snapshots(
                folder, spec["prefix"], spec["suffix"]
            )

        # Tablas sin ningun snapshot → faltan archivos.
        empty = [name for name, ids in per_table_snapshots.items() if not ids]
        if empty:
            raise FileNotFoundError(
                "Faltan archivos para las tablas: " + ", ".join(empty)
                + ". Verifica que en data/ esten los CSVs del mes para todas las 14 tablas."
            )

        common_ids = set.intersection(*per_table_snapshots.values())
        if not common_ids:
            raise FileNotFoundError(
                "No hay un snapshot YYYYMM comun a las 14 tablas. "
                "Snapshots por tabla:\n"
                + "\n".join(
                    f"  - {name}: {sorted(ids)}"
                    for name, ids in per_table_snapshots.items()
                )
            )

        snapshot_id = max(common_ids)

        # Diagnostico de divergencia: que tablas tienen un snapshot mas nuevo
        # que el comun elegido.
        diagnostics: dict[str, str] = {}
        for name, ids in per_table_snapshots.items():
            newest = max(ids)
            if newest != snapshot_id:
                diagnostics[name] = newest
                print(
                    f"[WARN] Tabla '{name}' tiene snapshot mas nuevo "
                    f"({newest}) pero usaremos {snapshot_id} porque otras "
                    f"tablas no llegaron a ese mes. Si esperabas {newest}, "
                    f"verificale al pipeline R que los datos del interior / "
                    f"AMBA esten actualizados.",
                    file=sys.stderr,
                )

        # Cargar.
        tables: dict[str, list[dict[str, object]]] = {}
        for name, spec in TABLE_SPECS.items():
            path = cls._resolve_snapshot_file(
                root, spec["folder"], spec["prefix"], spec["suffix"], snapshot_id
            )
            tables[name] = load_csv(path)

        return cls(
            root=root,
            snapshot_id=snapshot_id,
            tables=tables,
            snapshot_diagnostics=diagnostics or None,
        )

    @staticmethod
    def _resolve_snapshot_file(
        root: Path, folder: str, prefix: str, suffix: str, snapshot_id: str
    ) -> Path:
        path = root / folder / f"{prefix}{snapshot_id}{suffix}.csv"
        if not path.exists():
            raise FileNotFoundError(f"No se encontro archivo: {path}")
        return path

    def get_series(
        self,
        table_name: str,
        *keys: object,
        until_month: str | None = None,
    ) -> list[dict[str, object]]:
        """Serie temporal para una combinacion (region, inmueble).

        Las filas ya vienen ordenadas por ``Mes`` (orden ASCII funciona porque
        el formato es ``YYYY-MM``). ``until_month`` filtra al vuelo si se
        necesita un corte explicito.
        """
        if table_name not in self.series:
            raise KeyError(f"Tabla desconocida: {table_name!r}")
        rows = self.series[table_name].get(tuple(keys), [])
        if until_month is None:
            return list(rows)
        return [row for row in rows if str(row.get("Mes", "")) <= until_month]


__all__ = ["TABLE_SPECS", "DatasetBundle", "load_csv"]
