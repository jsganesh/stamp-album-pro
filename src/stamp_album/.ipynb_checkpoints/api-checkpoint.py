from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import tempfile
from pathlib import Path
import dataclasses

from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.engines.pdf_generator import PDFGenerator, HTMLRenderer

app = FastAPI(title="StampAlbum Pro API")
parser = AlbumParser()
serializer = AlbumSerializer()

class RenderRequest(BaseModel):
    dsl: str
    source_path: Optional[str] = "untitled.slbum"

class VisualUpdateRequest(BaseModel):
    dsl: str
    page_idx: int
    row_idx: int
    stamp_idx: int
    width: float
    height: float

@app.post("/render", response_class=HTMLResponse)
async def render_preview(request: RenderRequest):
    try:
        album = parser.parse(request.dsl, request.source_path)
        renderer = HTMLRenderer(album)
        return renderer.render()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/parse")
async def parse_album(request: RenderRequest):
    try:
        album = parser.parse(request.dsl, request.source_path)
        return {
            "title": album.title,
            "pages": [dataclasses.asdict(p) for p in album.pages]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/visual-update")
async def visual_update(request: VisualUpdateRequest):
    try:
        updated_dsl = serializer.update_stamp_position(
            request.dsl, request.page_idx, request.row_idx, request.stamp_idx, request.width, request.height
        )
        return {"dsl": updated_dsl}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/export")
async def export_pdf(request: RenderRequest):
    try:
        album = parser.parse(request.dsl, request.source_path)
        generator = PDFGenerator(album)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name
            generator.generate(pdf_path)
        return FileResponse(pdf_path, filename="album.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if name == "main":
    uvicorn.run(app, host="0.0.0.0", port=8000)
