"""Strings de UI por idioma y constructor del paquete de traduccion.

Dos diccionarios planos con las MISMAS claves: ``LANG_ES`` y ``LANG_EN``.
El front-end (``explorer.js``) consume ``bootstrap.lang`` y reemplaza
cada string hardcodeado por su clave correspondiente.

Reglas
------
- Toda string visible al usuario vive aca. Si necesitas agregar una
  nueva, ponela en AMBOS diccionarios.
- ``_assert_keys_in_sync()`` se ejecuta al importar el modulo: si las
  claves se desincronizan el build falla con un mensaje claro en lugar
  de generar un HTML con strings mezcladas.
- Los identificadores de DATOS (nombres de mercados, niveles, regiones)
  NO se traducen — son ``proper nouns`` para Python/JSON/JS.
- Lo que SI se traduce: el display de Casa/Departamento, los aglomerados
  con calificadores de zona (``GBA Zona Norte`` → ``GBA North``), las
  zonas de Cordoba/Rosario (``Cordoba Centro`` → ``Cordoba Center``), y
  los labels de mercado / nivel / region label.
- El locale (``es-AR``, ``en-US``) define como el front formatea numeros:
  ``1.234,56`` en castellano vs ``1,234.56`` en ingles.

Sub-diccionarios auditados por el linter
----------------------------------------
``saleMetrics``, ``rentMetrics``, ``inmuebleDisplay``, ``regionDisplay``,
``marketDisplay`` — todos deben tener las mismas claves en ES y EN.
"""

from __future__ import annotations


LANG_ES: dict[str, object] = {
    # ---- Metadata de pagina ----
    "locale": "es-AR",
    "htmlLang": "es",
    "title": "Explorador Inmobiliario · Mercado Libre · UdeSA",
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

    # ---- Mercado (selector de Nivel 1) ----
    "marketLabel": "Mercado",

    # ---- Niveles geograficos (label del dropdown de nivel) ----
    "levelLabel": "Nivel geográfico",
    # Buenos Aires
    "levelAglomeradoBA": "Aglomerado",
    "levelBarrioCABA": "Barrio (CABA)",
    "levelMunicipioGBA": "Partido (GBA)",
    # Cordoba
    "levelCiudadCordoba": "Ciudad",
    "levelZonaCordoba": "Zona",
    "levelBarrioCordoba": "Barrio",
    # Rosario
    "levelCiudadRosario": "Ciudad",
    "levelZonaRosario": "Zona",
    "levelBarrioRosario": "Barrio",

    # ---- Label de la columna "region" en el dropdown (en singular) ----
    "regionAglomerado": "Aglomerado",
    "regionBarrioCABA": "Barrio",
    "regionMunicipio": "Partido",
    "regionCiudad": "Ciudad",
    "regionZona": "Zona",
    "regionBarrioCordoba": "Barrio",
    "regionBarrioRosario": "Barrio",

    # ---- Inmueble y metrica ----
    "inmuebleLabel": "Tipo de propiedad",
    "metricLabel": "Métrica",
    "metricPrecio": "Precio mediano por m²",
    "metricDemanda": "Demanda (contactos)",
    "metricOferta": "Oferta (publicaciones activas)",

    # ---- Chips de periodo ----
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
    "searchAriaPrefix": "Buscar en",
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

    # ---- Titulo y subtitulo del panel ----
    "titleSeparator": "·",
    "titleBarriosCABA": "Barrios CABA",
    "titleMunicipiosGBA": "Partidos GBA",
    # Plantillas para mercados del interior: ``{market}`` se reemplaza
    # con el display del mercado (Cordoba / Rosario, con acento).
    "titleMarketCiudad": "{market}",
    "titleMarketZonas": "Zonas de {market}",
    "titleMarketBarrios": "Barrios de {market}",
    "subtitleOfertaSuffix": "Serie normalizada como índice, base enero 2018 = 1.",
    "subtitleDemandaSuffix": (
        "Serie normalizada como índice, base enero 2019 = 1. "
        "El último mes disponible se excluye por estar incompleto."
    ),

    # ---- Empty / blocked states ----
    "emptyBlockedTitle": "Esta combinación no tiene datos disponibles.",
    "emptyWidenPeriod": "Probá ampliar el período o activar más regiones en la leyenda.",
    "emptyChangeCombo": "Probá con otra combinación de mercado, nivel, tipo de propiedad o métrica.",
    "emptyNoPrecio": (
        "No hay datos de precio disponibles para esta combinación. "
        "Probá con otra región o tipo de propiedad."
    ),
    # Mensajes especificos cuando el lado quedo oculto por politica editorial.
    "emptyRentHiddenCordobaBarrio": (
        "Por cobertura limitada, no se muestra alquiler por barrio en Córdoba. "
        "Probá con Ciudad o Zona, o cambiá a Venta."
    ),
    "emptyRentHiddenCordobaZonaCasa": (
        "Por datos insuficientes, no se muestra alquiler de Casa por zona en Córdoba "
        "(solo 2 de 5 zonas tienen cobertura). Probá con Departamento."
    ),
    "emptyRentHiddenRosarioZona": (
        "Por datos insuficientes, no se muestra alquiler por zona en Rosario "
        "(solo Rosario Centro tiene cobertura, equivalente al nivel Ciudad). "
        "Probá con Ciudad o cambiá a Venta."
    ),
    "emptyRentHiddenRosarioBarrio": (
        "Por datos insuficientes, no se muestra alquiler por barrio en Rosario "
        "(solo el barrio CENTRO tiene cobertura). Probá con Ciudad o cambiá a Venta."
    ),

    # ---- Toasts ----
    "toastKeepOnePrefix": "Mantenemos al menos un",
    "toastSelectOnePrefix": "Seleccioná al menos un",
    "toastReset": "Filtros restablecidos.",
    "toastImageOk": "Imagen descargada.",
    "toastImageFail": "No se pudo generar la imagen.",
    "toastNoChart": "No hay gráfico para exportar.",
    "toastMarketReset": "Filtros actualizados al cambiar de mercado.",

    # ---- Formato numerico y stats ----
    "noData": "N/D",
    "statsAccumSuffix": "acum.",
    "statsPpSuffix": "pp",

    # ---- Boton de descarga embebido ----
    "panelDownloadBtn": "Descargar PNG",

    # ---- Creditos ----
    "footerCredit": (
        "Centro de Estudios Cuantitativos en Negocios · Universidad de San Andrés · "
        "Datos: Mercado Libre · Mes de referencia: {snapshot}."
    ),
    "pngFooterCredit": (
        "Datos: Mercado Libre · Centro de Estudios Cuantitativos en Negocios · UdeSA · "
        "Mes de referencia: {snapshot}"
    ),
    "snapshotPrefix": "Mes de referencia",

    # ---- Display de inmuebles (data key → label localizado) ----
    "inmuebleDisplay": {
        "Casa": "Casa",
        "Departamento": "Departamento",
    },

    # ---- Display de mercados (data key → label localizado) ----
    "marketDisplay": {
        "buenos_aires": "Buenos Aires",
        "cordoba": "Córdoba",
        "rosario": "Rosario",
    },

    # ---- Display de regiones (data key → label localizado) ----
    # Esta es la fuente unificada de traduccion. Cualquier nombre cuya
    # version visible difiera del data key debe entrar aca. Barrios CABA,
    # municipios AMBA y barrios Cordoba/Rosario no se traducen (proper nouns
    # mayusculas) — el front cae al data key si no esta listada.
    "regionDisplay": {
        # Aglomerados Buenos Aires
        "AMBA": "AMBA",
        "CABA": "CABA",
        "GBA Zona Norte": "GBA Zona Norte",
        "GBA Zona Oeste": "GBA Zona Oeste",
        "GBA Zona Sur": "GBA Zona Sur",
        # Ciudades y zonas del interior (acentuamos en ES para display)
        "Cordoba": "Córdoba",
        "Cordoba Centro": "Córdoba Centro",
        "Cordoba Este": "Córdoba Este",
        "Cordoba Norte": "Córdoba Norte",
        "Cordoba Oeste": "Córdoba Oeste",
        "Cordoba Sur": "Córdoba Sur",
        "Rosario": "Rosario",
        "Rosario Centro": "Rosario Centro",
        "Rosario Norte": "Rosario Norte",
        "Rosario Oeste": "Rosario Oeste",
        "Rosario Sur": "Rosario Sur",
    },

    # ---- Metricas para el bootstrap (label/unit/shortUnit/axisLabel) ----
    "saleMetrics": {
        "precio": {
            "label": "Precio mediano de venta",
            "unit": "USD por m²",
            "shortUnit": "USD/m²",
            "axisLabel": "USD por m²",
        },
        "demanda": {
            "label": "Demanda (contactos)",
            "unit": "Índice de contactos",
            "shortUnit": "índice",
            "axisLabel": "Índice de contactos (2019=1)",
        },
        "oferta": {
            "label": "Oferta (publicaciones activas)",
            "unit": "Índice de publicaciones activas",
            "shortUnit": "índice",
            "axisLabel": "Índice de oferta (2018=1)",
        },
    },
    "rentMetrics": {
        "precio": {
            "label": "Precio mediano de alquiler",
            "unit": "ARS por m² (corrientes)",
            "shortUnit": "ARS/m²",
            "axisLabel": "ARS por m² (corrientes)",
        },
        "demanda": {
            "label": "Demanda (contactos)",
            "unit": "Índice de contactos",
            "shortUnit": "índice",
            "axisLabel": "Índice de contactos (2019=1)",
        },
        "oferta": {
            "label": "Oferta (publicaciones activas)",
            "unit": "Índice de publicaciones activas",
            "shortUnit": "índice",
            "axisLabel": "Índice de oferta (2018=1)",
        },
    },
}


LANG_EN: dict[str, object] = {
    # ---- Page metadata ----
    "locale": "en-US",
    "htmlLang": "en",
    "title": "Real Estate Explorer · Mercado Libre · UdeSA",
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

    # ---- Market (Level-1 selector) ----
    "marketLabel": "Market",

    # ---- Geographic levels ----
    "levelLabel": "Geographic level",
    # Buenos Aires
    "levelAglomeradoBA": "Region",
    "levelBarrioCABA": "Neighborhood (CABA)",
    "levelMunicipioGBA": "District (GBA)",
    # Cordoba
    "levelCiudadCordoba": "City",
    "levelZonaCordoba": "Zone",
    "levelBarrioCordoba": "Neighborhood",
    # Rosario
    "levelCiudadRosario": "City",
    "levelZonaRosario": "Zone",
    "levelBarrioRosario": "Neighborhood",

    # ---- Region label (singular) ----
    "regionAglomerado": "Region",
    "regionBarrioCABA": "Neighborhood",
    "regionMunicipio": "District",
    "regionCiudad": "City",
    "regionZona": "Zone",
    "regionBarrioCordoba": "Neighborhood",
    "regionBarrioRosario": "Neighborhood",

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
    "titleBarriosCABA": "CABA neighborhoods",
    "titleMunicipiosGBA": "GBA districts",
    "titleMarketCiudad": "{market}",
    "titleMarketZonas": "{market} zones",
    "titleMarketBarrios": "{market} neighborhoods",
    "subtitleOfertaSuffix": "Series normalized as an index, base January 2018 = 1.",
    "subtitleDemandaSuffix": (
        "Series normalized as an index, base January 2019 = 1. "
        "The last snapshot month is excluded as it is partial."
    ),

    # ---- Empty / blocked states ----
    "emptyBlockedTitle": "This combination has no data available.",
    "emptyWidenPeriod": "Try widening the period or activating more regions in the legend.",
    "emptyChangeCombo": "Try a different combination of market, level, property type, or metric.",
    "emptyNoPrecio": (
        "No price data available for this combination. "
        "Try another region or property type."
    ),
    "emptyRentHiddenCordobaBarrio": (
        "Rental data by neighborhood is not available for Córdoba due to limited coverage. "
        "Try City or Zone, or switch to Sales."
    ),
    "emptyRentHiddenCordobaZonaCasa": (
        "House rental data by zone is not available for Córdoba due to insufficient coverage "
        "(only 2 of 5 zones available). Try Apartment."
    ),
    "emptyRentHiddenRosarioZona": (
        "Rental data by zone is not available for Rosario due to insufficient coverage "
        "(only Rosario Center available, equivalent to the City level). "
        "Try City or switch to Sales."
    ),
    "emptyRentHiddenRosarioBarrio": (
        "Rental data by neighborhood is not available for Rosario due to insufficient coverage "
        "(only the CENTRO neighborhood available). Try City or switch to Sales."
    ),

    # ---- Toasts ----
    "toastKeepOnePrefix": "We keep at least one",
    "toastSelectOnePrefix": "Please select at least one",
    "toastReset": "Filters reset.",
    "toastImageOk": "Image downloaded.",
    "toastImageFail": "Could not generate the image.",
    "toastNoChart": "No chart available to export.",
    "toastMarketReset": "Market changed: filters refreshed.",

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

    # ---- Market display ----
    "marketDisplay": {
        "buenos_aires": "Buenos Aires",
        "cordoba": "Córdoba",
        "rosario": "Rosario",
    },

    # ---- Region display ----
    # GBA = Greater Buenos Aires. Acronym keeps in EN; only the zone
    # qualifier is translated. AMBA and CABA stay as acronyms.
    "regionDisplay": {
        # Aglomerados Buenos Aires
        "AMBA": "AMBA",
        "CABA": "CABA",
        "GBA Zona Norte": "GBA North",
        "GBA Zona Oeste": "GBA West",
        "GBA Zona Sur": "GBA South",
        # Interior cities + zones
        "Cordoba": "Córdoba",
        "Cordoba Centro": "Córdoba Center",
        "Cordoba Este": "Córdoba East",
        "Cordoba Norte": "Córdoba North",
        "Cordoba Oeste": "Córdoba West",
        "Cordoba Sur": "Córdoba South",
        "Rosario": "Rosario",
        "Rosario Centro": "Rosario Center",
        "Rosario Norte": "Rosario North",
        "Rosario Oeste": "Rosario West",
        "Rosario Sur": "Rosario South",
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
            "unit": "Contacts index",
            "shortUnit": "index",
            "axisLabel": "Contacts index (2019=1)",
        },
        "oferta": {
            "label": "Supply (active listings)",
            "unit": "Active-listings index",
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
            "unit": "Contacts index",
            "shortUnit": "index",
            "axisLabel": "Contacts index (2019=1)",
        },
        "oferta": {
            "label": "Supply (active listings)",
            "unit": "Active-listings index",
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
    """Devuelve el diccionario de strings para un codigo de idioma."""
    code = (code or "es").lower()
    if code not in _LANGS:
        raise ValueError(
            f"Idioma '{code}' no soportado. Opciones validas: {sorted(_LANGS.keys())}."
        )
    return _LANGS[code]


def _assert_keys_in_sync() -> None:
    """Linter de traduccion: ambos idiomas tienen exactamente las mismas claves.

    Llamado al importar el modulo. Cubre el nivel raiz y todos los
    sub-diccionarios auditados.
    """
    es_keys = set(LANG_ES.keys())
    en_keys = set(LANG_EN.keys())
    only_es = es_keys - en_keys
    only_en = en_keys - es_keys
    if only_es or only_en:
        raise AssertionError(
            "LANG_ES y LANG_EN estan desincronizadas. "
            f"Solo en ES: {sorted(only_es)}. Solo en EN: {sorted(only_en)}."
        )
    # Sub-diccionarios anidados auditados.
    for nested in ("saleMetrics", "rentMetrics", "inmuebleDisplay",
                   "marketDisplay", "regionDisplay"):
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
