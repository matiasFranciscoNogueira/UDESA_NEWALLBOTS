"""Strings de UI por idioma y constructor de paquete de traducción.

Dos diccionarios planos con las mismas claves: `LANG_ES` y `LANG_EN`.
El front-end (`explorer.js`) consume `bootstrap.lang` y reemplaza cada
string hardcodeado por su clave correspondiente.

Reglas:
- Toda string visible al usuario vive acá. Si necesitás agregar una nueva,
  agregala en AMBOS diccionarios.
- El assert al final del módulo falla el build si las claves se
  desincronizan — funciona como linter de traducción.
- Los identificadores de DATOS (nombres de aglomerados, barrios,
  municipios) NO se traducen — son proper nouns. Lo que sí se traduce es
  el display de "Casa"/"Departamento" → "House"/"Apartment" (ver
  `inmuebleDisplay`).
- El locale (`es-AR`, `en-US`) define cómo el front formatea números:
  `1.234,56` en castellano vs `1,234.56` en inglés.
"""

from __future__ import annotations


LANG_ES: dict[str, object] = {
    # ---- Metadata de página ----
    "locale": "es-AR",
    "htmlLang": "es",
    "title": "Explorador AMBA · Mercado Inmobiliario · UdeSA",
    "bootLoading": "Cargando explorador…",
    "bootError": "No se pudo inicializar el explorador.",
    "toolbarAria": "Filtros del explorador",

    # ---- Meses ----
    "monthsLong": [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ],
    "monthsShort": [
        "Ene", "Feb", "Mar", "Abr", "May", "Jun",
        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
    ],
    "monthConnector": "de",  # "Enero de 2026"

    # ---- Niveles geográficos ----
    "levelLabel": "Nivel geográfico",
    "levelAglomerado": "Aglomerado",
    "levelBarrio": "Barrio (CABA)",
    "levelMunicipio": "Municipio (AMBA)",
    "regionAglomerado": "Aglomerado",
    "regionBarrio": "Barrio",
    "regionMunicipio": "Municipio",

    # ---- Inmueble y métrica ----
    "inmuebleLabel": "Tipo de propiedad",
    "metricLabel": "Métrica",
    "metricPrecio": "Precio mediano por m²",
    "metricDemanda": "Demanda (contactos)",
    "metricOferta": "Oferta (publicaciones activas)",

    # ---- Chips de período ----
    "periodLabel": "Período",
    "periodAria": "Período del gráfico",
    "range12Long": "12 meses",
    "range12Short": "12 m",
    "range24Long": "24 meses",
    "range24Short": "24 m",
    "range60Long": "60 meses",
    "range60Short": "60 m",
    "rangeAllLong": "Histórico completo",
    "rangeAllShort": "Histórico",

    # ---- Descriptor de regiones seleccionadas ----
    "regionsNone": "Ninguna seleccionada",
    "regionsAllPrefix": "Todas",          # "Todas (5)"
    "regionsSelectedSuffix": "sel.",      # "PALERMO, RECOLETA · 12 sel."

    # ---- Dropdown menu ----
    "searchPlaceholder": "Buscar...",
    "searchAriaPrefix": "Buscar en",      # "Buscar en {label}"
    "menuSelectAll": "Seleccionar todos",
    "menuClear": "Limpiar",

    # ---- Toolbar actions ----
    "actionResetTitle": "Restablecer filtros",
    "actionResetLabel": "Restablecer",
    "actionDownloadSaleTitle": "Descargar venta",
    "actionDownloadSaleAria": "Descargar venta como PNG",
    "actionDownloadSaleLabel": "Venta",
    "actionDownloadRentTitle": "Descargar alquiler",
    "actionDownloadRentAria": "Descargar alquiler como PNG",
    "actionDownloadRentLabel": "Alquiler",

    # ---- Paneles ----
    "sideSale": "Venta",
    "sideRent": "Alquiler",
    "sideSaleAria": "Gráfico de venta",
    "sideRentAria": "Gráfico de alquiler",
    "sideSaleLegendAria": "Leyenda Venta",
    "sideRentLegendAria": "Leyenda Alquiler",

    # ---- Título y subtítulo del panel ----
    "titleSeparator": "·",
    "titleBarriosCaba": "Barrios CABA",
    "titleMunicipiosAmba": "Municipios AMBA",
    "subtitleOfertaSuffix": (
        "Serie normalizada como índice base enero 2018 = 1 (pipeline del Centro). "
        "El último mes del snapshot se excluye por ser parcial."
    ),
    "subtitleDemandaSuffix": (
        "Serie normalizada como índice base enero 2019 = 1 (pipeline del Centro). "
        "El último mes del snapshot se excluye por ser parcial."
    ),

    # ---- Empty states ----
    "emptyBlockedTitle": "No hay visualización disponible para esta selección.",
    "emptyWidenPeriod": "Probá ampliar el período o activar más aglomerados en la leyenda.",
    "emptyChangeCombo": "Probá con otra combinación de aglomerado, tipo de propiedad o métrica.",
    "emptyNoPrecio": (
        "No hay datos de precio para esta combinación en el snapshot. "
        "Probá con otra región o tipo de propiedad."
    ),

    # ---- Toasts ----
    "toastKeepOnePrefix": "Mantenemos al menos un",      # + noun + "."
    "toastSelectOnePrefix": "Seleccioná al menos un",    # + noun + "."
    "toastReset": "Filtros restablecidos.",
    "toastImageOk": "Imagen descargada.",
    "toastImageFail": "No se pudo generar la imagen.",
    "toastNoChart": "No hay gráfico para exportar.",

    # ---- Formato numérico y stats ----
    "noData": "N/D",
    "statsAccumSuffix": "acum.",
    "statsPpSuffix": "pp",

    # ---- Botón de descarga embebido ----
    "panelDownloadBtn": "Descargar PNG",

    # ---- Créditos ----
    "footerCredit": (
        "Centro de Estudios Cuantitativos en Negocios · Universidad de San Andrés · "
        "Datos: Mercado Libre · Snapshot {snapshot}."
    ),
    "pngFooterCredit": (
        "Datos: Mercado Libre · Centro de Estudios Cuantitativos en Negocios · UdeSA · "
        "Snapshot {snapshot}"
    ),
    "snapshotPrefix": "Snapshot",

    # ---- Display de inmuebles (data key → label localizado) ----
    "inmuebleDisplay": {
        "Casa": "Casa",
        "Departamento": "Departamento",
    },

    # ---- Display de aglomerados (data key → label localizado) ----
    # Identidad en castellano. En EN se traduce el calificador de zona.
    "aglomeradoDisplay": {
        "AMBA": "AMBA",
        "CABA": "CABA",
        "GBA Zona Norte": "GBA Zona Norte",
        "GBA Zona Oeste": "GBA Zona Oeste",
        "GBA Zona Sur": "GBA Zona Sur",
    },

    # ---- Métricas para el bootstrap (label/unit/shortUnit/axisLabel) ----
    "saleMetrics": {
        "precio": {
            "label": "Precio mediano de venta",
            "unit": "USD por m²",
            "shortUnit": "USD/m²",
            "axisLabel": "USD por m²",
        },
        "demanda": {
            "label": "Demanda (contactos)",
            "unit": "Índice de contactos (base 2019 = 1)",
            "shortUnit": "índice",
            "axisLabel": "Índice de contactos (2019=1)",
        },
        "oferta": {
            "label": "Oferta (publicaciones activas)",
            "unit": "Índice de publicaciones activas (base 2018 = 1)",
            "shortUnit": "índice",
            "axisLabel": "Índice de oferta (2018=1)",
        },
    },
    "rentMetrics": {
        "precio": {
            "label": "Precio mediano de alquiler",
            "unit": "ARS corrientes por m²",
            "shortUnit": "ARS/m²",
            "axisLabel": "ARS por m² (corrientes)",
        },
        "demanda": {
            "label": "Demanda (contactos)",
            "unit": "Índice de contactos (base 2019 = 1)",
            "shortUnit": "índice",
            "axisLabel": "Índice de contactos (2019=1)",
        },
        "oferta": {
            "label": "Oferta (publicaciones activas)",
            "unit": "Índice de publicaciones activas (base 2018 = 1)",
            "shortUnit": "índice",
            "axisLabel": "Índice de oferta (2018=1)",
        },
    },
}


LANG_EN: dict[str, object] = {
    # ---- Page metadata ----
    "locale": "en-US",
    "htmlLang": "en",
    "title": "AMBA Explorer · Real Estate Market · UdeSA",
    "bootLoading": "Loading explorer…",
    "bootError": "The explorer could not be initialized.",
    "toolbarAria": "Explorer filters",

    # ---- Months ----
    "monthsLong": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
    "monthsShort": [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ],
    "monthConnector": "",  # "January 2026"

    # ---- Geographic levels ----
    "levelLabel": "Geographic level",
    "levelAglomerado": "Region",
    "levelBarrio": "Neighborhood (CABA)",
    "levelMunicipio": "Municipality (AMBA)",
    "regionAglomerado": "Region",
    "regionBarrio": "Neighborhood",
    "regionMunicipio": "Municipality",

    # ---- Property and metric ----
    "inmuebleLabel": "Property type",
    "metricLabel": "Metric",
    "metricPrecio": "Median price per m²",
    "metricDemanda": "Demand (contacts)",
    "metricOferta": "Supply (active listings)",

    # ---- Period chips ----
    "periodLabel": "Period",
    "periodAria": "Chart period",
    "range12Long": "12 months",
    "range12Short": "12 m",
    "range24Long": "24 months",
    "range24Short": "24 m",
    "range60Long": "60 months",
    "range60Short": "60 m",
    "rangeAllLong": "Full history",
    "rangeAllShort": "All",

    # ---- Region selector descriptor ----
    "regionsNone": "None selected",
    "regionsAllPrefix": "All",
    "regionsSelectedSuffix": "sel.",

    # ---- Dropdown menu ----
    "searchPlaceholder": "Search...",
    "searchAriaPrefix": "Search in",
    "menuSelectAll": "Select all",
    "menuClear": "Clear",

    # ---- Toolbar actions ----
    "actionResetTitle": "Reset filters",
    "actionResetLabel": "Reset",
    "actionDownloadSaleTitle": "Download sales chart",
    "actionDownloadSaleAria": "Download sales chart as PNG",
    "actionDownloadSaleLabel": "Sales",
    "actionDownloadRentTitle": "Download rental chart",
    "actionDownloadRentAria": "Download rental chart as PNG",
    "actionDownloadRentLabel": "Rentals",

    # ---- Panels ----
    "sideSale": "Sales",
    "sideRent": "Rentals",
    "sideSaleAria": "Sales chart",
    "sideRentAria": "Rentals chart",
    "sideSaleLegendAria": "Sales legend",
    "sideRentLegendAria": "Rentals legend",

    # ---- Panel title and subtitle ----
    "titleSeparator": "·",
    "titleBarriosCaba": "CABA neighborhoods",
    "titleMunicipiosAmba": "AMBA municipalities",
    "subtitleOfertaSuffix": (
        "Series normalized as an index, base January 2018 = 1 (Centro pipeline). "
        "The last snapshot month is excluded as it is partial."
    ),
    "subtitleDemandaSuffix": (
        "Series normalized as an index, base January 2019 = 1 (Centro pipeline). "
        "The last snapshot month is excluded as it is partial."
    ),

    # ---- Empty states ----
    "emptyBlockedTitle": "No visualization available for this selection.",
    "emptyWidenPeriod": "Try widening the period or activating more regions in the legend.",
    "emptyChangeCombo": "Try a different combination of region, property type, or metric.",
    "emptyNoPrecio": (
        "No price data for this combination in the snapshot. "
        "Try another region or property type."
    ),

    # ---- Toasts ----
    "toastKeepOnePrefix": "We keep at least one",
    "toastSelectOnePrefix": "Please select at least one",
    "toastReset": "Filters reset.",
    "toastImageOk": "Image downloaded.",
    "toastImageFail": "Could not generate the image.",
    "toastNoChart": "No chart available to export.",

    # ---- Number formatting and stats ----
    "noData": "N/A",
    "statsAccumSuffix": "cum.",
    "statsPpSuffix": "pp",

    # ---- Embedded download button ----
    "panelDownloadBtn": "Download PNG",

    # ---- Credits ----
    "footerCredit": (
        "Center for Quantitative Business Studies · Universidad de San Andrés · "
        "Data: Mercado Libre · Snapshot {snapshot}."
    ),
    "pngFooterCredit": (
        "Data: Mercado Libre · Center for Quantitative Business Studies · UdeSA · "
        "Snapshot {snapshot}"
    ),
    "snapshotPrefix": "Snapshot",

    # ---- Property display (data key → localized label) ----
    "inmuebleDisplay": {
        "Casa": "House",
        "Departamento": "Apartment",
    },

    # ---- Aglomerado display (data key → localized label) ----
    # GBA = Greater Buenos Aires. Acronym is the same in EN, only the
    # zone qualifier is translated. AMBA and CABA stay as acronyms.
    "aglomeradoDisplay": {
        "AMBA": "AMBA",
        "CABA": "CABA",
        "GBA Zona Norte": "GBA North",
        "GBA Zona Oeste": "GBA West",
        "GBA Zona Sur": "GBA South",
    },

    # ---- Metrics for the bootstrap ----
    "saleMetrics": {
        "precio": {
            "label": "Median sale price",
            "unit": "USD per m²",
            "shortUnit": "USD/m²",
            "axisLabel": "USD per m²",
        },
        "demanda": {
            "label": "Demand (contacts)",
            "unit": "Contacts index (base 2019 = 1)",
            "shortUnit": "index",
            "axisLabel": "Contacts index (2019=1)",
        },
        "oferta": {
            "label": "Supply (active listings)",
            "unit": "Active-listings index (base 2018 = 1)",
            "shortUnit": "index",
            "axisLabel": "Supply index (2018=1)",
        },
    },
    "rentMetrics": {
        "precio": {
            "label": "Median rental price",
            "unit": "ARS per m² (nominal)",
            "shortUnit": "ARS/m²",
            "axisLabel": "ARS per m² (nominal)",
        },
        "demanda": {
            "label": "Demand (contacts)",
            "unit": "Contacts index (base 2019 = 1)",
            "shortUnit": "index",
            "axisLabel": "Contacts index (2019=1)",
        },
        "oferta": {
            "label": "Supply (active listings)",
            "unit": "Active-listings index (base 2018 = 1)",
            "shortUnit": "index",
            "axisLabel": "Supply index (2018=1)",
        },
    },
}


_LANGS: dict[str, dict[str, object]] = {
    "es": LANG_ES,
    "en": LANG_EN,
}


def get_lang(code: str) -> dict[str, object]:
    """Devuelve el diccionario de strings para un código de idioma."""
    code = (code or "es").lower()
    if code not in _LANGS:
        raise ValueError(
            f"Idioma '{code}' no soportado. Opciones válidas: {sorted(_LANGS.keys())}."
        )
    return _LANGS[code]


def _assert_keys_in_sync() -> None:
    """Linter de traducción: ambos idiomas tienen exactamente las mismas claves.

    Llamado al importar el módulo. Si alguien agrega una clave en ES y se
    olvida del EN (o viceversa), el build falla con un mensaje claro en vez
    de generar un HTML con strings mezcladas en dos idiomas.
    """
    es_keys = set(LANG_ES.keys())
    en_keys = set(LANG_EN.keys())
    only_es = es_keys - en_keys
    only_en = en_keys - es_keys
    if only_es or only_en:
        raise AssertionError(
            "LANG_ES y LANG_EN están desincronizadas. "
            f"Solo en ES: {sorted(only_es)}. Solo en EN: {sorted(only_en)}."
        )
    # Sub-diccionarios anidados que también deben mantener simetría.
    for nested in ("saleMetrics", "rentMetrics", "inmuebleDisplay", "aglomeradoDisplay"):
        es_sub = set(LANG_ES[nested].keys())
        en_sub = set(LANG_EN[nested].keys())
        if es_sub != en_sub:
            raise AssertionError(
                f"Subclaves de '{nested}' desincronizadas. "
                f"Solo en ES: {sorted(es_sub - en_sub)}. "
                f"Solo en EN: {sorted(en_sub - es_sub)}."
            )


_assert_keys_in_sync()


__all__ = ["LANG_ES", "LANG_EN", "get_lang"]
