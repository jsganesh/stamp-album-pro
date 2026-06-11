import os
import tempfile
import shutil
import secrets
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel

from stamp_album.core.parser import AlbumParser, ParseError
from stamp_album.core.serializer import AlbumSerializer
from stamp_album.engines.pdf_generator import HTMLRenderer, PDFGenerator

app = FastAPI(title="StampAlbum Pro")
parser = AlbumParser()
serializer = AlbumSerializer()

# Security: CSRF token for session validation
_CSRF_TOKEN = secrets.token_urlsafe(32)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdnjs.cloudflare.com; "
        "style-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' https://cdnjs.cloudflare.com; "
        "connect-src 'self'; "
        "frame-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


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


def _handle_parse_error(e: Exception) -> None:
    """Convert parser errors to appropriate HTTP exceptions."""
    if isinstance(e, ParseError):
        raise HTTPException(status_code=400, detail=str(e))
    raise HTTPException(status_code=400, detail=f"Request error: {e}")


@app.post("/render", response_class=HTMLResponse)
async def render_preview(request: RenderRequest):
    try:
        album = parser.parse(request.dsl, request.source_path)
        renderer = HTMLRenderer(album, None)
        html = renderer.render()
        import re
        html = re.sub(
            r'src="([^\"/"][^"]*\.(?:png|jpg|jpeg|gif|bmp|tiff|tif|webp))"',
            r'src="/images/\1"',
            html,
        )
        return html
    except Exception as e:
        _handle_parse_error(e)


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
        _handle_parse_error(e)


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
        )
        return {"dsl": updated_dsl}
    except Exception as e:
        _handle_parse_error(e)


@app.post("/validate")
async def validate_album(request: RenderRequest):
    """Validate a DSL document and return warnings/errors."""
    try:
        album = parser.parse(request.dsl, request.source_path)
        warnings = parser.validate(album)
        stamp_count = sum(
            len(row.stamps) for page in album.pages for row in page.rows
        )
        return {
            "valid": True,
            "warnings": warnings,
            "title": album.title,
            "pages": len(album.pages),
            "stamps": stamp_count,
        }
    except ParseError as e:
        return {
            "valid": False,
            "error": str(e),
            "line_number": e.line_number,
            "warnings": [],
        }


class ExportRequest(BaseModel):
    dsl: str
    format: str = "pdf"  # pdf, png, svg, html
    source_path: Optional[str] = "untitled.slbum"
    dpi: int = 150


@app.post("/export")
async def export_album(request: ExportRequest):
    """Export album to PDF, PNG, SVG, or HTML gallery."""
    fmt = request.format.lower()
    if fmt not in ("pdf", "png", "svg", "html", "epub"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    try:
        album = parser.parse(request.dsl, request.source_path)
        generator = PDFGenerator()
        html_content = generator.get_html_preview(album)

        import re
        html_content = re.sub(
            r'src="([^\"/"][^"]*\.(?:png|jpg|jpeg|gif|bmp|tiff|tif|webp))"',
            r'src="/images/\1"',
            html_content,
        )

        if fmt == "pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                pdf_path = tmp.name
                generator.generate(album, pdf_path, base_url="http://localhost:8080")
            return FileResponse(pdf_path, media_type="application/pdf", filename="album.pdf")

        elif fmt == "png":
            from weasyprint import HTML as WPHTML
            doc = WPHTML(string=html_content, base_url="http://localhost:8080").render()
            if not doc.pages:
                raise HTTPException(status_code=400, detail="No pages to export")
            # Export first page as PNG
            png_bytes = doc.pages[0].write_png(resolution=request.dpi)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(png_bytes)
                tmp.flush()
                return FileResponse(tmp.name, media_type="image/png", filename="album.png")

        elif fmt == "svg":
            from weasyprint import HTML as WPHTML
            doc = WPHTML(string=html_content, base_url="http://localhost:8080").render()
            if not doc.pages:
                raise HTTPException(status_code=400, detail="No pages to export")
            svg_bytes = doc.pages[0].write_svg()
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
                tmp.write(svg_bytes)
                tmp.flush()
                return FileResponse(tmp.name, media_type="image/svg+xml", filename="album.svg")

        elif fmt == "html":
            gallery_html = _build_html_gallery(html_content, album)
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
                tmp.write(gallery_html)
                tmp.flush()
                return FileResponse(tmp.name, media_type="text/html", filename="album-gallery.html")

        elif fmt == "epub":
            epub_html = _build_html_gallery(html_content, album)
            with tempfile.NamedTemporaryFile(suffix=".epub", delete=False, mode="w", encoding="utf-8") as tmp:
                tmp.write(epub_html)
                tmp.flush()
                return FileResponse(tmp.name, media_type="application/epub+zip", filename="album.epub")

    except ParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")


def _build_html_gallery(html_content: str, album: "Album") -> str:
    """Build a self-contained HTML gallery from album HTML."""
    title = album.title or "Stamp Album"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Gallery</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
        h1 {{ text-align: center; color: #333; margin-bottom: 30px; }}
        .gallery {{ display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; }}
        .page {{ background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 4px; overflow: hidden; }}
        .page-label {{ text-align: center; padding: 8px; font-size: 12px; color: #666; background: #fafafa; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="gallery">
        {html_content}
    </div>
</body>
</html>"""


# ============================================================
# Stamp Collection API
# ============================================================

from stamp_album.collection import (
    load_collection, save_collection, add_stamp, update_stamp,
    delete_stamp, search_stamps, import_csv, get_collection_stats,
    COLLECTION_FILE,
)


class StampData(BaseModel):
    country: str = ""
    year: int = 0
    description: str = ""
    catalog_number: str = ""
    catalog_type: str = "SG"
    denomination: str = ""
    condition: str = ""
    purchase_price: float = 0.0
    image_path: str = ""
    notes: str = ""


class StampUpdate(BaseModel):
    country: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    catalog_number: Optional[str] = None
    catalog_type: Optional[str] = None
    denomination: Optional[str] = None
    condition: Optional[str] = None
    purchase_price: Optional[float] = None
    image_path: Optional[str] = None
    notes: Optional[str] = None


@app.get("/api/stamps")
async def list_stamps(
    query: str = "",
    country: str = "",
    year_from: int = 0,
    year_to: int = 0,
    catalog_type: str = "",
    condition: str = "",
    sort_by: str = "country",
    sort_order: str = "asc",
    page: int = 1,
    per_page: int = 20,
):
    results, total = search_stamps(
        query=query, country=country, year_from=year_from, year_to=year_to,
        catalog_type=catalog_type, condition=condition,
        sort_by=sort_by, sort_order=sort_order, page=page, per_page=per_page,
    )
    return {"stamps": results, "total": total, "page": page, "per_page": per_page}


@app.get("/api/stamps/stats")
async def collection_stats():
    return get_collection_stats()


@app.get("/api/stamps/{stamp_id}")
async def get_stamp(stamp_id: str):
    stamps = load_collection()
    for s in stamps:
        if s.get("id") == stamp_id:
            return s
    raise HTTPException(status_code=404, detail="Stamp not found")


@app.post("/api/stamps")
async def create_stamp(data: StampData):
    return add_stamp(data.model_dump())


@app.put("/api/stamps/{stamp_id}")
async def edit_stamp(stamp_id: str, data: StampUpdate):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    result = update_stamp(stamp_id, update_data)
    if not result:
        raise HTTPException(status_code=404, detail="Stamp not found")
    return result


@app.delete("/api/stamps/{stamp_id}")
async def remove_stamp(stamp_id: str):
    if delete_stamp(stamp_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Stamp not found")


@app.post("/api/stamps/import")
async def import_stamps_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")
    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content.decode("latin-1")
    count, errors = import_csv(csv_text)
    return {"imported": count, "errors": errors}


@app.get("/api/stamps/export/csv")
async def export_collection_csv():
    import csv, io
    stamps = load_collection()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "country", "year", "description", "catalog_number", "catalog_type",
        "denomination", "condition", "purchase_price", "image_path", "notes",
        "created_at", "updated_at",
    ])
    writer.writeheader()
    for s in stamps:
        writer.writerow(s)
    return PlainTextResponse(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=collection.csv"},
    )


class AutoLayoutRequest(BaseModel):
    dsl: str
    strategy: str = "row_first"
    page_idx: int = 0
    spacing: float = 6.0


@app.post("/api/auto-layout")
async def auto_layout(request: AutoLayoutRequest):
    """Auto-arrange stamps on a page using the specified layout strategy."""
    from stamp_album.engines.layout_engine import LayoutStrategy
    try:
        album = parser.parse(request.dsl)
    except ParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if request.page_idx >= len(album.pages):
        raise HTTPException(status_code=400, detail="Page index out of range")
    page = album.pages[request.page_idx]
    all_stamps = []
    for row in page.rows:
        for stamp in row.stamps:
            all_stamps.append(stamp)
    if not all_stamps:
        raise HTTPException(status_code=400, detail="No stamps on page")
    strategy_map = {"row_first": LayoutStrategy.ROW_FIRST, "column_first": LayoutStrategy.COLUMN_FIRST, "grid": LayoutStrategy.GRID, "packing": LayoutStrategy.PACKING, "balanced": LayoutStrategy.BALANCED}
    strategy = strategy_map.get(request.strategy, LayoutStrategy.ROW_FIRST)
    ps = album.page_setup
    content_width = ps.width - ps.margin_left - ps.margin_right
    from stamp_album.engines.layout_engine import LayoutEngine
    engine = LayoutEngine(ps)
    result = engine.auto_arrange_stamps(all_stamps, max_width=content_width, spacing=request.spacing, strategy=strategy)
    page.rows = result.rows
    page.content_flow = [("row", row) for row in result.rows]
    updated_dsl = serializer.to_dsl(album)
    return {"dsl": updated_dsl, "strategy": request.strategy, "rows_created": len(result.rows), "stamps_arranged": sum(len(r.stamps) for r in result.rows), "fits_on_page": result.fits_on_page}


# ============================================================
# Excel Import for Collection
# ============================================================

@app.post("/api/stamps/import-excel")
async def import_stamps_excel(file: UploadFile = File(...)):
    """Import stamps from an Excel (.xlsx) file."""
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Please upload an Excel file (.xlsx)")
    try:
        import openpyxl
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl not installed. Run: pip install openpyxl")
    content = await file.read()
    try:
        wb = openpyxl.load_workbook(filename=__import__("io").BytesIO(content))
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            raise HTTPException(status_code=400, detail="Excel file must have a header row and at least one data row")
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        for row in rows:
            writer.writerow(row)
        csv_text = output.getvalue()
        count, errors = import_csv(csv_text)
        return {"imported": count, "errors": errors}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel file: {e}")


# ============================================================
# WebSocket Real-Time Preview (P2-13)
# ============================================================

import json
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

active_connections: Dict[str, WebSocket] = {}


@app.websocket("/ws/preview")
async def websocket_preview(websocket: WebSocket):
    await websocket.accept()
    client_id = str(id(websocket))
    active_connections[client_id] = websocket
    try:
        await websocket.send_json({"type": "connected", "client_id": client_id})
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "render")
                if msg_type == "render":
                    dsl = msg.get("dsl", "")
                    if not dsl.strip():
                        await websocket.send_json({"type": "preview", "html": "", "status": "empty"})
                        continue
                    try:
                        album = parser.parse(dsl)
                        renderer = HTMLRenderer(album, None)
                        html = renderer.render()
                        warnings = parser.validate(album)
                        await websocket.send_json({"type": "preview", "html": html, "status": "ok", "warnings": warnings})
                    except ParseError as e:
                        await websocket.send_json({"type": "error", "message": str(e), "line": e.line_number})
                    except Exception as e:
                        await websocket.send_json({"type": "error", "message": "Render error: " + str(e)})
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "validate":
                    dsl = msg.get("dsl", "")
                    try:
                        album = parser.parse(dsl)
                        warnings = parser.validate(album)
                        await websocket.send_json({"type": "validation", "valid": True, "warnings": warnings})
                    except ParseError as e:
                        await websocket.send_json({"type": "validation", "valid": False, "error": str(e)})
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
            except Exception as e:
                await websocket.send_json({"type": "error", "message": "Server error: " + str(e)})
    except WebSocketDisconnect:
        active_connections.pop(client_id, None)
    except Exception:
        active_connections.pop(client_id, None)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
