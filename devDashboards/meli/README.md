# Explorador Inmobiliario · Multi-mercado

Dashboard interactivo del mercado inmobiliario argentino, cubriendo
**Buenos Aires (AMBA + CABA + GBA)**, **Córdoba** y **Rosario**.
Producido por el Centro de Estudios Cuantitativos en Negocios de la
Universidad de San Andrés, en colaboración con Mercado Libre.

**Versión:** `new_version` (multi-mercado). Reemplaza `version_final` (AMBA-only).
**Snapshot empaquetado:** `202608` (agosto 2026). Deploy en el server: ver `DEPLOY.md`.
**Idiomas:** Español (`amba_explorer.html`) e Inglés (`amba_explorer_en.html`).
**Estado:** verificado contra el dashboard anterior (646 series bit-idénticas
para Buenos Aires) y contra los informes oficiales de Córdoba y Rosario
(22/22 spot checks dentro de la precisión de los informes).

---

## Quickstart

```bash
# Sin dependencias externas: solo Python 3.10+.
cd new_version

# Opción 1 — usar el HTML pre-empaquetado
python serve.py        # abre el server local en http://localhost:8000

# Opción 2 — regenerar el HTML desde los CSVs
python build.py                # → amba_explorer.html
python build.py --lang en      # → amba_explorer_en.html
python serve.py                # luego servir
```

Para exponer públicamente via ngrok:

```bash
python serve.py             # terminal 1
ngrok http 8000             # terminal 2 — toma la URL https://...ngrok-free.app
```

---

## Estructura del proyecto

```
new_version/
├── README.md                   este archivo
├── README_EN.md                versión en inglés
├── ACTUALIZAR_DATOS.md         runbook para actualizar snapshot mensual
├── build.py                    construye el HTML autocontenido
├── serve.py                    servidor HTTP estático local
├── requirements.txt            (vacío: solo stdlib)
├── amba_explorer.html          output: ES, ~5 MB, autocontenido
├── amba_explorer_en.html       output: EN, ~5 MB, autocontenido
├── data/                       14 CSVs del pipeline R (snapshot vigente; anteriores en data/older/)
├── lib/dashboard/              paquete Python
│   ├── catalogs.py             MARKETS registry + reglas de visibilidad
│   ├── data_store.py           descubre snapshot + carga CSVs
│   ├── metrics.py              definición de métricas
│   ├── i18n.py                 strings ES + EN + linter de sincronización
│   ├── utils.py                safe_float
│   └── assets/branding/        logos UdeSA + Mercado Libre
├── source/                     frontend (template + CSS + JS)
│   ├── template.html
│   ├── explorer.css
│   └── explorer.js
└── intern/                     TODO LO NO ESENCIAL para correr o entregar
    ├── README_intern.md        qué hay acá y por qué
    ├── CHANGELOG.md            diferencias vs version_final
    ├── docs/
    │   ├── ARQUITECTURA.md     explicación detallada de Alternativa C
    │   └── DECISIONES.md       registro de decisiones de visibilidad
    ├── verification/           artefactos de QA (regenerables)
    │   ├── verify_baseline.py  compara new vs version_final
    │   ├── verify_informes.py  spot checks vs informes oficiales
    │   ├── verify_full.py      75 claims de los 3 informes 202605
    │   ├── verification_report.md
    │   └── spot_checks.md
    ├── AMBA_Informe202605.docx      informe oficial AMBA (fuente de verdad)
    ├── Cordoba_Informe202605.docx   informe oficial Córdoba
    ├── Rosario_Informe202605.docx   informe oficial Rosario
    ├── Indices_AMBA.html            informe HTML del Centro (referencia)
    └── Indices_AMBA_files/          assets del informe HTML de referencia
```

---

## Cobertura

Tres mercados, con niveles geográficos y disponibilidad heterogéneos.

### Buenos Aires
- **Aglomerado** (Nivel 1): AMBA, CABA, GBA Zona Norte / Oeste / Sur.
- **Barrio CABA**: 43 barrios.
- **Partido GBA**: 30 partidos del conurbano + Capital Federal.

### Córdoba
- **Ciudad**: Córdoba.
- **Zona**: Córdoba Centro / Este / Norte / Oeste / Sur (5 zonas).
- **Barrio**: 30 barrios de Córdoba ciudad (Venta solamente — ver
  decisión editorial abajo).

### Rosario
- **Ciudad**: Rosario.
- **Zona**: Rosario Centro / Norte / Oeste / Sur (4 zonas, sin Este).
- **Barrio**: 14 barrios de Rosario ciudad (Venta solamente — ver
  decisión editorial abajo).

### Lo que NO está expuesto (decisiones editoriales)

Estas celdas existen en los CSVs pero el dashboard NO las muestra
(documentado en `intern/docs/DECISIONES.md`):

- **Córdoba Zonas Alquiler — Casa**: solo 2 de 5 zonas tienen Casa.
- **Córdoba Barrios Alquiler**: solo 4 barrios, sin Casa.
- **Rosario Zonas Alquiler**: solo Rosario Centro tiene datos.
- **Rosario Barrios Alquiler**: solo CENTRO tiene datos.

En esas combinaciones el panel muestra un mensaje editorial explicando
por qué no hay gráfico.

### Series excluidas
- **ARGUELLO/Casa en Córdoba**: serie discontinuada en enero 2024,
  excluida del dropdown de barrios cuando se selecciona Casa.

---

## Métricas

Idénticas al dashboard anterior, alineadas con los informes del Centro:

| Lado | Métrica | Unidad | Notas |
|---|---|---|---|
| Venta | Precio mediano | USD/m² (stock + flujo cuando aplica) | No excluye el último mes |
| Venta | Demanda | Índice de contactos (base ene 2019 = 1) | Excluye último mes (parcial) + ceros iniciales |
| Venta | Oferta | Índice de publicaciones activas (base ene 2018 = 1) | Excluye último mes |
| Alquiler | Precio mediano | ARS/m² corrientes | No excluye el último mes |
| Alquiler | Demanda | Índice de contactos (base ene 2019 = 1) | Excluye último mes |
| Alquiler | Oferta | Índice de publicaciones activas (base ene 2018 = 1) | Excluye último mes |

Las bases de los índices **vienen calculadas del pipeline R**. El
dashboard no recalcula bases.

---

## Inmuebles en scope

Solo `Casa` y `Departamento`. Oficina, Local y subagregaciones por
ambientes están fuera del scope (documentado como diferimiento en
`intern/docs/DECISIONES.md`).

---

## Verificación numérica

Dos protocolos automatizados, ambos pasan al checkout:

### Buenos Aires vs version_final
- **646 series comparadas: 453 idénticas bit-a-bit + 193 con 1 punto
  adicional.** Las 193 son todas de **oferta** y crecen exactamente 1 punto
  (mayo 2026): es el fix intencional del último mes parcial documentado en
  `intern/CHANGELOG.md` (sección "Fix de oferta"). **Precio y demanda quedan
  100% bit-idénticos.** Cualquier otro tipo de mismatch = investigar antes de
  publicar.
- Reporte: `intern/verification/verification_report.md`.
- Re-ejecutar: `python intern/verification/verify_baseline.py`.

### Córdoba + Rosario vs informes oficiales
- **22 spot checks, 22 PASS** (tolerancia 0.06 pp).
- Reporte: `intern/verification/spot_checks.md`.
- Re-ejecutar: `python intern/verification/verify_informes.py`.

Los valores verificados son los citados literalmente en los informes
`Cordoba_Informe202605.docx` y `Rosario_Informe202605.docx` (mayo 2026):
variaciones intermensuales e interanuales por ciudad, zonas y barrios.

---

## Filtros disponibles

| Filtro | Opciones |
|---|---|
| Mercado | Buenos Aires · Córdoba · Rosario |
| Nivel geográfico | Aglomerado/Barrio/Partido (BA) · Ciudad/Zona/Barrio (Cba, Ros) |
| Regiones | Multi-select con buscador cuando hay más de 15 opciones |
| Tipo de propiedad | Casa · Departamento |
| Métrica | Precio mediano · Demanda · Oferta |
| Período | 12 m · 24 m · 60 m · Histórico completo |

Los dropdowns son **dinámicos**: al cambiar mercado / nivel / inmueble,
las opciones se filtran a las que tienen datos disponibles según la
matriz de visibilidad. El usuario no puede seleccionar una combinación
que el Centro no publica.

---

## Internacionalización

Dos HTMLs separados: `amba_explorer.html` (default) y `amba_explorer_en.html`.
El front consume `bootstrap.lang` para todas las strings visibles.
Identificadores de datos (claves de mercado, nivel, región, inmueble) NO
se traducen — solo el display.

Para agregar un idioma nuevo:
1. Copiar `LANG_ES` en `lib/dashboard/i18n.py`, renombrar y traducir.
2. Agregarlo a `_LANGS` y a las opciones de `--lang`.
3. El linter `_assert_keys_in_sync()` falla el build si faltan claves.

---

## Paleta institucional

- **Buenos Aires**: paleta original (azul AMBA, coral CABA, etc.).
- **Córdoba**: familia rojo-anaranjada.
- **Rosario**: familia verde-azulada.
- **Venta**: borde superior navy UdeSA (`#0F3E7D`).
- **Alquiler**: borde superior azul acero (`#4A8CC1`).

Definida en `lib/dashboard/catalogs.py` (constante `COLORS`).

---

## Actualización mensual

Ver `ACTUALIZAR_DATOS.md` para el protocolo paso a paso.

Resumen: el pipeline R del Centro genera 14 CSVs nuevos por mes con
sufijo `_YYYYMM`. Copiarlos a `data/` y correr `python build.py` para
regenerar el HTML.

---

## Documentación adicional

- `intern/docs/ARQUITECTURA.md` — arquitectura "Mercado + niveles dinámicos"
  (Alternativa C). Explica el flujo `MARKETS → availability → state machine`.
- `intern/docs/DECISIONES.md` — registro completo de decisiones editoriales con
  justificación: por qué se oculta cada celda, por qué se excluye ARGUELLO,
  por qué se difiere Oficina.
- `intern/CHANGELOG.md` — diferencias concretas vs `version_final`.

---

## Soporte

- Issues internos / preguntas: contactar al equipo del Centro de Estudios
  Cuantitativos en Negocios (UdeSA).
- Para verificación contra informes mensuales nuevos: editar la lista
  ``CASES`` en `intern/verification/verify_informes.py` con los valores
  destacados del nuevo informe y correr el script.
