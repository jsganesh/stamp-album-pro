/**
 * Version History UI (P2-15)
 * Browse, restore, and manage file versions.
 */

(function() {
    "use strict";

    var historyOpen = false;

    function initVersionHistory() {
        var toggle = document.getElementById("toggle-history");
        if (toggle) {
            toggle.addEventListener("change", function(e) {
                historyOpen = e.target.checked;
                var panel = document.getElementById("history-panel");
                if (historyOpen) {
                    panel.classList.add("open");
                    loadVersions();
                } else {
                    panel.classList.remove("open");
                }
            });
        }

        var closeBtn = document.getElementById("history-close");
        if (closeBtn) closeBtn.addEventListener("click", function() {
            historyOpen = false;
            document.getElementById("history-panel").classList.remove("open");
            if (toggle) toggle.checked = false;
        });

        var saveBtn = document.getElementById("history-save-btn");
        if (saveBtn) saveBtn.addEventListener("click", saveCurrentVersion);

        var filterInput = document.getElementById("history-filter");
        if (filterInput) {
            var filterTimer = null;
            filterInput.addEventListener("input", function() {
                clearTimeout(filterTimer);
                filterTimer = setTimeout(function() { loadVersions(); }, 300);
            });
        }
    }

    async function loadVersions() {
        var filename = currentFile || "";
        var filter = document.getElementById("history-filter") ? document.getElementById("history-filter").value : "";

        try {
            var url = API_BASE + "/api/version/" + encodeURIComponent(filename);
            var response = await fetch(url);
            if (!response.ok) return;
            var data = await response.json();

            var list = document.getElementById("history-list");
            var stats = document.getElementById("history-stats");
            if (stats) stats.textContent = data.count + " version" + (data.count !== 1 ? "s" : "");

            if (data.versions.length === 0) {
                list.innerHTML = '<div class="collection-empty">No versions saved yet.</div>';
                return;
            }

            list.innerHTML = data.versions.map(function(v) {
                var time = new Date(v.timestamp);
                var timeStr = time.toLocaleDateString() + " " + time.toLocaleTimeString();
                var meta = v.dsl_length + " chars";
                var comment = v.comment ? escapeHtml(v.comment) : "";
                return '<div class="history-item" data-version-id="' + escapeAttr(v.id) + '">' +
                    '<div class="history-item-info">' +
                        '<div class="history-item-time">' + escapeHtml(timeStr) + '</div>' +
                        '<div class="history-item-meta">' + escapeHtml(meta) + ' &middot; ' + escapeHtml(v.dsl_hash) + '</div>' +
                        (comment ? '<div class="history-item-comment">' + comment + '</div>' : '') +
                    '</div>' +
                    '<div class="history-item-actions">' +
                        '<button class="history-action-btn restore" title="Restore this version" data-version-id="' + escapeAttr(v.id) + '">Restore</button>' +
                        '<button class="history-action-btn delete" title="Delete" data-version-id="' + escapeAttr(v.id) + '">&times;</button>' +
                    '</div>' +
                '</div>';
            }).join("");

            // Add click handlers
            list.querySelectorAll(".history-action-btn.restore").forEach(function(btn) {
                btn.addEventListener("click", function(e) {
                    e.stopPropagation();
                    restoreVersion(btn.dataset.versionId);
                });
            });
            list.querySelectorAll(".history-action-btn.delete").forEach(function(btn) {
                btn.addEventListener("click", function(e) {
                    e.stopPropagation();
                    deleteVersion(btn.dataset.versionId);
                });
            });

        } catch (e) {
            console.error("Failed to load versions:", e);
        }
    }

    async function saveCurrentVersion() {
        var dsl = editor.getValue();
        if (!dsl.trim()) { showToast("Nothing to save", "error"); return; }
        var filename = currentFile || "untitled.slbum";
        var comment = document.getElementById("history-comment") ? document.getElementById("history-comment").value : "";

        try {
            var response = await fetch(API_BASE + "/api/version/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: filename, dsl: dsl, comment: comment }),
            });
            if (!response.ok) throw new Error("Save failed");
            var result = await response.json();
            showToast("Version saved (" + result.dsl_hash + ")", "success");
            loadVersions();
        } catch (e) {
            showToast("Error: " + e.message, "error");
        }
    }

    async function restoreVersion(versionId) {
        if (!confirm("Restore this version? Current changes will be lost.")) return;
        var filename = currentFile || "untitled.slbum";

        try {
            var response = await fetch(API_BASE + "/api/version/" + encodeURIComponent(filename) + "/" + encodeURIComponent(versionId));
            if (!response.ok) throw new Error("Version not found");
            var data = await response.json();
            editor.setValue(data.dsl);
            saveUndoState();
            schedulePreview();
            showToast("Version restored", "success");
        } catch (e) {
            showToast("Error: " + e.message, "error");
        }
    }

    async function deleteVersion(versionId) {
        if (!confirm("Delete this version permanently?")) return;
        var filename = currentFile || "untitled.slbum";

        try {
            var response = await fetch(API_BASE + "/api/version/" + encodeURIComponent(filename) + "/" + encodeURIComponent(versionId), {
                method: "DELETE",
            });
            if (!response.ok) throw new Error("Delete failed");
            showToast("Version deleted", "success");
            loadVersions();
        } catch (e) {
            showToast("Error: " + e.message, "error");
        }
    }

    // Auto-save version on file save
    var origSaveFile = window.saveFile;
    window.saveFile = async function() {
        if (origSaveFile) await origSaveFile();
        // Auto-save a version
        var dsl = editor.getValue();
        if (dsl.trim() && currentFile) {
            try {
                await fetch(API_BASE + "/api/version/save", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filename: currentFile, dsl: dsl, comment: "Auto-save" }),
                });
            } catch (e) { /* silent */ }
        }
    };

    document.addEventListener("DOMContentLoaded", initVersionHistory);
})();
