/**
 * Leyenda custom para EPU dashboard (Dash/Plotly)
 * Panel flotante con checkboxes, búsqueda y drag — igual al nowcast.
 */
(function () {
  'use strict';

  var GID = 'epu-graph';
  var PANEL_ID = 'cb-epu-panel';
  var DATEPICKER_ID = 'cb-epu-datepicker';
  var STYLE_ID = 'cb-epu-style';

  // ─── Helpers de visibilidad ─────────────────────────────────────────────────

  function isVisible(gd, idx) {
    var v = gd.data[idx].visible;
    return v === undefined || v === true;
  }

  function setVisible(gd, idx, on) {
    return Plotly.restyle(gd, { visible: on ? true : 'legendonly' }, [idx]);
  }

  function setMany(gd, indices, on) {
    if (!indices.length) return Promise.resolve();
    var vis = indices.map(function () { return on ? true : 'legendonly'; });
    return Plotly.restyle(gd, { visible: vis }, indices);
  }

  // ─── Aislar / restaurar ─────────────────────────────────────────────────────

  var isolateState = { active: false, saved: null, key: null };

  function snapshot(gd) {
    return gd.data.map(function (t) { return t.visible === undefined ? true : t.visible; });
  }

  function restoreVisible(gd, saved) {
    var idx = saved.map(function (_, k) { return k; });
    return Plotly.restyle(gd, { visible: saved }, idx);
  }

  function isolate(gd, indices, key, syncFn) {
    if (isolateState.active && isolateState.key === key) {
      var saved = isolateState.saved;
      isolateState.active = false;
      isolateState.saved = null;
      isolateState.key = null;
      return restoreVisible(gd, saved).then(syncFn);
    }
    isolateState.active = true;
    isolateState.saved = snapshot(gd);
    isolateState.key = key;
    var all = gd.data.map(function (_, k) { return k; });
    var vis = all.map(function (k) { return indices.indexOf(k) >= 0 ? true : 'legendonly'; });
    return Plotly.restyle(gd, { visible: vis }, all).then(syncFn);
  }

  // ─── Construir items desde gd.data ─────────────────────────────────────────

  function buildItems(data) {
    return (data || [])
      .map(function (tr, idx) { return { tr: tr, idx: idx }; })
      .filter(function (o) { return o.tr.showlegend !== false && o.tr.name; })
      .map(function (o) {
        var tr = o.tr;
        var color =
          (tr.line && tr.line.color) ||
          tr.fillcolor ||
          (tr.marker && typeof tr.marker.color === 'string' && tr.marker.color) ||
          'rgba(120,120,120,1)';
        return { i: o.idx, name: String(tr.name), color: String(color) };
      });
  }

  // ─── CSS ────────────────────────────────────────────────────────────────────

  function injectStyles(doc) {
    if (doc.getElementById(STYLE_ID)) return;
    var st = doc.createElement('style');
    st.id = STYLE_ID;
    st.textContent =
      '.cb-panel{position:absolute;top:52px;left:443px;z-index:50;width:230px;max-width:calc(100% - 20px);background:rgba(255,255,255,0.90);border:1px solid rgba(0,0,0,0.14);box-shadow:0 8px 20px rgba(0,0,0,0.10);border-radius:12px;padding:8px;font-family:Helvetica,Arial,sans-serif;color:#111;user-select:none;}' +
      '.cb-header{display:flex;align-items:center;gap:6px;cursor:move;margin-bottom:0;}' +
      '.cb-grip{font-size:18px;color:#aaa;cursor:move;padding:0 4px;flex-shrink:0;line-height:1;user-select:none;}' +
      '.cb-editbtn{font-size:12px;font-weight:700;padding:4px 10px;border-radius:10px;border:1px solid rgba(0,0,0,0.14);background:rgba(255,255,255,0.85);cursor:pointer;flex:1;}' +
      '.cb-editbtn:hover{background:rgba(255,255,255,1);}' +
      '.cb-body{margin-top:8px;}' +
      '.cb-actions{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 8px 0;}' +
      '.cb-btn{font-size:10px;padding:5px 7px;border-radius:10px;border:1px solid rgba(0,0,0,0.12);background:rgba(255,255,255,0.85);cursor:pointer;}' +
      '.cb-btn:hover{background:rgba(255,255,255,1);border-color:rgba(0,0,0,0.18);}' +
      '.cb-search{width:100%;box-sizing:border-box;border-radius:10px;border:1px solid rgba(0,0,0,0.12);padding:6px 8px;font-size:11px;outline:none;background:rgba(255,255,255,0.90);}' +
      '.cb-groups{margin-top:8px;display:flex;flex-direction:column;gap:5px;max-height:220px;overflow:auto;padding-right:4px;}' +
      '.cb-item{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:12px;cursor:pointer;border:1px solid rgba(0,0,0,0.06);background:rgba(255,255,255,0.60);}' +
      '.cb-item:hover{background:rgba(255,255,255,0.95);border-color:rgba(0,0,0,0.10);}' +
      '.cb-item.off{opacity:0.55;}' +
      '.cb-box{width:15px;height:15px;border-radius:5px;border:1px solid rgba(0,0,0,0.35);display:inline-flex;align-items:center;justify-content:center;font-size:11px;line-height:1;color:white;background:transparent;flex:0 0 auto;}' +
      '.cb-box.on{background:rgba(16,185,129,0.95);border-color:rgba(16,185,129,1);}' +
      '.cb-swatch{width:11px;height:11px;border-radius:4px;border:1px solid rgba(0,0,0,0.15);flex:0 0 auto;}' +
      '.cb-label{font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}';
    doc.head.appendChild(st);
  }

  // ─── DOM helpers ────────────────────────────────────────────────────────────

  function el(tag, attrs, html) {
    var x = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        if (k === 'style') x.setAttribute('style', attrs[k]);
        else x.setAttribute(k, attrs[k]);
      });
    }
    if (html !== undefined) x.innerHTML = html;
    return x;
  }

  // ─── Sync estado de checkboxes ──────────────────────────────────────────────

  function setBoxState(boxEl, on) {
    boxEl.classList.toggle('on', on);
    boxEl.textContent = on ? '✓' : '';
  }

  function rowState(row, on) {
    var box = row.querySelector('.cb-box');
    if (box) setBoxState(box, on);
    row.classList.toggle('off', !on);
  }

  function syncAll(gd, items) {
    items.forEach(function (it) {
      var row = document.getElementById('cb-epu-item-' + it.i);
      if (row) rowState(row, isVisible(gd, it.i));
    });
  }

  // ─── Date picker overlay ─────────────────────────────────────────────────────

  function buildDatePicker(gd) {
    var initRange = ((gd.layout || {}).xaxis || {}).range || [];
    var xDataMin = initRange[0] ? String(initRange[0]).split('T')[0] : null;
    var xDataMax = initRange[1] ? String(initRange[1]).split('T')[0] : null;

    var dpDiv = el('div', {
      id: DATEPICKER_ID,
      style:
        'position:absolute; top:52px; left:78px; display:flex; align-items:center; ' +
        'background:rgba(255,255,255,0.88); border-radius:6px; padding:4px 8px; z-index:10; ' +
        'font-family:Helvetica,Arial,sans-serif;'
    });

    var fromSpan = el('span', { style: 'font-size:13px; color:#555; margin-right:4px;' }, 'From:');
    var fromInput = el('input', {
      type: 'date',
      style: 'font-size:13px; border:1px solid rgba(0,0,0,0.15); border-radius:4px; padding:2px 4px;'
    });
    var toSpan = el('span', { style: 'font-size:13px; color:#555; margin:0 4px 0 10px;' }, 'To:');
    var toInput = el('input', {
      type: 'date',
      style: 'font-size:13px; border:1px solid rgba(0,0,0,0.15); border-radius:4px; padding:2px 4px;'
    });

    dpDiv.appendChild(fromSpan);
    dpDiv.appendChild(fromInput);
    dpDiv.appendChild(toSpan);
    dpDiv.appendChild(toInput);
    gd.appendChild(dpDiv);

    function applyDateRange() {
      var from = fromInput.value;
      var to = toInput.value;
      Plotly.relayout(gd, {
        'xaxis.range[0]': from || xDataMin,
        'xaxis.range[1]': to || xDataMax,
      });
    }

    fromInput.addEventListener('change', applyDateRange);
    toInput.addEventListener('change', applyDateRange);
  }

  // ─── Construir panel ────────────────────────────────────────────────────────

  function buildPanel(gd, items) {
    if (!gd.style.position || gd.style.position === 'static') {
      gd.style.position = 'relative';
    }

    var sync = function () { syncAll(gd, items); };

    // Date picker (a la izquierda, misma altura que el panel Edit)
    if (!gd.querySelector('#' + DATEPICKER_ID)) {
      buildDatePicker(gd);
    }

    var panel = el('div', { id: PANEL_ID, class: 'cb-panel' });

    // Header (drag handle) con botón Edit
    var header = el('div', { class: 'cb-header' });
    var grip = el('span', { class: 'cb-grip' }, '⠿');
    var editBtn = el('button', { class: 'cb-editbtn', type: 'button' }, 'Editar Indicadores');
    header.appendChild(grip);
    header.appendChild(editBtn);
    panel.appendChild(header);

    // Cuerpo colapsable (empieza oculto)
    var body = el('div', { class: 'cb-body', style: 'display:none;' });

    // Search
    var search = el('input', { class: 'cb-search', type: 'text', placeholder: 'Buscar...' });
    body.appendChild(search);

    // Botones
    var actions = el('div', { class: 'cb-actions' });
    var btnOn  = el('button', { class: 'cb-btn', type: 'button' }, 'All on');
    var btnOff = el('button', { class: 'cb-btn', type: 'button' }, 'All off');
    actions.appendChild(btnOn);
    actions.appendChild(btnOff);
    body.appendChild(actions);

    // Lista de items
    var groupsBox = el('div', { class: 'cb-groups' });

    items.forEach(function (it) {
      var row = el('div', { class: 'cb-item', id: 'cb-epu-item-' + it.i });
      var box = el('span', { class: 'cb-box' });
      var swatch = el('span', { class: 'cb-swatch', style: 'background:' + it.color + ';' });
      var label = el('span', { class: 'cb-label' });
      label.textContent = it.name;
      row.appendChild(box);
      row.appendChild(swatch);
      row.appendChild(label);

      // click simple → toggle; doble click → aislar
      var timer = null;
      row.addEventListener('click', function () {
        if (timer) return;
        timer = setTimeout(function () {
          setVisible(gd, it.i, !isVisible(gd, it.i)).then(sync);
          timer = null;
        }, 220);
      });
      row.addEventListener('dblclick', function () {
        if (timer) { clearTimeout(timer); timer = null; }
        isolate(gd, [it.i], 'trace:' + it.i, sync);
      });

      groupsBox.appendChild(row);
    });

    body.appendChild(groupsBox);
    panel.appendChild(body);
    gd.appendChild(panel);

    // Toggle Edit (no propaga pointerdown para no activar drag)
    editBtn.addEventListener('pointerdown', function (e) { e.stopPropagation(); });
    editBtn.addEventListener('click', function () {
      body.style.display = body.style.display === 'none' ? '' : 'none';
    });

    // Botones all on/off
    btnOn.addEventListener('click', function () {
      setMany(gd, items.map(function (it) { return it.i; }), true).then(sync);
    });
    btnOff.addEventListener('click', function () {
      setMany(gd, items.map(function (it) { return it.i; }), false).then(sync);
    });

    // Buscar
    search.addEventListener('input', function () {
      var q = (search.value || '').trim().toLowerCase();
      items.forEach(function (it) {
        var row = document.getElementById('cb-epu-item-' + it.i);
        if (row) row.style.display = (!q || it.name.toLowerCase().indexOf(q) >= 0) ? '' : 'none';
      });
    });

    // Estado inicial
    syncAll(gd, items);

    // ─── Drag ───────────────────────────────────────────────────────────────
    var dragging = false, offX = 0, offY = 0;

    header.addEventListener('pointerdown', function (e) {
      e.preventDefault();
      dragging = true;
      var rectG = gd.getBoundingClientRect();
      var rectP = panel.getBoundingClientRect();
      panel.style.right = 'auto';
      panel.style.bottom = 'auto';
      panel.style.left = (rectP.left - rectG.left) + 'px';
      panel.style.top  = (rectP.top  - rectG.top)  + 'px';
      offX = e.clientX - rectP.left;
      offY = e.clientY - rectP.top;
      header.setPointerCapture(e.pointerId);
    });

    header.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      var rectG = gd.getBoundingClientRect();
      var rectP = panel.getBoundingClientRect();
      var pad = 6;
      var L = Math.max(pad, Math.min(e.clientX - rectG.left - offX, rectG.width  - rectP.width  - pad));
      var T = Math.max(pad, Math.min(e.clientY - rectG.top  - offY, rectG.height - rectP.height - pad));
      panel.style.left = L + 'px';
      panel.style.top  = T + 'px';
    });

    header.addEventListener('pointerup', function (e) {
      dragging = false;
      try { header.releasePointerCapture(e.pointerId); } catch (_) {}
    });
  }

  // ─── Init ────────────────────────────────────────────────────────────────────

  function init() {
    // En Dash, dcc.Graph(id=GID) crea un wrapper div; el gd de Plotly es el hijo .js-plotly-plot
    var wrapper = document.getElementById(GID);
    if (!wrapper) return false;
    var gd = wrapper.querySelector('.js-plotly-plot') || wrapper;
    if (!gd || !gd.data || !gd.data.length) return false;

    var items = buildItems(gd.data);
    if (!items.length) return false;

    injectStyles(document);

    if (!gd.querySelector('#' + PANEL_ID)) {
      buildPanel(gd, items);
    }

    if (!gd._epuLegendAttached) {
      gd._epuLegendAttached = true;
      gd.on('plotly_afterplot', function () {
        if (!gd.querySelector('#' + PANEL_ID)) buildPanel(gd, buildItems(gd.data));
        else syncAll(gd, buildItems(gd.data));
      });
    }

    return true;
  }

  var obs = new MutationObserver(function () { if (init()) obs.disconnect(); });
  obs.observe(document.body, { childList: true, subtree: true });
  setTimeout(init, 500);

})();
