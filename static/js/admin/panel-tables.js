(function() {
    'use strict';

    function escapeHTML(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str || ''));
        return div.innerHTML;
    }

    function escapeAttr(str) {
        var div = document.createElement('div');
        div.setAttribute('data-x', str || '');
        return div.getAttribute('data-x') || '';
    }

    window.AdminTable = AdminTable;

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
            var self = this;
            this.data.sort(this.defaultSort);
            this.filteredData.sort(this.defaultSort);
        }

        this.render();
        this.bindFilterForm();
    }

    AdminTable.prototype.render = function() {
        this.renderTable();
        this.renderPagination();
        this.renderFooter();
        if (this.onAfterRender) this.onAfterRender();
    };

    AdminTable.prototype.applySearch = function(searchText) {
        var self = this;
        var q = (searchText || '').toLowerCase();
        this.filteredData = this.data.filter(function(row) {
            if (!q) return true;
            return self.filterFns.some(function(fn) { return fn(row, q); });
        });
    };

    AdminTable.prototype.applyFilter = function(filterKey, filterValue) {
        if (!filterValue || filterValue === '') {
            this.applySearch(this._lastSearch || '');
            return;
        }
        var self = this;
        var val = filterValue.toLowerCase();
        this.filteredData = this.filteredData.filter(function(row) {
            var cell = row[filterKey];
            if (cell === null || cell === undefined) return false;
            return String(cell).toLowerCase() === val;
        });
    };

    AdminTable.prototype.fullFilter = function() {
        this.applySearch(this._lastSearch || '');
        if (!this._extraFilters) return;
        var self = this;
        Object.keys(this._extraFilters).forEach(function(key) {
            var val = self._extraFilters[key];
            if (val === null || val === undefined || val === '') return;
            var matchVal = typeof val === 'boolean' ? val : String(val).toLowerCase();
            self.filteredData = self.filteredData.filter(function(row) {
                var cell = row[key];
                if (cell === null || cell === undefined) return false;
                if (typeof matchVal === 'boolean') return cell === matchVal;
                return String(cell).toLowerCase() === matchVal;
            });
        });
    };

    AdminTable.prototype.setSearch = function(text) {
        this._lastSearch = text;
        this.currentPage = 1;
        this.fullFilter();
        this.filteredData = this.filteredData.slice();
        this.render();
    };

    AdminTable.prototype.setExtraFilter = function(key, value) {
        if (!this._extraFilters) this._extraFilters = {};
        this._extraFilters[key] = value;
        this.currentPage = 1;
        this.fullFilter();
        this.render();
    };

    AdminTable.prototype.removeExtraFilter = function(key) {
        if (!this._extraFilters) return;
        delete this._extraFilters[key];
        this.currentPage = 1;
        this.fullFilter();
        this.render();
    };

    AdminTable.prototype.clearExtraFilters = function() {
        this._extraFilters = {};
        this.currentPage = 1;
        this.fullFilter();
        this.render();
    };

    AdminTable.prototype.setFilters = function(search, extraFilters) {
        this._lastSearch = search || '';
        this._extraFilters = extraFilters || {};
        this.currentPage = 1;
        this.fullFilter();
        this.render();
    };

    AdminTable.prototype.bindFilterForm = function() {
        if (!this.filterFormId) return;
        var self = this;
        var form = document.getElementById(this.filterFormId);
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var searchInput = form.querySelector('input[name="q"]');
            if (searchInput) self.setSearch(searchInput.value || '');
        });

        var qInput = form.querySelector('input[name="q"]');
        if (qInput) {
            qInput.addEventListener('input', function() {
                if (!this.value.trim()) self.setSearch('');
            });
        }
    };

    AdminTable.prototype.renderTable = function() {
        var self = this;
        var start = (this.currentPage - 1) * this.pageSize;
        var page = this.filteredData.slice(start, start + this.pageSize);
        var tbody = document.getElementById(this.tableBodyId);
        if (!tbody) return;
        var cols = this.columns.length;

        if (!page.length) {
            tbody.innerHTML = '<tr><td colspan="' + cols + '" class="text-center text-muted py-4">No se encontraron registros.</td></tr>';
            return;
        }

        tbody.innerHTML = page.map(function(row) { return self.renderRow(row); }).join('');
    };

    AdminTable.prototype.renderRow = function(data) {
        var cells = this.columns.map(function(col) {
            var cls = col.className ? ' class="' + col.className + '"' : '';
            return '<td' + cls + '>' + col.render(data) + '</td>';
        });
        return '<tr>' + cells.join('') + '</tr>';
    };

    AdminTable.prototype.renderPagination = function() {
        var total = this.filteredData.length;
        var pages = Math.ceil(total / this.pageSize);
        var pager = document.getElementById(this.pagerId);
        if (!pager) return;

        if (pages <= 1) {
            pager.innerHTML = '';
            return;
        }

        var html = '';
        html += '<li class="page-item' + (this.currentPage <= 1 ? ' disabled' : '') + '">'
            + '<a class="page-link" href="#" data-page="prev">&laquo; Anterior</a></li>';

        var maxVisible = 5;
        var half = Math.floor(maxVisible / 2);
        var startPage = Math.max(1, this.currentPage - half);
        var endPage = Math.min(pages, startPage + maxVisible - 1);
        if (endPage - startPage + 1 < maxVisible) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        for (var i = startPage; i <= endPage; i++) {
            html += '<li class="page-item' + (i === this.currentPage ? ' active' : '') + '">'
                + '<a class="page-link" href="#" data-page="' + i + '">' + i + '</a></li>';
        }

        html += '<li class="page-item' + (this.currentPage >= pages ? ' disabled' : '') + '">'
            + '<a class="page-link" href="#" data-page="next">Siguiente &raquo;</a></li>';

        pager.innerHTML = html;
        this._bindPagerEvents(pager);
    };

    AdminTable.prototype._bindPagerEvents = function(pager) {
        var self = this;
        var totalPages = Math.ceil(this.filteredData.length / this.pageSize);

        pager.querySelectorAll('.page-link').forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                var page = this.dataset.page;
                if (page === 'prev') {
                    if (self.currentPage > 1) self.currentPage--;
                } else if (page === 'next') {
                    if (self.currentPage < totalPages) self.currentPage++;
                } else {
                    var p = parseInt(page);
                    if (p >= 1 && p <= totalPages) self.currentPage = p;
                }
                self.render();
            });
        });
    };

    AdminTable.prototype.renderFooter = function() {
        var total = this.filteredData.length;
        var start = total ? (this.currentPage - 1) * this.pageSize + 1 : 0;
        var end = Math.min(start + this.pageSize - 1, total);

        if (this.countBadgeId) {
            var badge = document.getElementById(this.countBadgeId);
            if (badge) badge.textContent = total + ' registros';
        }

        if (this.footerInfoId) {
            var footer = document.getElementById(this.footerInfoId);
            if (footer) footer.textContent = 'Mostrando ' + start + '\u2013' + end + ' de ' + total + ' registros';
        }
    };

    window.AdminTable = AdminTable;
    window.escapeHTML = escapeHTML;
    window.escapeAttr = escapeAttr;
})();

function readJSONData(scriptId) {
    var el = document.getElementById(scriptId);
    if (!el) return [];
    try {
        var data = JSON.parse(el.textContent || '[]');
        return Array.isArray(data) ? data : [];
    } catch (e) {
        return [];
    }
}
