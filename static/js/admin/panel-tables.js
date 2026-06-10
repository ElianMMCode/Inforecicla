(function () {
  "use strict";

  function escapeHTML(str) {
    let div = document.createElement("div");
    div.appendChild(document.createTextNode(str || ""));
    return div.innerHTML;
  }

  function escapeAttr(str) {
    let div = document.createElement("div");
    div.dataset.x = str || "";
    return div.dataset.x || "";
  }

  globalThis.AdminTable = AdminTable;

  function AdminTable(config) {
    this.data = config.data || [];
    this.filteredData = this.data.slice();
    this.pageSize = config.pageSize || 10;
    this.currentPage = 1;
    this.tableBodyId = config.tableBodyId || config.containerId;
    this.pagerId = config.pagerId;
    this.footerInfoId = config.footerInfoId;
    this.countBadgeId = config.countBadgeId;
    this.columns = config.columns || [];
    this.filterFns = config.filterFns || [];
    this.onAfterRender = config.onAfterRender || null;
    this.defaultSort = config.defaultSort || null;
    this.filterFormId = config.filterFormId || null;

    if (this.defaultSort) {
      this.data.sort(this.defaultSort);
      this.filteredData.sort(this.defaultSort);
    }

    this.render();
    this.bindFilterForm();
  }

  AdminTable.prototype.render = function () {
    this.renderTable();
    this.renderPagination();
    this.renderFooter();
    if (this.onAfterRender) this.onAfterRender();
  };

  AdminTable.prototype.applySearch = function (searchText) {
    let q = (searchText || "").toLowerCase();
    this.filteredData = this.data.filter((row) => {
      if (!q) return true;
      return this.filterFns.some((fn) => fn(row, q));
    });
  };

  AdminTable.prototype.applyFilter = function (filterKey, filterValue) {
    if (!filterValue || filterValue === "") {
      this.applySearch(this._lastSearch || "");
      return;
    }
    let val = filterValue.toLowerCase();
    this.filteredData = this.filteredData.filter((row) => {
      let cell = row[filterKey];
      if (cell === null || cell === undefined) return false;
      return String(cell).toLowerCase() === val;
    });
  };

  AdminTable.prototype.fullFilter = function () {
    this.applySearch(this._lastSearch || "");
    if (!this._extraFilters) return;
    Object.keys(this._extraFilters).forEach((key) => {
      let val = this._extraFilters[key];
      if (val === null || val === undefined || val === "") return;
      let matchVal = typeof val === "boolean" ? val : String(val).toLowerCase();
      this.filteredData = this.filteredData.filter((row) => {
        let cell = row[key];
        if (cell === null || cell === undefined) return false;
        if (typeof matchVal === "boolean") return cell === matchVal;
        return String(cell).toLowerCase() === matchVal;
      });
    });
  };

  AdminTable.prototype.setSearch = function (text) {
    this._lastSearch = text;
    this.currentPage = 1;
    this.fullFilter();
    this.filteredData = this.filteredData.slice();
    this.render();
  };

  AdminTable.prototype.setExtraFilter = function (key, value) {
    if (!this._extraFilters) this._extraFilters = {};
    this._extraFilters[key] = value;
    this.currentPage = 1;
    this.fullFilter();
    this.render();
  };

  AdminTable.prototype.removeExtraFilter = function (key) {
    if (!this._extraFilters) return;
    delete this._extraFilters[key];
    this.currentPage = 1;
    this.fullFilter();
    this.render();
  };

  AdminTable.prototype.clearExtraFilters = function () {
    this._extraFilters = {};
    this.currentPage = 1;
    this.fullFilter();
    this.render();
  };

  AdminTable.prototype.setFilters = function (search, extraFilters) {
    this._lastSearch = search || "";
    this._extraFilters = extraFilters || {};
    this.currentPage = 1;
    this.fullFilter();
    this.render();
  };

  AdminTable.prototype.bindFilterForm = function () {
    if (!this.filterFormId) return;
    let form = document.getElementById(this.filterFormId);
    if (!form) return;

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      let searchInput = form.querySelector('input[name="q"]');
      if (searchInput) this.setSearch(searchInput.value || "");
    });

    let qInput = form.querySelector('input[name="q"]');
    if (qInput) {
      qInput.addEventListener("input", () => {
        if (!qInput.value.trim()) this.setSearch("");
      });
    }
  };

  AdminTable.prototype.renderTable = function () {
    let start = (this.currentPage - 1) * this.pageSize;
    let page = this.filteredData.slice(start, start + this.pageSize);
    let tbody = document.getElementById(this.tableBodyId);
    if (!tbody) return;
    let cols = this.columns.length;

    if (!page.length) {
      tbody.innerHTML =
        '<tr><td colspan="' +
        cols +
        '" class="text-center text-muted py-4">No se encontraron registros.</td></tr>';
      return;
    }

    tbody.innerHTML = page
      .map((row) => {
        return this.renderRow(row);
      })
      .join("");
  };

  AdminTable.prototype.renderRow = function (data) {
    let cells = this.columns.map((col) => {
      let cls = col.className ? ' class="' + col.className + '"' : "";
      return "<td" + cls + ">" + col.render(data) + "</td>";
    });
    return "<tr>" + cells.join("") + "</tr>";
  };

  AdminTable.prototype.renderPagination = function () {
    let total = this.filteredData.length;
    let pages = Math.ceil(total / this.pageSize);
    let pager = document.getElementById(this.pagerId);
    if (!pager) return;

    if (pages <= 1) {
      pager.innerHTML = "";
      return;
    }

    let html = "";
    html +=
      '<li class="page-item' +
      (this.currentPage <= 1 ? " disabled" : "") +
      '">' +
      '<a class="page-link" href="#" data-page="prev">&laquo; Anterior</a></li>';

    let maxVisible = 5;
    let half = Math.floor(maxVisible / 2);
    let startPage = Math.max(1, this.currentPage - half);
    let endPage = Math.min(pages, startPage + maxVisible - 1);
    if (endPage - startPage + 1 < maxVisible) {
      startPage = Math.max(1, endPage - maxVisible + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      html +=
        '<li class="page-item' +
        (i === this.currentPage ? " active" : "") +
        '">' +
        '<a class="page-link" href="#" data-page="' +
        i +
        '">' +
        i +
        "</a></li>";
    }

    html +=
      '<li class="page-item' +
      (this.currentPage >= pages ? " disabled" : "") +
      '">' +
      '<a class="page-link" href="#" data-page="next">Siguiente &raquo;</a></li>';

    pager.innerHTML = html;
    this._bindPagerEvents(pager);
  };

  AdminTable.prototype._bindPagerEvents = function (pager) {
    let totalPages = Math.ceil(this.filteredData.length / this.pageSize);

    pager.querySelectorAll(".page-link").forEach((link) => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        let page = link.dataset.page;
        if (page === "prev") {
          if (this.currentPage > 1) this.currentPage--;
        } else if (page === "next") {
          if (this.currentPage < totalPages) this.currentPage++;
        } else {
          let p = Number.parseInt(page, 10);
          if (p >= 1 && p <= totalPages) this.currentPage = p;
        }
        this.render();
      });
    });
  };

  AdminTable.prototype.renderFooter = function () {
    let total = this.filteredData.length;
    let start = total ? (this.currentPage - 1) * this.pageSize + 1 : 0;
    let end = Math.min(start + this.pageSize - 1, total);

    if (this.countBadgeId) {
      let badge = document.getElementById(this.countBadgeId);
      if (badge) badge.textContent = total + " registros";
    }

    if (this.footerInfoId) {
      let footer = document.getElementById(this.footerInfoId);
      if (footer)
        footer.textContent =
          "Mostrando " + start + "\u2013" + end + " de " + total + " registros";
    }
  };

  globalThis.AdminTable = AdminTable;
  globalThis.escapeHTML = escapeHTML;
  globalThis.escapeAttr = escapeAttr;
})();

function readJSONData(scriptId) {
  let el = document.getElementById(scriptId);
  if (!el) return [];
  try {
    let data = JSON.parse(el.textContent || "[]");
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}
