"""Catálogos geográficos, paleta institucional y mapeo CSV→nivel.

Este módulo concentra todo lo que es "data del dominio" (qué aglomerados
existen, qué barrios cubre CABA, qué color usar para AMBA) separado de
la lógica de build. Si el Centro agrega un barrio o cambia un nombre, se
toca un solo archivo.

Los nombres de aglomerados, barrios, municipios e inmuebles son
**identificadores de datos** — coinciden con los valores en los CSVs
publicados por el pipeline R. NO se traducen al inglés acá; la traducción
del display name vive en `i18n.py` (ver `inmuebleDisplay`).
"""

from __future__ import annotations


# Aglomerados expuestos al usuario. AMBA = agregado regional.
AGLOMERADOS: list[str] = [
    "AMBA",
    "CABA",
    "GBA Zona Norte",
    "GBA Zona Oeste",
    "GBA Zona Sur",
]

# Barrios CABA (42, alfabético). Lista cerrada y validada contra el snapshot
# en runtime: si un barrio no aparece en los CSVs, se omite silenciosamente.
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

# Municipios del AMBA (30). Incluye Capital Federal como el agregado del partido.
MUNICIPIOS_GBA: list[str] = [
    "Almirante Brown", "Avellaneda", "Berazategui", "Capital Federal",
    "Escobar", "Esteban Echeverría", "Ezeiza", "Florencio Varela",
    "General Rodríguez", "General San Martín", "Hurlingham", "Ituzaingó",
    "José C. Paz", "La Matanza", "La Plata", "Lanús", "Lomas de Zamora",
    "Malvinas Argentinas", "Merlo", "Moreno", "Morón", "Pilar",
    "Presidente Perón", "Quilmes", "San Fernando", "San Isidro",
    "San Miguel", "Tigre", "Tres de febrero", "Vicente López",
]

# Solo Casa y Departamento (sin Oficina ni otras agrupaciones).
# Scope deliberado: la referencia del Centro (Indices_AMBA.html) cubre
# Oficina además de Casa/Depto, pero el dashboard la omite porque no aporta
# valor explicativo para el público general. Documentado como scope.
INMUEBLES: list[str] = ["Casa", "Departamento"]

# Paleta institucional UdeSA + colores del dashboard publicado. Solo se aplica
# a aglomerados. Para barrios y municipios la paleta se genera en runtime
# (HSL equiespaciado) — ver explorer.js.
COLORS: dict[str, str] = {
    "AMBA": "#1d42ff",
    "CABA": "#f26c63",
    "GBA Zona Norte": "#79ac00",
    "GBA Zona Oeste": "#18b9c8",
    "GBA Zona Sur": "#bd7cff",
}


# ---------------------------------------------------------------------------
# Mapeo nivel → tabla CSV → nombres de columna
# ---------------------------------------------------------------------------
#
# Tres niveles geográficos, con disponibilidad de columnas distinta:
#
#   Nivel        | sale.precio.stock | sale.precio.flujo | sale.demanda/oferta | rent.precio | rent.demanda/oferta
#   aglomerado   |   Mediana Stock   |   Mediana Flujo   |  Contactos/Oferta   |  Mediana por m2 corrientes | Contactos/Oferta
#   barrio CABA  |   Mediana.Stock   |   (no existe)     |  Contactos/Oferta   |  Mediana por m2 corrientes | Contactos/Oferta
#   municipio    |   Mediana Stock   |   Mediana Flujo   |  Contactos/Oferta   |  Mediana por m2 corrientes | Contactos/Oferta
#
# Ojo: R write.csv reemplaza espacios por puntos en encabezados. VentasCABA
# arrastra ese trato porque se exporta con un workflow distinto.

LEVELS: dict[str, dict] = {
    "aglomerado": {
        "sale_table": "sale_group",
        "rent_table": "rent_group",
        "region_field": "Aglomerado",
        "regions": AGLOMERADOS,
        "sale": {
            "precio_stock": "Mediana Stock",
            "precio_flujo": "Mediana Flujo",
            "demanda": "Contactos",
            "oferta": "Oferta",
        },
        "rent": {
            "precio_corrientes": "Mediana por m2 a precios corrientes",
            "demanda": "Contactos",
            "oferta": "Oferta",
        },
    },
    "barrio": {
        "sale_table": "sale_caba",
        "rent_table": "rent_caba",
        "region_field": "Barrio",
        "regions": BARRIOS_CABA,
        "sale": {
            "precio_stock": "Mediana.Stock",   # write.csv R → punto
            # No hay Mediana.Flujo en VentasCABA.
            "demanda": "Contactos",
            "oferta": "Oferta",
        },
        "rent": {
            "precio_corrientes": "Mediana por m2 a precios corrientes",
            "demanda": "Contactos",
            "oferta": "Oferta",
        },
    },
    "municipio": {
        "sale_table": "sale_muni",
        "rent_table": "rent_muni",
        "region_field": "Municipio",
        "regions": MUNICIPIOS_GBA,
        "sale": {
            "precio_stock": "Mediana Stock",
            "precio_flujo": "Mediana Flujo",
            "demanda": "Contactos",
            "oferta": "Oferta",
        },
        "rent": {
            "precio_corrientes": "Mediana por m2 a precios corrientes",
            "demanda": "Contactos",
            "oferta": "Oferta",
        },
    },
}


REGIONS_BY_LEVEL: dict[str, list[str]] = {
    "aglomerado": AGLOMERADOS,
    "barrio": BARRIOS_CABA,
    "municipio": MUNICIPIOS_GBA,
}


__all__ = [
    "AGLOMERADOS",
    "BARRIOS_CABA",
    "MUNICIPIOS_GBA",
    "INMUEBLES",
    "COLORS",
    "LEVELS",
    "REGIONS_BY_LEVEL",
]
