const API_BASE = "";
const DEBOUNCE_MS = 400;

let editor = null;
let currentFile = null;
let debounceTimer = null;
let isModified = false;

// Default template
const DEFAULT_DSL = `ALBUM_TITLE("My Stamp Album")
ALBUM_AUTHOR("Collector")

ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)

PAGE_START
PAGE_TEXT_CENTER("Helvetica" 18 "My Stamp Collection" 5)
PAGE_TEXT_CENTER("Helvetica" 12 "A carefully curated album")

ROW_START_FS("Helvetica" 10 5 180)
STAMP_ADD(40 30 "First Stamp")
STAMP_ADD(40 30 "Second Stamp")
STAMP_ADD(40 30 "Third Stamp")

ROW_START_FS("Helvetica" 10 5 180)
STAMP_ADD(40 30 "Fourth Stamp")
STAMP_ADD(40 30 "Fifth Stamp")
`;

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    initEditor();
    initButtons();
    initKeyboardShortcuts();
    initVisualBuilder();
    loadFileList();
    setEditorContent(DEFAULT_DSL);
    refreshPreview();
});

function initEditor() {
    editor = CodeMirror(document.getElementById("editor-container"), {
        value: "",
        mode: "xml",
        theme: "material-darker",
        lineNumbers: true,
        lineWrapping: true,
        tabSize: 4,
        indentWithTabs: false,
        extraKeys: {
            "Ctrl-S": () => saveFile(),
            "Cmd-S": () => saveFile(),
        },
    });

    editor.on("change", () => {
        isModified = true;
        updateSaveStatus("Modified");
        schedulePreview();
    });
}

function initButtons() {
    document.getElementById("btn-new").addEventListener("click", newAlbum);
    document.getElementById("btn-open").addEventListener("click", openFile);
    document.getElementById("btn-save").addEventListener("click", saveFile);
    document.getElementById("btn-export").addEventListener("click", exportPDF);
    document.getElementById("btn-refresh-preview").addEventListener("click", refreshPreview);
    document.getElementById("btn-upload").addEventListener("click", () => {
        document.getElementById("file-input").click();
    });
    document.getElementById("file-input").addEventListener("change", handleFileUpload);

    document.getElementById("toggle-preview").addEventListener("change", (e) => {
        const panel = document.getElementById("preview-panel");
        panel.classList.toggle("preview-hidden", !e.target.checked);
    });

    document.getElementById("toggle-sidebar").addEventListener("change", (e) => {
        const sidebar = document.getElementById("sidebar");
        sidebar.classList.toggle("sidebar-hidden", !e.target.checked);
    });
}

function initKeyboardShortcuts() {
    document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "n") {
            e.preventDefault();
            newAlbum();
        }
        if ((e.ctrlKey || e.metaKey) && e.key === "o") {
            e.preventDefault();
            openFile();
        }
        if ((e.ctrlKey || e.metaKey) && e.key === "e") {
            e.preventDefault();
            exportPDF();
        }
    });
}

// Editor operations
function setEditorContent(content) {
    editor.setValue(content);
    editor.setCursor(0, 0);
    isModified = false;
    updateSaveStatus("Saved");
}

function getEditorContent() {
    return editor.getValue();
}

// Preview
function schedulePreview() {
    clearTimeout(debounceTimer);
    document.getElementById("preview-status").innerHTML = '<span class="spinner"></span> Rendering...';
    debounceTimer = setTimeout(refreshPreview, DEBOUNCE_MS);
}

async function refreshPreview() {
    const dsl = getEditorContent();
    if (!dsl.trim()) {
        setPreviewHtml("<html><body style='display:flex;align-items:center;justify-content:center;height:100vh;color:#999;font-family:system-ui'><p>Enter DSL code to see preview</p></body></html>");
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/render`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dsl, source_path: currentFile || "untitled.slbum" }),
        });

        if (!response.ok) {
            const error = await response.json();
            setPreviewHtml(`<html><body style='padding:40px;font-family:system-ui;color:#f85149'><h3>Preview Error</h3><pre>${escapeHtml(error.detail)}</pre></body></html>`);
            document.getElementById("preview-status").textContent = "Error";
            return;
        }

        const html = await response.text();
        setPreviewHtml(html);
        document.getElementById("preview-status").textContent = "Preview updated";
    } catch (err) {
        document.getElementById("preview-status").textContent = "Preview failed";
    }
}

function setPreviewHtml(html) {
    const frame = document.getElementById("preview-frame");
    frame.srcdoc = html;
}

// File operations
function newAlbum() {
    if (isModified && !confirm("Discard unsaved changes?")) return;
    currentFile = null;
    document.getElementById("file-name").textContent = "Untitled";
    document.getElementById("btn-save").disabled = true;
    document.getElementById("btn-export").disabled = true;
    setEditorContent(DEFAULT_DSL);
    updateFileListActive();
}

function openFile() {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".slbum,.txt";
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            currentFile = file.name;
            document.getElementById("file-name").textContent = file.name;
            document.getElementById("btn-save").disabled = false;
            document.getElementById("btn-export").disabled = false;
            setEditorContent(ev.target.result);
            showToast(`Opened ${file.name}`, "success");
        };
        reader.onerror = () => showToast("Failed to read file", "error");
        reader.readAsText(file);
    };
    input.click();
}

async function loadFile(filename) {
    try {
        const response = await fetch(`${API_BASE}/files/${encodeURIComponent(filename)}`);
        if (!response.ok) throw new Error("Failed to load file");
        const content = await response.text();
        currentFile = filename;
        document.getElementById("file-name").textContent = filename;
        document.getElementById("btn-save").disabled = false;
        document.getElementById("btn-export").disabled = false;
        setEditorContent(content);
        updateFileListActive();
        showToast(`Opened ${filename}`, "success");
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

async function saveFile() {
    if (!currentFile) {
        const name = prompt("Save as:", "album.slbum");
        if (!name) return;
        currentFile = name.endsWith(".slbum") ? name : name + ".slbum";
        document.getElementById("file-name").textContent = currentFile;
    }

    try {
        const response = await fetch(`${API_BASE}/files/${encodeURIComponent(currentFile)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: getEditorContent() }),
        });

        if (!response.ok) throw new Error("Failed to save file");
        isModified = false;
        updateSaveStatus("Saved");
        document.getElementById("btn-export").disabled = false;
        loadFileList();
        showToast(`Saved ${currentFile}`, "success");
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

async function deleteFile(filename) {
    if (!confirm(`Delete ${filename}?`)) return;
    try {
        const response = await fetch(`${API_BASE}/files/${encodeURIComponent(filename)}`, {
            method: "DELETE",
        });
        if (!response.ok) throw new Error("Failed to delete");
        if (currentFile === filename) newAlbum();
        loadFileList();
        showToast(`Deleted ${filename}`, "success");
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    try {
        const content = await file.text();
        const response = await fetch(`${API_BASE}/files/${encodeURIComponent(file.name)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content }),
        });

        if (!response.ok) throw new Error("Failed to upload");
        loadFileList();
        loadFile(file.name);
        showToast(`Uploaded ${file.name}`, "success");
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }

    e.target.value = "";
}

// PDF Export
async function exportPDF() {
    const dsl = getEditorContent();
    document.getElementById("status-left").textContent = "Generating PDF...";

    try {
        const response = await fetch(`${API_BASE}/export`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dsl, source_path: currentFile || "untitled.slbum" }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = currentFile ? currentFile.replace(".slbum", ".pdf") : "album.pdf";
        a.click();
        URL.revokeObjectURL(url);
        document.getElementById("status-left").textContent = "PDF exported";
        showToast("PDF exported successfully", "success");
    } catch (err) {
        document.getElementById("status-left").textContent = "Export failed";
        showToast("Export failed: " + err.message, "error");
    }
}

// File list sidebar
async function loadFileList() {
    try {
        const response = await fetch(`${API_BASE}/files`);
        if (!response.ok) return;
        const files = await response.json();
        renderFileList(files);
    } catch (err) {
        // Silently fail - sidebar is optional
    }
}

function renderFileList(files) {
    const list = document.getElementById("file-list");
    if (files.length === 0) {
        list.innerHTML = '<div style="padding:16px;text-align:center;color:var(--text-muted);font-size:13px">No files yet.<br>Upload a .slbum file to get started.</div>';
        return;
    }

    list.innerHTML = files.map((f) => `
        <div class="file-item ${f === currentFile ? 'active' : ''}" onclick="loadFile('${escapeAttr(f)}')">
            <span>${escapeHtml(f)}</span>
            <div class="file-actions">
                <button onclick="event.stopPropagation();deleteFile('${escapeAttr(f)}')" title="Delete">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </div>
        </div>
    `).join("");
}

function updateFileListActive() {
    document.querySelectorAll(".file-item").forEach((el) => {
        el.classList.toggle("active", el.textContent.trim() === currentFile);
    });
}

// UI helpers
function updateSaveStatus(status) {
    document.getElementById("save-status").textContent = status;
}

function showToast(message, type = "info") {
    const existing = document.querySelector(".toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    return str.replace(/'/g, "\\'").replace(/"/g, "&quot;");
}

// Visual Builder
let visualMode = false;
let visualElements = [];
let dragData = null;

function initVisualBuilder() {
    const toggle = document.getElementById("toggle-visual");
    toggle.addEventListener("change", (e) => {
        visualMode = e.target.checked;
        document.body.classList.toggle("visual-mode", visualMode);
        document.getElementById("visual-toolbox").classList.toggle("toolbox-hidden", !visualMode);
        document.getElementById("visual-overlay").classList.toggle("visual-hidden", !visualMode);

        if (visualMode) {
            renderVisualOverlay();
        } else {
            clearVisualOverlay();
        }
    });

    initToolboxDrag();
    initOverlayDrop();
}

function initToolboxDrag() {
    document.querySelectorAll(".toolbox-item").forEach((item) => {
        item.addEventListener("dragstart", (e) => {
            dragData = {
                type: item.dataset.type,
                align: item.dataset.align || "left",
                shape: item.dataset.shape || "rectangle",
                width: parseFloat(item.dataset.w) || 40,
                height: parseFloat(item.dataset.h) || 30,
                style: item.dataset.style || "FS",
            };
            e.dataTransfer.effectAllowed = "copy";
            e.dataTransfer.setData("text/plain", JSON.stringify(dragData));
        });
    });
}

function initOverlayDrop() {
    const overlay = document.getElementById("visual-overlay");
    const container = document.getElementById("preview-container");

    container.addEventListener("dragover", (e) => {
        if (!visualMode) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = "copy";
    });

    container.addEventListener("drop", (e) => {
        if (!visualMode) return;
        e.preventDefault();

        try {
            const data = JSON.parse(e.dataTransfer.getData("text/plain"));
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left + container.scrollLeft;
            const y = e.clientY - rect.top + container.scrollTop;

            if (data.type === "text") {
                insertTextElement(data.align, x, y);
            } else if (data.type === "stamp") {
                insertStampElement(data.shape, data.width, data.height, x, y);
            } else if (data.type === "row") {
                insertRowElement(data.style, x, y);
            }
        } catch (err) {
            // Ignore invalid drops
        }
    });
}

function insertTextElement(align, x, y) {
    const dsl = getEditorContent();
    const lines = dsl.split("\n");
    const text = "New Text";
    const fontId = "HN";
    const size = 12;

    const alignSuffix = align === "center" ? "_CENTRE" : align === "right" ? "_RIGHT" : "";
    const newLine = `PAGE_TEXT${alignSuffix}("${fontId}" ${size} "${text}")`;

    // Find the last PAGE_START or insert after existing text elements
    let insertIdx = -1;
    for (let i = lines.length - 1; i >= 0; i--) {
        if (lines[i].trim().startsWith("PAGE_START")) {
            insertIdx = i + 1;
            break;
        }
    }

    if (insertIdx === -1) {
        lines.push("PAGE_START");
        lines.push(newLine);
    } else {
        lines.splice(insertIdx, 0, newLine);
    }

    setEditorContent(lines.join("\n"));
    refreshPreview();
    showToast("Text element added", "success");
}

function insertStampElement(shape, width, height, x, y) {
    const dsl = getEditorContent();
    const lines = dsl.split("\n");

    const shapeCmd = shape === "rectangle" ? "STAMP_ADD" : `STAMP_ADD_${shape.toUpperCase()}`;
    const newLine = `${shapeCmd}(${width} ${height} "New Stamp")`;

    // Find the last row to add to, or create a new row
    let insertIdx = -1;
    for (let i = lines.length - 1; i >= 0; i--) {
        if (lines[i].trim().startsWith("ROW_START_")) {
            insertIdx = i + 1;
            break;
        }
    }

    if (insertIdx === -1) {
        // Find last PAGE_START
        for (let i = lines.length - 1; i >= 0; i--) {
            if (lines[i].trim().startsWith("PAGE_START")) {
                lines.splice(i + 1, 0, 'ROW_START_FS("HN" 10 5 180)');
                lines.splice(i + 2, 0, newLine);
                break;
            }
        }
    } else {
        lines.splice(insertIdx, 0, newLine);
    }

    setEditorContent(lines.join("\n"));
    refreshPreview();
    showToast("Stamp element added", "success");
}

function insertRowElement(style, x, y) {
    const dsl = getEditorContent();
    const lines = dsl.split("\n");

    const newLine = `ROW_START_${style}("HN" 10 5 180)`;

    // Find the last PAGE_START
    let insertIdx = -1;
    for (let i = lines.length - 1; i >= 0; i--) {
        if (lines[i].trim().startsWith("PAGE_START")) {
            insertIdx = i + 1;
            break;
        }
    }

    if (insertIdx === -1) {
        lines.push("PAGE_START");
        lines.push(newLine);
    } else {
        lines.splice(insertIdx, 0, newLine);
    }

    setEditorContent(lines.join("\n"));
    refreshPreview();
    showToast("Row element added", "success");
}

function renderVisualOverlay() {
    clearVisualOverlay();
    // Parse current DSL and render draggable elements
    // This is a simplified version - full implementation would parse all elements
    const overlay = document.getElementById("visual-overlay");
    overlay.innerHTML = '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:var(--text-muted);font-size:13px;text-align:center;pointer-events:none">Drag elements from the toolbox onto the preview</div>';
}

function clearVisualOverlay() {
    const overlay = document.getElementById("visual-overlay");
    overlay.innerHTML = "";
}
