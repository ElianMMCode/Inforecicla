/* AdminCharts — helper para reducir duplicidad de Chart.js en templates admin */
var AdminCharts = (function() {
  var C = { success: '#198754', warning: '#ffc107', danger: '#dc3545', info: '#0dcaf0', primary: '#0d6efd', dark: '#212529' };
  var PALETA = [C.success, C.warning, C.danger, C.info, C.primary, '#6f42c1', '#fd7e14', '#20c997', '#d63384'];
  var BG_RGBA = { primary: 'rgba(13,110,253,0.08)', success: 'rgba(25,135,84,0.08)' };

  function _data(id) {
    var el = document.getElementById(id);
    return el ? JSON.parse(el.textContent) : [];
  }

  function doughnut(canvasId, dataId, labelKey, valueKey, colors) {
    var data = _data(dataId);
    if (!data.length) return;
    new Chart(document.getElementById(canvasId), {
      type: 'doughnut',
      data: {
        labels: data.map(function(d) { return d[labelKey]; }),
        datasets: [{ data: data.map(function(d) { return d[valueKey]; }), backgroundColor: colors || PALETA.slice(0, data.length), borderColor: '#fff', borderWidth: 2 }]
      },
      options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { position: 'bottom', labels: { padding: 10, usePointStyle: true, font: { size: 10 } } } } }
    });
  }

  function barH(canvasId, dataId, labelKey, valueKey, color, label) {
    var data = _data(dataId);
    if (!data.length) return;
    new Chart(document.getElementById(canvasId), {
      type: 'bar',
      data: { labels: data.map(function(d) { return d[labelKey]; }), datasets: [{ label: label || '', data: data.map(function(d) { return d[valueKey]; }), backgroundColor: color || C.info, borderRadius: 4 }] },
      options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true, ticks: { precision: 0 } }, y: { ticks: { font: { size: 9 } } } } }
    });
  }

  function trendLine(canvasId, dataId, colorKey) {
    var data = _data(dataId);
    if (!data.length) return;
    var ck = colorKey || 'primary';
    new Chart(document.getElementById(canvasId), {
      type: 'line',
      data: { labels: data.map(function(d) { return d.date; }), datasets: [{ label: '', data: data.map(function(d) { return d.count; }), borderColor: C[ck], backgroundColor: BG_RGBA[ck] || BG_RGBA.primary, fill: true, tension: 0.3, pointRadius: 2, pointHoverRadius: 4 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } }, x: { ticks: { maxTicksLimit: 8, font: { size: 9 } } } } }
    });
  }

  function initAll(configs) {
    configs.forEach(function(cfg) {
      if (cfg.type === 'doughnut') doughnut(cfg.canvas, cfg.dataId, cfg.labelKey || 'label', cfg.valueKey || 'count', cfg.colors);
      else if (cfg.type === 'barH') barH(cfg.canvas, cfg.dataId, cfg.labelKey || 'label', cfg.valueKey || 'count', cfg.color, cfg.label);
      else if (cfg.type === 'trendLine') trendLine(cfg.canvas, cfg.dataId, cfg.colorKey);
    });
  }

  return { C: C, PALETA: PALETA, doughnut: doughnut, barH: barH, trendLine: trendLine, initAll: initAll };
})();
