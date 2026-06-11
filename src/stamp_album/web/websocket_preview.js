/**
 * WebSocket Real-Time Preview (P2-13)
 * Replaces HTTP polling with WebSocket for instant preview updates.
 */

(function() {
    "use strict";

    var ws = null;
    var wsConnected = false;
    var wsReconnectTimer = null;
    var wsReconnectDelay = 1000;
    var renderSeq = 0; // Sequence number to handle out-of-order responses

    function initWebSocket() {
        var protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        var wsUrl = protocol + "//" + window.location.host + "/ws/preview";

        try {
            ws = new WebSocket(wsUrl);
        } catch (e) {
            console.warn("WebSocket not available, falling back to HTTP");
            return;
        }

        ws.onopen = function() {
            wsConnected = true;
            wsReconnectDelay = 1000;
            clearTimeout(wsReconnectTimer);
            console.log("WebSocket connected");
        };

        ws.onmessage = function(event) {
            try {
                var msg = JSON.parse(event.data);
                handleWSMessage(msg);
            } catch (e) {
                console.error("WebSocket message parse error:", e);
            }
        };

        ws.onclose = function() {
            wsConnected = false;
            scheduleReconnect();
        };

        ws.onerror = function(err) {
            console.warn("WebSocket error:", err);
            wsConnected = false;
        };
    }

    function handleWSMessage(msg) {
        switch (msg.type) {
            case "connected":
                console.log("WebSocket session:", msg.client_id);
                break;
            case "preview":
                if (msg.status === "empty") {
                    setPreviewHtml("<html><body style='display:flex;align-items:center;justify-content:center;height:100vh;color:#999;font-family:system-ui'><p>Enter DSL code to see preview</p></body></html>");
                } else {
                    setPreviewHtml(msg.html);
                }
                if (msg.warnings && msg.warnings.length > 0) {
                    // Show warnings in status bar
                    var warnEl = document.getElementById("preview-status");
                    if (warnEl) warnEl.textContent = msg.warnings.length + " warning(s)";
                }
                break;
            case "error":
                var detail = msg.message || "Unknown error";
                if (msg.line) detail += " (line " + msg.line + ")";
                setPreviewHtml("<html><body style='padding:40px;font-family:system-ui;color:#f85149'><h3>Preview Error</h3><pre>" + escapeHtml(detail) + "</pre></body></html>");
                break;
            case "validation":
                // Could show validation UI
                break;
            case "pong":
                break;
        }
    }

    function scheduleReconnect() {
        clearTimeout(wsReconnectTimer);
        wsReconnectTimer = setTimeout(function() {
            if (!wsConnected) {
                console.log("WebSocket reconnecting...");
                initWebSocket();
                // Exponential backoff up to 30s
                wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000);
            }
        }, wsReconnectDelay);
    }

    // Override the existing schedulePreview to use WebSocket
    var origSchedulePreview = window.schedulePreview;
    window.schedulePreview = function() {
        if (!editor) return;

        if (wsConnected && ws && ws.readyState === WebSocket.OPEN) {
            // Use WebSocket for real-time preview
            var dsl = editor.getValue();
            renderSeq++;
            ws.send(JSON.stringify({ type: "render", dsl: dsl, seq: renderSeq }));
        } else if (origSchedulePreview) {
            // Fall back to HTTP
            origSchedulePreview();
        }
    };

    // Heartbeat to keep connection alive
    setInterval(function() {
        if (wsConnected && ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
        }
    }, 30000);

    // Initialize on DOM ready
    document.addEventListener("DOMContentLoaded", initWebSocket);
})();
