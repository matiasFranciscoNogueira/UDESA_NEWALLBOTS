"""Paquete auxiliar del explorador inmobiliario multi-mercado.

Tres mercados de propiedad cubiertos:

- **buenos_aires**: AMBA + CABA (43 barrios) + GBA (30 partidos + zonas).
- **cordoba**:      Cordoba ciudad + 5 zonas + 30 barrios (con ventas).
- **rosario**:      Rosario ciudad + 4 zonas + 14 barrios (con ventas).

API publica:

- ``DatasetBundle`` — carga y serializa los 14 CSVs del pipeline R
  (descubre el snapshot mas reciente automaticamente, con warning si
  las tablas estan desincronizadas).
- ``safe_float`` — conversor robusto de strings a float (maneja NA/null).
- Submodulos: ``catalogs`` (MARKETS registry + reglas de visibilidad),
  ``metrics`` (definicion de metricas), ``i18n`` (traduccion ES/EN).
"""

from .data_store import DatasetBundle
from .utils import safe_float

__all__ = ["DatasetBundle", "safe_float"]
