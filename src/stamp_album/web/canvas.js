"use strict";
console.log("canvas.js: loaded");

var _overlay = null, _canvasEl = null, _stamps = [], _active = false, _drag = null;
var _scale = 2.5, _snap = 5, _pw = 210, _ph = 297, _nextId = 1, _initialized = false;

function initCanvas() {
    if (_initialized) return;
    _initialized = true;
    _overlay = document.getElementById("visual-overlay");
    if (!_overlay) return;
    _canvasEl = document.createElement("div");
    _canvasEl.id = "layout-canvas";
    _canvasEl.className = "layout-canvas";
    _canvasEl.style.width = (_pw * _scale) + "px";
    _canvasEl.style.height = (_ph * _scale) + "px";
    _overlay.appendChild(_canvasEl);
    _canvasEl.addEventListener("dragover", function(e) { if (!_active) return; e.preventDefault(); _canvasEl.classList.add("drop-target"); });
    _canvasEl.addEventListener("dragleave", function() { _canvasEl.classList.remove("drop-target"); });
    _canvasEl.addEventListener("drop", onCanvasDrop);
    _canvasEl.addEventListener("mousedown", onCanvasMouseDown);
    document.addEventListener("mousemove", onCanvasMouseMove);
    document.addEventListener("mouseup", onCanvasMouseUp);
    document.addEventListener("keydown", onCanvasKey);
    console.log("canvas.js: init complete");
}

function snapMm(v) { return _snap > 0 ? Math.round(v / _snap) * _snap : Math.round(v * 10) / 10; }

function onCanvasDrop(e) {
    if (!_active) return;
    e.preventDefault(); _canvasEl.classList.remove("drop-target");
    var r = _canvasEl.getBoundingClientRect();
    var xm = Math.max(0, Math.min(snapMm((e.clientX - r.left) / _scale), _pw - 40));
    var ym = Math.max(0, Math.min(snapMm((e.clientY - r.top) / _scale), _ph - 30));
    var shape = "rectangle", w = 40, h = 30, type = "stamp";
    try { var d = JSON.parse(e.dataTransfer.getData("text/plain")); if (d) { type = d.type || "stamp"; shape = d.shape || "rectangle"; w = d.width || 40; h = d.height || 30; } } catch (_) {}
    if (type === "text") addElement({ type: "text", shape: "text", x: xm, y: ym, w: 60, h: 10, description: "Text", align: d.align || "left" });
    else if (type === "row") addElement({ type: "row", shape: "row", x: xm, y: ym, w: 180, h: 30, description: "Row", style: d.style || "FS" });
    else addElement({ type: "stamp", shape: shape, x: xm, y: ym, w: w, h: h, description: "" });
}

function addElement(params) {
    var s = { id: "cs" + (_nextId++), type: params.type, shape: params.shape, x: params.x, y: params.y, w: params.w, h: params.h, description: params.description || "" };
    if (params.align) s.align = params.align;
    if (params.style) s.style = params.style;
    var el = document.createElement("div");
    el.className = "canvas-stamp shape-" + (s.shape || "rectangle");
    el.dataset.stampId = s.id;
    el.style.left = (s.x * _scale) + "px";
    el.style.top = (s.y * _scale) + "px";
    el.style.width = (s.w * _scale) + "px";
    el.style.height = (s.h * _scale) + "px";
    var lbl = document.createElement("span"); lbl.className = "canvas-stamp-label"; lbl.textContent = s.description || s.shape; el.appendChild(lbl);
    ["nw","ne","sw","se","n","s","e","w"].forEach(function(h) { var ha = document.createElement("div"); ha.className = "canvas-handle canvas-handle-" + h; ha.dataset.handle = h; ha.dataset.stampId = s.id; el.appendChild(ha); });
    s.el = el; _canvasEl.appendChild(el); _stamps.push(s);
    selectStamp(s.id); syncToDSL();
}

function selectStamp(id) { _stamps.forEach(function(s) { s.selected = (s.id === id); if (s.el) { s.el.className = "canvas-stamp shape-" + (s.shape || "rectangle") + (s.selected ? " selected" : ""); s.el.style.left = (s.x*_scale)+"px"; s.el.style.top = (s.y*_scale)+"px"; s.el.style.width = (s.w*_scale)+"px"; s.el.style.height = (s.h*_scale)+"px"; } }); }
function findStamp(id) { for (var i=0;i<_stamps.length;i++) if (_stamps[i].id===id) return _stamps[i]; return null; }
function getSelected() { for (var i=0;i<_stamps.length;i++) if (_stamps[i].selected) return _stamps[i]; return null; }
function removeStamp(id) { var s=findStamp(id); if(!s)return; if(s.el)s.el.remove(); _stamps=_stamps.filter(function(x){return x.id!==id;}); syncToDSL(); }

function onCanvasMouseDown(e) {
    if (!_active) return;
    var t=e.target;
    if (t.classList.contains("canvas-handle")) { var s=findStamp(t.dataset.stampId); if(!s)return; selectStamp(s.id); _drag={id:s.id,handle:t.dataset.handle,sx:e.clientX,sy:e.clientY,ox:s.x,oy:s.y,ow:s.w,oh:s.h}; e.preventDefault(); e.stopPropagation(); return; }
    var el=t.closest(".canvas-stamp");
    if(el){var s2=findStamp(el.dataset.stampId);if(!s2)return;selectStamp(s2.id);_drag={id:s2.id,handle:"move",sx:e.clientX,sy:e.clientY,ox:s2.x,oy:s2.y,ow:s2.w,oh:s2.h};e.preventDefault();e.stopPropagation();return;}
    if(t===_canvasEl) selectStamp(null);
}
function onCanvasMouseMove(e) {
    if(!_drag||!_active)return; var s=findStamp(_drag.id); if(!s)return;
    var dx=snapMm((e.clientX-_drag.sx)/_scale), dy=snapMm((e.clientY-_drag.sy)/_scale);
    var h=_drag.handle,x=_drag.ox,y=_drag.oy,w=_drag.ow,oh=_drag.oh;
    if(h==="move"){x+=dx;y+=dy;}else{if(h.indexOf("w")>=0){x+=dx;w-=dx;}if(h.indexOf("e")>=0){w+=dx;}if(h.indexOf("n")>=0){y+=dy;oh-=dy;}if(h.indexOf("s")>=0){oh+=dy;}if(w<5)w=5;if(oh<5)oh=5;}
    s.x=Math.max(0,x);s.y=Math.max(0,y);s.w=Math.min(w,_pw-s.x);s.h=Math.min(oh,_ph-s.y);
    if(s.el){s.el.style.left=(s.x*_scale)+"px";s.el.style.top=(s.y*_scale)+"px";s.el.style.width=(s.w*_scale)+"px";s.el.style.height=(s.h*_scale)+"px";}
    syncToDSL();
}
function onCanvasMouseUp(e){_drag=null;}
function onCanvasKey(e){if(!_active)return;var s=getSelected();if(!s)return;if(e.key==="Delete"||e.key==="Backspace")removeStamp(s.id);if(e.key==="Escape")selectStamp(null);}

function syncToDSL() {
    var ed = window.editor; if (!ed) return;
    var lines = ed.getValue().split("\n"), out = [];
    for (var i=0;i<lines.length;i++){
        var t=lines[i].trim();
        // Remove ALL layout commands (old row-based and canvas absolute)
        if(t.startsWith("ROW_START")||t.startsWith("STAMP_ADD")||t.startsWith("PAGE_TEXT")||t==="ROW_SPACE") continue;
        out.push(lines[i]);
    }
    var ins=out.length;
    for(var j=out.length-1;j>=0;j--){var lt=out[j].trim();if(lt==="PAGE_START"||lt.startsWith("ROW_START")||lt.startsWith("STAMP_ADD")||lt.startsWith("PAGE_TEXT")){ins=j+1;break;}}
    _stamps.forEach(function(s){
        if(s.type==="text"){var cmd=s.align==="center"?"PAGE_TEXT_CENTRE":s.align==="right"?"PAGE_TEXT_RIGHT":"PAGE_TEXT";out.splice(ins++,0,cmd+"(\"HN\" 12 \""+(s.description||"Text")+"\")");}
        else if(s.type==="row"){out.splice(ins++,0,"ROW_START_AT("+s.x.toFixed(1)+" "+s.y.toFixed(1)+" \""+(s.style||"FS")+"\" \"HN\" 10 5 180)");}
        else{out.splice(ins++,0,"STAMP_ADD_AT("+s.x.toFixed(1)+" "+s.y.toFixed(1)+" "+s.w.toFixed(1)+" "+s.h.toFixed(1)+" \""+(s.description||"")+"\" \"\" \"\"\")");}
    });
    ed.setValue(out.join("\n"));
    if(typeof schedulePreview==="function") schedulePreview();
}

function syncFromDSL() {
    var ed=window.editor; if(!ed) return;
    _stamps.forEach(function(s){if(s.el)s.el.remove();}); _stamps=[];
    var lines=ed.getValue().split("\n");
    for(var i=0;i<lines.length;i++){
        var t=lines[i].trim();
        var m=t.match(/^STAMP_ADD_AT\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"/);
        if(m){addElement({type:"stamp",shape:"rectangle",x:parseFloat(m[1]),y:parseFloat(m[2]),w:parseFloat(m[3]),h:parseFloat(m[4]),description:m[5]||""});continue;}
        var m2=t.match(/^(PAGE_TEXT|PAGE_TEXT_CENTRE|PAGE_TEXT_CENTER|PAGE_TEXT_RIGHT)\(\s*"HN"\s+(\d+)\s+"([^"]*)"/);
        if(m2){var align=m2[1]==="PAGE_TEXT_CENTRE"?"center":m2[1]==="PAGE_TEXT_RIGHT"?"right":"left";addElement({type:"text",shape:"text",x:parseFloat(m2[2]),y:0,w:60,h:10,description:m2[3]||"Text",align:align});continue;}
        var m3=t.match(/^ROW_START_AT\(\s*([\d.]+)\s+([\d.]+)\s+"(\w+)"/);
        if(m3){addElement({type:"row",shape:"row",x:parseFloat(m3[1]),y:parseFloat(m3[2]),w:180,h:30,description:"Row",style:m3[3]});}
    }
}

// Toggle handler — init canvas on first click
var _toggleHandler = function(e) {
    var t = e.target;
    initCanvas(); // ensure initialized
    _active = t.checked;
    if (_active) {
        document.body.classList.add("layout-mode");
        _canvasEl.style.pointerEvents = "auto";
        var f = document.getElementById("preview-frame");
        if (f) f.style.pointerEvents = "none";
        // Clear the default template and start fresh for free-form layout
        if (window.editor) {
            window.editor.setValue("PAGE_START");
        }
        _stamps = [];
        if (typeof showToast === "function") showToast("Layout mode ON — click or drag stamps", "info");
    } else {
        document.body.classList.remove("layout-mode");
        _canvasEl.style.pointerEvents = "none";
        var f2 = document.getElementById("preview-frame");
        if (f2) f2.style.pointerEvents = "auto";
    }
};
var _toggle = document.getElementById("toggle-layout");
if (_toggle) _toggle.addEventListener("change", _toggleHandler);

// Public API
window.addStampToCanvas = function(shape,w,h,x,y,desc){initCanvas();addElement({type:"stamp",shape:shape||"rectangle",x:x||10,y:y||10,w:w||40,h:h||30,description:desc||""});};
window.addTextToCanvas = function(x,y,align){initCanvas();addElement({type:"text",shape:"text",x:x||10,y:y||10,w:60,h:10,description:"Text",align:align||"left"});};
window.addRowToCanvas = function(x,y,style){initCanvas();addElement({type:"row",shape:"row",x:x||10,y:y||10,w:180,h:30,description:"Row",style:style||"FS"});};

console.log("canvas.js: ready");