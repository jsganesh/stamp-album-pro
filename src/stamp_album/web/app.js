/**
 * StampAlbum Pro — Visual Canvas Editor (Redesign)
 *
 * Default mode: visual drag-and-drop canvas.
 * Advanced mode: DSL editor toggle.
 */

(function() {
    "use strict";

    var elements = [];
    var selectedId = null;
    var nextId = 1;
    var undoStack = [], redoStack = [];
    var _scale = 2.5, _snap = 5, _pw = 595, _ph = 842, _initialized = false;
    var _dragging = false, _dragEl = null, _dragHandle = null, _dragStart = {};

    function $(id) { return document.getElementById(id); }

    function init() {
        if (_initialized) return;
        _initialized = true;
        var page = $("page");
        if (!page) return;

        // Palette drag
        document.querySelectorAll(".palette-item[draggable]").forEach(function(item) {
            item.addEventListener("dragstart", function(e) {
                e.dataTransfer.setData("text/plain", JSON.stringify({
                    type: item.dataset.type, shape: item.dataset.shape || "rectangle",
                    subtype: item.dataset.subtype || "", w: parseFloat(item.dataset.w) || 40, h: parseFloat(item.dataset.h) || 30
                }));
                e.dataTransfer.effectAllowed = "copy";
            });
        });

        // Page drop
        page.addEventListener("dragover", function(e) { e.preventDefault(); page.classList.add("drag-over"); });
        page.addEventListener("dragleave", function() { page.classList.remove("drag-over"); });
        page.addEventListener("drop", function(e) {
            e.preventDefault(); page.classList.remove("drag-over");
            var d; try { d = JSON.parse(e.dataTransfer.getData("text/plain")); } catch(_) { return; }
            var r = page.getBoundingClientRect();
            var x = Math.max(0, Math.min(Math.round((e.clientX - r.left) / _snap) * _snap, _pw - 80));
            var y = Math.max(0, Math.min(Math.round((e.clientY - r.top) / _snap) * _snap, _ph - 60));
            addElement({ type: d.type||"stamp", shape: d.shape||"rectangle", x: x, y: y, w: d.w||80, h: d.h||60, label: d.type==="text"?"Text":"", align: d.subtype||"left" });
        });

        // Mouse interaction on canvas
        page.addEventListener("mousedown", function(e) {
            var el = e.target.closest(".canvas-el");
            if (!el) { selectedId = null; renderAll(); return; }
            var eid = el.dataset.elId;
            var obj = elements.find(function(x){return x.id===eid;});
            if (!obj) return;
            if (e.target.classList.contains("resize-handle")) {
                _dragHandle = e.target.dataset.handle;
            } else {
                _dragHandle = "move";
            }
            select(eid);
            _dragging = true; _dragEl = obj;
            _dragStart = { x: e.clientX, y: e.clientY, ox: obj.x, oy: obj.y, ow: obj.w, oh: obj.h };
            e.preventDefault(); e.stopPropagation();
        });

        document.addEventListener("mousemove", function(e) {
            if (!_dragging || !_dragEl) return;
            var dx = Math.round((e.clientX - _dragStart.x) / _snap) * _snap;
            var dy = Math.round((e.clientY - _dragStart.y) / _snap) * _snap;
            var h = _dragHandle, x = _dragStart.ox, y = _dragStart.oy, w = _dragStart.ow, oh = _dragStart.oh;
            if (h === "move") { x += dx; y += dy; }
            else {
                if (h.indexOf("w")>=0) { x+=dx; w-=dx; } if (h.indexOf("e")>=0) { w+=dx; }
                if (h.indexOf("n")>=0) { y+=dy; oh-=dy; } if (h.indexOf("s")>=0) { oh+=dy; }
                if (w<10) w=10; if (oh<10) oh=10;
            }
            _dragEl.x = Math.max(0, Math.min(x, _pw-_dragEl.w));
            _dragEl.y = Math.max(0, Math.min(y, _ph-_dragEl.h));
            _dragEl.w = Math.min(w, _pw-_dragEl.x);
            _dragEl.h = Math.min(oh, _ph-_dragEl.y);
            renderAll();
        });

        document.addEventListener("mouseup", function() { _dragging=false; _dragEl=null; _dragHandle=null; });

        // Props panel
        ["prop-x","prop-y","prop-w","prop-h"].forEach(function(id){
            $(id).addEventListener("change", function(){
                var el=elements.find(function(x){return x.id===selectedId;}); if(!el)return;
                el[id.replace("prop-","")] = parseFloat(this.value)||0; renderAll();
            });
        });
        $("prop-label").addEventListener("change", function(){
            var el=elements.find(function(x){return x.id===selectedId;}); if(!el)return;
            el.label=this.value; renderAll();
        });
        $("prop-border-style").addEventListener("change", function(){
            var el=elements.find(function(x){return x.id===selectedId;}); if(!el)return;
            el.borderStyle=this.value; renderAll();
        });
        $("prop-border-color").addEventListener("change", function(){
            var el=elements.find(function(x){return x.id===selectedId;}); if(!el)return;
            el.borderColor=this.value; renderAll();
        });
        $("prop-fill-color").addEventListener("change", function(){
            var el=elements.find(function(x){return x.id===selectedId;}); if(!el)return;
            el.fillColor=this.value; renderAll();
        });
        $("btn-delete-el").addEventListener("click", function(){
            if(!selectedId)return;
            elements=elements.filter(function(x){return x.id!==selectedId;}); selectedId=null; renderAll();
        });

        // Keyboard
        document.addEventListener("keydown", function(e){
            if(e.target.tagName==="INPUT"||e.target.tagName==="TEXTAREA"||e.target.tagName==="SELECT")return;
            if(e.key==="Delete"||e.key==="Backspace"){if(selectedId){elements=elements.filter(function(x){return x.id!==selectedId;});selectedId=null;renderAll();}}
            if(e.key==="Escape"){selectedId=null;renderAll();}
        });

        // Toolbar
        $("btn-new").addEventListener("click", function(){elements=[];selectedId=null;renderAll();});
        $("btn-toggle-dsl").addEventListener("click", function(){
            $("dsl-panel").classList.toggle("open");
            if($("dsl-panel").classList.contains("open")){ $("dsl-textarea").value = buildDSL(); }
        });
        $("btn-apply-dsl").addEventListener("click", function(){
            parseDSL($("dsl-textarea").value); renderAll();
        });
        $("btn-close-dsl").addEventListener("click", function(){ $("dsl-panel").classList.remove("open"); });

        // Image upload
        $("img-upload-input").addEventListener("change", function(e){
            if(e.target.files.length===0)return;
            var file=e.target.files[0];
            var reader=new FileReader();
            reader.onload=function(ev){
                addElement({type:"image",shape:"rectangle",x:50,y:50,w:80,h:60,label:file.name,imagePath:ev.target.result,borderStyle:"solid",borderColor:"#999",borderWidth:0.5,fillColor:"#fff",fillOpacity:100});
            };
            reader.readAsDataURL(file);
        });

        console.log("StampAlbum Pro: canvas initialized");
    }

    function addElement(params) {
        var s = { id:"el"+(nextId++), type:params.type||"stamp", shape:params.shape||"rectangle",
            x:params.x||50, y:params.y||50, w:params.w||80, h:params.h||60,
            label:params.label||"", align:params.align||"left",
            borderStyle:params.borderStyle||"solid", borderColor:params.borderColor||"#666", borderWidth:params.borderWidth||1,
            fillColor:params.fillColor||"#fff", fillOpacity:params.fillOpacity||100,
            imagePath:params.imagePath||"" };
        elements.push(s); select(s.id); renderAll();
    }

    function select(id) {
        selectedId = id; renderAll();
        var el = elements.find(function(x){return x.id===id;});
        if (!el) { $("props-content").style.display="none"; $("props-panel").querySelector(".no-selection").style.display="block"; return; }
        $("props-content").style.display="block"; $("props-panel").querySelector(".no-selection").style.display="none";
        $("prop-x").value=Math.round(el.x); $("prop-y").value=Math.round(el.y);
        $("prop-w").value=Math.round(el.w); $("prop-h").value=Math.round(el.h);
        $("prop-label").value=el.label||"";
        $("prop-border-style").value=el.borderStyle||"solid";
        $("prop-border-color").value=el.borderColor||"#666";
        $("prop-fill-color").value=el.fillColor||"#fff";
    }

    function renderAll() {
        var page = $("page");
        page.querySelectorAll(".canvas-el").forEach(function(el){el.remove();});
        elements.forEach(function(el){
            var div = document.createElement("div");
            div.className = "canvas-el shape-" + (el.shape||"rectangle") + (el.id===selectedId?" selected":"");
            div.dataset.elId = el.id;
            div.style.left = el.x+"px"; div.style.top = el.y+"px";
            div.style.width = el.w+"px"; div.style.height = el.h+"px";
            div.style.border = (el.borderWidth||0) + "pt " + (el.borderStyle||"solid") + " " + (el.borderColor||"#666");
            div.style.backgroundColor = el.fillColor||"#fff";
            if (el.imagePath) { var img=document.createElement("img"); img.className="el-img"; img.src=el.imagePath; div.appendChild(img); }
            else if (el.label) { var lbl=document.createElement("span"); lbl.className="el-label"; lbl.textContent=el.label; div.appendChild(lbl); }
            ["nw","ne","sw","se","n","s","e","w"].forEach(function(h){
                var ha=document.createElement("div"); ha.className="resize-handle "+h; ha.dataset.handle=h; div.appendChild(ha);
            });
            page.appendChild(div);
        });
    }

    function buildDSL() {
        var lines = ["ALBUM_TITLE(\"My Album\")","ALBUM_PAGES_SIZE(210 297)","ALBUM_PAGES_MARGINS(15 15 15 15)","PAGE_START"];
        elements.forEach(function(el){
            if(el.type==="image") {
                lines.push("STAMP_ADD_IMG("+el.x.toFixed(1)+" "+el.y.toFixed(1)+" "+el.w.toFixed(1)+" "+el.h.toFixed(1)+" \""+(el.imagePath||"")+"\" \""+(el.label||"")+"\" \"\" \"\"\")");
            } else if(el.type==="text") {
                var cmd=el.align==="center"?"PAGE_TEXT_CENTRE":el.align==="right"?"PAGE_TEXT_RIGHT":"PAGE_TEXT";
                lines.push(cmd+"(\"HN\" 12 \""+(el.label||"Text")+"\")");
            } else {
                lines.push("STAMP_ADD_AT("+el.x.toFixed(1)+" "+el.y.toFixed(1)+" "+el.w.toFixed(1)+" "+el.h.toFixed(1)+" \""+(el.label||"")+"\" \""+el.shape+"\" \""+el.borderStyle+"\" \""+el.fillColor+"\")");
            }
        });
        return lines.join("\n");
    }

    function parseDSL(dsl) {
        elements = [];
        var lines = dsl.split("\n");
        for (var i=0;i<lines.length;i++) {
            var t = lines[i].trim();
            var m = t.match(/^(STAMP_ADD_AT|STAMP_ADD_IMG)\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"\s+"([^"]*)"\s+"([^"]*)"\s+"([^"]*)"\)/);
            if (m) { elements.push({id:"el"+(nextId++),type:m[1]==="STAMP_ADD_IMG"?"image":"stamp",shape:m[7]||"rectangle",x:parseFloat(m[2]),y:parseFloat(m[3]),w:parseFloat(m[4]),h:parseFloat(m[5]),label:m[6]||"",borderStyle:m[8]||"solid",fillColor:m[9]||"#fff",fillOpacity:100,imagePath:m[1]||""}); continue; }
            var m2 = t.match(/^(PAGE_TEXT|PAGE_TEXT_CENTRE|PAGE_TEXT_RIGHT)\(\s*"HN"\s+(\d+)\s+"([^"]*)"\)/);
            if (m2) { elements.push({id:"el"+(nextId++),type:"text",shape:"text",x:10,y:10,w:100,h:20,label:m[3]||"Text",align:m[2]==="PAGE_TEXT_CENTRE"?"center":m[2]==="PAGE_TEXT_RIGHT"?"right":"left",borderStyle:"none",fillColor:"transparent",fillOpacity:0}); }
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
})();
