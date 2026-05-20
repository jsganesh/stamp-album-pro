import tempfile
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.engines.pdf_generator import HTMLRenderer, PDFGenerator

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
        renderer = HTMLRenderer(album, None)
        return renderer.render()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/parse")
async def parse_album(request: RenderRequest):
    try:
        album = parser.parse(request.dsl, request.source_path)
        return {
            "title": album.title,
            "pages": len(album.pages),
            "fonts": len(album.fonts),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/visual-update")
async def visual_update(request: VisualUpdateRequest):
    try:
        updated_dsl = serializer.update_stamp_position(
            request.dsl,
            request.page_idx,
            request.row_idx,
            request.stamp_idx,
            request.width,
            request.height,
            request.source_path if hasattr(request, "source_path") else None,
        )
        return {"dsl": updated_dsl}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/export")
async def export_pdf(request: RenderRequest):
    try:
        album = parser.parse(request.dsl, request.source_path)
        generator = PDFGenerator()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name
            generator.generate(album, pdf_path)
        return FileResponse(pdf_path, filename="album.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

