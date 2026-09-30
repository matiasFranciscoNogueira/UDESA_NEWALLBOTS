"""Catalogos por mercado, paleta institucional y reglas de visibilidad.

Tres mercados de propiedad cubiertos por el dashboard:

- **buenos_aires**: AMBA agregado + CABA (43 barrios) + GBA (30 partidos)
                    + 3 zonas norte/oeste/sur.
- **cordoba**:      Cordoba ciudad + 5 zonas (Centro/Este/Norte/Oeste/Sur)
                    + 30 barrios.
- **rosario**:      Rosario ciudad + 4 zonas (Centro/Norte/Oeste/Sur — sin
                    Este, a diferencia de Cordoba) + 14 barrios.

Cada mercado declara, por nivel geografico, su tabla CSV de respaldo, la
columna que identifica a la region, y la lista de unidades disponibles.
La heterogeneidad de niveles entre mercados (Buenos Aires tiene
'aglomerado/barrio/municipio'; Cordoba y Rosario tienen 'ciudad/zona/
barrio') es intencional y se refleja en las etiquetas que ve el usuario:
cada mercado muestra su propio vocabulario.

Reglas de visibilidad
---------------------
Aunque los CSVs incluyen ciertas combinaciones, hay celdas que el cliente
decidio NO publicar como grafico en el dashboard. Documentadas en
``docs/DECISIONES.md`` con su justificacion editorial.

- ``HIDDEN_CELLS``: ``(market, level, side, inmueble)`` → clave i18n del
  mensaje que ve el usuario cuando intenta acceder a esa celda. El front
  consulta este mapa para decidir si mostrar el panel o un mensaje
  editorial.
- ``SKIP_REGIONS``: ``(market, level, side, inmueble)`` → set de regiones
  individuales a excluir del dropdown (por ejemplo, series discontinuadas).

Convencion de nombres
---------------------
Las claves de DATOS (mercado, nivel, region, inmueble) NO se traducen
nunca: son identificadores estables compartidos entre Python, JSON y JS.
Lo que se traduce a EN es el display name y vive en ``i18n.py``.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Inmuebles en scope
# ---------------------------------------------------------------------------

# Scope deliberado: solo Casa y Departamento. Los informes del Centro
# reportan ademas Oficina (en Cordoba/Rosario) y subagregaciones por
# ambientes; estan fuera del scope actual y documentados como
# diferimiento en docs/DECISIONES.md.
INMUEBLES: list[str] = ["Casa", "Departamento"]


# ---------------------------------------------------------------------------
# Paleta institucional UdeSA + colores por mercado
# ---------------------------------------------------------------------------

# Aglomerados de Buenos Aires: hereda exactamente la paleta del dashboard
# anterior (continuidad visual). Para el interior se usan familias de
# color que contrastan con la paleta de BA.
COLORS: dict[str, str] = {
    # Buenos Aires (paleta original heredada)
    "AMBA": "#1d42ff",
    "CABA": "#f26c63",
    "GBA Zona Norte": "#79ac00",
    "GBA Zona Oeste": "#18b9c8",
    "GBA Zona Sur": "#bd7cff",
    # Cordoba (familia rojo-anaranjada)
    "Cordoba": "#c54a2c",
    "Cordoba Centro": "#c54a2c",
    "Cordoba Norte": "#ee7c4f",
    "Cordoba Sur": "#9a3415",
    "Cordoba Este": "#f0a072",
    "Cordoba Oeste": "#cf6c40",
    # Rosario (familia verde-azulada)
    "Rosario": "#0a6e6b",
    "Rosario Centro": "#0a6e6b",
    "Rosario Norte": "#2a9694",
    "Rosario Sur": "#054a48",
    "Rosario Oeste": "#1b8077",
}


# ---------------------------------------------------------------------------
# Catalogos de regiones por nivel
# ---------------------------------------------------------------------------

AGLOMERADOS_BA: list[str] = [
    "AMBA",
    "CABA",
    "GBA Zona Norte",
    "GBA Zona Oeste",
    "GBA Zona Sur",
]

BARRIOS_CABA: list[str] = [
    "AGRONOMIA", "ALMAGRO", "BALVANERA", "BARRACAS", "BELGRANO", "BOEDO",
    "CABALLITO", "CHACARITA", "COLEGIALES", "CONSTITUCION", "DEVOTO",
    "FLORES", "FLORESTA", "LA BOCA", "LINIERS", "MATADEROS", "MONTE CASTRO",
    "MONTSERRAT", "NUNEZ", "PALERMO", "PARQUE AVELLANEDA",
    "PARQUE CHACABUCO", "PARQUE PATRICIOS", "PATERNAL", "PUERTO MADERO",
    "RECOLETA", "RETIRO", "SAAVEDRA", "SAN CRISTOBAL", "SAN NICOLAS",
    "SAN TELMO", "SANTA RITA", "VELEZ SARFIELD", "VERSALLES", "VILLA CRESPO",
    "VILLA DEL PARQUE", "VILLA GRAL MITRE", "VILLA LUGANO", "VILLA LURO",
    "VILLA ORTUZAR", "VILLA PUEYRREDON", "VILLA URQUIZA",
]

MUNICIPIOS_GBA: list[str] = [
    "Almirante Brown", "Avellaneda", "Berazategui", "Capital Federal",
    "Escobar", "Esteban Echeverría", "Ezeiza", "Florencio Varela",
    "General Rodríguez", "General San Martín", "Hurlingham", "Ituzaingó",
    "José C. Paz", "La Matanza", "La Plata", "Lanús", "Lomas de Zamora",
    "Malvinas Argentinas", "Merlo", "Moreno", "Morón", "Pilar",
    "Presidente Perón", "Quilmes", "San Fernando", "San Isidro",
    "San Miguel", "Tigre", "Tres de febrero", "Vicente López",
]

CIUDADES_CORDOBA: list[str] = ["Cordoba"]
ZONAS_CORDOBA: list[str] = [
    "Cordoba Centro", "Cordoba Este", "Cordoba Norte",
    "Cordoba Oeste", "Cordoba Sur",
]
BARRIOS_CORDOBA: list[str] = [
    "ALBERDI", "ALTA CORDOBA", "ALTO VERDE", "ARGUELLO", "CENTRO",
    "CERRO DE LAS ROSAS", "CHATEAU CARRERAS", "COFICO", "GENERAL PAZ",
    "GENERAL PUEYRREDON", "GRANJA DE FUNES", "GUEMES", "JARDIN",
    "JARDIN ESPINOSA", "LAS DELICIAS", "LAS ROSAS", "MANANTIALES",
    "MARQUES DE SOBREMONTE", "NUEVA CORDOBA", "OBSERVATORIO",
    "PARQUE VELEZ SARSFIELD", "POETA LUGONES", "PROVIDENCIA",
    "QUEBRADA DE LAS ROSAS", "SAN MARTIN", "URCA", "VILLA BELGRANO",
    "VILLA RIVERA INDARTE", "VILLA SERRANA", "VILLA WARCALDE",
]

CIUDADES_ROSARIO: list[str] = ["Rosario"]
ZONAS_ROSARIO: list[str] = [
    "Rosario Centro", "Rosario Norte", "Rosario Oeste", "Rosario Sur",
]
BARRIOS_ROSARIO: list[str] = [
    "ABASTO", "ALBERDI", "ALVEAR", "BELGRANO", "CENTRO", "FISHERTON",
    "FUNES", "GRANADERO BAIGORRIA", "IBARLUCEA", "LISANDRO DE LA TORRE",
    "MARTIN", "PUEBLO ESTHER", "PUERTO NORTE", "REMEDIOS DE ESCALADA",
]


# ---------------------------------------------------------------------------
# Mapeo de campos por tabla
# ---------------------------------------------------------------------------
#
# Disponibilidad de campos por tabla:
#
#   Tabla                              | precio_stock        | precio_flujo        | precio_corrientes (rent)
#   sale/rent group, muni, barrios int | "Mediana Stock"     | "Mediana Flujo"     | "Mediana por m2 a precios corrientes"
#   sale CABA <= 202606 (make.names)   | "Mediana.Stock"     | (no existe)         | n/a (rent CABA usa el estandar)
#   sale CABA >= 202608 (estandar)     | "Mediana Stock"     | "Mediana Flujo"*    | n/a
#   rent CABA                          | n/a                 | n/a                 | "Mediana por m2 a precios corrientes"
#
#   * existe en el CSV pero no se consume: el front fija universo "stock".
#
# Alias: un valor puede ser un string o una TUPLA de nombres de columna en
# orden de preferencia. ``build._resolve_field`` usa el primero que exista
# en la tabla. Sirve para tolerar renames del pipeline R sin tocar codigo
# (VentasCABA paso de ``Mediana.Stock`` a ``Mediana Stock`` en 202608).

_SALE_FIELDS_STD: dict[str, str] = {
    "precio_stock": "Mediana Stock",
    "precio_flujo": "Mediana Flujo",
    "demanda": "Contactos",
    "oferta": "Oferta",
}

_SALE_FIELDS_CABA: dict[str, str | tuple[str, ...]] = {
    "precio_stock": ("Mediana Stock", "Mediana.Stock"),  # alias: formato nuevo | viejo
    "demanda": "Contactos",
    "oferta": "Oferta",
}

_RENT_FIELDS_STD: dict[str, str] = {
    "precio_corrientes": "Mediana por m2 a precios corrientes",
    "demanda": "Contactos",
    "oferta": "Oferta",
}


# ---------------------------------------------------------------------------
# Registry MARKETS
# ---------------------------------------------------------------------------
#
# Forma:
#   MARKETS[market_key] = {
#       "label_key":        str,                  # clave i18n para mostrar el mercado
#       "default_level":    str,                  # nivel activo al cargar este mercado
#       "levels": {
#           level_key: {
#               "label_key":        str,          # clave i18n del nivel
#               "region_label_key": str,          # clave i18n para "Aglomerado"/"Barrio"/etc
#               "sale_table":       str,          # nombre logico en TABLE_SPECS
#               "rent_table":       str,
#               "region_field":     str,          # columna del CSV con la region
#               "regions":          list[str],    # regiones expuestas a nivel datos
#               "sale_fields":      dict,
#               "rent_fields":      dict,
#               "default_regions":  list[str],    # seleccion inicial al activar el nivel
#           }, ...
#       },
#   }
#
# Las tablas estan SIEMPRE pobladas (existen los CSVs). La decision de
# ocultar una celda al usuario se maneja en HIDDEN_CELLS (mas abajo),
# no en este registry.

MARKETS: dict[str, dict] = {
    "buenos_aires": {
        "label_key": "marketBuenosAires",
        "default_level": "aglomerado",
        "levels": {
            "aglomerado": {
                "label_key": "levelAglomeradoBA",
                "region_label_key": "regionAglomerado",
                "sale_table": "sale_group_ba",
                "rent_table": "rent_group_ba",
                "region_field": "Aglomerado",
                "regions": AGLOMERADOS_BA,
                "sale_fields": _SALE_FIELDS_STD,
                "rent_fields": _RENT_FIELDS_STD,
                "default_regions": ["AMBA", "CABA"],
            },
            "barrio": {
                "label_key": "levelBarrioCABA",
                "region_label_key": "regionBarrioCABA",
                "sale_table": "sale_caba",
                "rent_table": "rent_caba",
                "region_field": "Barrio",
                "regions": BARRIOS_CABA,
                "sale_fields": _SALE_FIELDS_CABA,
                "rent_fields": _RENT_FIELDS_STD,
                "default_regions": ["PALERMO", "RECOLETA"],
            },
            "municipio": {
                "label_key": "levelMunicipioGBA",
                "region_label_key": "regionMunicipio",
                "sale_table": "sale_muni_ba",
                "rent_table": "rent_muni_ba",
                "region_field": "Municipio",
                "regions": MUNICIPIOS_GBA,
                "sale_fields": _SALE_FIELDS_STD,
                "rent_fields": _RENT_FIELDS_STD,
                "default_regions": ["Tigre", "Vicente López"],
            },
        },
    },
    "cordoba": {
        "label_key": "marketCordoba",
        "default_level": "ciudad",
        "levels": {
            "ciudad": {
                "label_key": "levelCiudadCordoba",
                "region_label_key": "regionCiudad",
                "sale_table": "sale_muni_interior",
                "rent_table": "rent_muni_interior",
                "region_field": "Municipio",
                "regions": CIUDADES_CORDOBA,
                "sale_fields": _SALE_FIELDS_STD,
                "rent_fields": _RENT_FIELDS_STD,
                "default_regions": ["Cordoba"],
            },
            "zona": {
                "label_key": "levelZonaCordoba",
                "region_label_key": "regionZona",
                "sale_table": "sale_group_interior",
                "rent_table": "rent_group_interior",
                "region_field": "Aglomerado",
                "regions": ZONAS_CORDOBA,
                "sale_fields": _SALE_FIELDS_STD,
                "rent_fields": _RENT_FIELDS_STD,
                "default_regions": ["Cordoba Centro", "Cordoba Norte"],
            },
            "barrio": {
                "label_key": "levelBarrioCordoba",
                "region_label_key": "regionBarrioCordoba",
                "sale_table": "sale_cordoba",
                "rent_table": "rent_cordoba",
                "region_field": "Barrio",
                "regions": BARRIOS_CORDOBA,
                "sale_fields": _SALE_FIELDS_STD,
                "rent_fields": _RENT_FIELDS_STD,
                "default_regions": ["NUEVA CORDOBA", "CENTRO"],
            },
        },
    },
    "rosario": {
        "label_key": "marketRosario",
        "default_level": "ciudad",
        "levels": {
            "ciudad": {
                "label_key": "levelCiudadRosario",
                "region_label_key": "regionCiudad",
                "sale_table": "sale_muni_interior",
                "rent_table": "rent_muni_interior",
                "region_field": "Municipio",
                "regions": CIUDADES_ROSARIO,
                "sale_fields": _SALE_FIELDS_STD,
                "rent_fields": _RENT_FIELDS_STD,
                "default_regions": ["Rosario"],
            },
            "zona": {
                "label_key": "levelZonaRosario",
                "region_label_key": "regionZona",
                "sale_table": "sale_group_interior",
                "rent_table": "rent_group_interior",
                "region_field": "Aglomerado",
                "regions": ZONAS_ROSARIO,
                "sale_fields": _SALE_FIELDS_STD,
                "rent_fields": _RENT_FIELDS_STD,
                "default_regions": ["Rosario Centro", "Rosario Norte"],
            },
            "barrio": {
                "label_key": "levelBarrioRosario",
                "region_label_key": "regionBarrioRosario",
                "sale_table": "sale_rosario",
                "rent_table": "rent_rosario",
                "region_field": "Barrio",
                "regions": BARRIOS_ROSARIO,
                "sale_fields": _SALE_FIELDS_STD,
                "rent_fields": _RENT_FIELDS_STD,
                "default_regions": ["CENTRO", "FUNES"],
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Reglas de visibilidad (decisiones editoriales del cliente)
# ---------------------------------------------------------------------------
#
# ``HIDDEN_CELLS``: ``(market, level, side, inmueble)`` → clave i18n del
# mensaje editorial que se muestra al usuario cuando la celda esta oculta.
# Es la decision de negocio aplicada sobre los datos disponibles.
#
# El front-end recibe ``hiddenReason`` dentro del bootstrap y muestra el
# mensaje correspondiente cuando una combinacion queda oculta. Los datos
# de esas celdas NO se incluyen en el bootstrap (ahorro de bytes y
# consistencia con la decision editorial).

HIDDEN_CELLS: dict[tuple[str, str, str, str], str] = {
    # Cordoba Zonas Alquiler — Casa: solo 2 de 5 zonas tienen Casa-Alquiler;
    # el informe del Centro no la desagrega por zona. Decision: ocultar
    # Casa (mantener Departamento que cubre 4 de 5 zonas).
    ("cordoba", "zona", "rent", "Casa"): "emptyRentHiddenCordobaZonaCasa",
    # Cordoba Barrios Alquiler — Casa y Depto: solo 4 barrios, sin Casa;
    # bajo politica del cliente ("no exponer barrios con cobertura pobre").
    ("cordoba", "barrio", "rent", "Casa"): "emptyRentHiddenCordobaBarrio",
    ("cordoba", "barrio", "rent", "Departamento"): "emptyRentHiddenCordobaBarrio",
    # Rosario Zonas Alquiler — Casa y Depto: solo Rosario Centro existe,
    # redundante con el nivel ciudad.
    ("rosario", "zona", "rent", "Casa"): "emptyRentHiddenRosarioZona",
    ("rosario", "zona", "rent", "Departamento"): "emptyRentHiddenRosarioZona",
    # Rosario Barrios Alquiler — Casa y Depto: solo CENTRO, duplica el
    # nivel ciudad sin agregar valor.
    ("rosario", "barrio", "rent", "Casa"): "emptyRentHiddenRosarioBarrio",
    ("rosario", "barrio", "rent", "Departamento"): "emptyRentHiddenRosarioBarrio",
}


# ``SKIP_REGIONS``: regiones individuales excluidas dentro de una celda
# (market, level, side, inmueble) → set de regiones a saltar.
SKIP_REGIONS: dict[tuple[str, str, str, str], set[str]] = {
    # ARGUELLO/Casa en Cordoba: la serie esta discontinuada (ultimo mes
    # 2024-01). Excluirla del dropdown para no dejar al usuario con una
    # serie que termina abruptamente sin explicacion.
    ("cordoba", "barrio", "sale", "Casa"): {"ARGUELLO"},
}


# ---------------------------------------------------------------------------
# Helpers expuestos al build
# ---------------------------------------------------------------------------

def cell_hidden_reason(market: str, level: str, side: str, inmueble: str) -> str | None:
    """Devuelve la clave i18n del mensaje editorial si la celda esta oculta.

    Devuelve ``None`` si la celda es visible.
    """
    return HIDDEN_CELLS.get((market, level, side, inmueble))


def skip_region(market: str, level: str, side: str, inmueble: str, region: str) -> bool:
    """Devuelve True si la region puntual debe excluirse del dropdown / datos."""
    return region in SKIP_REGIONS.get((market, level, side, inmueble), set())


__all__ = [
    "INMUEBLES",
    "COLORS",
    "AGLOMERADOS_BA",
    "BARRIOS_CABA",
    "MUNICIPIOS_GBA",
    "CIUDADES_CORDOBA",
    "ZONAS_CORDOBA",
    "BARRIOS_CORDOBA",
    "CIUDADES_ROSARIO",
    "ZONAS_ROSARIO",
    "BARRIOS_ROSARIO",
    "MARKETS",
    "HIDDEN_CELLS",
    "SKIP_REGIONS",
    "cell_hidden_reason",
    "skip_region",
]
