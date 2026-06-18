"""Helpers de bajo nivel usados por el build.

Reducido al mínimo después del refactor del 2026-06: solo `safe_float`,
que es lo único que consume `build.py`. Los helpers de manejo de meses
y nombres de meses en castellano vivían acá; ahora viven en
`intern/legacy_code/utils_legacy_constants.py` (no se importan en
runtime).

Justificación: los helpers de mes eran herencia del dashboard Quarto
original. El explorador hace todo el manejo de fechas en JavaScript
(`addMonths`, `fmtMonth*`) y los nombres de meses por idioma viven en
`i18n.py`. Mantenerlos acá creaba confusión sobre qué se usa de verdad.
"""

from __future__ import annotations


def safe_float(value: object) -> float | None:
    """Convierte un valor del CSV a float, devolviendo None si no es numérico.

    Maneja explícitamente NA / NaN / null como ausencia de dato.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or text.upper() in {"NA", "NAN", "NULL"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


__all__ = ["safe_float"]
