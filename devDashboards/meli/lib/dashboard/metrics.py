"""Definicion de metricas expuestas en el dashboard.

Las metricas tienen dos componentes:

1. **Estructura** (que metricas existen, cuales admiten distincion
   stock/flujo). Es invariante al idioma — vive en este modulo.

2. **Display** (etiquetas, unidades, axisLabel). Depende del idioma —
   viene de ``i18n.LANG_*.saleMetrics`` / ``rentMetrics``.

``build_sale_metric_info(lang)`` y ``build_rent_metric_info(lang)``
componen ambos componentes y devuelven el dict listo para serializar al
bootstrap del front.

Contrato con el pipeline R upstream
-----------------------------------
Las bases de los indices ("base 2018 = 1" para Oferta, "base 2019 = 1"
para Demanda) **vienen calculadas desde los CSVs del pipeline R**. Este
modulo NO recalcula bases: solo declara el label que el dashboard
mostrara. Si el Centro cambia las bases upstream, hay que actualizar las
strings en ``i18n.LANG_*.saleMetrics`` y ``rentMetrics``, y este
comentario. Verificado contra el snapshot 202605: la base es uniforme
por inmueble y por geografia, y aplica por igual a las tres regiones del
proyecto (Buenos Aires, Cordoba, Rosario).
"""

from __future__ import annotations


# Estructura invariante: que metricas existen y cuales admiten universo.
# Solo Precio admite distincion stock/flujo, y SOLO en ventas. En alquileres
# y en barrios CABA siempre es "stock" (unica serie publicada). Para todas
# las metricas de venta a nivel ciudad/zona/municipio/barrio interior, solo
# se publica stock en los informes del Centro.
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
                f"Falta el display de la metrica '{key}' en el diccionario de idioma."
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
    """Devuelve el dict de metricas de venta para el bootstrap."""
    return _merge_display(SALE_METRIC_KEYS, lang["saleMetrics"], SALE_HAS_UNIVERSO)


def build_rent_metric_info(lang: dict) -> dict:
    """Devuelve el dict de metricas de alquiler para el bootstrap."""
    return _merge_display(RENT_METRIC_KEYS, lang["rentMetrics"], RENT_HAS_UNIVERSO)


__all__ = [
    "SALE_METRIC_KEYS",
    "RENT_METRIC_KEYS",
    "SALE_HAS_UNIVERSO",
    "RENT_HAS_UNIVERSO",
    "build_sale_metric_info",
    "build_rent_metric_info",
]
