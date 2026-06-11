/**
 * Stamp Collection Manager — P1-2
 * Full CRUD UI for managing stamp collections with search, CSV import/export.
 */

(function() {
    "use strict";

    var collectionOpen = false;
    var collectionPage = 1;
    var collectionTotal = 0;
    var collectionSearch = "";
    var collectionSort = "country";
    var editingStampId = null;

    function initCollectionManager() {
        // Toggle
        var toggle = document.getElementById("toggle-collection");
        if (toggle) {
            toggle.addEventListener("change", function(e) {
                collectionOpen = e.target.checked;
                var panel = document.getElementById("collection-panel");
                if (collectionOpen) {
                    panel.classList.add("open");
                    loadCollection();
                } else {
                    panel.classList.remove("open");
                }
            });
        }

        var closeBtn = document.getElementById("collection-close");
        if (closeBtn) closeBtn.addEventListener("click", function() {
            collectionOpen = false;
            document.getElementById("collection-panel").classList.remove("open");
            if (toggle) toggle.checked = false;
        });

        // Search
        var searchInput = document.getElementById("collection-search");
        if (searchInput) {
            var searchTimer = null;
            searchInput.addEventListener("input", function() {
                clearTimeout(searchTimer);
                searchTimer = setTimeout(function() {
                    collectionSearch = searchInput.value;
                    collectionPage = 1;
                    loadCollection();
                }, 300);
            });
        }

        // Sort
        var sortSelect = document.getElementById("collection-sort");
        if (sortSelect) {
            sortSelect.addEventListener("change", function() {
                collectionSort = sortSelect.value;
                collectionPage = 1;
                loadCollection();
            });
        }

        // Add stamp
        var addBtn = document.getElementById("collection-add-btn");
        if (addBtn) addBtn.addEventListener("click", function() { openStampModal(); });

        // Import CSV
        var importBtn = document.getElementById("collection-import-btn");
        var csvInput = document.getElementById("collection-csv-input");
        if (importBtn && csvInput) {
            importBtn.addEventListener("click", function() { csvInput.click(); });
            csvInput.addEventListener("change", function() {
                if (csvInput.files.length > 0) importCSV(csvInput.files[0]);
            });
        }

        // Export CSV
        var exportBtn = document.getElementById("collection-export-btn");
        if (exportBtn) {
            exportBtn.addEventListener("click", function() {
                window.location.href = API_BASE + "/api/stamps/export/csv";
            });
        }

        // Import Excel
        var importExcelBtn = document.getElementById("collection-import-excel-btn");
        var excelInput = document.getElementById("collection-excel-input");
        if (importExcelBtn && excelInput) {
            importExcelBtn.addEventListener("click", function() { excelInput.click(); });
            excelInput.addEventListener("change", function() {
                if (excelInput.files.length > 0) importExcel(excelInput.files[0]);
            });
        }

        // Modal
        var modalClose = document.getElementById("stamp-modal-close");
        var modalCancel = document.getElementById("stamp-modal-cancel");
        var modalSave = document.getElementById("stamp-modal-save");
        var modalBackdrop = document.querySelector(".stamp-modal-backdrop");
        if (modalClose) modalClose.addEventListener("click", closeStampModal);
        if (modalCancel) modalCancel.addEventListener("click", closeStampModal);
        if (modalBackdrop) modalBackdrop.addEventListener("click", closeStampModal);
        if (modalSave) modalSave.addEventListener("click", saveStampModal);

        // Collection list click delegation
        var list = document.getElementById("collection-list");
        if (list) {
            list.addEventListener("click", function(e) {
                var item = e.target.closest(".collection-item");
                if (!item) return;
                var stampId = item.dataset.stampId;
                if (e.target.classList.contains("collection-item-delete")) {
                    e.stopPropagation();
                    deleteCollectionStamp(stampId);
                } else {
                    editCollectionStamp(stampId);
                }
            });
        }
    }

    async function loadCollection() {
        try {
            var params = new URLSearchParams({
                query: collectionSearch,
                sort_by: collectionSort,
                page: collectionPage,
                per_page: 20,
            });
            var response = await fetch(API_BASE + "/api/stamps?" + params);
            if (!response.ok) return;
            var data = response.json();
            collectionTotal = data.total;
            renderCollectionList(data.stamps);
            renderCollectionPagination();
            updateCollectionStats();
        } catch (e) {
            console.error("Failed to load collection:", e);
        }
    }

    function renderCollectionList(stamps) {
        var list = document.getElementById("collection-list");
        if (!list) return;
        if (stamps.length === 0) {
            list.innerHTML = '<div class="collection-empty">No stamps found. Add your first stamp or import from CSV.</div>';
            return;
        }
        list.innerHTML = stamps.map(function(s) {
            var imgHtml = s.image_path
                ? '<img src="' + API_BASE + '/images/' + escapeAttr(s.image_path) + '" style="width:100%;height:100%;object-fit:cover;border-radius:3px">'
                : '🏛';
            return '<div class="collection-item" data-stamp-id="' + escapeAttr(s.id) + '">' +
                '<div class="collection-item-img">' + imgHtml + '</div>' +
                '<div class="collection-item-info">' +
                    '<div class="collection-item-title">' + escapeHtml(s.description || "Untitled") + '</div>' +
                    '<div class="collection-item-meta">' + escapeHtml(s.country || "Unknown") + (s.year ? " · " + s.year : "") + (s.catalog_number ? " · " + s.catalog_number : "") + '</div>' +
                '</div>' +
                (s.purchase_price ? '<div class="collection-item-price">$' + parseFloat(s.purchase_price).toFixed(2) + '</div>' : '') +
                '<button class="collection-item-delete" title="Delete" style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:4px;font-size:14px;">✕</button>' +
            '</div>';
        }).join("");
    }

    function renderCollectionPagination() {
        var container = document.getElementById("collection-pagination");
        if (!container) return;
        var totalPages = Math.ceil(collectionTotal / 20);
        if (totalPages <= 1) { container.innerHTML = ""; return; }
        var html = '';
        if (collectionPage > 1) {
            html += '<button class="collection-page-btn" data-page="' + (collectionPage - 1) + '">←</button>';
        }
        html += '<span class="collection-page-info">Page ' + collectionPage + ' of ' + totalPages + ' (' + collectionTotal + ' stamps)</span>';
        if (collectionPage < totalPages) {
            html += '<button class="collection-page-btn" data-page="' + (collectionPage + 1) + '">→</button>';
        }
        container.innerHTML = html;
        container.querySelectorAll(".collection-page-btn").forEach(function(btn) {
            btn.addEventListener("click", function() {
                collectionPage = parseInt(btn.dataset.page);
                loadCollection();
            });
        });
    }

    async function updateCollectionStats() {
        try {
            var response = await fetch(API_BASE + "/api/stamps/stats");
            if (!response.ok) return;
            var stats = response.json();
            var el = document.getElementById("collection-stats");
            if (el) el.textContent = stats.total_stamps + " stamp" + (stats.total_stamps !== 1 ? "s" : "");
        } catch (e) {}
    }

    function openStampModal(stamp) {
        editingStampId = stamp ? stamp.id : null;
        document.getElementById("stamp-modal-title").textContent = stamp ? "Edit Stamp" : "Add Stamp";
        document.getElementById("sm-country").value = stamp ? stamp.country || "" : "";
        document.getElementById("sm-year").value = stamp ? stamp.year || "" : "";
        document.getElementById("sm-description").value = stamp ? stamp.description || "" : "";
        document.getElementById("sm-catalog").value = stamp ? stamp.catalog_number || "" : "";
        document.getElementById("sm-catalog-type").value = stamp ? stamp.catalog_type || "SG" : "SG";
        document.getElementById("sm-denomination").value = stamp ? stamp.denomination || "" : "";
        document.getElementById("sm-condition").value = stamp ? stamp.condition || "" : "";
        document.getElementById("sm-price").value = stamp ? stamp.purchase_price || "" : "";
        document.getElementById("sm-notes").value = stamp ? stamp.notes || "" : "";

        // Populate image dropdown
        var imgSelect = document.getElementById("sm-image");
        imgSelect.innerHTML = '<option value="">No image</option>';
        var images = window._uploadedImages || [];
        images.forEach(function(img) {
            var opt = document.createElement("option");
            opt.value = img;
            opt.textContent = img;
            if (stamp && img === stamp.image_path) opt.selected = true;
            imgSelect.appendChild(opt);
        });

        document.getElementById("stamp-modal").classList.add("open");
    }

    function closeStampModal() {
        document.getElementById("stamp-modal").classList.remove("open");
        editingStampId = null;
    }

    async function saveStampModal() {
        var data = {
            country: document.getElementById("sm-country").value,
            year: parseInt(document.getElementById("sm-year").value) || 0,
            description: document.getElementById("sm-description").value,
            catalog_number: document.getElementById("sm-catalog").value,
            catalog_type: document.getElementById("sm-catalog-type").value,
            denomination: document.getElementById("sm-denomination").value,
            condition: document.getElementById("sm-condition").value,
            purchase_price: parseFloat(document.getElementById("sm-price").value) || 0,
            image_path: document.getElementById("sm-image").value,
            notes: document.getElementById("sm-notes").value,
        };
        if (!data.description) {
            showToast("Description is required", "error");
            return;
        }
        try {
            var url = API_BASE + "/api/stamps" + (editingStampId ? "/" + editingStampId : "");
            var method = editingStampId ? "PUT" : "POST";
            var response = await fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data),
            });
            if (!response.ok) {
                var err = await response.json();
                throw new Error(err.detail || "Save failed");
            }
            closeStampModal();
            loadCollection();
            showToast(editingStampId ? "Stamp updated" : "Stamp added", "success");
        } catch (e) {
            showToast("Error: " + e.message, "error");
        }
    }

    async function editCollectionStamp(stampId) {
        try {
            var response = await fetch(API_BASE + "/api/stamps/" + stampId);
            if (!response.ok) throw new Error("Stamp not found");
            var stamp = await response.json();
            openStampModal(stamp);
        } catch (e) {
            showToast("Error: " + e.message, "error");
        }
    }

    async function deleteCollectionStamp(stampId) {
        if (!confirm("Delete this stamp from your collection?")) return;
        try {
            var response = await fetch(API_BASE + "/api/stamps/" + stampId, { method: "DELETE" });
            if (!response.ok) throw new Error("Delete failed");
            loadCollection();
            showToast("Stamp deleted", "success");
        } catch (e) {
            showToast("Error: " + e.message, "error");
        }
    }

    async function importCSV(file) {
        try {
            var formData = new FormData();
            formData.append("file", file);
            var response = await fetch(API_BASE + "/api/stamps/import", {
                method: "POST",
                body: formData,
            });
            if (!response.ok) throw new Error("Import failed");
            var result = await response.json();
            var msg = "Imported " + result.imported + " stamps";
            if (result.errors.length > 0) {
                msg += " (" + result.errors.length + " errors)";
            }
            showToast(msg, result.errors.length > 0 ? "info" : "success");
            loadCollection();
        } catch (e) {
            showToast("Import error: " + e.message, "error");
        }
        // Reset input
        document.getElementById("collection-csv-input").value = "";
    }

    async function importExcel(file) {
        try {
            var formData = new FormData();
            formData.append("file", file);
            var response = await fetch(API_BASE + "/api/stamps/import-excel", {
                method: "POST",
                body: formData,
            });
            if (!response.ok) {
                var err = await response.json();
                throw new Error(err.detail || "Import failed");
            }
            var result = await response.json();
            var msg = "Imported " + result.imported + " stamps from Excel";
            if (result.errors.length > 0) msg += " (" + result.errors.length + " errors)";
            showToast(msg, result.errors.length > 0 ? "info" : "success");
            loadCollection();
        } catch (e) {
            showToast("Import error: " + e.message, "error");
        }
        document.getElementById("collection-excel-input").value = "";
    }

    // Initialize on DOM ready
    document.addEventListener("DOMContentLoaded", initCollectionManager);
})();
