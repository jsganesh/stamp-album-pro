"use strict";
(function(){
var E=[],sel=null,nid=1,_sc=2.5,_sn=5,_pw=595,_ph=842,_init=false;
var _drg=false,_dragEl=null,_dragH=null,_ds={};
var _defBdr="solid",_defBdrC="#666",_defFillC="#fff";

function $(id){return document.getElementById(id);}
function mm(px){return Math.round(px/_sc*10)/10;}

function init(){
    if(_init)return;_init=true;
    var pg=$("page");if(!pg)return;

    // Palette drag
    document.querySelectorAll(".p-item[draggable]").forEach(function(it){
        it.addEventListener("dragstart",function(e){
            e.dataTransfer.setData("text/plain",JSON.stringify({
                t:it.dataset.t,s:it.dataset.s||"rectangle",st:it.dataset.st||"",
                w:parseFloat(it.dataset.w)||80,h:parseFloat(it.dataset.h)||60,
                font:it.dataset.font||"HN",fs:parseFloat(it.dataset.fs)||12
            }));
            e.dataTransfer.effectAllowed="copy";
        });
    });

    // Page drop
    pg.addEventListener("dragover",function(e){e.preventDefault();pg.classList.add("drag-over");});
    pg.addEventListener("dragleave",function(){pg.classList.remove("drag-over");});
    pg.addEventListener("drop",function(e){
        e.preventDefault();pg.classList.remove("drag-over");
        var d;try{d=JSON.parse(e.dataTransfer.getData("text/plain"));}catch(_){return;}
        var r=pg.getBoundingClientRect();
        var x=Math.max(0,Math.min(Math.round((e.clientX-r.left)/_sn)*_sn,_pw-40));
        var y=Math.max(0,Math.min(Math.round((e.clientY-r.top)/_sn)*_sn,_ph-30));
        add({t:d.t||"stamp",s:d.s||"rectangle",x:x,y:y,w:d.w||80,h:d.h||60,
            lbl:d.t==="text"?"Text":"",font:d.font||"HN",fs:d.fs||12,
            bdr:_defBdr,bdrC:_defBdrC,bdrW:1,fill:_defFillC,fillA:100,img:""});
    });

    // Mouse on canvas
    pg.addEventListener("mousedown",function(e){
        var el=e.target.closest(".cel");
        if(!el){sel=null;render();return;}
        var obj=E.find(function(x){return x.id===el.dataset.id;});if(!obj)return;
        _dragH=e.target.classList.contains("rh")?e.target.dataset.h:"move";
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
        render();
        updateProps();
    });

    document.addEventListener("mouseup",function(){_drg=false;_dragEl=null;_dragH=null;});

    // Props panel
    ["px","py","pw","ph"].forEach(function(id){
        $(id).addEventListener("change",function(){
            var el=E.find(function(x){return x.id===sel;});if(!el)return;
            el[id.replace("p","")]=parseFloat(this.value)||0;render();
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
    $("btn-chg-img").addEventListener("click",function(){
        var el=E.find(function(x){return x.id===sel;});if(!el)return;
        var inp=document.createElement("input");inp.type="file";inp.accept="image/*";
        inp.onchange=function(ev){var f=ev.target.files[0];if(!f)return;var r=new FileReader();r.onload=function(rv){el.img=rv.target.result;render();};r.readAsDataURL(f);};
        inp.click();
    });
    $("btn-rm-img").addEventListener("click",function(){var el=E.find(function(x){return x.id===sel;});if(!el)return;el.img="";render();});

    // Default border/fill from toolbar
    $("def-bdr").addEventListener("change",function(){_defBdr=this.value;});
    $("def-bdr-c").addEventListener("change",function(){_defBdrC=this.value;});
    $("def-fill-c").addEventListener("change",function(){_defFillC=this.value;});

    // Keyboard
    document.addEventListener("keydown",function(e){
        if(e.target.tagName==="INPUT"||e.target.tagName==="TEXTAREA"||e.target.tagName==="SELECT")return;
        if(e.key==="Delete"||e.key==="Backspace"){if(sel){E=E.filter(function(x){return x.id!==sel;});sel=null;render();updateProps();}}
        if(e.key==="Escape"){sel=null;render();updateProps();}
    });

    // Toolbar
    $("btn-new").addEventListener("click",function(){E=[];sel=null;render();updateProps();});
    $("btn-dsl").addEventListener("click",function(){$("dsl-panel").classList.toggle("open");if($("dsl-panel").classList.contains("open")){$("dsl-ta").value=buildDSL();}});
    $("btn-app-dsl").addEventListener("click",function(){parseDSL($("dsl-ta").value);render();});
    $("btn-cls-dsl").addEventListener("click",function(){$("dsl-panel").classList.remove("open");});
    $("btn-pdf").addEventListener("click",function(){
        var dsl=buildDSL();
        fetch("/export",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({dsl:dsl,format:"pdf"})})
        .then(function(r){return r.blob();}).then(function(b){var a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="album.pdf";a.click();})
        .catch(function(e){alert("Export failed: "+e);});
    });

    // Image upload
    $("btn-upl").addEventListener("click",function(){$("upl-inp").click();});
    $("upl-inp").addEventListener("change",function(e){
        if(e.target.files.length===0)return;var f=e.target.files[0];
        var r=new FileReader();r.onload=function(ev){
            add({t:"image",s:"rectangle",x:50,y:50,w:80,h:60,lbl:f.name,img:ev.target.result,bdr:"solid",bdrC:"#999",bdrW:.5,fill:"#fff",fillA:100,font:"HN",fs:12});
        };r.readAsDataURL(f);
    });

    // Page size
    $("pg-size").addEventListener("change",function(){
        var s={a4:[595,842],letter:[612,792],a3:[842,1191]};
        var v=s[this.value]||s.a4;_pw=v[0];_ph=v[1];
        pg.className="page "+this.value;render();
    });
    $("grid").addEventListener("change",function(){_sn=parseInt(this.value)||0;});

    console.log("StampAlbum Pro: ready");
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

function render(){
    var pg=$("page");
    pg.querySelectorAll(".cel").forEach(function(el){el.remove();});
    E.forEach(function(el){
        var d=document.createElement("div");
        d.className="cel shape-"+(el.s||"rectangle")+(el.id===sel?" selected":"");
        d.dataset.id=el.id;
        d.style.left=el.x+"px";d.style.top=el.y+"px";
        d.style.width=el.w+"px";d.style.height=el.h+"px";
        d.style.border=(el.bdrW||0)+"pt "+(el.bdr||"solid")+" "+(el.bdrC||"#666");
        d.style.backgroundColor=el.fill||"transparent";
        if(el.fillA!==undefined&&el.fillA<100)d.style.opacity=el.fillA/100;
        if(el.img){var img=document.createElement("img");img.className="eimg";img.src=el.img;d.appendChild(img);}
        else if(el.lbl){var l=document.createElement("span");l.className="elbl";l.textContent=el.lbl;l.style.fontFamily=el.font==="HN"?"Helvetica,Arial,sans-serif":el.font==="HB"?"Helvetica,Arial,sans-serif":el.font==="TN"?"Times,serif":el.font==="TB"?"Times,serif":"Courier,monospace";l.style.fontWeight=el.font==="HB"||el.font==="TB"?"bold":"normal";l.style.fontSize=(el.fs||12)+"px";d.appendChild(l);}
        // Dimension label
        var dim=document.createElement("span");dim.className="dim";dim.textContent=mm(el.w)+"×"+mm(el.h)+"mm";d.appendChild(dim);
        // Resize handles
        ["nw","ne","sw","se","n","s","e","w"].forEach(function(h){
            var ha=document.createElement("div");ha.className="rh "+h;ha.dataset.h=h;d.appendChild(ha);
        });
        pg.appendChild(d);
    });
}

function buildDSL(){
    var lines=["ALBUM_TITLE(\"My Album\")","ALBUM_PAGES_SIZE(210 297)","ALBUM_PAGES_MARGINS(15 15 15 15)","PAGE_START"];
    E.forEach(function(el){
        if(el.t==="image"){lines.push("STAMP_ADD_IMG("+el.x.toFixed(1)+" "+el.y.toFixed(1)+" "+el.w.toFixed(1)+" "+el.h.toFixed(1)+" \""+(el.img||"")+"\" \""+(el.label||"")+"\" \"\" \"\"\")");}
        else if(el.t==="text"){var cmd=el.align==="center"?"PAGE_TEXT_CENTRE":el.align==="right"?"PAGE_TEXT_RIGHT":"PAGE_TEXT";lines.push(cmd+"(\""+(el.font||"HN")+"\" "+(el.fs||12)+" \""+(el.lbl||"Text")+"\")");}
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
