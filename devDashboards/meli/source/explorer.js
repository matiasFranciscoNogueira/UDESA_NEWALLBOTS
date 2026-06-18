(function () {
  'use strict';

  const bootstrap = window.EXPLORER_BOOTSTRAP || {};
  const app = document.getElementById('app');
  const lang = bootstrap.lang || {};
  if (!app || !bootstrap || !bootstrap.data) {
    if (app) {
      const msg = lang.bootError || 'The explorer could not be initialized.';
      app.innerHTML = `<div class="boot-shell"><p>${msg}</p></div>`;
    }
    return;
  }

  const {
    data,
    saleMetrics,
    rentMetrics,
    regions,
    inmuebles,
    colors,
    snapshotId,
    logos,
  } = bootstrap;

  // ===============================================================
  // Helpers de idioma
  // ===============================================================

  // Display localizado del inmueble: state.inmueble guarda la clave de
  // datos ("Casa"/"Departamento"), todo lo que se muestra al usuario
  // pasa por esta función.
  function inmuebleDisplay(key) {
    const map = lang.inmuebleDisplay || {};
    return map[key] || key;
  }

  // Display localizado de una región. Solo los aglomerados tienen un mapa
  // de traducción (GBA Zona Norte → GBA North, etc.). Para barrios CABA y
  // municipios — que son nombres propios — la función devuelve el data key
  // sin cambio. La data del bootstrap sigue indexada por la clave original.
  function regionDisplay(key) {
    const map = lang.aglomeradoDisplay || {};
    return map[key] || key;
  }

  function pluralInmueble(v) {
    return v + (v.endsWith('s') ? '' : 's');
  }

  // ===============================================================
  // Niveles geográficos
  // ===============================================================

  const LEVEL_OPTIONS = [
    { value: 'aglomerado', label: lang.levelAglomerado || 'Aglomerado' },
    { value: 'barrio', label: lang.levelBarrio || 'Barrio (CABA)' },
    { value: 'municipio', label: lang.levelMunicipio || 'Municipio (AMBA)' },
  ];

  // Etiqueta del dropdown de regiones según el nivel activo.
  const REGION_LABEL = {
    aglomerado: lang.regionAglomerado || 'Aglomerado',
    barrio: lang.regionBarrio || 'Barrio',
    municipio: lang.regionMunicipio || 'Municipio',
  };

  // Selección por defecto al cambiar de nivel. Tiene que existir en el dataset.
  const DEFAULT_SELECTION = {
    aglomerado: ['AMBA', 'CABA'],
    barrio: ['PALERMO', 'RECOLETA'],
    municipio: ['Tigre', 'Vicente López'],
  };

  // ===============================================================
  // Helpers de formato
  // ===============================================================

  const locale = lang.locale || 'es-AR';
  const nfInt = new Intl.NumberFormat(locale, { maximumFractionDigits: 0 });
  const nf1 = new Intl.NumberFormat(locale, { maximumFractionDigits: 1, minimumFractionDigits: 1 });
  const nf2 = new Intl.NumberFormat(locale, { maximumFractionDigits: 2, minimumFractionDigits: 2 });

  const MONTHS_LONG = lang.monthsLong || [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
  ];
  const MONTHS_SHORT = lang.monthsShort || [
    'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
  ];
  const MONTH_CONNECTOR = lang.monthConnector || '';
  const NO_DATA = lang.noData || 'N/D';

  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;');
  }

  function fmtNumber(value, mode) {
    if (value === null || value === undefined || Number.isNaN(value)) return NO_DATA;
    if (mode === 'yoy' || mode === 'mom') return fmtPercent(value);
    if (mode === 'index') return nf1.format(value);
    const abs = Math.abs(value);
    if (abs >= 1000) return nfInt.format(value);
    if (abs >= 100) return nf1.format(value);
    if (abs >= 10) return nf1.format(value);
    return nf2.format(value);
  }

  function fmtPercent(value) {
    if (value === null || value === undefined || Number.isNaN(value)) return NO_DATA;
    const sign = value > 0 ? '+' : '';
    return `${sign}${nf1.format(value)}%`;
  }

  function fmtMonthLong(monthLabel) {
    const [y, m] = monthLabel.split('-').map(Number);
    const month = MONTHS_LONG[m - 1];
    // ES: "Enero de 2026"   ·   EN: "January 2026"
    return MONTH_CONNECTOR ? `${month} ${MONTH_CONNECTOR} ${y}` : `${month} ${y}`;
  }

  function fmtMonthShort(monthLabel) {
    const [y, m] = monthLabel.split('-').map(Number);
    return `${MONTHS_SHORT[m - 1]} ${String(y).slice(2)}`;
  }

  function addMonths(monthLabel, offset) {
    const [y, m] = monthLabel.split('-').map(Number);
    const total = y * 12 + (m - 1) + offset;
    const ny = Math.floor(total / 12);
    const nm = (total % 12) + 1;
    return `${String(ny).padStart(4, '0')}-${String(nm).padStart(2, '0')}`;
  }

  function formatSnapshot(id) {
    if (!id || id.length < 6) return id || '—';
    const y = id.slice(0, 4);
    const m = Number(id.slice(4, 6));
    return `${MONTHS_LONG[m - 1]} ${y}`;
  }

  // ===============================================================
  // Estado y catálogos
  // ===============================================================

  const RANGE_OPTIONS = [
    { value: '12', label: lang.range12Long || '12 meses', shortLabel: lang.range12Short || '12 m' },
    { value: '24', label: lang.range24Long || '24 meses', shortLabel: lang.range24Short || '24 m' },
    { value: '60', label: lang.range60Long || '60 meses', shortLabel: lang.range60Short || '60 m' },
    { value: 'all', label: lang.rangeAllLong || 'Histórico completo', shortLabel: lang.rangeAllShort || 'Histórico' },
  ];

  // Modo y universo quedan fijados como constantes: cada métrica se ve en su
  // unidad natural (precio en nivel, contactos/oferta como índice base
  // 2018/2019=1 que ya viene normalizado en el pipeline R) y siempre usamos
  // el universo "todos los avisos" (stock). El usuario puede calcular
  // variaciones aparte si las necesita; mantenemos la vista alineada con el
  // informe oficial.
  const FIXED_MODE = 'level';
  const FIXED_UNIVERSO = 'stock';

  const RANGE_MONTHS = { '12': 12, '24': 24, '60': 60, 'all': null };

  // Labels genéricos para el dropdown (sin sesgo a venta/alquiler).
  // Cada panel sigue mostrando su título específico ("...de venta" / "...de alquiler").
  const METRIC_LABELS_GENERIC = {
    precio: lang.metricPrecio || 'Precio mediano por m²',
    demanda: lang.metricDemanda || 'Demanda (contactos)',
    oferta: lang.metricOferta || 'Oferta (publicaciones activas)',
  };

  const METRIC_OPTIONS = Object.keys(saleMetrics).map((key) => ({
    value: key,
    label: METRIC_LABELS_GENERIC[key] || saleMetrics[key].label,
  }));

  const defaultInmueble = inmuebles.includes('Departamento') ? 'Departamento' : inmuebles[0];

  const state = {
    nivel: 'aglomerado',
    selectedRegions: new Set(DEFAULT_SELECTION.aglomerado),
    inmueble: defaultInmueble,
    metric: 'precio',
    universo: FIXED_UNIVERSO,
    range: 'all',
    mode: FIXED_MODE,
    hiddenSeries: { sale: new Set(), rent: new Set() },
  };

  function currentRegionList() {
    return regions[state.nivel] || [];
  }

  // ¿La métrica actual admite la elección de universo de avisos?
  // Sólo Precio admite distinción stock/flujo, y SÓLO en ventas y a nivel
  // aglomerado o municipio (barrio CABA solo trae stock).
  function metricHasUniverso(metricKey) {
    return metricKey === 'precio';
  }

  // Paleta para barrios y municipios: HSL distribuida según índice
  // alfabético. Para aglomerados se usa la paleta fija de COLORS.
  function colorFor(regionName) {
    if (colors[regionName]) return colors[regionName];
    const list = currentRegionList();
    const idx = list.indexOf(regionName);
    if (idx < 0) return '#0f3e7d';
    // Distribuyo en hue 0..330 (saltando rojo puro) y alterno luminosidad
    // para que regiones consecutivas no queden iguales si hay > 12.
    const hue = (idx * 47) % 360;
    const sat = 62;
    const lig = 42 + (idx % 3) * 8;
    return `hsl(${hue}, ${sat}%, ${lig}%)`;
  }

  // ===============================================================
  // Reglas de visualización (combos bloqueados)
  // ===============================================================

  // Combinaciones que el Centro no publica como gráfico (regla curada).
  // Vacío por ahora: las reglas viejas referenciaban modo/universo que ya no
  // se exponen al usuario. Si en el futuro aparecen casos que requieran
  // bloqueo (p. ej. nivel × métrica sin datos), agregar entradas acá.
  const BLOCKED = [];

  function getBlockedReason(s) {
    for (const rule of BLOCKED) {
      if (rule.when(s)) return rule.reason;
    }
    return null;
  }

  // ===============================================================
  // Datos
  // ===============================================================

  function getRawSeries(side, inmueble, metric, region) {
    const levelRoot = data[side] && data[side][state.nivel];
    if (!levelRoot || !levelRoot[inmueble] || !levelRoot[inmueble][metric]) return null;
    const metricNode = levelRoot[inmueble][metric];
    // Precio guarda {stock: {region: pts}, flujo?: {region: pts}}.
    if (metricHasUniverso(metric)) {
      const universoNode = metricNode[state.universo];
      if (!universoNode) return null;
      const series = universoNode[region];
      return series && series.length ? series : null;
    }
    const series = metricNode[region];
    return series && series.length ? series : null;
  }

  // Devuelve true si la combinación actual de side+metric+universo tiene datos
  // disponibles en el dataset (independientemente de la región).
  function universoAvailableFor(side, metric, universo) {
    if (!metricHasUniverso(metric)) return true; // el filtro no aplica
    const node = data[side]
      && data[side][state.nivel]
      && data[side][state.nivel][state.inmueble]
      && data[side][state.nivel][state.inmueble][metric];
    return Boolean(node && node[universo]);
  }


  function applyRange(series, range) {
    if (!series || !series.length) return series;
    const months = RANGE_MONTHS[range];
    if (!months) return series.slice();
    return series.slice(-months);
  }

  function transformSeries(series, mode, fullSeries) {
    if (!series || !series.length) return [];
    if (mode === 'level') return series.map((p) => ({ x: p.x, y: p.y }));
    if (mode === 'index') {
      const base = series[0].y;
      if (!base) return series.map((p) => ({ x: p.x, y: null }));
      return series.map((p) => ({ x: p.x, y: (p.y / base) * 100 }));
    }
    if (mode === 'yoy' || mode === 'mom') {
      // mom = lag 1 mes; yoy = lag 12 meses. Buscamos el valor previo en
      // la serie *completa* (no recortada) para que la primera observacion
      // del rango visible tambien tenga variacion calculada.
      const lag = mode === 'mom' ? -1 : -12;
      const map = new Map((fullSeries || series).map((p) => [p.x, p.y]));
      return series.map((p) => {
        const prev = map.get(addMonths(p.x, lag));
        if (prev === undefined || prev === null || prev === 0 || p.y === null) {
          return { x: p.x, y: null };
        }
        return { x: p.x, y: (p.y / prev - 1) * 100 };
      });
    }
    return series.map((p) => ({ x: p.x, y: p.y }));
  }

  function buildPanelSeries(side) {
    const metricInfo = (side === 'sale' ? saleMetrics : rentMetrics)[state.metric];
    const out = [];
    for (const region of currentRegionList()) {
      if (!state.selectedRegions.has(region)) continue;
      const raw = getRawSeries(side, state.inmueble, state.metric, region);
      if (!raw) continue;
      const trimmed = applyRange(raw, state.range);
      const points = transformSeries(trimmed, state.mode, raw);
      const cleanPoints = points.filter((p) => p.y !== null && !Number.isNaN(p.y));
      if (!cleanPoints.length) continue;
      out.push({
        name: region,
        color: colorFor(region),
        points: cleanPoints,
      });
    }
    return { series: out, metricInfo };
  }

  function computeDomains(series) {
    const xs = new Set();
    let yMin = Infinity;
    let yMax = -Infinity;
    for (const s of series) {
      for (const p of s.points) {
        xs.add(p.x);
        if (p.y < yMin) yMin = p.y;
        if (p.y > yMax) yMax = p.y;
      }
    }
    if (yMin === Infinity) { yMin = 0; yMax = 1; }
    if (yMin === yMax) { yMin -= 1; yMax += 1; }
    return { xList: Array.from(xs).sort(), yMin, yMax };
  }

  function niceTicks(min, max, count) {
    if (min === max) return { ticks: [min], niceMin: min, niceMax: max };
    const span = max - min;
    const step0 = span / count;
    const exp = Math.floor(Math.log10(Math.abs(step0)));
    const base = Math.pow(10, exp);
    const candidates = [1, 2, 2.5, 5, 10].map((m) => m * base);
    let step = candidates[candidates.length - 1];
    for (const c of candidates) {
      if (c >= step0) { step = c; break; }
    }
    const niceMin = Math.floor(min / step) * step;
    const niceMax = Math.ceil(max / step) * step;
    const ticks = [];
    for (let v = niceMin; v <= niceMax + step / 2; v += step) {
      ticks.push(Math.round(v * 1e6) / 1e6);
    }
    return { ticks, niceMin, niceMax };
  }

  // ===============================================================
  // Render principal
  // ===============================================================

  function render() {
    app.removeAttribute('aria-busy');
    app.innerHTML = `
      <div class="shell">
        ${renderToolbar()}
        ${renderRangeBar()}
        <section class="charts-grid" id="charts-grid">
          ${renderChartShell('sale')}
          ${renderChartShell('rent')}
        </section>
      </div>
      <div class="toast" id="toast" role="status" aria-live="polite"></div>
    `;
    bindDropdownEvents();
    bindActionEvents();
    bindRangeChipEvents();
    drawAllCharts();
    bindChartEvents();
  }

  let resizeTimer = null;
  window.addEventListener('resize', () => {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(drawAllCharts, 120);
  });

  function drawAllCharts() {
    drawChart('sale');
    drawChart('rent');
  }

  // ---------------- TOOLBAR ----------------

  function renderToolbar() {
    const regionsLabel = describeRegions();
    const regionDropdownLabel = REGION_LABEL[state.nivel];
    const nivelLabel = (LEVEL_OPTIONS.find((o) => o.value === state.nivel) || {}).label || '—';
    const inmuebleLabel = inmuebleDisplay(state.inmueble);
    const metricLabel = (METRIC_OPTIONS.find((o) => o.value === state.metric) || {}).label || '—';

    const regionOptions = currentRegionList().map((r) => ({
      value: r,
      label: regionDisplay(r),
      color: colorFor(r),
    }));
    const enableSearch = regionOptions.length > 15;

    // Opciones del dropdown de inmueble: value = data key (Casa/Departamento),
    // label = display localizado.
    const inmuebleOptions = inmuebles.map((v) => ({ value: v, label: inmuebleDisplay(v) }));

    return `
      <section class="toolbar" role="toolbar" aria-label="${escapeHtml(lang.toolbarAria || 'Filtros del explorador')}">
        <div class="toolbar-filters">
          ${dropdownButton('nivel', lang.levelLabel || 'Nivel geográfico', nivelLabel)}
          ${dropdownButton('regions', regionDropdownLabel, regionsLabel)}
          ${dropdownButton('inmueble', lang.inmuebleLabel || 'Tipo de propiedad', inmuebleLabel)}
          ${dropdownButton('metric', lang.metricLabel || 'Métrica', metricLabel)}
        </div>
        <div class="toolbar-actions">
          <button type="button" class="action-btn secondary" data-action="reset" title="${escapeHtml(lang.actionResetTitle || 'Restablecer filtros')}" aria-label="${escapeHtml(lang.actionResetTitle || 'Restablecer filtros')}">${iconReset()}<span class="label-text">${escapeHtml(lang.actionResetLabel || 'Restablecer')}</span></button>
          <button type="button" class="action-btn" data-action="download-sale" title="${escapeHtml(lang.actionDownloadSaleTitle || 'Descargar venta')}" aria-label="${escapeHtml(lang.actionDownloadSaleAria || 'Descargar venta como PNG')}">${iconDownload()}<span class="label-text">${escapeHtml(lang.actionDownloadSaleLabel || 'Venta')}</span></button>
          <button type="button" class="action-btn" data-action="download-rent" title="${escapeHtml(lang.actionDownloadRentTitle || 'Descargar alquiler')}" aria-label="${escapeHtml(lang.actionDownloadRentAria || 'Descargar alquiler como PNG')}">${iconDownload()}<span class="label-text">${escapeHtml(lang.actionDownloadRentLabel || 'Alquiler')}</span></button>
        </div>

        ${dropdownMenu('nivel', lang.levelLabel || 'Nivel geográfico', LEVEL_OPTIONS, false, state.nivel)}
        ${dropdownMenu('regions', regionDropdownLabel, regionOptions, true, state.selectedRegions, enableSearch)}
        ${dropdownMenu('inmueble', lang.inmuebleLabel || 'Tipo de propiedad', inmuebleOptions, false, state.inmueble)}
        ${dropdownMenu('metric', lang.metricLabel || 'Métrica', METRIC_OPTIONS, false, state.metric)}
      </section>
    `;
  }

  // ---------------- RANGE CHIPS (período) ----------------

  function renderRangeBar() {
    const chips = RANGE_OPTIONS.map((opt) => {
      const active = state.range === opt.value;
      return `<button type="button" class="range-chip ${active ? 'is-active' : ''}" data-range="${escapeHtml(opt.value)}" aria-pressed="${active}" title="${escapeHtml(opt.label)}">${escapeHtml(opt.shortLabel)}</button>`;
    }).join('');
    return `
      <section class="range-bar" role="group" aria-label="${escapeHtml(lang.periodAria || 'Período del gráfico')}">
        <span class="range-bar-label">${escapeHtml(lang.periodLabel || 'Período')}</span>
        <div class="range-chips">${chips}</div>
      </section>
    `;
  }

  function bindRangeChipEvents() {
    document.querySelectorAll('.range-chip').forEach((btn) => {
      btn.addEventListener('click', () => {
        const value = btn.dataset.range;
        if (state.range === value) return;
        state.range = value;
        render();
      });
    });
  }

  function describeRegions() {
    const list = Array.from(state.selectedRegions);
    const total = currentRegionList().length;
    if (!list.length) return lang.regionsNone || 'Ninguna seleccionada';
    if (list.length === 1) return regionDisplay(list[0]);
    if (list.length === total) return `${lang.regionsAllPrefix || 'Todas'} (${list.length})`;
    return `${list.slice(0, 2).map(regionDisplay).join(', ')} · ${list.length} ${lang.regionsSelectedSuffix || 'sel.'}`;
  }

  function dropdownButton(key, label, value) {
    return `
      <div class="dropdown" data-key="${key}">
        <button type="button" class="dropdown-trigger" data-dropdown="${key}" aria-haspopup="listbox" aria-expanded="false">
          <span class="dropdown-trigger-text">
            <span class="dropdown-trigger-label">${escapeHtml(label)}</span>
            <span class="dropdown-trigger-value" title="${escapeHtml(value)}">${escapeHtml(value)}</span>
          </span>
          ${iconChevron()}
        </button>
      </div>
    `;
  }

  function dropdownMenu(key, label, options, multi, currentValueOrSet, enableSearch) {
    // El menú se renderiza aparte y se posiciona via JS al abrir (lo dejamos como
    // hijo del propio .dropdown contenedor para que el position:absolute lo ancle).
    const menuClass = enableSearch ? 'dropdown-menu has-search' : 'dropdown-menu';
    const searchPlaceholder = lang.searchPlaceholder || 'Buscar...';
    const searchAriaPrefix = lang.searchAriaPrefix || 'Buscar en';
    const selectAllLabel = lang.menuSelectAll || 'Seleccionar todos';
    const clearLabel = lang.menuClear || 'Limpiar';
    return `
      <template id="tpl-menu-${key}">
        <div class="${menuClass}" role="listbox" data-menu="${key}" aria-label="${escapeHtml(label)}">
          ${enableSearch ? `
            <div class="dropdown-search">
              <input type="search" class="dropdown-search-input" data-menu-search="${key}" placeholder="${escapeHtml(searchPlaceholder)}" aria-label="${escapeHtml(searchAriaPrefix)} ${escapeHtml(label)}" />
            </div>` : ''
          }
          ${multi ? `
            <div class="dropdown-menu-head">
              <button type="button" data-menu-action="all" data-menu="${key}">${escapeHtml(selectAllLabel)}</button>
              <button type="button" data-menu-action="clear" data-menu="${key}">${escapeHtml(clearLabel)}</button>
            </div>` : ''
          }
          <div class="dropdown-menu-options" data-menu-options="${key}">
          ${options.map((opt) => {
            const checked = multi
              ? currentValueOrSet.has(opt.value)
              : currentValueOrSet === opt.value;
            const dot = opt.color ? `<span class="option-dot" style="background:${opt.color}"></span>` : '';
            const input = multi
              ? `<input type="checkbox" data-menu="${key}" data-value="${escapeHtml(opt.value)}" ${checked ? 'checked' : ''} />`
              : `<input type="radio" name="menu-${key}" data-menu="${key}" data-value="${escapeHtml(opt.value)}" ${checked ? 'checked' : ''} />`;
            return `
              <label class="dropdown-option" data-search-text="${escapeHtml(opt.label.toLowerCase())}">
                ${input}
                ${dot}
                <span class="option-text">${escapeHtml(opt.label)}</span>
              </label>
            `;
          }).join('')}
          </div>
        </div>
      </template>
    `;
  }

  function bindDropdownEvents() {
    // Cerrar al click fuera
    document.addEventListener('click', closeAllDropdownsOnOutsideClick, true);

    document.querySelectorAll('.dropdown-trigger').forEach((trigger) => {
      trigger.addEventListener('click', (ev) => {
        ev.stopPropagation();
        const key = trigger.dataset.dropdown;
        const dropdown = trigger.closest('.dropdown');
        const isOpen = trigger.classList.contains('is-open');
        closeAllDropdowns();
        if (!isOpen) openDropdown(dropdown, trigger, key);
      });
    });
  }

  function openDropdown(dropdownEl, trigger, key) {
    const tpl = document.getElementById(`tpl-menu-${key}`);
    if (!tpl) return;
    const menu = tpl.content.firstElementChild.cloneNode(true);
    dropdownEl.appendChild(menu);
    menu.classList.add('is-open');
    trigger.classList.add('is-open');
    trigger.setAttribute('aria-expanded', 'true');

    menu.addEventListener('click', (ev) => ev.stopPropagation());

    menu.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach((input) => {
      input.addEventListener('change', () => applyMenuChange(key, menu));
    });

    const searchInput = menu.querySelector('.dropdown-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        const q = searchInput.value.trim().toLowerCase();
        menu.querySelectorAll('.dropdown-option').forEach((opt) => {
          const txt = opt.dataset.searchText || '';
          opt.style.display = !q || txt.includes(q) ? '' : 'none';
        });
      });
      // Foco automático al abrir
      setTimeout(() => searchInput.focus(), 30);
    }

    menu.querySelectorAll('[data-menu-action]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.menuAction;
        if (key !== 'regions') return;
        const list = currentRegionList();
        if (action === 'all') {
          state.selectedRegions = new Set(list);
        } else if (action === 'clear') {
          // Mantenemos al menos uno seleccionado para no quedar sin datos.
          state.selectedRegions = new Set([list[0]]);
          const noun = REGION_LABEL[state.nivel].toLowerCase();
          showToast(`${lang.toastKeepOnePrefix || 'Mantenemos al menos un'} ${noun}.`);
        }
        render();
      });
    });
  }

  function applyMenuChange(key, menuEl) {
    if (key === 'regions') {
      const checked = Array.from(menuEl.querySelectorAll('input[type="checkbox"]:checked')).map((i) => i.dataset.value);
      if (!checked.length) {
        const noun = REGION_LABEL[state.nivel].toLowerCase();
        showToast(`${lang.toastSelectOnePrefix || 'Seleccioná al menos un'} ${noun}.`);
        // re-check el primero por seguridad
        const fallbackVal = state.selectedRegions.values().next().value || currentRegionList()[0];
        const fallback = menuEl.querySelector(`input[data-value="${fallbackVal}"]`);
        if (fallback) fallback.checked = true;
        return;
      }
      state.selectedRegions = new Set(checked);
      render();
      // Re-abrir el menú para que el usuario pueda seguir tildando
      reopenDropdown('regions');
      return;
    }

    const selected = menuEl.querySelector(`input[data-menu="${key}"]:checked`);
    if (!selected) return;
    const value = selected.dataset.value;
    if (state[key] === value) {
      closeAllDropdowns();
      return;
    }
    if (key === 'nivel') {
      // Cambiar de nivel resetea selección de regiones al default del nivel
      // y limpia las series ocultas (los nombres ya no aplican).
      state.nivel = value;
      const fallback = DEFAULT_SELECTION[value] || [regions[value][0]];
      // Filtrar a las que efectivamente existen en este snapshot.
      const valid = fallback.filter((r) => regions[value].includes(r));
      state.selectedRegions = new Set(valid.length ? valid : [regions[value][0]]);
      state.hiddenSeries = { sale: new Set(), rent: new Set() };
      render();
      return;
    }
    if (key === 'inmueble' || key === 'metric') {
      state.hiddenSeries = { sale: new Set(), rent: new Set() };
    }
    state[key] = value;
    render();
  }

  function reopenDropdown(key) {
    requestAnimationFrame(() => {
      const trigger = document.querySelector(`.dropdown-trigger[data-dropdown="${key}"]`);
      const dropdown = trigger ? trigger.closest('.dropdown') : null;
      if (trigger && dropdown) openDropdown(dropdown, trigger, key);
    });
  }

  function closeAllDropdowns() {
    document.querySelectorAll('.dropdown-trigger.is-open').forEach((trigger) => {
      trigger.classList.remove('is-open');
      trigger.setAttribute('aria-expanded', 'false');
    });
    document.querySelectorAll('.dropdown-menu').forEach((menu) => menu.remove());
  }

  function closeAllDropdownsOnOutsideClick(ev) {
    if (!ev.target.closest('.dropdown')) closeAllDropdowns();
  }

  // ---------------- ACTIONS ----------------

  function bindActionEvents() {
    document.querySelectorAll('[data-action]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        if (action === 'reset') {
          state.nivel = 'aglomerado';
          state.selectedRegions = new Set(DEFAULT_SELECTION.aglomerado);
          state.inmueble = defaultInmueble;
          state.metric = 'precio';
          state.universo = FIXED_UNIVERSO;
          state.range = 'all';
          state.mode = FIXED_MODE;
          state.hiddenSeries = { sale: new Set(), rent: new Set() };
          render();
          showToast(lang.toastReset || 'Filtros restablecidos.');
        }
        if (action === 'download-sale') downloadPanelPng('sale');
        if (action === 'download-rent') downloadPanelPng('rent');
      });
    });
  }

  // ---------------- CHART SHELL ----------------

  function renderChartShell(side) {
    const sideLabel = side === 'sale' ? (lang.sideSale || 'Venta') : (lang.sideRent || 'Alquiler');
    const legendAria = side === 'sale'
      ? (lang.sideSaleLegendAria || 'Leyenda Venta')
      : (lang.sideRentLegendAria || 'Leyenda Alquiler');
    const tagClass = side === 'sale' ? 'sale' : 'rent';
    return `
      <article class="chart-panel ${tagClass}" data-side="${side}" id="panel-${side}">
        <header class="chart-head">
          <span class="chart-tag ${tagClass}">${escapeHtml(sideLabel)}</span>
          <h2 class="chart-title" id="title-${side}">—</h2>
          <p class="chart-sub" id="sub-${side}">—</p>
          <div class="chart-stats" id="stats-${side}"></div>
        </header>
        <div class="chart-canvas-wrap" id="canvas-${side}"></div>
        <div class="chart-legend" id="legend-${side}" role="group" aria-label="${escapeHtml(legendAria)}"></div>
        <div class="chart-footnote">
          <span id="note-${side}">—</span>
          <button type="button" class="panel-download" data-action="download-${side}">${iconDownload()} ${escapeHtml(lang.panelDownloadBtn || 'Descargar PNG')}</button>
        </div>
      </article>
    `;
  }

  // ---------------- CHART DRAWING ----------------

  function drawChart(side) {
    const panel = document.getElementById(`panel-${side}`);
    if (!panel) return;
    const canvasHost = panel.querySelector('.chart-canvas-wrap');
    const titleEl = panel.querySelector('.chart-title');
    const subEl = panel.querySelector('.chart-sub');
    const statsEl = panel.querySelector('.chart-stats');
    const legendEl = panel.querySelector('.chart-legend');
    const noteEl = panel.querySelector(`#note-${side}`);

    const { series, metricInfo } = buildPanelSeries(side);

    // Header text (siempre presente, aún si el panel queda bloqueado)
    titleEl.textContent = composeTitle(metricInfo);
    subEl.textContent = composeSubtitle(metricInfo);
    const credit = (lang.footerCredit || '{snapshot}').replace('{snapshot}', formatSnapshot(snapshotId));
    noteEl.textContent = credit;

    // 1. Regla de combo bloqueado (combinación explícitamente curada)
    const blockedReason = getBlockedReason(state);
    if (blockedReason) {
      statsEl.innerHTML = '';
      legendEl.innerHTML = '';
      canvasHost.innerHTML = renderEmptyState(blockedReason, true);
      return;
    }

    // 2. ¿El universo "stock" existe para este lado? (defensivo: en la
    // práctica el pipeline siempre publica stock para precio en venta y
    // alquiler. Mantenemos la guarda para no romper si un snapshot futuro
    // viene incompleto.)
    if (metricHasUniverso(state.metric) && !universoAvailableFor(side, state.metric, state.universo)) {
      statsEl.innerHTML = '';
      legendEl.innerHTML = '';
      canvasHost.innerHTML = renderEmptyState(
        lang.emptyNoPrecio || 'No hay datos de precio para esta combinación en el snapshot.',
        false,
      );
      return;
    }

    // 3. Datos suficientes?
    const visible = series.filter((s) => !state.hiddenSeries[side].has(s.name));
    if (!visible.length || !visible.some((s) => s.points.length)) {
      statsEl.innerHTML = '';
      renderLegend(legendEl, side, series);
      canvasHost.innerHTML = renderEmptyState(
        series.length
          ? (lang.emptyWidenPeriod || 'Probá ampliar el período o activar más aglomerados en la leyenda.')
          : (lang.emptyChangeCombo || 'Probá con otra combinación de aglomerado, tipo de propiedad o métrica.'),
        false,
      );
      return;
    }

    // 3. Render normal
    renderStats(statsEl, side, series, visible, metricInfo);
    renderLegend(legendEl, side, series);
    canvasHost.innerHTML = renderSvg(side, visible, metricInfo);
    attachTooltip(side, canvasHost, visible);
  }

  function composeTitle(metricInfo) {
    const sep = lang.titleSeparator || '·';
    const inmuebleLabel = pluralInmueble(inmuebleDisplay(state.inmueble));
    const parts = [metricInfo.label, sep, inmuebleLabel];
    // Indicador del nivel geográfico cuando NO es aglomerado (default).
    // Convención: cada segmento después de "·" arranca con mayúscula.
    if (state.nivel === 'barrio') parts.push(sep, lang.titleBarriosCaba || 'Barrios CABA');
    else if (state.nivel === 'municipio') parts.push(sep, lang.titleMunicipiosAmba || 'Municipios AMBA');
    return parts.join(' ');
  }

  function composeSubtitle(metricInfo) {
    // Cada métrica se muestra en su unidad natural (alineada al informe oficial):
    //   - Precio: USD/m² (venta) o ARS/m² corrientes (alquiler), mediana winsorizada.
    //   - Oferta: índice normalizado a 1 en enero 2018 en el pipeline R.
    //   - Demanda (Contactos): índice normalizado a 1 en enero 2019 en el
    //     pipeline R (la captura de contactos arranca un año después que la
    //     de publicaciones activas).
    //   Verificado contra los CSVs del snapshot 202604/202605: la base es
    //   uniforme por inmueble y por geografía (no depende de Casa vs Depto
    //   ni de aglomerado vs barrio vs municipio).
    //   El último mes del snapshot se excluye porque Demanda y Oferta siguen
    //   acumulando después del corte mensual.
    const sep = lang.titleSeparator || '·';
    if (state.metric === 'oferta') {
      return `${metricInfo.unit} ${sep} ${lang.subtitleOfertaSuffix || ''}`;
    }
    if (state.metric === 'demanda') {
      return `${metricInfo.unit} ${sep} ${lang.subtitleDemandaSuffix || ''}`;
    }
    // Precio: la unidad ya describe completamente el subtítulo. No hace falta
    // aclarar el universo porque siempre usamos "todos los avisos".
    return metricInfo.unit;
  }

  function renderEmptyState(message, isBlocked) {
    const klass = isBlocked ? 'chart-empty is-blocked' : 'chart-empty';
    return `
      <div class="${klass}">
        ${iconEmpty()}
        <strong>${escapeHtml(lang.emptyBlockedTitle || 'No hay visualización disponible para esta selección.')}</strong>
        ${escapeHtml(message)}
      </div>
    `;
  }

  function renderStats(host, side, allSeries, visible, metricInfo) {
    const items = [];
    for (const s of visible) {
      const pts = s.points;
      if (!pts.length) continue;
      const first = pts[0];
      const last = pts[pts.length - 1];
      let delta = null;
      let deltaClass = 'flat';
      if (state.mode === 'level') {
        if (first.y !== null && first.y !== 0 && last.y !== null) {
          delta = (last.y / first.y - 1) * 100;
        }
      } else {
        delta = last.y - first.y;
      }
      if (delta !== null && !Number.isNaN(delta)) {
        if (delta > 0.05) deltaClass = 'up';
        else if (delta < -0.05) deltaClass = 'down';
      }
      const accumSuffix = lang.statsAccumSuffix || 'acum.';
      const ppSuffix = lang.statsPpSuffix || 'pp';
      const deltaTxt = state.mode === 'level'
        ? (delta === null ? '—' : `${fmtPercent(delta)} ${accumSuffix}`)
        : (delta === null ? '—' : `${delta > 0 ? '+' : ''}${nf1.format(delta)} ${ppSuffix}`);

      items.push(`
        <div class="stat-card" style="border-color:${s.color}33;">
          <div class="stat-label" style="color:${s.color}">${escapeHtml(regionDisplay(s.name))}</div>
          <div class="stat-value">${escapeHtml(fmtNumber(last.y, state.mode))}</div>
          <div class="stat-delta ${deltaClass}">${escapeHtml(deltaTxt)} · ${escapeHtml(fmtMonthShort(first.x))} → ${escapeHtml(fmtMonthShort(last.x))}</div>
        </div>
      `);
    }
    host.innerHTML = items.join('');
  }

  function renderLegend(host, side, series) {
    if (!series.length) { host.innerHTML = ''; return; }
    host.innerHTML = series.map((s) => {
      const hidden = state.hiddenSeries[side].has(s.name);
      // data-name guarda la clave de datos (para el toggle de hiddenSeries);
      // el texto visible usa el display localizado.
      return `<button type="button" data-side="${side}" data-name="${escapeHtml(s.name)}" class="${hidden ? 'is-hidden' : ''}" aria-pressed="${!hidden}">
        <span class="legend-swatch" style="background:${s.color}"></span>${escapeHtml(regionDisplay(s.name))}
      </button>`;
    }).join('');
  }

  function renderSvg(side, series, metricInfo) {
    const W = 720;
    const H = 380;
    const margin = { top: 18, right: 18, bottom: 40, left: 80 };
    const innerW = W - margin.left - margin.right;
    const innerH = H - margin.top - margin.bottom;

    const { xList, yMin, yMax } = computeDomains(series);

    let yLow = yMin;
    let yHigh = yMax;
    if (state.mode !== 'level') {
      yLow = Math.min(yMin, 0);
      yHigh = Math.max(yMax, 0);
    } else if (yLow > 0) {
      yLow = Math.max(0, yLow - (yHigh - yLow) * 0.08);
    } else {
      yLow = yLow - (yHigh - yLow) * 0.08;
    }
    yHigh = yHigh + (yHigh - yLow) * 0.08;
    const niced = niceTicks(yLow, yHigh, 5);
    yLow = niced.niceMin;
    yHigh = niced.niceMax;
    const ticks = niced.ticks;

    const xIndex = new Map(xList.map((m, i) => [m, i]));
    const xPos = (m) => xList.length === 1 ? innerW / 2 : (xIndex.get(m) / (xList.length - 1)) * innerW;
    const yPos = (v) => innerH - ((v - yLow) / (yHigh - yLow)) * innerH;

    const xTicks = pickEvenly(xList, Math.min(8, xList.length));

    const gridLines = ticks.map((t) => `<line x1="0" x2="${innerW}" y1="${yPos(t)}" y2="${yPos(t)}" />`).join('');

    const yAxis = ticks.map((t) => (
      `<text x="-10" y="${yPos(t)}" text-anchor="end" dominant-baseline="middle" font-size="11">${escapeHtml(formatTick(t, state.mode))}</text>`
    )).join('');

    const xAxis = xTicks.map((m) => (
      `<text x="${xPos(m)}" y="${innerH + 22}" text-anchor="middle" font-size="11">${escapeHtml(fmtMonthShort(m))}</text>`
    )).join('');

    const zeroLine = (state.mode !== 'level' && yLow < 0 && yHigh > 0)
      ? `<line class="chart-zero-line" x1="0" x2="${innerW}" y1="${yPos(0)}" y2="${yPos(0)}" />`
      : '';

    const linesSvg = series.map((s) => {
      if (!s.points.length) return '';
      const d = s.points.map((p, i) => `${i === 0 ? 'M' : 'L'}${xPos(p.x).toFixed(2)},${yPos(p.y).toFixed(2)}`).join(' ');
      return `<path class="chart-line" d="${d}" stroke="${s.color}" />`;
    }).join('');

    const pointsSvg = series.map((s) => (
      s.points.map((p, i) => (
        `<circle class="chart-point" data-side="${side}" data-name="${escapeHtml(s.name)}" data-x="${escapeHtml(p.x)}" data-i="${i}" cx="${xPos(p.x).toFixed(2)}" cy="${yPos(p.y).toFixed(2)}" r="3.4" fill="${s.color}" stroke="#ffffff" stroke-width="1.2" />`
      )).join('')
    )).join('');

    const hoverGuides = xList.map((m) => (
      `<rect class="chart-hover" data-x="${escapeHtml(m)}" x="${(xPos(m) - innerW / xList.length / 2).toFixed(2)}" y="0" width="${(innerW / xList.length).toFixed(2)}" height="${innerH}" fill="transparent" pointer-events="all" />`
    )).join('');

    const axisLabel = metricInfo.axisLabel;

    // Eje Y label rotado -90° alrededor de su propia ancla, centrado en altura.
    // Se posiciona suficientemente a la izquierda como para no chocar con los tick labels.
    const labelX = -(margin.left - 22);
    const labelY = innerH / 2;
    const yAxisTitle = `<text class="axis-title-y" x="${labelX}" y="${labelY}" transform="rotate(-90, ${labelX}, ${labelY})" text-anchor="middle" font-size="12">${escapeHtml(axisLabel)}</text>`;

    const svgAria = side === 'sale'
      ? (lang.sideSaleAria || 'Gráfico de venta')
      : (lang.sideRentAria || 'Gráfico de alquiler');

    return `
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${escapeHtml(svgAria)}" preserveAspectRatio="xMidYMid meet">
        <g transform="translate(${margin.left},${margin.top})">
          <g class="chart-grid" stroke-width="1">${gridLines}</g>
          ${zeroLine}
          <g class="chart-axis"><line x1="0" x2="${innerW}" y1="${innerH}" y2="${innerH}" stroke="rgba(91,107,133,0.55)" /></g>
          ${yAxisTitle}
          <g>${yAxis}</g>
          <g>${xAxis}</g>
          <g>${linesSvg}</g>
          <g>${pointsSvg}</g>
          <g class="chart-hover-layer">${hoverGuides}</g>
        </g>
      </svg>
    `;
  }

  function pickEvenly(list, n) {
    if (list.length <= n) return list.slice();
    if (n <= 1) return [list[Math.floor(list.length / 2)]];
    const out = [];
    for (let i = 0; i < n; i++) {
      const idx = Math.round((i * (list.length - 1)) / (n - 1));
      out.push(list[idx]);
    }
    return Array.from(new Set(out));
  }

  function formatTick(value, mode) {
    if (mode === 'yoy' || mode === 'mom') {
      const sign = value > 0 ? '+' : '';
      return `${sign}${nf1.format(value)}%`;
    }
    if (mode === 'index') return nf1.format(value);
    const abs = Math.abs(value);
    if (abs >= 100000) return nfInt.format(value / 1000) + 'k';
    if (abs >= 1000) return nfInt.format(value);
    if (abs >= 10) return nf1.format(value);
    return nf2.format(value);
  }

  // ---------------- TOOLTIP ----------------

  function attachTooltip(side, host, visibleSeries) {
    const tooltip = document.createElement('div');
    tooltip.className = 'chart-tooltip';
    host.appendChild(tooltip);

    const svg = host.querySelector('svg');
    if (!svg) return;
    const points = svg.querySelectorAll('.chart-point');
    const hovers = svg.querySelectorAll('.chart-hover');

    function showAt(monthLabel, originX, originY) {
      const items = visibleSeries.map((s) => {
        const found = s.points.find((p) => p.x === monthLabel);
        const valTxt = !found || found.y === null
          ? NO_DATA
          : fmtNumber(found.y, state.mode);
        return `<div class="tooltip-row">
          <span class="swatch" style="background:${s.color}"></span>
          <span class="name">${escapeHtml(regionDisplay(s.name))}</span>
          <span class="value">${escapeHtml(valTxt)}</span>
        </div>`;
      }).join('');
      tooltip.innerHTML = `<h6>${escapeHtml(fmtMonthLong(monthLabel))}</h6>${items}`;
      const hostRect = host.getBoundingClientRect();
      tooltip.style.left = `${originX - hostRect.left}px`;
      tooltip.style.top = `${originY - hostRect.top}px`;
      tooltip.classList.add('is-visible');
    }
    function hide() { tooltip.classList.remove('is-visible'); }

    hovers.forEach((rect) => {
      rect.addEventListener('mousemove', () => {
        const monthLabel = rect.dataset.x;
        const rectBox = rect.getBoundingClientRect();
        showAt(monthLabel, rectBox.left + rectBox.width / 2, rectBox.top);
      });
      rect.addEventListener('mouseleave', hide);
      rect.addEventListener('touchstart', (ev) => {
        const monthLabel = rect.dataset.x;
        const rectBox = rect.getBoundingClientRect();
        showAt(monthLabel, rectBox.left + rectBox.width / 2, rectBox.top);
        ev.preventDefault();
      }, { passive: false });
    });

    points.forEach((p) => {
      p.addEventListener('mouseenter', () => {
        const monthLabel = p.dataset.x;
        const cx = Number(p.getAttribute('cx'));
        const cy = Number(p.getAttribute('cy'));
        const svgBox = svg.getBoundingClientRect();
        const scaleX = svgBox.width / svg.viewBox.baseVal.width;
        const scaleY = svgBox.height / svg.viewBox.baseVal.height;
        const x = svgBox.left + (cx + 80) * scaleX;
        const y = svgBox.top + (cy + 18) * scaleY;
        showAt(monthLabel, x, y);
        p.setAttribute('r', '5');
      });
      p.addEventListener('mouseleave', () => { hide(); p.setAttribute('r', '3.4'); });
    });
  }

  function bindChartEvents() {
    document.querySelectorAll('.chart-legend button').forEach((btn) => {
      btn.addEventListener('click', () => {
        const side = btn.dataset.side;
        const name = btn.dataset.name;
        const set = state.hiddenSeries[side];
        if (set.has(name)) set.delete(name); else set.add(name);
        drawChart(side);
        bindChartEvents();
      });
    });

    document.querySelectorAll('.panel-download[data-action], .chart-footnote [data-action]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        if (action === 'download-sale') downloadPanelPng('sale');
        if (action === 'download-rent') downloadPanelPng('rent');
      });
    });
  }

  // ---------------- TOAST ----------------

  function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('is-visible');
    setTimeout(() => toast.classList.remove('is-visible'), 2400);
  }

  // ===============================================================
  // DOWNLOAD PNG
  // ===============================================================

  async function downloadPanelPng(side) {
    const panel = document.getElementById(`panel-${side}`);
    if (!panel) return;
    const svg = panel.querySelector('svg');
    if (!svg) {
      showToast(lang.toastNoChart || 'No hay gráfico para exportar.');
      return;
    }
    try {
      const canvas = await renderPanelToCanvas(side);
      triggerCanvasDownload(canvas, buildDownloadName(side));
      showToast(lang.toastImageOk || 'Imagen descargada.');
    } catch (err) {
      console.error(err);
      showToast(lang.toastImageFail || 'No se pudo generar la imagen.');
    }
  }

  async function renderPanelToCanvas(side) {
    const panel = document.getElementById(`panel-${side}`);
    const svg = panel.querySelector('svg');
    if (!svg) throw new Error('SVG no disponible (combinación bloqueada).');

    const clone = svg.cloneNode(true);
    embedStylesIntoSvg(clone);

    const viewBox = svg.viewBox.baseVal;
    const scale = 2.4;
    const targetW = viewBox.width * scale;
    const targetH = viewBox.height * scale;

    clone.setAttribute('width', targetW);
    clone.setAttribute('height', targetH);

    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(clone);
    const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);

    try {
      const img = await loadImage(url);
      const headTxt = collectPanelTexts(panel);

      // Layout del PNG exportado.
      // Comparado con la vista en pantalla, agrandamos título, subtítulo y
      // leyenda para que respiren contra la imagen del chart (que ya viene
      // escalada 2.4×). Si se queda corto el bloque de leyenda con muchas
      // regiones, se reparte en varias filas (calculadas abajo).
      const cardPadding = 36;
      const tagSize = 22;
      const titleSize = 34;
      const subSize = 19;
      const titleBlockHeight = 132;     // tag + título + subtítulo + padding
      const legendRowHeight = 30;
      const legendDotRadius = 8;
      const legendSize = 19;
      const footerSize = 15;
      const footerHeight = 56;

      const innerWidth = targetW;
      const innerHeight = targetH;
      const canvasWidth = innerWidth + cardPadding * 2;

      // Calcular cuántas filas de leyenda vamos a necesitar para asignar la altura adecuada.
      const tmpCanvas = document.createElement('canvas');
      const tmpCtx = tmpCanvas.getContext('2d');
      tmpCtx.font = `${legendSize}px "Aptos","Segoe UI",sans-serif`;
      const legendItemSpacing = 22;
      let legendRows = headTxt.legend.length ? 1 : 0;
      {
        let lx = cardPadding;
        for (const item of headTxt.legend) {
          const w = tmpCtx.measureText(item.name).width + legendDotRadius * 2 + legendItemSpacing;
          if (lx + w > canvasWidth - cardPadding) {
            legendRows += 1;
            lx = cardPadding;
          }
          lx += w;
        }
      }
      const legendBlockHeight = legendRows ? (legendRows * legendRowHeight + 12) : 0;
      const canvasHeight = innerHeight + cardPadding * 2 + titleBlockHeight + legendBlockHeight + footerHeight;

      const canvas = document.createElement('canvas');
      canvas.width = canvasWidth;
      canvas.height = canvasHeight;
      const ctx = canvas.getContext('2d');

      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, canvasWidth, canvasHeight);

      const accent = side === 'sale' ? '#0f3e7d' : '#4a8cc1';
      ctx.fillStyle = accent;
      ctx.fillRect(0, 0, canvasWidth, 10);

      ctx.fillStyle = accent;
      ctx.font = `700 ${tagSize}px "Aptos","Segoe UI",sans-serif`;
      ctx.textBaseline = 'top';
      ctx.fillText(headTxt.tag.toUpperCase(), cardPadding, cardPadding + 6);

      ctx.fillStyle = '#0f1f3a';
      ctx.font = `700 ${titleSize}px "Iowan Old Style","Palatino Linotype","Georgia",serif`;
      ctx.fillText(headTxt.title, cardPadding, cardPadding + tagSize + 18);

      ctx.fillStyle = '#5b6b85';
      ctx.font = `${subSize}px "Aptos","Segoe UI",sans-serif`;
      ctx.fillText(headTxt.sub, cardPadding, cardPadding + tagSize + titleSize + 30);

      ctx.drawImage(img, cardPadding, cardPadding + titleBlockHeight);

      // Legend
      let legendY = cardPadding + titleBlockHeight + innerHeight + 14;
      let lx = cardPadding;
      ctx.font = `${legendSize}px "Aptos","Segoe UI",sans-serif`;
      for (const item of headTxt.legend) {
        const labelWidth = ctx.measureText(item.name).width + legendDotRadius * 2 + legendItemSpacing;
        if (lx + labelWidth > canvasWidth - cardPadding) {
          lx = cardPadding;
          legendY += legendRowHeight;
        }
        ctx.fillStyle = item.color;
        ctx.beginPath();
        ctx.arc(lx + legendDotRadius, legendY + legendDotRadius + 3, legendDotRadius, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#0f1f3a';
        ctx.textBaseline = 'top';
        ctx.fillText(item.name, lx + legendDotRadius * 2 + 8, legendY + 2);
        lx += labelWidth;
      }

      // Footer
      ctx.fillStyle = '#5b6b85';
      ctx.font = `${footerSize}px "Aptos","Segoe UI",sans-serif`;
      ctx.textBaseline = 'bottom';
      const pngCredit = (lang.pngFooterCredit || '{snapshot}').replace('{snapshot}', formatSnapshot(snapshotId));
      ctx.fillText(pngCredit, cardPadding, canvasHeight - cardPadding + 14);

      URL.revokeObjectURL(url);
      return canvas;
    } catch (err) {
      URL.revokeObjectURL(url);
      throw err;
    }
  }

  function collectPanelTexts(panel) {
    const tag = panel.querySelector('.chart-tag').textContent.trim();
    const title = panel.querySelector('.chart-title').textContent.trim();
    const sub = panel.querySelector('.chart-sub').textContent.trim();
    const legend = Array.from(panel.querySelectorAll('.chart-legend button:not(.is-hidden)')).map((btn) => {
      const swatch = btn.querySelector('.legend-swatch');
      const color = swatch ? window.getComputedStyle(swatch).backgroundColor : '#0f3e7d';
      return { name: btn.textContent.trim(), color };
    });
    return { tag, title, sub, legend };
  }

  function embedStylesIntoSvg(svgEl) {
    const styleEl = document.createElementNS('http://www.w3.org/2000/svg', 'style');
    styleEl.textContent = `
      text { font-family: "Aptos","Segoe UI",sans-serif; fill: #5b6b85; }
      .axis-title-y { font-weight: 600; letter-spacing: 0.04em; fill: #1b3358; }
      .chart-line { fill: none; stroke-width: 2.4; stroke-linejoin: round; stroke-linecap: round; }
      .chart-point { stroke-width: 1.2; }
      .chart-grid line { stroke: rgba(91,107,133,0.18); }
      .chart-axis line { stroke: rgba(91,107,133,0.5); }
      .chart-hover { display: none; }
      .chart-zero-line { stroke: rgba(91,107,133,0.55); stroke-dasharray: 4 4; }
    `;
    svgEl.insertBefore(styleEl, svgEl.firstChild);
    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bg.setAttribute('x', 0);
    bg.setAttribute('y', 0);
    bg.setAttribute('width', svgEl.viewBox.baseVal.width);
    bg.setAttribute('height', svgEl.viewBox.baseVal.height);
    bg.setAttribute('fill', '#ffffff');
    svgEl.insertBefore(bg, styleEl.nextSibling);
  }

  function loadImage(url) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('No se pudo cargar la imagen SVG.'));
      img.src = url;
    });
  }

  function triggerCanvasDownload(canvas, filename) {
    canvas.toBlob((blob) => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setTimeout(() => URL.revokeObjectURL(url), 1500);
    }, 'image/png');
  }

  function buildDownloadName(suffix) {
    // Filename usa la clave de datos (Spanish) para que el nombre sea estable
    // entre idiomas: ej "cecn_amba_sale_precio_departamento_all.png".
    const inmueble = state.inmueble.toLowerCase();
    return `cecn_amba_${suffix}_${state.metric}_${inmueble}_${state.range}.png`;
  }

  // ---------------- ICONS ----------------

  function iconDownload() {
    return `<svg class="icon" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 2v8m0 0 3-3m-3 3-3-3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M2.5 12.5v.5A1.5 1.5 0 0 0 4 14.5h8a1.5 1.5 0 0 0 1.5-1.5v-.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`;
  }

  function iconReset() {
    return `<svg class="icon" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2.5 8a5.5 5.5 0 1 0 1.7-3.97" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M2.5 2.5V5h2.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }

  function iconChevron() {
    return `<svg class="dropdown-chevron" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M3 4.5 6 7.5l3-3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }

  function iconEmpty() {
    return `<svg class="empty-icon" viewBox="0 0 32 32" fill="none" aria-hidden="true"><circle cx="16" cy="16" r="12" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 3"/><path d="M11 20l4-6 3 4 4-7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  }

  // ===============================================================
  // Boot
  // ===============================================================

  render();
})();
