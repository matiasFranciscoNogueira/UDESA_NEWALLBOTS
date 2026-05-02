# Nowcast de Actividad Económica Argentina — Fuentes de Datos Gratuitos

Este proyecto utiliza únicamente **fuentes de datos abiertas y de alta frecuencia** para construir un indicador diario de actividad económica tipo EMAE. A continuación se listan las principales fuentes de datos, con sus respectivos enlaces de descarga o APIs para implementación.

## 📊 Fuentes de datos públicas

| Variable | Fuente | URL / API |
|---------|--------|-----------|
| **Demanda eléctrica diaria (GWh)** | CAMMESA | https://cammesaweb.cammesa.com/informe-diario-de-operacion/ (CSV descargables) |
| **Transacciones SUBE** | Datos.gob.ar | https://datos.gob.ar/dataset/transporte-transacciones-sube/archivo (CSV con frecuencia diaria) |
| **Base monetaria, tasas BCRA, CCL, MEP, MERVAL** | Estadísticas BCRA | https://estadisticasbcra.com/ (requiere clave gratuita - API JSON) |
| **Precio de la soja (CBOT)** | Stooq | https://stooq.com/q/d/?s=zs.f&c=0&d1=20240101&d2=20241231 (descarga directa de CSV histórico) |
| **EMAE mensual (INDEC)** | INDEC | https://www.indec.gob.ar/indec/web/Nivel3-Tema-3-5 (XLS/SDMX con datos históricos) |

## 🔧 Recomendaciones para desarrollo

- Ver la clase Fetchers como base y notecast_fetchers.ipynb para dev.
- Documentar cada script indicando fuente y fecha de actualización.
- Usar typing en tipos de entrada y salida de los métodos.
- Guardar datos crudos y tratados por separado.

---

Para dudas o problemas con la implementación, escribime o abrí un issue.
