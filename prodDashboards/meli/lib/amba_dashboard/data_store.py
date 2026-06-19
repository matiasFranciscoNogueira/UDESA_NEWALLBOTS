"""Carga de los CSVs del pipeline R y descubrimiento automático de snapshot.

Este módulo no asume nada sobre la máquina donde corre: las tablas viven
en una carpeta relativa al `root` que se le pase a `DatasetBundle.discover`.

En la versión autocontenida de `version_final/`, el root es la misma
carpeta `version_final/` y los CSVs viven en `version_final/data/`.

API pública
-----------
- `DatasetBundle.discover(root)` — encuentra el snapshot más reciente común
  a las 6 tablas requeridas y carga todo en memoria.
- `bundle.get_series(table, region, inmueble)` — devuelve la serie temporal
  para una combinación, ordenada por mes.
- `bundle.tables[name]` — acceso crudo al listado de filas (fallback).

API legacy (movida a `intern/legacy_code/data_store_legacy_methods.py`):
- `get_row(table, *keys)` — no se usa en `build.py`.
- `filter_rows(table, ...)` — no se usa en `build.py`.
- `self.indices` y `self.common_months` — solo servían a los métodos
  legacy de arriba.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


TABLE_SPECS = {
    "sale_group": {
        "folder": "data",
        "prefix": "VentasAgrupacion_",
        "series_keys": ("Aglomerado", "Inmueble"),
    },
    "rent_group": {
        "folder": "data",
        "prefix": "AlquileresAgrupacion_",
        "series_keys": ("Aglomerado", "Inmueble"),
    },
    "sale_caba": {
        "folder": "data",
        "prefix": "VentasCABA_",
        "series_keys": ("Barrio", "Inmueble"),
    },
    "rent_caba": {
        "folder": "data",
        "prefix": "AlquileresCABA_",
        "series_keys": ("Barrio", "Inmueble"),
    },
    "sale_muni": {
        "folder": "data",
        "prefix": "VentasMunicipios_",
        "series_keys": ("Municipio", "Inmueble"),
    },
    "rent_muni": {
        "folder": "data",
        "prefix": "AlquileresMunicipios_",
        "series_keys": ("Municipio", "Inmueble"),
    },
}


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
        # Limpia BOM (zero-width no-break space U+FEFF) que algunos
        # editores pegan al primer encabezado en CSVs en Windows.
        key = (raw_key or "").replace("﻿", "").strip()
        if not key:
            continue
        clean_row[key] = _coerce_value(key, raw_value)
    return clean_row


def load_csv(path: Path) -> list[dict[str, object]]:
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


def _build_series(
    rows: list[dict[str, object]],
    keys: tuple[str, ...],
) -> dict[tuple[object, ...], list[dict[str, object]]]:
    grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(tuple(row[key] for key in keys), []).append(row)
    for values in grouped.values():
        values.sort(key=lambda item: str(item["Mes"]))
    return grouped


@dataclass
class DatasetBundle:
    root: Path
    snapshot_id: str
    tables: dict[str, list[dict[str, object]]]

    def __post_init__(self) -> None:
        self.series = {
            name: _build_series(rows, TABLE_SPECS[name]["series_keys"])
            for name, rows in self.tables.items()
        }

    @classmethod
    def discover(cls, root: Path) -> "DatasetBundle":
        """Encuentra el snapshot más reciente común a las 6 tablas y carga todo.

        El "snapshot id" es el sufijo YYYYMM del nombre del archivo
        (ej. `VentasAgrupacion_202605.csv` → `202605`). Si no hay un sufijo
        compartido entre las 6 tablas, levanta `FileNotFoundError` con un
        mensaje explicando qué falta.
        """
        snapshot_sets: list[set[str]] = []
        for spec in TABLE_SPECS.values():
            folder = root / spec["folder"]
            ids = set()
            for path in folder.glob(f"{spec['prefix']}*.csv"):
                match = re.search(r"_(20\d{4})", path.name)
                if match:
                    ids.add(match.group(1))
            snapshot_sets.append(ids)
        common_ids = set.intersection(*snapshot_sets) if snapshot_sets else set()
        if not common_ids:
            raise FileNotFoundError(
                "No se encontró un snapshot común entre las 6 tablas requeridas. "
                "Verificá que en data/ estén los 6 archivos del mismo mes "
                "(VentasAgrupacion_YYYYMM, AlquileresAgrupacion_YYYYMM, "
                "VentasCABA_YYYYMM, AlquileresCABA_YYYYMM, "
                "VentasMunicipios_YYYYMM, AlquileresMunicipios_YYYYMM)."
            )
        snapshot_id = max(common_ids)
        tables: dict[str, list[dict[str, object]]] = {}
        for name, spec in TABLE_SPECS.items():
            path = cls._resolve_snapshot_file(root, spec["folder"], spec["prefix"], snapshot_id)
            tables[name] = load_csv(path)
        return cls(root=root, snapshot_id=snapshot_id, tables=tables)

    @staticmethod
    def _resolve_snapshot_file(root: Path, folder: str, prefix: str, snapshot_id: str) -> Path:
        candidates = sorted((root / folder).glob(f"{prefix}{snapshot_id}*.csv"))
        if not candidates:
            raise FileNotFoundError(f"No se encontró archivo para {prefix}{snapshot_id}")
        candidates.sort(key=lambda item: (len(item.name), item.name))
        return candidates[0]

    def get_series(
        self,
        table_name: str,
        *keys: object,
        until_month: str | None = None,
    ) -> list[dict[str, object]]:
        """Devuelve la serie temporal para una combinación region × inmueble.

        Las filas ya vienen ordenadas por `Mes` (orden ASCII funciona porque
        el formato es YYYY-MM). Si se pasa `until_month`, filtra al vuelo.
        """
        rows = self.series[table_name].get(tuple(keys), [])
        if until_month is None:
            return list(rows)
        return [row for row in rows if str(row["Mes"]) <= until_month]
