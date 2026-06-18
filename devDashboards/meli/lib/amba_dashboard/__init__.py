"""Paquete auxiliar del explorador AMBA.

Expone:

- `DatasetBundle` — carga y serializa los CSVs del pipeline R (descubre
  el snapshot más reciente automáticamente).
- `safe_float` — conversor robusto de strings → float (maneja NA/null).
- `catalogs`, `metrics`, `i18n` — submódulos de configuración del
  dashboard (catálogos geográficos, definición de métricas, traducción).

NO incluye `published_content` ni `render` (eran del dashboard Quarto
original; quedaron archivados en `intern/legacy_code/` del proyecto).
"""

from .data_store import DatasetBundle
from .utils import safe_float

__all__ = ["DatasetBundle", "safe_float"]
