import os
import tempfile
import shutil
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel

from stamp_album.core.parser import AlbumParser
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.engines.pdf_generator import HTMLRenderer, PDFGenerator

app = FastAPI(title="StampAlbum Pro")
parser = AlbumParser()
serializer = AlbumSerializer()

# Directory for user files
FILES_DIR = Path(os.environ.get("STAMP_ALBUM_FILES", Path.home() / "StampAlbum"))
FILES_DIR.mkdir(parents=True, exist_ok=True)

# Directory for uploaded images
IMAGES_DIR = FILES_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Serve web UI
WEB_DIR = Path(__file__).parent / "web"


@app.get("/")
async def root():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/style.css")
async def serve_css():
    return FileResponse(WEB_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
async def serve_js():
    return FileResponse(WEB_DIR / "app.js", media_type="application/javascript")


# File management endpoints
class FileContent(BaseModel):
    content: str


@app.get("/files")
async def list_files():
    files = sorted(
        [f.name for f in FILES_DIR.iterdir() if f.suffix in (".slbum", ".txt")]
    )
    return files


@app.get("/files/{filename}")
async def get_file(filename: str):
    filepath = FILES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return PlainTextResponse(filepath.read_text(encoding="utf-8"))


@app.post("/files/{filename}")
async def save_file(filename: str, request: FileContent):
    filepath = FILES_DIR / filename
    filepath.write_text(request.content, encoding="utf-8")
    return {"status": "saved", "path": str(filepath)}


@app.delete("/files/{filename}")
async def delete_file(filename: str):
    filepath = FILES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    filepath.unlink()
    return {"status": "deleted"}


# Image management endpoints
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"}


@app.get("/images")
async def list_images():
    images = sorted(
        [f.name for f in IMAGES_DIR.iterdir() if f.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS]
    )
    return images


@app.get("/images/{filename}")
async def get_image(filename: str):
    filepath = IMAGES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath)


@app.post("/images")
async def upload_image(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported image format: {ext}")

    filepath = IMAGES_DIR / file.filename
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"status": "uploaded", "filename": file.filename, "path": str(filepath)}


@app.delete("/images/{filename}")
async def delete_image(filename: str):
    filepath = IMAGES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    filepath.unlink()
    return {"status": "deleted"}


# API endpoints
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
        html = renderer.render()
        # Replace image paths with API endpoints (only for local filenames)
        import re
        html = re.sub(r'src="([^"/][^"]*\.(?:png|jpg|jpeg|gif|bmp|tiff|tif|webp))"', r'src="/images/\1"', html)
        return html
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
            # Use localhost:8080 as base URL for image resolution
            generator.generate(album, pdf_path, base_url="http://localhost:8080")
        return FileResponse(
            pdf_path, media_type="application/pdf", filename="album.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
