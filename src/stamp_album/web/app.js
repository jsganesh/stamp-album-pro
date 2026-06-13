"use strict";
(function(){
var E=[],sel=null,nid=1,_sc=2.5,_sn=5,_pw=595,_ph=842,_init=false;
var _drg=false,_dragEl=null,_dragH=null,_ds={};
var _defBdr="solid",_defBdrC="#666",_defFillC="#fff";
var _collapsed={sb:false,rp:false};

function $(id){return document.getElementById(id);}
function mm(px){return Math.round(px/_sc*10)/10;}
function px(mm){return Math.round(mm*_sc);}

// ── System Fonts ──
var SYSTEM_FONTS=[];
function detectFonts(){
    var testStr="mmmmmmmmmmlli";
    var testSize="72px";
    var defaults={serif:"serif",sansSerif:"sans-serif",monospace:"monospace"};
    var testSpan=document.createElement("span");
    testSpan.style.fontSize=testSize;
    testSpan.style.position="absolute";
    testSpan.style.left="-9999px";
    testSpan.innerHTML=testStr;
    document.body.appendChild(testSpan);
    var defaultWidth={};
    for(var d in defaults){testSpan.style.fontFamily=defaults[d];defaultWidth[d]=testSpan.offsetWidth;}
    var candidates=["Arial","Arial Black","Arial Narrow","Calibri","Cambria","Candara","Comic Sans MS","Consolas","Courier New","Franklin Gothic","Garamond","Georgia","Helvetica","Impact","Lucida Console","Lucida Sans","Microsoft Sans Serif","Palatino","Segoe UI","Tahoma","Times New Roman","Trebuchet MS","Verdana","Bookman Old Style","Century Gothic","Gill Sans","Rockwell","Perpetua","Baskerville","Didot","Optima","Futura","Avant Garde","Goudy","American Typewriter","Andale Mono","Apple Chancery","Brush Script MT","Chalkduster","Copperplate","Herculanum","Luminari","Marker Felt","Noteworthy","Papyrus","Zapfino"];
    SYSTEM_FONTS=[];
    for(var i=0;i<candidates.length;i++){
        testSpan.style.fontFamily="'"+candidates[i]+"',sans-serif";
        if(testSpan.offsetWidth!==defaultWidth.sansSerif){SYSTEM_FONTS.push(candidates[i]);}
    }
    testSpan.remove();
    SYSTEM_FONTS.sort();
}
detectFonts();

function init(){
    if(_init)return;_init=true;
    var pg=$("page");if(!pg)return;

    // ── Palette Drag ──
    document.querySelectorAll(".p-item[draggable]").forEach(function(it){
        it.addEventListener("dragstart",function(e){
            e.dataTransfer.setData("text/plain",JSON.stringify({
                t:it.dataset.t,s:it.dataset.s||"rectangle",st:it.dataset.st||"",
                w:parseFloat(it.dataset.w)||80,h:parseFloat(it.dataset.h)||60,
                font:"HN",fs:12
            }));
            e.dataTransfer.effectAllowed="copy";
        });
    });

    // ── Page Drop ──
    pg.addEventListener("dragover",function(e){e.preventDefault();pg.classList.add("drag-over");});
    pg.addEventListener("dragleave",function(){pg.classList.remove("drag-over");});
    pg.addEventListener("drop",function(e){
        e.preventDefault();pg.classList.remove("drag-over");
        var d;try{d=JSON.parse(e.dataTransfer.getData("text/plain"));}catch(_){return;}
        var r=pg.getBoundingClientRect();
        var x=Math.max(0,Math.min(Math.round((e.clientX-r.left)/_sn)*_sn,_pw-40));
        var y=Math.max(0,Math.min(Math.round((e.clientY-r.top)/_sn)*_sn,_ph-30));
        var w=d.w||80,h=d.h||60;
        if(d.t==="text"){w=120;h=d.st==="heading"?24:d.st==="desc"?16:18;}
        if(d.t==="freehand"){w=100;h=80;}
        add({t:d.t||"stamp",s:d.s||"rectangle",x:x,y:y,w:w,h:h,
            lbl:d.t==="text"?(d.st==="heading"?"Heading":d.st==="desc"?"Description":"Label"):"",
            font:d.font||"HN",fs:d.st==="heading"?16:d.st==="desc"?10:12,
            bdr:_defBdr,bdrC:_defBdrC,bdrW:1,fill:_defFillC,fillA:100,img:""});
    });

    // ── Mouse on Canvas ──
    pg.addEventListener("mousedown",function(e){
        var el=e.target.closest(".cel");
        if(!el){sel=null;render();return;}
        var obj=E.find(function(x){return x.id===el.dataset.id;});if(!obj)return;
        if(e.target.classList.contains("rh")){_dragH=e.target.dataset.h;}else{_dragH="move";}
        select(obj.id);_drg=true;_dragEl=obj;
        _ds={x:e.clientX,y:e.clientY,ox:obj.x,oy:obj.y,ow:obj.w,oh:obj.h};
        e.preventDefault();e.stopPropagation();
    });

    document.addEventListener("mousemove",function(e){
        if(!_drg||!_dragEl)return;
        var dx=Math.round((e.clientX-_ds.x)/_sn)*_sn;
        var dy=Math.round((e.clientY-_ds.y)/_sn)*_sn;
        var h=_dragH,x=_ds.ox,y=_ds.oy,w=_ds.ow,oh=_ds.oh;
        if(h==="move"){x+=dx;y+=dy;}else{
            if(h.indexOf("w")>=0){x+=dx;w-=dx;}if(h.indexOf("e")>=0){w+=dx;}
            if(h.indexOf("n")>=0){y+=dy;oh-=dy;}if(h.indexOf("s")>=0){oh+=dy;}
            if(w<10)w=10;if(oh<10)oh=10;
        }
        _dragEl.x=Math.max(0,Math.min(x,_pw-_dragEl.w));
        _dragEl.y=Math.max(0,Math.min(y,_ph-_dragEl.h));
        _dragEl.w=Math.min(w,_pw-_dragEl.x);
        _dragEl.h=Math.min(oh,_ph-_dragEl.y);
        render();updateProps();
    });

    document.addEventListener("mouseup",function(){_drg=false;_dragEl=null;_dragH=null;});

    // ── Props Panel ──
    ["px","py","pw","ph"].forEach(function(id){
        $(id).addEventListener("change",function(){
            var el=E.find(function(x){return x.id===sel;});if(!el)return;
            el[id.replace("p","")]=mm(parseFloat(this.value)||0);render();
        });
    });
    $("plbl").addEventListener("change",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;el.lbl=this.value;render();});
    $("pbs").addEventListener("change",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;el.bdr=this.value;render();});
    $("pbc").addEventListener("change",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;el.bdrC=this.value;render();});
    $("pbw").addEventListener("change",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;el.bdrW=parseFloat(this.value)||0;render();});
    $("pfc").addEventListener("change",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;el.fill=this.value;render();});
    $("pfa").addEventListener("input",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;el.fillA=parseInt(this.value);$("pfa-v").textContent=this.value+"%";render();});
    $("pfnt").addEventListener("change",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;el.font=this.value;render();});
    $("pfs").addEventListener("change",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;el.fs=parseFloat(this.value)||12;render();});
    $("btn-del").addEventListener("click",function(){if(!sel)return;E=E.filter(function(x){return x.id!==sel;});sel=null;render();updateProps();});
    $("btn-dup-el").addEventListener("click",function(){if(!sel)return;var el=E.find(function(x){return x.id===sel;});if(!el)return;
        add(Object.assign({},el,{id:"el"+(nid++),x:el.x+20,y:el.y+20}));});
    $("btn-center").addEventListener("click",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;
        el.x=Math.round((_pw-el.w)/2);el.y=Math.round((_ph-el.h)/2);render();updateProps();});
    $("btn-chg-img").addEventListener("click",function(){
        var el=E.find(function(x){return x.id===sel;});if(!el)return;
        var inp=document.createElement("input");inp.type="file";inp.accept="image/*";
        inp.onchange=function(ev){var f=ev.target.files[0];if(!f)return;var r=new FileReader();r.onload=function(rv){el.img=rv.target.result;render();};r.readAsDataURL(f);};
        inp.click();
    });
    $("btn-rm-img").addEventListener("click",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;el.img="";render();});

    // ── Toolbar ──
    $("def-bdr").addEventListener("change",function(){_defBdr=this.value;});
    $("def-bdr-c").addEventListener("change",function(){_defBdrC=this.value;});
    $("def-fill-c").addEventListener("change",function(){_defFillC=this.value;});
    $("btn-new").addEventListener("click",function(){E=[];sel=null;render();updateProps();});
    $("btn-dup").addEventListener("click",function(){
        if(!sel){alert("Select an element first");return;}
        var el=E.find(function(x){return x.id===sel;});if(!el)return;
        add(Object.assign({},el,{id:"el"+(nid++),x:el.x+20,y:el.y+20}));
    });
    $("btn-grid").addEventListener("click",function(){
        if(!sel){alert("Select a stamp to duplicate in grid");return;}
        var el=E.find(function(x){return x.id===sel;});if(!el)return;
        var cols=parseInt(prompt("Number of columns:","3"))||3;
        var rows=parseInt(prompt("Number of rows:","3"))||3;
        var gapX=parseFloat(prompt("Horizontal gap (mm):","5"))||5;
        var gapY=parseFloat(prompt("Vertical gap (mm):","5"))||5;
        var startX=el.x,startY=el.y;
        for(var r=0;r<rows;r++){for(var c=0;c<cols;c++){
            if(r===0&&c===0)continue;
            add(Object.assign({},el,{id:"el"+(nid++),x:startX+c*(el.w+px(gapX)),y:startY+r*(el.h+px(gapY)),lbl:el.label?el.label+" ("+(r+1)+","+(c+1)+")":""}));
        }}
        render();updateProps();
    });
    $("btn-undo").addEventListener("click",function(){alert("Undo: coming soon");});
    $("btn-redo").addEventListener("click",function(){alert("Redo: coming soon");});
    $("btn-dsl").addEventListener("click",function(){$("dsl-panel").classList.toggle("open");if($("dsl-panel").classList.contains("open")){$("dsl-ta").value=buildDSL();}});
    $("btn-app-dsl").addEventListener("click",function(){parseDSL($("dsl-ta").value);render();});
    $("btn-cls-dsl").addEventListener("click",function(){$("dsl-panel").classList.remove("open");});
    $("btn-pdf").addEventListener("click",function(){
        var dsl=buildDSL();
        fetch("/export",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({dsl:dsl,format:"pdf"})})
        .then(function(r){return r.blob();}).then(function(b){var a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="album.pdf";a.click();})
        .catch(function(e){alert("Export failed: "+e);});
    });

    // ── Image Upload ──
    $("btn-upl").addEventListener("click",function(){$("upl-inp").click();});
    $("upl-inp").addEventListener("change",function(e){
        if(e.target.files.length===0)return;var f=e.target.files[0];
        var r=new FileReader();r.onload=function(ev){
            add({t:"image",s:"rectangle",x:50,y:50,w:80,h:60,lbl:f.name,img:ev.target.result,bdr:"solid",bdrC:"#999",bdrW:.5,fill:"#fff",fillA:100,font:"HN",fs:12});
        };r.readAsDataURL(f);
    });

    // ── Page Size ──
    $("pg-size").addEventListener("change",function(){
        var s={a4:[595,842],letter:[612,792],a3:[842,1191]};
        var v=s[this.value]||s.a4;_pw=v[0];_ph=v[1];
        pg.className="page "+this.value;render();
    });
    $("grid").addEventListener("change",function(){_sn=parseInt(this.value)||0;});

    // ── Collapsible Panels ──
    $("sb-toggle").addEventListener("click",function(){
        _collapsed.sb=!_collapsed.sb;
        $("sidebar").classList.toggle("collapsed",_collapsed.sb);
        this.textContent=_collapsed.sb?"▶":"◀";
    });
    $("rp-toggle").addEventListener("click",function(){
        _collapsed.rp=!_collapsed.rp;
        $("rp").classList.toggle("collapsed",_collapsed.rp);
        this.textContent=_collapsed.rp?"◀":"▶";
    });
    $("sb-handle").addEventListener("click",function(){$("sb-toggle").click();});
    $("rp-handle").addEventListener("click",function(){$("rp-toggle").click();});

    // ── Keyboard ──
    document.addEventListener("keydown",function(e){
        if(e.target.tagName==="INPUT"||e.target.tagName==="TEXTAREA"||e.target.tagName==="SELECT")return;
        if(e.key==="Delete"||e.key==="Backspace"){if(sel){E=E.filter(function(x){return x.id!==sel;});sel=null;render();updateProps();}}
        if(e.key==="Escape"){sel=null;render();updateProps();}
        if((e.ctrlKey||e.metaKey)&&e.key==="d"&&sel){e.preventDefault();var el=E.find(function(x){return x.id===sel;});if(el)add(Object.assign({},el,{id:"el"+(nid++),x:el.x+20,y:el.y+20}));}
    });

    // ── Font Population ──
    var pfnt=$("pfnt");
    if(pfnt){
        pfnt.innerHTML="";
        var groups=[{label:"System Fonts",fonts:SYSTEM_FONTS},{label:"Web Safe",fonts:["Arial","Helvetica","Times New Roman","Courier New","Georgia","Verdana","Trebuchet MS","Impact","Comic Sans MS"]}];
        groups.forEach(function(g){
            var og=document.createElement("optgroup");og.label=g.label;
            g.fonts.forEach(function(f){
                var o=document.createElement("option");o.value=f;o.textContent=f;og.appendChild(o);
            });
            pfnt.appendChild(og);
        });
        // Style options
        var styles=document.createElement("optgroup");styles.label="Styles";
        [{v:"normal",t:"Normal"},{v:"bold",t:"Bold"},{v:"italic",t:"Italic"},{v:"bolditalic",t:"Bold Italic"}].forEach(function(s){
            var o=document.createElement("option");o.value=s.v;o.textContent=s.t;styles.appendChild(o);
        });
        pfnt.appendChild(styles);
    }

    console.log("StampAlbum Pro: ready with "+SYSTEM_FONTS.length+" system fonts");
}

function add(p){
    var s={id:"el"+(nid++),t:p.t||"stamp",s:p.s||"rectangle",x:p.x||50,y:p.y||50,w:p.w||80,h:p.h||60,
        lbl:p.lbl||"",font:p.font||"HN",fs:p.fs||12,align:p.align||"left",
        bdr:p.bdr||"solid",bdrC:p.bdrC||"#666",bdrW:p.bdrW||1,
        fill:p.fill||"#fff",fillA:p.fillA||100,img:p.img||""};
    E.push(s);select(s.id);render();
}

function select(id){
    sel=id;render();
    var el=E.find(function(x){return x.id===id;});
    if(!el){$("rp-content").style.display="none";$("rp-none").style.display="block";return;}
    $("rp-content").style.display="block";$("rp-none").style.display="none";
    $("px").value=mm(el.x);$("py").value=mm(el.y);
    $("pw").value=mm(el.w);$("ph").value=mm(el.h);
    $("plbl").value=el.lbl||"";
    $("pbs").value=el.bdr||"solid";
    $("pbc").value=el.bdrC||"#666";
    $("pbw").value=el.bdrW||1;
    $("pfc").value=el.fill||"#fff";
    $("pfa").value=el.fillA||100;$("pfa-v").textContent=(el.fillA||100)+"%";
    $("pfnt").value=el.font||"HN";
    $("pfs").value=el.fs||12;
    var isImg=el.t==="image";
    $("img-sec").style.display=isImg?"block":"none";
    $("img-row").style.display=isImg?"flex":"none";
}

function updateProps(){
    var el=E.find(function(x){return x.id===sel;});if(!el)return;
    $("px").value=mm(el.x);$("py").value=mm(el.y);
    $("pw").value=mm(el.w);$("ph").value=mm(el.h);
}

function getShapePath(shape,w,h){
    var hw=w/2,hh=h/2;
    if(shape==="oval")return "M "+hw+" 0 A "+hw+" "+hh+" 0 1 0 "+hw+" "+h+" A "+hw+" "+hh+" 0 1 0 "+hw+" 0 Z";
    if(shape==="diamond")return "M "+hw+" 0 L "+w+" "+hh+" L "+hw+" "+h+" L 0 "+hh+" Z";
    if(shape==="triangle")return "M "+hw+" 0 L "+w+" "+h+" L 0 "+h+" Z";
    if(shape==="hexagon"){var x1=w*0.25,x2=w*0.75,y1=h*0.1,y2=h*0.5,y3=h*0.9;return "M "+x1+" 0 L "+x2+" 0 L "+w+" "+y2+" L "+x2+" "+h+" L "+x1+" "+h+" L 0 "+y2+" Z";}
    if(shape==="octagon"){var a=w*0.3,b=h*0.3;return "M "+a+" 0 L "+(w-a)+" 0 L "+w+" "+b+" L "+w+" "+(h-b)+" L "+(w-a)+" "+h+" L "+a+" "+h+" L 0 "+(h-b)+" L 0 "+b+" Z";}
    if(shape==="pentagon"){var cx=w/2;return "M "+cx+" 0 L "+w+" "+(h*0.38)+" L "+(w*0.82)+" "+h+" L "+(w*0.18)+" "+h+" L 0 "+(h*0.38)+" Z";}
    return "M 0 0 L "+w+" 0 L "+w+" "+h+" L 0 "+h+" Z";
}

function render(){
    var pg=$("page");
    pg.querySelectorAll(".cel").forEach(function(el){el.remove();});
    E.forEach(function(el){
        var d=document.createElement("div");
        d.className="cel shape-"+(el.s||"rectangle")+(el.id===sel?" selected":"");
        d.dataset.id=el.id;
        d.style.left=el.x+"px";d.style.top=el.y+"px";
        d.style.width=el.w+"px";d.style.height=el.h+"px";

        // SVG shape for proper borders
        if(el.s&&el.s!=="rectangle"&&el.s!=="text"&&el.s!=="freehand"){
            var svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
            svg.setAttribute("class","shape-svg");
            svg.setAttribute("viewBox","0 0 "+el.w+" "+el.h);
            svg.style.position="absolute";svg.style.top="0";svg.style.left="0";
            svg.style.width="100%";svg.style.height="100%";
            var path=document.createElementNS("http://www.w3.org/2000/svg","path");
            path.setAttribute("d",getShapePath(el.s,el.w,el.h));
            path.setAttribute("fill",el.fill||"#fff");
            path.setAttribute("stroke",el.bdrC||"#666");
            path.setAttribute("stroke-width",(el.bdrW||1)*2);
            if(el.bdr==="dashed")path.setAttribute("stroke-dasharray","4,2");
            if(el.bdr==="dotted")path.setAttribute("stroke-dasharray","1,2");
            if(el.bdr==="double"){path.setAttribute("stroke-width",1);
                var path2=path.cloneNode();path2.setAttribute("transform","translate(3,3) scale(0.95)");path2.setAttribute("fill","none");path2.setAttribute("stroke-width",1);
                svg.appendChild(path2);
            }
            svg.appendChild(path);
            d.appendChild(svg);
            d.style.border="none";
        } else {
            d.style.border=(el.bdrW||0)+"pt "+(el.bdr||"solid")+" "+(el.bdrC||"#666");
            d.style.backgroundColor=el.fill||"transparent";
        }
        if(el.fillA!==undefined&&el.fillA<100)d.style.opacity=el.fillA/100;

        if(el.img){var img=document.createElement("img");img.className="eimg";img.src=el.img;d.appendChild(img);}
        else if(el.lbl){var l=document.createElement("span");l.className="elbl";l.textContent=el.lbl;l.contentEditable="true";l.spellcheck=false;
            l.style.fontFamily=el.font||"Helvetica,Arial,sans-serif";
            l.style.fontSize=(el.fs||12)+"px";
            l.style.fontWeight=el.font==="HB"||el.font==="TB"?"bold":"normal";
            l.style.fontStyle=el.font==="TI"?"italic":"normal";
            l.addEventListener("blur",function(){el.lbl=this.textContent;});
            l.addEventListener("keydown",function(e){if(e.key==="Enter"){e.preventDefault();this.blur();}});
            d.appendChild(l);
        }
        if(el.t==="freehand"){d.style.border="1pt dashed #999";d.style.backgroundColor="rgba(200,200,200,0.1)";
            var fh=document.createElement("div");fh.style.cssText="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:10px;color:#999;text-align:center;";
            fh.innerHTML="✎ Free Shape<br><small>Draw custom shape</small>";d.appendChild(fh);}

        // Dimension label
        var dim=document.createElement("span");dim.className="dim";dim.textContent=mm(el.w)+"×"+mm(el.h)+"mm";d.appendChild(dim);

        // Resize handles
        ["nw","ne","sw","se","n","s","e","w"].forEach(function(h){
            var ha=document.createElement("div");ha.className="rh "+h;ha.dataset.h=h;d.appendChild(ha);
        });

        // Click to select (not on resize handles)
        d.addEventListener("mousedown",function(e){
            if(e.target.classList.contains("rh"))return;
            e.stopPropagation();
            select(el.id);
            _drg=true;_dragEl=el;_dragH="move";
            _ds={x:e.clientX,y:e.clientY,ox:el.x,oy:el.y,ow:el.w,oh:el.h};
        });

        pg.appendChild(d);
    });
}

function buildDSL(){
    var lines=["ALBUM_TITLE(\"My Album\")","ALBUM_PAGES_SIZE(210 297)","ALBUM_PAGES_MARGINS(15 15 15 15)","PAGE_START"];
    E.forEach(function(el){
        if(el.t==="image"){lines.push("STAMP_ADD_IMG("+el.x.toFixed(1)+" "+el.y.toFixed(1)+" "+el.w.toFixed(1)+" "+el.h.toFixed(1)+" \""+(el.img||"")+"\" \""+(el.lbl||"")+"\" \"\" \"\"\")");}
        else if(el.t==="text"){var cmd=el.align==="center"?"PAGE_TEXT_CENTRE":el.align==="right"?"PAGE_TEXT_RIGHT":"PAGE_TEXT";lines.push(cmd+"(\""+(el.font||"HN")+"\" "+(el.fs||12)+" \""+(el.lbl||"Text")+"\")");}
        else if(el.t==="freehand"){lines.push("STAMP_ADD_AT("+el.x.toFixed(1)+" "+el.y.toFixed(1)+" "+el.w.toFixed(1)+" "+el.h.toFixed(1)+" \""+(el.lbl||"")+"\" \"freehand\" \""+el.bdr+"\" \""+el.fill+"\")");}
        else{lines.push("STAMP_ADD_AT("+el.x.toFixed(1)+" "+el.y.toFixed(1)+" "+el.w.toFixed(1)+" "+el.h.toFixed(1)+" \""+(el.lbl||"")+"\" \""+el.s+"\" \""+el.bdr+"\" \""+el.fill+"\")");}
    });
    return lines.join("\n");
}

function parseDSL(dsl){
    E=[];var lines=dsl.split("\n");
    for(var i=0;i<lines.length;i++){
        var t=lines[i].trim();
        var m=t.match(/^(STAMP_ADD_AT|STAMP_ADD_IMG)\(\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"([^"]*)"\s+"([^"]*)"/);
        if(m){E.push({id:"el"+(nid++),t:m[1]==="STAMP_ADD_IMG"?"image":"stamp",s:m[7]||"rectangle",x:parseFloat(m[2]),y:parseFloat(m[3]),w:parseFloat(m[4]),h:parseFloat(m[5]),lbl:m[6]||"",bdr:"solid",bdrC:"#666",bdrW:1,fill:"#fff",fillA:100,img:m[1]==="STAMP_ADD_IMG"?m[6]:"",font:"HN",fs:12});continue;}
        var m2=t.match(/^(PAGE_TEXT|PAGE_TEXT_CENTRE|PAGE_TEXT_RIGHT)\(\s*"([^"]*)"\s+(\d+)\s+"([^"]*)"\)/);
        if(m2){E.push({id:"el"+(nid++),t:"text",s:"text",x:10,y:10,w:100,h:20,lbl:m[4]||"Text",font:m[2]||"HN",fs:parseFloat(m[3])||12,align:m2[1]==="PAGE_TEXT_CENTRE"?"center":m2[1]==="PAGE_TEXT_RIGHT"?"right":"left",bdr:"none",fill:"transparent",fillA:0});}
    }
}

if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);
else init();
})();
