const API_BASE = "";
const DEBOUNCE_MS = 400;

let editor = null;
let currentFile = null;
let debounceTimer = null;
let isModified = false;
let wizardState = {
    step: 1,
    paperSize: null,
    paperWidth: null,
    paperHeight: null,
    border: null,
    columns: null,
    complete: false,
};

const DEFAULT_DSL = `ALBUM_TITLE("My Stamp Album")
ALBUM_AUTHOR("Collector")

ALBUM_PAGES_SIZE(210 297)
ALBUM_PAGES_MARGINS(15 15 15 15)

PAGE_START
PAGE_TEXT_CENTER("Helvetica" 18 "My Stamp Collection" 5)
PAGE_TEXT_CENTER("Helvetica" 12 "A carefully curated album")

ROW_START_FS("Helvetica" 10 5 180)
STAMP_ADD(40 30 "First Stamp" "" "" "")
STAMP_ADD(40 30 "Second Stamp" "" "" "")
STAMP_ADD(40 30 "Third Stamp" "" "" "")

ROW_START_FS("Helvetica" 10 5 180)
STAMP_ADD(40 30 "Fourth Stamp" "" "" "")
STAMP_ADD(40 30 "Fifth Stamp" "" "" "")
`;

document.addEventListener("DOMContentLoaded", () => {
    initEditor();
    initButtons();
    initKeyboardShortcuts();
    initWizard();
    loadFileList();
    initImageDragDrop();
    document.getElementById("btn-export").disabled = false;
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
    document.getElementById("btn-upload-dsl").addEventListener("click", () => {
        document.getElementById("file-input").click();
    });
    document.getElementById("file-input").addEventListener("change", handleFileUpload);

    document.getElementById("btn-upload-img").addEventListener("click", () => {
        document.getElementById("image-input").click();
    });
    document.getElementById("image-input").addEventListener("change", handleImageUpload);

    document.getElementById("btn-upload-folder").addEventListener("click", () => {
        document.getElementById("folder-input").click();
    });
    document.getElementById("folder-input").addEventListener("change", handleFolderUpload);

    document.getElementById("toggle-wizard").addEventListener("change", (e) => {
        const panel = document.getElementById("wizard-panel");
        panel.classList.toggle("wizard-hidden", !e.target.checked);
    });

    document.getElementById("toggle-sidebar").addEventListener("change", (e) => {
        const sidebar = document.getElementById("sidebar");
        sidebar.classList.toggle("sidebar-hidden", !e.target.checked);
    });

    document.getElementById("toggle-visual").addEventListener("change", (e) => {
        if (e.target.checked) {
            enableVisualMode();
        } else {
            document.body.classList.remove("visual-mode");
            document.getElementById("visual-overlay").classList.add("visual-hidden");
            document.getElementById("preview-frame").style.pointerEvents = "";
        }
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

// Wizard
function initWizard() {
    // Accordion toggle
    document.querySelectorAll(".section-header").forEach((header) => {
        header.addEventListener("click", () => {
            const section = header.closest(".wizard-section");
            const wasOpen = section.classList.contains("open");
            // Close all sections
            document.querySelectorAll(".wizard-section").forEach((s) => s.classList.remove("open"));
            // Toggle clicked section
            if (!wasOpen) {
                section.classList.add("open");
            }
        });
    });

    // Paper size selection
    document.querySelectorAll(".paper-option").forEach((opt) => {
        opt.addEventListener("click", () => {
            document.querySelectorAll(".paper-option").forEach((o) => o.classList.remove("selected"));
            opt.classList.add("selected");
            wizardState.paperSize = opt.dataset.size;
            wizardState.paperWidth = parseFloat(opt.dataset.w);
            wizardState.paperHeight = parseFloat(opt.dataset.h);
            document.getElementById("val-paper").textContent = `${wizardState.paperSize} (${wizardState.paperWidth}×${wizardState.paperHeight}mm)`;
            document.getElementById("btn-export").disabled = false;
            collapseAndOpen("section-paper", "section-border");
            updatePreviewFromWizard();
        });
    });

    // Border selection
    document.querySelectorAll(".border-option").forEach((opt) => {
        opt.addEventListener("click", () => {
            document.querySelectorAll(".border-option").forEach((o) => o.classList.remove("selected"));
            opt.classList.add("selected");
            wizardState.border = opt.dataset.border;
            const label = opt.querySelector("span").textContent;
            document.getElementById("val-border").textContent = label;
            collapseAndOpen("section-border", "section-layout");
            updatePreviewFromWizard();
        });
    });

    // Column layout selection
    document.querySelectorAll(".layout-option").forEach((opt) => {
        opt.addEventListener("click", () => {
            document.querySelectorAll(".layout-option").forEach((o) => o.classList.remove("selected"));
            opt.classList.add("selected");
            wizardState.columns = parseInt(opt.dataset.columns);
            const labels = { 0: "Free", 1: "Single", 2: "Two", 3: "Three" };
            document.getElementById("val-layout").textContent = labels[wizardState.columns] || "Not set";
            collapseAndOpen("section-layout", "section-build");
            updatePreviewFromWizard();
            enableVisualMode();
            initDragDrop();
        });
    });

    // Start with first section open
    document.getElementById("section-paper").classList.add("open");
}

function collapseAndOpen(closeId, openId) {
    document.getElementById(closeId).classList.remove("open");
    document.getElementById(openId).classList.add("open");
}

function enableVisualMode() {
    document.body.classList.add("visual-mode");
    document.getElementById("visual-overlay").classList.remove("visual-hidden");
    document.getElementById("preview-frame").style.pointerEvents = "none";
}

function updatePreviewFromWizard() {
    const dsl = getEditorContent();
    const lines = dsl.split("\n");

    // Extract existing page content (everything from PAGE_START onward)
    const pageContentLines = [];
    const titleLines = [];
    let foundPageStart = false;

    for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("PAGE_START") || trimmed.startsWith("PAGE_TEXT") ||
            trimmed.startsWith("ROW_START") || trimmed.startsWith("STAMP_") ||
            trimmed.startsWith("PAGE_COLUMN") || trimmed.startsWith("PAGE_VSPACE") ||
            trimmed.startsWith("PAGE_SET") || trimmed.startsWith("PAGE_BACKGROUND") ||
            trimmed.startsWith("PAGE_ADD") || trimmed.startsWith("PAGE_RULE") ||
            trimmed.startsWith("PAGE_QUADRILLE") || trimmed.startsWith("PAGE_TEXT_PARAGRAPH")) {
            foundPageStart = true;
            pageContentLines.push(line);
        } else if (trimmed.startsWith("ALBUM_TITLE") || trimmed.startsWith("ALBUM_AUTHOR") || trimmed.startsWith("ALBUM_DEFINE_FONT")) {
            titleLines.push(line);
        }
        // Skip old setup lines - they'll be regenerated
    }

    // Build new DSL
    const result = [...titleLines];

    if (wizardState.paperSize) {
        result.push(`ALBUM_PAGES_SIZE(${wizardState.paperWidth} ${wizardState.paperHeight})`);
        result.push("ALBUM_PAGES_MARGINS(15 15 15 15)");
    }

    if (wizardState.border && wizardState.border !== "none") {
        const borderMap = {
            single: "ALBUM_PAGES_BORDER(0.5 0 0 0)",
            double: "ALBUM_PAGES_BORDER(0.5 0.5 0 1.0)",
            triple: "ALBUM_PAGES_BORDER(0.5 0.5 0.5 1.5)",
            heritage: "ALBUM_PAGES_BORDER(0.5 0.3 0.5 1.0)",
            geometric: "ALBUM_PAGES_DECORATIVE_BORDER(\"geometric\")",
            vine: "ALBUM_PAGES_DECORATIVE_BORDER(\"vine\")",
            elegant: "ALBUM_PAGES_DECORATIVE_BORDER(\"elegant\")",
            accent: "ALBUM_PAGES_DECORATIVE_BORDER(\"accent\")",
            dashed: "ALBUM_PAGES_BORDER(0.5 0 0 0)",
            dotted: "ALBUM_PAGES_BORDER(0.5 0 0 0)",
            diamond: "ALBUM_PAGES_DECORATIVE_BORDER(\"diamond\")",
            greek: "ALBUM_PAGES_DECORATIVE_BORDER(\"greek\")",
            zigzag: "ALBUM_PAGES_DECORATIVE_BORDER(\"zigzag\")",
        };
        if (borderMap[wizardState.border]) {
            result.push(borderMap[wizardState.border]);
        }
    }

    // Always add PAGE_START if we have any page-level settings or content
    if (wizardState.paperSize || wizardState.border || wizardState.columns !== null || pageContentLines.length > 0) {
        result.push("PAGE_START");

        // Column mode goes after PAGE_START
        if (wizardState.columns !== null && wizardState.columns > 1) {
            result.push(`PAGE_COLUMN_START(${wizardState.columns})`);
        }
    }

    // Append existing page content (skip duplicate PAGE_START and PAGE_COLUMN_START)
    for (const line of pageContentLines) {
        const t = line.trim();
        if (t === "PAGE_START" && result[result.length - 1] === "PAGE_START") continue;
        if (t.startsWith("PAGE_COLUMN_START") && wizardState.columns !== null) continue;
        result.push(line);
    }

    editor.setValue(result.join("\n"));
    editor.setCursor(editor.lineCount() - 1, 0);
    refreshPreview();
}

// Drag and drop (initialized after step 4)
let dragDropInitialized = false;

function initDragDrop() {
    if (dragDropInitialized) return;
    dragDropInitialized = true;

    document.querySelectorAll(".build-item").forEach((item) => {
        item.addEventListener("dragstart", (e) => {
            const data = {
                type: item.dataset.type,
                align: item.dataset.align || "left",
                shape: item.dataset.shape || "rectangle",
                width: parseFloat(item.dataset.w) || 40,
                height: parseFloat(item.dataset.h) || 30,
                style: item.dataset.style || "FS",
            };
            e.dataTransfer.effectAllowed = "copy";
            e.dataTransfer.setData("text/plain", JSON.stringify(data));
            item.style.opacity = "0.5";
        });

        item.addEventListener("dragend", (e) => {
            item.style.opacity = "1";
            removeDropIndicator();
        });
    });

    const overlay = document.getElementById("visual-overlay");

    overlay.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = "copy";
        showDropIndicator(e);
    });

    overlay.addEventListener("dragleave", () => {
        removeDropIndicator();
    });

    overlay.addEventListener("drop", (e) => {
        e.preventDefault();
        e.stopPropagation();
        removeDropIndicator();

        // Check if files are being dropped (images)
        if (e.dataTransfer.files.length > 0) {
            handleImageDrop(e.dataTransfer.files);
            return;
        }

        try {
            const raw = e.dataTransfer.getData("text/plain");
            if (!raw) return;
            const data = JSON.parse(raw);

            if (data.type === "text") {
                insertTextElement(data.align);
            } else if (data.type === "stamp") {
                insertStampElement(data.shape, data.width, data.height);
            } else if (data.type === "row") {
                insertRowElement(data.style);
            }
        } catch (err) {
            console.error("Drop failed:", err);
        }
    });
}

async function handleImageDrop(files) {
    const imageExts = ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "webp"];

    for (const file of files) {
        const ext = file.name.toLowerCase().split(".").pop();
        if (!imageExts.includes(ext)) continue;

        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch(`${API_BASE}/images`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) throw new Error(`Failed to upload ${file.name}`);

            // Insert into editor
            insertImageRef(file.name);
            showToast(`Dropped & added ${file.name}`, "success");
        } catch (err) {
            showToast("Error: " + err.message, "error");
        }
    }

    loadFileList();
}

// Enable image drag-and-drop on editor and preview
function initImageDragDrop() {
    const editorContainer = document.getElementById("editor-container");
    const previewContainer = document.getElementById("preview-container");

    [editorContainer, previewContainer].forEach((container) => {
        container.addEventListener("dragover", (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = "copy";
            container.classList.add("drag-over");
        });

        container.addEventListener("dragleave", () => {
            container.classList.remove("drag-over");
        });

        container.addEventListener("drop", (e) => {
            e.preventDefault();
            container.classList.remove("drag-over");
            if (e.dataTransfer.files.length > 0) {
                handleImageDrop(e.dataTransfer.files);
            }
        });
    });
}

function showDropIndicator(e) {
    if (!dropIndicator) {
        dropIndicator = document.createElement("div");
        dropIndicator.className = "drop-indicator";
        document.getElementById("visual-overlay").appendChild(dropIndicator);
    }
    const rect = document.getElementById("visual-overlay").getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    dropIndicator.style.left = (x - 30) + "px";
    dropIndicator.style.top = (y - 15) + "px";
    dropIndicator.style.width = "60px";
    dropIndicator.style.height = "30px";
    dropIndicator.style.display = "block";
}

function removeDropIndicator() {
    if (dropIndicator) {
        dropIndicator.style.display = "none";
    }
}

let dropIndicator = null;

function insertTextElement(align) {
    const dsl = getEditorContent();
    const lines = dsl.split("\n");
    const text = "New Text";
    const fontId = "HN";
    const size = 12;

    const alignSuffix = align === "center" ? "_CENTRE" : align === "right" ? "_RIGHT" : "";
    const newLine = `PAGE_TEXT${alignSuffix}("${fontId}" ${size} "${text}")`;

    lines.push(newLine);

    editor.setValue(lines.join("\n"));
    editor.setCursor(editor.lineCount() - 1, 0);
    showToast("Text element added", "success");
}

function insertStampElement(shape, width, height) {
    const dsl = getEditorContent();
    const lines = dsl.split("\n");

    const catalogRefs = '"" "" ""';
    const newLine =
        shape === "rectangle"
            ? `STAMP_ADD(${width} ${height} "New Stamp" ${catalogRefs})`
            : `STAMP_ADD_${shape.toUpperCase()}(${width} ${height} "New Stamp" ${catalogRefs})`;

    const lastLine = lines[lines.length - 1].trim();
    if (lastLine.startsWith("ROW_START_") || lastLine.startsWith("STAMP_ADD")) {
        lines.push(newLine);
    } else {
        lines.push('ROW_START_FS("HN" 10 5 180)');
        lines.push(newLine);
    }

    editor.setValue(lines.join("\n"));
    editor.setCursor(editor.lineCount() - 1, 0);
    showToast("Stamp element added", "success");
}

function insertRowElement(style) {
    const dsl = getEditorContent();
    const lines = dsl.split("\n");

    const newLine = `ROW_START_${style}("HN" 10 5 180)`;

    lines.push(newLine);

    editor.setValue(lines.join("\n"));
    editor.setCursor(editor.lineCount() - 1, 0);
    showToast("Row element added", "success");
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
        clearErrorHighlight();
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
            const detail = error.detail || "Unknown error";
            // Try to extract line number from error message (e.g., "at line 5")
            const lineMatch = detail.match(/at line (\d+)/);
            const errorLine = lineMatch ? parseInt(lineMatch[1]) : null;

            // Highlight the error line in the editor
            if (errorLine) {
                highlightErrorLine(errorLine);
            }

            // Build a helpful error page
            const errorHtml = [
                "<html><body style='padding:40px;font-family:system-ui;max-width:600px;margin:0 auto'>",
                "<div style='background:#FFF3CD;border:1px solid #FFC107;border-radius:8px;padding:20px;margin-bottom:20px'>",
                "<h3 style='color:#856404;margin:0 0 10px 0'>⚠ DSL Error</h3>",
                `<p style='color:#856404;margin:0;font-family:monospace;font-size:14px'>${escapeHtml(detail)}</p>`,
                "</div>",
                "<p style='color:#666;font-size:13px'>Check the highlighted line in the editor above.</p>",
                "<p style='color:#666;font-size:13px'>Common fixes:</p>",
                "<ul style='color:#666;font-size:13px'>",
                "<li>Text commands need <code>PAGE_TEXT</code> inside a <code>PAGE_START</code> block</li>",
                "<li>Stamp commands need <code>STAMP_ADD</code> inside a <code>ROW_START_*</code> block</li>",
                "<li>Row commands need <code>ROW_START_FS</code> (or ES/JS) inside a <code>PAGE_START</code> block</li>",
                "</ul>",
                "</body></html>"
            ].join("\n");

            setPreviewHtml(errorHtml);
            document.getElementById("preview-status").textContent = `Error on line ${errorLine || "?"}`;
            document.getElementById("preview-status").style.color = "#f85149";
            return;
        }

        const html = await response.text();
        setPreviewHtml(html);
        clearErrorHighlight();
        document.getElementById("preview-status").textContent = "Preview updated";
        document.getElementById("preview-status").style.color = "";
    } catch (err) {
        document.getElementById("preview-status").textContent = "Preview failed";
        document.getElementById("preview-status").style.color = "#f85149";
        clearErrorHighlight();
    }
}

function highlightErrorLine(lineNumber) {
    // Clear previous error highlights
    clearErrorHighlight();
    // Add error class to the line (CodeMirror uses 0-based line numbers)
    const lineHandle = editor.addLineClass(lineNumber - 1, "background", "cm-error-line");
    // Store reference for cleanup
    window._errorLineHandle = { lineNumber: lineNumber - 1, handle: lineHandle };
    // Scroll to the error line
    editor.scrollIntoView({ line: lineNumber - 1, ch: 0 }, 100);
    // Set cursor to the error line
    editor.setCursor(lineNumber - 1, 0);
}

function clearErrorHighlight() {
    if (window._errorLineHandle) {
        const { lineNumber } = window._errorLineHandle;
        try {
            editor.removeLineClass(lineNumber, "background", "cm-error-line");
        } catch (e) {
            // Line may have been deleted
        }
        window._errorLineHandle = null;
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
    document.getElementById("btn-export").disabled = false;
    wizardState = { paperSize: null, paperWidth: null, paperHeight: null, border: null, columns: null };
    document.querySelectorAll(".paper-option, .border-option, .layout-option").forEach((o) => o.classList.remove("selected"));
    document.querySelectorAll(".wizard-section").forEach((s) => s.classList.remove("open"));
    document.getElementById("section-paper").classList.add("open");
    document.getElementById("val-paper").textContent = "Not set";
    document.getElementById("val-border").textContent = "Not set";
    document.getElementById("val-layout").textContent = "Not set";
    editor.setValue(DEFAULT_DSL);
    updateFileListActive();
    refreshPreview();
}

function openFile() {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".slbum,.txt";
    input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async (ev) => {
            currentFile = file.name;
            document.getElementById("file-name").textContent = file.name;
            document.getElementById("btn-save").disabled = false;
            document.getElementById("btn-export").disabled = false;
            setEditorContent(ev.target.result);

            // Upload to server so images in same folder can be referenced
            try {
                const response = await fetch(`${API_BASE}/files/${encodeURIComponent(file.name)}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content: ev.target.result }),
                });
                if (response.ok) {
                    loadFileList();
                }
            } catch (err) {
                // Server upload is optional - file still works locally
            }

            showToast(`Opened ${file.name}`, "success");
        };
        reader.onerror = () => showToast("Failed to read file", "error");
        reader.readAsText(file);
    };

    // Allow selecting multiple files (album + images)
    input.multiple = false;
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
        const name = prompt("Save as:", "album.txt");
        if (!name) return;
        currentFile = name.endsWith(".txt") || name.endsWith(".slbum") ? name : name + ".txt";
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

        // Also download as .txt file
        downloadFile(currentFile, getEditorContent());
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

function downloadFile(filename, content) {
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
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

async function handleImageUpload(e) {
    const files = e.target.files;
    if (!files.length) return;

    for (const file of files) {
        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch(`${API_BASE}/images`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) throw new Error(`Failed to upload ${file.name}`);
            showToast(`Uploaded ${file.name}`, "success");
        } catch (err) {
            showToast("Error: " + err.message, "error");
        }
    }

    loadFileList();
    e.target.value = "";
}

async function handleFolderUpload(e) {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    let uploaded = 0;
    let errors = 0;

    for (const file of files) {
        const ext = file.name.toLowerCase().split(".").pop();
        const imageExts = ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "webp"];
        const albumExts = ["slbum", "txt"];

        try {
            if (imageExts.includes(ext)) {
                const formData = new FormData();
                formData.append("file", file);
                const response = await fetch(`${API_BASE}/images`, {
                    method: "POST",
                    body: formData,
                });
                if (response.ok) uploaded++;
            } else if (albumExts.includes(ext)) {
                const content = await file.text();
                const response = await fetch(`${API_BASE}/files/${encodeURIComponent(file.name)}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content }),
                });
                if (response.ok) {
                    uploaded++;
                    if (!currentFile) {
                        currentFile = file.name;
                        document.getElementById("file-name").textContent = file.name;
                        document.getElementById("btn-save").disabled = false;
                        document.getElementById("btn-export").disabled = false;
                        setEditorContent(content);
                    }
                }
            }
        } catch (err) {
            errors++;
        }
    }

    loadFileList();
    showToast(`Uploaded ${uploaded} files${errors > 0 ? `, ${errors} failed` : ""}`, uploaded > 0 ? "success" : "error");
    e.target.value = "";
}

async function deleteImage(filename) {
    if (!confirm(`Delete image ${filename}?`)) return;
    try {
        const response = await fetch(`${API_BASE}/images/${encodeURIComponent(filename)}`, {
            method: "DELETE",
        });
        if (!response.ok) throw new Error("Failed to delete");
        loadFileList();
        showToast(`Deleted ${filename}`, "success");
    } catch (err) {
        showToast("Error: " + err.message, "error");
    }
}

function insertImageRef(filename) {
    const dsl = getEditorContent();
    const lines = dsl.split("\n");

    const newLine = `STAMP_ADD_IMG (40 30 "${filename}" "" "" "" )`;

    const lastLine = lines[lines.length - 1].trim();
    if (lastLine.startsWith("ROW_START_") || lastLine.startsWith("STAMP_ADD")) {
        lines.push(newLine);
    } else {
        lines.push('ROW_START_ES (HN 10 0.1 180)');
        lines.push(newLine);
    }

    editor.setValue(lines.join("\n"));
    editor.setCursor(editor.lineCount() - 1, 0);
    refreshPreview();
    showToast(`Added ${filename} to editor`, "success");
}

// PDF Export
async function exportPDF() {
    const dsl = getEditorContent();
    document.getElementById("status-left").textContent = "Generating PDF...";

    try {
        const response = await fetch(`${API_BASE}/export`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dsl, source_path: currentFile || "untitled.txt" }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        const pdfName = currentFile
            ? currentFile.replace(/\.(slbum|txt)$/, "") + ".pdf"
            : "album.pdf";
        a.href = url;
        a.download = pdfName;
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
    try {
        const response = await fetch(`${API_BASE}/images`);
        if (!response.ok) return;
        const images = await response.json();
        renderImageList(images);
    } catch (err) {
        // Silently fail
    }
}

function renderFileList(files) {
    const list = document.getElementById("file-list");
    if (files.length === 0) {
        list.innerHTML = '<div style="padding:12px 16px;color:var(--text-muted);font-size:12px">No album files</div>';
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

function renderImageList(images) {
    const list = document.getElementById("image-list");
    if (images.length === 0) {
        list.innerHTML = '<div style="padding:12px 16px;color:var(--text-muted);font-size:12px">No images uploaded</div>';
        return;
    }

    list.innerHTML = images.map((f) => `
        <div class="image-item" onclick="insertImageRef('${escapeAttr(f)}')">
            <img src="${API_BASE}/images/${escapeAttr(f)}" alt="${escapeHtml(f)}">
            <span class="image-name">${escapeHtml(f)}</span>
            <div class="image-actions">
                <button onclick="event.stopPropagation();deleteImage('${escapeAttr(f)}')" title="Delete">
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
    return str
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

// ============================================================
// Tutorial System
// ============================================================

const TUTORIAL_STEPS = [
    {
        title: "Welcome to StampAlbum Pro! 🎨",
        text: "This interactive tutorial will walk you through the key features of StampAlbum Pro. You can skip at any time and restart later by clicking the ? button.",
        target: null,
        position: "center",
    },
    {
        title: "The DSL Editor",
        text: "This is where you write your album definitions using our DSL (Domain Specific Language). Try typing ALBUM_TITLE(\"My Collection\") to get started. The editor has syntax highlighting and line numbers.",
        target: "#editor-panel",
        position: "right",
    },
    {
        title: "Live Preview",
        text: "As you type, the preview panel updates automatically (400ms after you stop typing). This shows exactly how your album pages will look when exported to PDF.",
        target: "#preview-panel",
        position: "left",
    },
    {
        title: "Album Setup Wizard",
        text: "Use the Setup panel on the left to quickly configure paper size, borders, and column layouts. Click each section to expand it. Changes are applied to your DSL in real-time.",
        target: "#wizard-panel",
        position: "right",
    },
    {
        title: "File Management",
        text: "Click the Files toggle to show the sidebar. You can create, open, save, and delete album files. Upload images to use in your stamp boxes. All files are stored in ~/StampAlbum/.",
        target: "#toggle-sidebar",
        position: "left",
        action: () => {
            const sidebar = document.getElementById("sidebar");
            const toggle = document.getElementById("toggle-sidebar");
            if (!toggle.checked) {
                toggle.checked = true;
                sidebar.classList.remove("sidebar-hidden");
            }
        },
    },
    {
        title: "Export to PDF",
        text: "When your album is ready, click Export PDF to generate a high-quality PDF file. The PDF uses professional typography and precise millimeter measurements for printing.",
        target: "#btn-export",
        position: "bottom",
    },
    {
        title: "You're Ready! 🚀",
        text: "You now know the basics. For more help, check the DSL reference in the documentation. Happy collecting!",
        target: null,
        position: "center",
    },
];

let tutorialStep = 0;
let tutorialActive = false;

function initTutorial() {
    const btn = document.getElementById("btn-tutorial");
    if (btn) {
        btn.addEventListener("click", startTutorial);
    }
    if (!localStorage.getItem("stampalbum-tutorial-done")) {
        setTimeout(() => startTutorial(), 500);
    }
}

function startTutorial() {
    tutorialActive = true;
    tutorialStep = 0;
    document.getElementById("tutorial-overlay").classList.add("active");
    showTutorialStep(0);
}

function endTutorial() {
    tutorialActive = false;
    document.getElementById("tutorial-overlay").classList.remove("active");
    clearTutorialHighlight();
    localStorage.setItem("stampalbum-tutorial-done", "true");
}

function showTutorialStep(idx) {
    const step = TUTORIAL_STEPS[idx];
    if (!step) { endTutorial(); return; }

    document.getElementById("tutorial-step-num").textContent = `${idx + 1}/${TUTORIAL_STEPS.length}`;
    document.getElementById("tutorial-title").textContent = step.title;
    document.getElementById("tutorial-text").textContent = step.text;

    document.getElementById("tutorial-prev").disabled = idx === 0;
    const nextBtn = document.getElementById("tutorial-next");
    nextBtn.textContent = idx === TUTORIAL_STEPS.length - 1 ? "Finish" : "Next →";

    const dotsContainer = document.getElementById("tutorial-dots");
    dotsContainer.innerHTML = TUTORIAL_STEPS.map((_, i) =>
        `<div class="tutorial-dot ${i === idx ? "active" : ""}"></div>`
    ).join("");

    clearTutorialHighlight();
    const tooltip = document.getElementById("tutorial-tooltip");
    const overlay = document.getElementById("tutorial-overlay");

    const oldBackdrop = overlay.querySelector(".tutorial-backdrop");
    if (oldBackdrop) oldBackdrop.remove();

    if (step.target) {
        const targetEl = document.querySelector(step.target);
        if (targetEl) {
            targetEl.classList.add("tutorial-highlight");
            const backdrop = document.createElement("div");
            backdrop.className = "tutorial-backdrop";
            overlay.appendChild(backdrop);

            const rect = targetEl.getBoundingClientRect();
            let top, left;
            switch (step.position) {
                case "right":
                    top = rect.top + rect.height / 2 - 60;
                    left = rect.right + 16;
                    break;
                case "left":
                    top = rect.top + rect.height / 2 - 60;
                    left = rect.left - 396;
                    break;
                case "bottom":
                    top = rect.bottom + 16;
                    left = rect.left + rect.width / 2 - 190;
                    break;
                default:
                    top = rect.top + rect.height / 2 - 60;
                    left = rect.right + 16;
            }
            top = Math.max(10, Math.min(top, window.innerHeight - 200));
            left = Math.max(10, Math.min(left, window.innerWidth - 400));
            tooltip.style.top = top + "px";
            tooltip.style.left = left + "px";
        }
    } else {
        tooltip.style.top = "50%";
        tooltip.style.left = "50%";
        tooltip.style.transform = "translate(-50%, -50%)";
    }

    if (step.action) step.action();
}

function clearTutorialHighlight() {
    document.querySelectorAll(".tutorial-highlight").forEach(el => {
        el.classList.remove("tutorial-highlight");
    });
    const backdrop = document.querySelector(".tutorial-backdrop");
    if (backdrop) backdrop.remove();
    const tooltip = document.getElementById("tutorial-tooltip");
    tooltip.style.transform = "";
}

function tutorialNext() {
    if (tutorialStep < TUTORIAL_STEPS.length - 1) {
        tutorialStep++;
        showTutorialStep(tutorialStep);
    } else {
        endTutorial();
    }
}

function tutorialPrev() {
    if (tutorialStep > 0) {
        tutorialStep--;
        showTutorialStep(tutorialStep);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initTutorial();
    document.getElementById("tutorial-next").addEventListener("click", tutorialNext);
    document.getElementById("tutorial-prev").addEventListener("click", tutorialPrev);
    document.getElementById("tutorial-skip").addEventListener("click", endTutorial);
});

// ============================================================
// Album Creation Wizard
// ============================================================

let wizardStep = 1;
const wizardData = {
    title: "",
    author: "",
    pageSize: "A4",
    pageWidth: 210,
    pageHeight: 297,
    marginLeft: 20,
    marginTop: 15,
    marginRight: 15,
    marginBottom: 15,
    border: "none",
    titleColor: "black",
    borderColor: "black",
    template: "blank",
    stamps: [{ description: "", catalog: "", width: 32, height: 37 }],
};

const WIZARD_TEMPLATES = {
    blank: "",
    classic: 'PAGE_TEXT_CENTRE(HS 14 "Section Title")\nPAGE_TEXT_CENTRE(HN 10 "Description text goes here.")\n\nPAGE_VSPACE(5)\n\nROW_START_FS(HN 8 0.5 6.0)\nSTAMP_ADD(32.0 37.0 "Description" "sg 1" "" "sacc 1")\nSTAMP_ADD(32.0 37.0 "Description" "sg 2" "" "sacc 2")',
    competition: 'PAGE_TEXT_CENTRE(HS 16 "Section Title")\nPAGE_TEXT_CENTRE(HN 12 "Brief description of this section.")\n\nPAGE_RULE_H(0.5 4 0)\n\nROW_START_FS(HN 9 0.5 7.0)\nSTAMP_ADD(35.0 40.0 "Stamp description" "sg 1" "" "")\nSTAMP_HEADING(HB 10 "Key Item")',
    modern: 'PAGE_TEXT(HN 11 "Section heading - left aligned")\n\nPAGE_VSPACE(8)\n\nROW_START_FS(HN 8 1.0 6.0)\nSTAMP_ADD(30.0 35.0 "Description" "" "" "")\nSTAMP_ADD(30.0 35.0 "Description" "" "" "")',
    two_column: 'PAGE_COLUMN_START(10.0)\n\nPAGE_TEXT_CENTRE(HS 12 "Left Column")\nROW_START_FS(HN 7 0.3 5.0)\nSTAMP_ADD(25.0 28.0 "Stamp" "" "" "")\n\nPAGE_COLUMN_NEXT\n\nPAGE_TEXT_CENTRE(HS 12 "Right Column")\nROW_START_FS(HN 7 0.3 5.0)\nSTAMP_ADD(25.0 28.0 "Stamp" "" "" "")\n\nPAGE_COLUMN_STOP',
    thematic: '# Theme: Section 1\nCOLOUR_PAGE_TEXT(darkblue)\nPAGE_TEXT_CENTRE(HS 14 "Theme: Birds")\nPAGE_TEXT_CENTRE(HN 10 "Description of this thematic section.")\n\nROW_START_FS(HN 8 0.5 6.0)\nSTAMP_ADD(32.0 37.0 "Bird stamp" "" "" "")\nSTAMP_ADD(32.0 37.0 "Bird stamp" "" "" "")',
};

function initWizard() {
    document.getElementById("wizard-close").addEventListener("click", closeWizard);
    document.getElementById("wizard-backdrop").addEventListener("click", closeWizard);
    document.getElementById("wizard-next").addEventListener("click", wizardNext);
    document.getElementById("wizard-prev").addEventListener("click", wizardPrev);
    document.getElementById("wizard-add-stamp").addEventListener("click", addWizardStamp);

    document.querySelectorAll(".wizard-paper-options .wizard-option-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".wizard-paper-options .wizard-option-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            wizardData.pageSize = btn.dataset.size;
            wizardData.pageWidth = parseInt(btn.dataset.w);
            wizardData.pageHeight = parseInt(btn.dataset.h);
        });
    });

    document.querySelectorAll(".wizard-style-options .wizard-option-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".wizard-style-options .wizard-option-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            wizardData.border = btn.dataset.border;
        });
    });

    document.querySelectorAll(".wizard-color-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".wizard-color-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            wizardData.titleColor = btn.dataset.title;
            wizardData.borderColor = btn.dataset.border;
        });
    });

    document.querySelectorAll(".wizard-template-card").forEach(card => {
        card.addEventListener("click", () => {
            document.querySelectorAll(".wizard-template-card").forEach(c => c.classList.remove("selected"));
            card.classList.add("selected");
            wizardData.template = card.dataset.template;
        });
    });

    document.getElementById("wizard-stamp-entries").addEventListener("click", (e) => {
        if (e.target.classList.contains("wizard-remove-stamp")) {
            const entry = e.target.closest(".wizard-stamp-entry");
            const entries = document.querySelectorAll(".wizard-stamp-entry");
            if (entries.length > 1) entry.remove();
        }
    });

    ["wizard-ml", "wizard-mt", "wizard-mr", "wizard-mb"].forEach(id => {
        document.getElementById(id).addEventListener("change", (e) => {
            const key = id.replace("wizard-m", "margin") + (id === "wizard-ml" ? "Left" : id === "wizard-mt" ? "Top" : id === "wizard-mr" ? "Right" : "Bottom");
            wizardData[key] = parseFloat(e.target.value) || 15;
        });
    });
}

function openWizard() {
    wizardStep = 1;
    document.getElementById("album-wizard").classList.add("open");
    document.getElementById("wizard-backdrop").classList.add("active");
    showWizardStep(1);
}

function closeWizard() {
    document.getElementById("album-wizard").classList.remove("open");
    document.getElementById("wizard-backdrop").classList.remove("active");
}

function showWizardStep(step) {
    wizardStep = step;
    document.querySelectorAll(".wizard-step-indicator").forEach((ind, i) => {
        ind.classList.remove("active", "done");
        if (i + 1 === step) ind.classList.add("active");
        if (i + 1 < step) ind.classList.add("done");
    });
    document.querySelectorAll(".wizard-pane").forEach(pane => {
        pane.classList.toggle("active", parseInt(pane.dataset.pane) === step);
    });
    document.getElementById("wizard-prev").disabled = step === 1;
    document.getElementById("wizard-next").textContent = step === 6 ? "Create Album" : "Next →";
    if (step === 6) updateWizardSummary();
}

function wizardNext() {
    if (wizardStep < 6) { showWizardStep(wizardStep + 1); }
    else { createAlbumFromWizard(); }
}

function wizardPrev() {
    if (wizardStep > 1) { showWizardStep(wizardStep - 1); }
}

function addWizardStamp() {
    const container = document.getElementById("wizard-stamp-entries");
    const entry = document.createElement("div");
    entry.className = "wizard-stamp-entry";
    entry.innerHTML = '<input type="text" placeholder="Stamp description" class="wizard-stamp-desc"><input type="text" placeholder="Catalog #" class="wizard-stamp-cat"><input type="number" placeholder="W" class="wizard-stamp-w" value="32" min="5" max="200"><input type="number" placeholder="H" class="wizard-stamp-h" value="37" min="5" max="200"><button class="wizard-remove-stamp" title="Remove">✕</button>';
    container.appendChild(entry);
}

function updateWizardSummary() {
    const title = document.getElementById("wizard-title").value || "Untitled";
    const author = document.getElementById("wizard-author").value || "Unknown";
    const stampEntries = document.querySelectorAll(".wizard-stamp-entry");
    const stamps = [];
    stampEntries.forEach(entry => {
        const desc = entry.querySelector(".wizard-stamp-desc").value;
        if (desc) stamps.push({ description: desc, catalog: entry.querySelector(".wizard-stamp-cat").value, width: entry.querySelector(".wizard-stamp-w").value, height: entry.querySelector(".wizard-stamp-h").value });
    });
    wizardData.title = title;
    wizardData.author = author;
    wizardData.stamps = stamps.length > 0 ? stamps : [{ description: "", catalog: "", width: 32, height: 37 }];
    const borderMap = { none: "None", single: "Single", double: "Double", triple: "Triple", elegant: "Elegant" };
    const tmplMap = { blank: "Blank", classic: "Classic", competition: "Competition", modern: "Modern", two_column: "Two Column", thematic: "Thematic" };
    document.getElementById("wizard-summary").innerHTML = '<div class="summary-row"><span>Title</span><strong>' + escapeHtml(title) + '</strong></div><div class="summary-row"><span>Author</span><strong>' + escapeHtml(author) + '</strong></div><div class="summary-row"><span>Page Size</span><strong>' + wizardData.pageSize + ' (' + wizardData.pageWidth + 'x' + wizardData.pageHeight + 'mm)</strong></div><div class="summary-row"><span>Border</span><strong>' + (borderMap[wizardData.border] || "None") + '</strong></div><div class="summary-row"><span>Template</span><strong>' + (tmplMap[wizardData.template] || "Blank") + '</strong></div><div class="summary-row"><span>Stamps</span><strong>' + stamps.length + ' stamp(s)</strong></div>';
}

function createAlbumFromWizard() {
    updateWizardSummary();
    const dsl = generateWizardDSL();
    editor.setValue(dsl);
    setEditorContent(dsl);
    closeWizard();
    refreshPreview();
    showToast("Album created! Edit the DSL or add more pages.", "success");
}

function generateWizardDSL() {
    const L = [];
    if (wizardData.title) L.push('ALBUM_TITLE("' + wizardData.title.replace(/"/g, '\\"') + '")');
    if (wizardData.author) L.push('ALBUM_AUTHOR("' + wizardData.author.replace(/"/g, '\\"') + '")');
    L.push("");
    L.push("ALBUM_PAGES_SIZE(" + wizardData.pageWidth + " " + wizardData.pageHeight + ")");
    L.push("ALBUM_PAGES_MARGINS(" + wizardData.marginLeft + " " + wizardData.marginRight + " " + wizardData.marginTop + " " + wizardData.marginBottom + ")");
    L.push("ALBUM_PAGES_SPACING(6.0 6.0)");
    if (wizardData.border === "single") L.push("ALBUM_PAGES_BORDER(0.5 0 0 0)");
    else if (wizardData.border === "double") L.push("ALBUM_PAGES_BORDER(0.5 0.5 0 1.0)");
    else if (wizardData.border === "triple") L.push("ALBUM_PAGES_BORDER(0.5 0.5 0.5 1.5)");
    else if (wizardData.border === "elegant") L.push("ALBUM_PAGES_BORDER(0.4 0.2 0.4 1.0)");
    if (wizardData.titleColor !== "black") L.push("COLOUR_ALBUM_TITLE(" + wizardData.titleColor + ")");
    if (wizardData.borderColor !== "black") L.push("COLOUR_ALBUM_BORDER(" + wizardData.borderColor + ")");
    if (wizardData.title) L.push('ALBUM_PAGES_TITLE(TB 16 "' + wizardData.title.replace(/"/g, '\\"') + '")');
    L.push("");
    if (wizardData.template !== "blank" && WIZARD_TEMPLATES[wizardData.template]) {
        L.push("PAGE_START");
        L.push("");
        L.push(WIZARD_TEMPLATES[wizardData.template]);
    } else {
        L.push("PAGE_START");
        L.push("");
        if (wizardData.stamps.length > 0 && wizardData.stamps[0].description) {
            L.push('ROW_START_FS(HN 8 0.5 6.0)');
            wizardData.stamps.forEach(s => {
                L.push('STAMP_ADD(' + s.width + ' ' + s.height + ' "' + s.description.replace(/"/g, '\\"').replace(/\n/g, '\\n') + '" "' + (s.catalog || "") + '" "" "")');
            });
        }
    }
    return L.join("\n");
}

document.addEventListener("DOMContentLoaded", () => {
    initWizard();
    var origNew = window.newAlbum;
    window.newAlbum = function() {
        if (isModified && !confirm("Discard unsaved changes?")) return;
        openWizard();
    };
});

// ============================================================
// P1-6: Export (PNG, SVG, HTML Gallery)
// ============================================================

function initExportDropdown() {
    const dropdown = document.querySelector(".export-dropdown");
    if (!dropdown) return;
    const btn = dropdown.querySelector("button");
    const menu = dropdown.querySelector(".export-menu");
    btn.addEventListener("click", (e) => {
        e.stopPropagation();
        menu.classList.toggle("open");
    });
    menu.addEventListener("click", async (e) => {
        const option = e.target.closest(".export-option");
        if (!option) return;
        menu.classList.remove("open");
        await doExport(option.dataset.format);
    });
    document.addEventListener("click", () => { menu.classList.remove("open"); });
}

async function doExport(format) {
    const dsl = getEditorContent();
    if (!dsl.trim()) { showToast("Nothing to export", "error"); return; }
    document.getElementById("status-left").textContent = "Exporting " + format.toUpperCase() + "...";
    try {
        const response = await fetch(`${API_BASE}/export`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dsl, format, source_path: currentFile || "untitled.slbum" }),
        });
        if (!response.ok) { const err = await response.json(); throw new Error(err.detail || "Export failed"); }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = (currentFile ? currentFile.replace(/\.(slbum|txt)$/, "") : "album") + "." + format;
        a.click();
        URL.revokeObjectURL(url);
        document.getElementById("status-left").textContent = format.toUpperCase() + " exported";
        showToast(format.toUpperCase() + " exported successfully", "success");
    } catch (err) {
        document.getElementById("status-left").textContent = "Export failed";
        showToast("Export failed: " + err.message, "error");
    }
}

// ============================================================
// P1-7: Undo/Redo System
// ============================================================

const undoStack = [];
const redoStack = [];
const MAX_UNDO = 50;

function saveUndoState() {
    if (!editor) return;
    const content = editor.getValue();
    if (undoStack.length > 0 && undoStack[undoStack.length - 1] === content) return;
    undoStack.push(content);
    if (undoStack.length > MAX_UNDO) undoStack.shift();
    redoStack.length = 0;
}

function undo() {
    if (undoStack.length <= 1) return;
    redoStack.push(undoStack.pop());
    editor.setValue(undoStack[undoStack.length - 1]);
    schedulePreview();
}

function redo() {
    if (redoStack.length === 0) return;
    const next = redoStack.pop();
    undoStack.push(next);
    editor.setValue(next);
    schedulePreview();
}

function initUndoRedo() {
    if (!editor) return;
    saveUndoState();
    let undoTimer = null;
    editor.on("change", () => { clearTimeout(undoTimer); undoTimer = setTimeout(() => saveUndoState(), 1000); });
    document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "z" && !e.shiftKey) { e.preventDefault(); undo(); }
        if ((e.ctrlKey || e.metaKey) && (e.key === "y" || (e.key === "z" && e.shiftKey))) { e.preventDefault(); redo(); }
    });
}

// ============================================================
// P1-10: Internationalization
// ============================================================

const I18N = {
    en: { "toolbar.new": "New", "toolbar.open": "Open", "toolbar.save": "Save", "toolbar.export": "Export", "status.ready": "Ready", "status.modified": "Modified", "status.saved": "Saved", "preview.ready": "Ready", "preview.updated": "Preview updated", "export.pdf": "Export PDF", "export.png": "Export PNG", "export.svg": "Export SVG", "export.html": "Export HTML Gallery" },
    fr: { "toolbar.new": "Nouveau", "toolbar.open": "Ouvrir", "toolbar.save": "Enregistrer", "toolbar.export": "Exporter", "status.ready": "Prêt", "status.modified": "Modifié", "status.saved": "Enregistré", "preview.ready": "Prêt", "preview.updated": "Aperçu mis à jour", "export.pdf": "Exporter PDF", "export.png": "Exporter PNG", "export.svg": "Exporter SVG", "export.html": "Exporter galerie HTML" },
    de: { "toolbar.new": "Neu", "toolbar.open": "Öffnen", "toolbar.save": "Speichern", "toolbar.export": "Exportieren", "status.ready": "Bereit", "status.modified": "Geändert", "status.saved": "Gespeichert", "preview.ready": "Bereit", "preview.updated": "Vorschau aktualisiert", "export.pdf": "PDF exportieren", "export.png": "PNG exportieren", "export.svg": "SVG exportieren", "export.html": "HTML-Galerie exportieren" },
    nl: { "toolbar.new": "Nieuw", "toolbar.open": "Openen", "toolbar.save": "Opslaan", "toolbar.export": "Exporteren", "status.ready": "Klaar", "status.modified": "Gewijzigd", "status.saved": "Opgeslagen", "preview.ready": "Klaar", "preview.updated": "Voorvertoning bijgewerkt", "export.pdf": "PDF exporteren", "export.png": "PNG exporteren", "export.svg": "SVG exporteren", "export.html": "HTML-galerie exporteren" },
    it: { "toolbar.new": "Nuovo", "toolbar.open": "Apri", "toolbar.save": "Salva", "toolbar.export": "Esporta", "status.ready": "Pronto", "status.modified": "Modificato", "status.saved": "Salvato", "preview.ready": "Pronto", "preview.updated": "Anteprima aggiornata", "export.pdf": "Esporta PDF", "export.png": "Esporta PNG", "export.svg": "Esporta SVG", "export.html": "Esporta galleria HTML" },
};

let currentLang = "en";

function t(key) { return I18N[currentLang]?.[key] || I18N.en[key] || key; }

function setLanguage(lang) {
    if (!I18N[lang]) return;
    currentLang = lang;
    localStorage.setItem("stampalbum-lang", lang);
    applyTranslations();
}

function applyTranslations() {
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const text = t(el.dataset.i18n);
        if (el.placeholder) el.placeholder = text;
        else el.textContent = text;
    });
}

function initI18n() {
    const saved = localStorage.getItem("stampalbum-lang");
    if (saved && I18N[saved]) { currentLang = saved; }
    else { const bl = navigator.language?.split("-")[0]; if (I18N[bl]) currentLang = bl; }
    applyTranslations();
}

// ============================================================
// P1-8: Responsive / Mobile
// ============================================================

function initResponsive() {
    const mq = window.matchMedia("(max-width: 768px)");
    function handleChange(e) {
        document.body.classList.toggle("is-mobile", e.matches);
        if (e.matches) {
            document.getElementById("wizard-panel")?.classList.add("wizard-hidden");
            document.getElementById("sidebar")?.classList.add("sidebar-hidden");
        }
    }
    mq.addEventListener("change", handleChange);
    handleChange(mq);
    if ("ontouchstart" in window || navigator.maxTouchPoints > 0) {
        document.body.classList.add("is-touch");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initExportDropdown();
    initUndoRedo();
    initI18n();
    initResponsive();
    // Language selector
    document.querySelectorAll(".lang-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".lang-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            setLanguage(btn.dataset.lang);
        });
    });
});

// ============================================================
// P1-4: Bidirectional DSL <-> Visual Sync
// ============================================================

let visualSyncEnabled = false;
let stampMap = [];
let selectedStampIdx = -1;

function initVisualSync() {
    var toggle = document.getElementById("toggle-visual");
    if (toggle) {
        toggle.addEventListener("change", function(e) {
            visualSyncEnabled = e.target.checked;
            if (visualSyncEnabled) enableVisualMode();
            else disableVisualMode();
        });
    }
    document.getElementById("vpp-close").addEventListener("click", closePropertyPanel);
    document.getElementById("vpp-apply").addEventListener("click", applyStampProperties);
    document.getElementById("vpp-delete").addEventListener("click", deleteSelectedStamp);
    var frame = document.getElementById("preview-frame");
    frame.addEventListener("load", function() {
        if (visualSyncEnabled) setTimeout(function() { buildStampMap(); }, 200);
    });
}

function enableVisualMode() {
    visualSyncEnabled = true;
    var overlay = document.getElementById("visual-overlay");
    overlay.classList.remove("visual-hidden");
    overlay.style.pointerEvents = "auto";
    buildStampMap();
}

function disableVisualMode() {
    visualSyncEnabled = false;
    var overlay = document.getElementById("visual-overlay");
    overlay.classList.add("visual-hidden");
    overlay.style.pointerEvents = "none";
    closePropertyPanel();
    clearDslHighlight();
}

function buildStampMap() {
    stampMap = [];
    if (!editor) return;
    var dsl = editor.getValue();
    var lines = dsl.split("\n");
    var currentPageIdx = 0;
    var currentRowIdx = 0;
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i].trim();
        if (line.startsWith("PAGE_START")) { currentPageIdx++; currentRowIdx = 0; }
        else if (line.match(/^ROW_START_/)) { currentRowIdx++; }
        else if (line.match(/^STAMP_ADD/)) {
            var parsed = parseStampLine(line, i);
            if (parsed) { parsed.pageIdx = currentPageIdx; parsed.rowIdx = currentRowIdx; stampMap.push(parsed); }
        }
    }
    renderStampOverlay();
}

function parseStampLine(line, lineIdx) {
    var match = line.match(/^(STAMP_ADD\w*)\s*\((.+)\)\s*$/);
    if (!match) return null;
    var cmd = match[1];
    var params = match[2];
    var args = [];
    var current = "";
    var inQuote = false;
    for (var i = 0; i < params.length; i++) {
        var ch = params[i];
        if (ch === '"') { inQuote = !inQuote; }
        else if (ch === ',' && !inQuote) { args.push(current.trim()); current = ""; }
        else { current += ch; }
    }
    if (current.trim()) args.push(current.trim());
    var unquote = function(s) { return s.replace(/^"/, "").replace(/"$/, ""); };
    var width = 0, height = 0, description = "", catalog = "", shape = "rectangle", imagePath = "";
    if (cmd === "STAMP_ADD_BLANK") { width = parseFloat(args[0]) || 0; height = parseFloat(args[1]) || 0; }
    else if (cmd === "STAMP_ADD_IMG") { width = parseFloat(args[0]) || 0; height = parseFloat(args[1]) || 0; imagePath = unquote(args[2]) || ""; description = unquote(args[3]) || ""; catalog = unquote(args[4]) || ""; }
    else {
        width = parseFloat(args[0]) || 0; height = parseFloat(args[1]) || 0;
        description = unquote(args[2]) || ""; catalog = unquote(args[3]) || "";
        if (cmd === "STAMP_ADD_TRIANGLE") shape = "triangle";
        else if (cmd === "STAMP_ADD_DIAMOND") shape = "diamond";
        else if (cmd === "STAMP_ADD_OVAL") shape = "oval";
        else if (cmd === "STAMP_ADD_HEXAGON") shape = "hexagon";
        else if (cmd === "STAMP_ADD_OCTAGON") shape = "octagon";
        else if (cmd === "STAMP_ADD_PENTAGON") shape = "pentagon";
    }
    return { line: lineIdx, cmd: cmd, width: width, height: height, description: description, catalog: catalog, shape: shape, imagePath: imagePath, heading: "", dslLine: line };
}

function renderStampOverlay() {
    var overlay = document.getElementById("visual-overlay");
    overlay.innerHTML = "";
    if (stampMap.length === 0) {
        overlay.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);font-size:13px;text-align:center;padding:20px;">No stamps found.<br>Add stamps via DSL or visual builder.</div>';
        return;
    }
    var frame = document.getElementById("preview-frame");
    var frameDoc = frame.contentDocument || frame.contentWindow.document;
    if (!frameDoc) return;
    var stampEls = frameDoc.querySelectorAll(".stamp");
    var frameRect = frame.getBoundingClientRect();
    stampEls.forEach(function(stampEl, idx) {
        var rect = stampEl.getBoundingClientRect();
        if (rect.width === 0) return;
        var el = document.createElement("div");
        el.className = "visual-stamp-overlay";
        el.style.cssText = "position:absolute;left:" + (rect.left - frameRect.left) + "px;top:" + (rect.top - frameRect.top) + "px;width:" + rect.width + "px;height:" + rect.height + "px;cursor:pointer;border-radius:2px;transition:outline 0.15s;";
        el.title = (stampMap[idx] && stampMap[idx].description) || ("Stamp " + (idx + 1));
        el.dataset.stampIdx = idx;
        el.addEventListener("click", function(e) { e.stopPropagation(); selectStamp(idx); });
        el.addEventListener("mouseenter", function() { if (selectedStampIdx !== idx) { el.style.outline = "2px dashed var(--accent)"; el.style.outlineOffset = "2px"; } });
        el.addEventListener("mouseleave", function() { if (selectedStampIdx !== idx) { el.style.outline = ""; } });
        overlay.appendChild(el);
    });
}

function selectStamp(idx) {
    selectedStampIdx = idx;
    var stamp = stampMap[idx];
    if (!stamp) return;
    document.querySelectorAll(".visual-stamp-overlay").forEach(function(el, i) {
        if (i === idx) { el.style.outline = "2px solid var(--accent)"; el.style.outlineOffset = "2px"; el.style.background = "rgba(88,166,255,0.1)"; }
        else { el.style.outline = ""; el.style.background = ""; }
    });
    highlightDslLine(stamp.line);
    showPropertyPanel(stamp);
}

function showPropertyPanel(stamp) {
    document.getElementById("visual-property-panel").classList.add("open");
    document.getElementById("vpp-desc").value = stamp.description || "";
    document.getElementById("vpp-cat").value = stamp.catalog || "";
    document.getElementById("vpp-width").value = stamp.width || 32;
    document.getElementById("vpp-height").value = stamp.height || 37;
    document.getElementById("vpp-shape").value = stamp.shape || "rectangle";
    document.getElementById("vpp-heading").value = stamp.heading || "";
    var imgSelect = document.getElementById("vpp-image");
    imgSelect.innerHTML = '<option value="">No image</option>';
    var images = window._uploadedImages || [];
    images.forEach(function(img) {
        var opt = document.createElement("option");
        opt.value = img; opt.textContent = img;
        if (img === stamp.imagePath) opt.selected = true;
        imgSelect.appendChild(opt);
    });
}

function closePropertyPanel() {
    document.getElementById("visual-property-panel").classList.remove("open");
    selectedStampIdx = -1;
    clearDslHighlight();
    document.querySelectorAll(".visual-stamp-overlay").forEach(function(el) { el.style.outline = ""; el.style.background = ""; });
}

function applyStampProperties() {
    if (selectedStampIdx < 0 || !stampMap[selectedStampIdx]) return;
    var stamp = stampMap[selectedStampIdx];
    var newDesc = document.getElementById("vpp-desc").value;
    var newCat = document.getElementById("vpp-cat").value;
    var newWidth = parseFloat(document.getElementById("vpp-width").value) || 32;
    var newHeight = parseFloat(document.getElementById("vpp-height").value) || 37;
    var newShape = document.getElementById("vpp-shape").value;
    var newHeading = document.getElementById("vpp-heading").value;
    var newImage = document.getElementById("vpp-image").value;
    var dsl = editor.getValue();
    var lines = dsl.split("\n");
    var lineIdx = stamp.line;
    var newLine;
    if (newImage) { newLine = "STAMP_ADD_IMG(" + newWidth + " " + newHeight + ' "' + newImage + '" "' + newDesc + '" "' + newCat + '" "" "")'; }
    else { var shapeCmd = newShape === "rectangle" ? "STAMP_ADD" : "STAMP_ADD_" + newShape.toUpperCase(); newLine = shapeCmd + "(" + newWidth + " " + newHeight + ' "' + newDesc + '" "' + newCat + '" "" "")'; }
    lines[lineIdx] = newLine;
    if (newHeading) {
        var nextLine = lines[lineIdx + 1] ? lines[lineIdx + 1].trim() : "";
        if (nextLine && nextLine.startsWith("STAMP_HEADING")) { lines[lineIdx + 1] = 'STAMP_HEADING(HB 10 "' + newHeading + '")'; }
        else { lines.splice(lineIdx + 1, 0, 'STAMP_HEADING(HB 10 "' + newHeading + '")'); stampMap.forEach(function(s, i) { if (i > selectedStampIdx) s.line++; }); }
    }
    editor.setValue(lines.join("\n"));
    saveUndoState();
    schedulePreview();
    setTimeout(function() { buildStampMap(); }, 500);
    showToast("Stamp updated", "success");
}

function deleteSelectedStamp() {
    if (selectedStampIdx < 0 || !stampMap[selectedStampIdx]) return;
    var stamp = stampMap[selectedStampIdx];
    var dsl = editor.getValue();
    var lines = dsl.split("\n");
    var lineIdx = stamp.line;
    var nextLine = lines[lineIdx + 1] ? lines[lineIdx + 1].trim() : "";
    if (nextLine && nextLine.startsWith("STAMP_HEADING")) { lines.splice(lineIdx, 2); }
    else { lines.splice(lineIdx, 1); }
    editor.setValue(lines.join("\n"));
    saveUndoState();
    closePropertyPanel();
    schedulePreview();
    setTimeout(function() { buildStampMap(); }, 500);
    showToast("Stamp deleted", "success");
}

function highlightDslLine(lineIdx) {
    clearDslHighlight();
    if (!editor) return;
    editor.addLineClass(lineIdx, "background", "cm-dsl-stamp-line");
    editor.scrollIntoView({ line: lineIdx, ch: 0 }, 100);
}

function clearDslHighlight() {
    if (!editor) return;
    var count = editor.lineCount();
    for (var i = 0; i < count; i++) { try { editor.removeLineClass(i, "background", "cm-dsl-stamp-line"); } catch(e) {} }
}

function trackUploadedImage(filename) {
    if (!window._uploadedImages) window._uploadedImages = [];
    if (window._uploadedImages.indexOf(filename) === -1) window._uploadedImages.push(filename);
}

var origLoadFileList = window.loadFileList;
window.loadFileList = async function() {
    if (origLoadFileList) await origLoadFileList();
    try {
        var response = await fetch(`${API_BASE}/images`);
        if (response.ok) { var images = await response.json(); window._uploadedImages = images; }
    } catch(e) {}
};

var stampMapTimer = null;
var origSchedulePreview = window.schedulePreview;
window.schedulePreview = function() {
    if (origSchedulePreview) origSchedulePreview();
    if (visualSyncEnabled) { clearTimeout(stampMapTimer); stampMapTimer = setTimeout(function() { buildStampMap(); }, 600); }
};

document.addEventListener("DOMContentLoaded", function() { initVisualSync(); });

// ============================================================
// P2-1: Inline Text Formatting Toolbar
// ============================================================

function initFormattingToolbar() {
    document.querySelectorAll(".fmt-btn").forEach(function(btn) {
        btn.addEventListener("click", function() {
            var fmt = btn.dataset.fmt;
            if (fmt === "help") {
                showToast("Formatting: **bold** *italic* _underline_ ~~strike~~ `code` ^sup^ ~sub~", "info");
                return;
            }
            applyFormatting(fmt);
        });
    });
    document.addEventListener("keydown", function(e) {
        if (!(e.ctrlKey || e.metaKey)) return;
        if (e.key === "b") { e.preventDefault(); applyFormatting("bold"); }
        if (e.key === "i") { e.preventDefault(); applyFormatting("italic"); }
        if (e.key === "u") { e.preventDefault(); applyFormatting("underline"); }
    });
}

function applyFormatting(fmt) {
    if (!editor) return;
    var sel = editor.getSelection();
    var cursor = editor.getCursor();
    var markers = { bold: ["**","**"], italic: ["*","*"], underline: ["_","_"], strikethrough: ["~~","~~"], code: ["`","`"], superscript: ["^","^"], subscript: ["~","~"] };
    var m = markers[fmt];
    if (!m) return;
    if (sel) { editor.replaceSelection(m[0] + sel + m[1]); }
    else { editor.replaceRange(m[0] + m[1], cursor); editor.setCursor({ line: cursor.line, ch: cursor.ch + m[0].length }); }
    editor.focus();
}

document.addEventListener("DOMContentLoaded", function() { initFormattingToolbar(); });
