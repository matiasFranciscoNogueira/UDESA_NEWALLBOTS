"""Definición de métricas expuestas en el dashboard.

Las métricas tienen dos componentes:

1. **Estructura** (qué métricas existen, cuáles admiten distinción
   stock/flujo). Es invariante al idioma — vive en este módulo.

2. **Display** (etiquetas, unidades, axisLabel). Depende del idioma —
   viene de `i18n.LANG_*.saleMetrics` / `rentMetrics`.

`build_sale_metric_info(lang)` y `build_rent_metric_info(lang)` componen
ambos componentes y devuelven el dict listo para serializar al
bootstrap del front.

Contrato con el pipeline R upstream
-----------------------------------
Las bases de los índices ("base 2018 = 1" para Oferta, "base 2019 = 1"
para Demanda) **vienen calculadas desde los CSVs del pipeline R**. Este
módulo NO recalcula bases: solo declara el label que el dashboard mostrará.
Si el Centro cambia las bases upstream, hay que actualizar las strings en
`i18n.LANG_*.saleMetrics` y `rentMetrics`, y este comentario.
"""

from __future__ import annotations


# Estructura invariante: qué métricas existen y cuáles admiten universo.
# Solo Precio admite distinción stock/flujo, y SÓLO en ventas. En alquileres
# y en barrios CABA siempre es "stock" (única serie publicada).
SALE_METRIC_KEYS: tuple[str, ...] = ("precio", "demanda", "oferta")
RENT_METRIC_KEYS: tuple[str, ...] = ("precio", "demanda", "oferta")

SALE_HAS_UNIVERSO: dict[str, bool] = {
    "precio": True,
    "demanda": False,
    "oferta": False,
}
RENT_HAS_UNIVERSO: dict[str, bool] = {
    "precio": False,
    "demanda": False,
    "oferta": False,
}


def _merge_display(keys: tuple[str, ...], display: dict, has_universo: dict) -> dict:
    """Combina la estructura (keys + hasUniverso) con el display por idioma."""
    out: dict = {}
    for key in keys:
        spec = display.get(key)
        if spec is None:
            raise KeyError(
                f"Falta el display de la métrica '{key}' en el diccionario de idioma."
            )
        out[key] = {
            "label": spec["label"],
            "unit": spec["unit"],
            "shortUnit": spec["shortUnit"],
            "axisLabel": spec["axisLabel"],
            "hasUniverso": has_universo[key],
        }
    return out


def build_sale_metric_info(lang: dict) -> dict:
    """Devuelve el dict de métricas de venta para el bootstrap."""
    return _merge_display(SALE_METRIC_KEYS, lang["saleMetrics"], SALE_HAS_UNIVERSO)


def build_rent_metric_info(lang: dict) -> dict:
    """Devuelve el dict de métricas de alquiler para el bootstrap."""
    return _merge_display(RENT_METRIC_KEYS, lang["rentMetrics"], RENT_HAS_UNIVERSO)


__all__ = [
    "SALE_METRIC_KEYS",
    "RENT_METRIC_KEYS",
    "SALE_HAS_UNIVERSO",
    "RENT_HAS_UNIVERSO",
    "build_sale_metric_info",
    "build_rent_metric_info",
]
