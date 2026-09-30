"""Helpers de bajo nivel usados por el build.

Solo ``safe_float``: lo unico que consume ``build.py``. El manejo de
nombres de mes y los formatos de fecha viven en JavaScript (el front es
responsable del display) y en ``i18n.py`` (strings localizadas).
"""

from __future__ import annotations


def safe_float(value: object) -> float | None:
    """Convierte un valor del CSV a float, devolviendo None si no es numerico.

    Maneja explicitamente NA / NaN / null como ausencia de dato.
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
