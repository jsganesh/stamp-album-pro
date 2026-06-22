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
from stamp_album.templates import TEMPLATES

app = FastAPI(title="StampAlbum Pro")
parser = AlbumParser()
serializer = AlbumSerializer()

# Security: CSRF token for session validation
_CSRF_TOKEN = secrets.token_urlsafe(32)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    # Allow frame-src 'self' for the preview iframe. The preview iframe
    # receives a synthetic HTML document via document.write() — it doesn't
    # load a URL, so CSP frame-src and X-Frame-Options cover it.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # Prevent caching so browser always gets latest app files
    response.headers["Cache-Control"] = "no-store, max-age=0"
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
    from starlette.background import BackgroundTask

    fmt = request.format.lower()
    if fmt not in ("pdf", "png", "svg", "html", "epub"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    def _cleanup(path: str):
        """Delete a temp file after the response has been sent."""
        try:
            os.unlink(path)
        except OSError:
            pass

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
            return FileResponse(
                pdf_path, media_type="application/pdf", filename="album.pdf",
                background=BackgroundTask(_cleanup, pdf_path),
            )

        elif fmt == "png":
            import fitz
            pdf_bytes = generator.generate_to_bytes(album)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if doc.page_count == 0:
                doc.close()
                raise HTTPException(status_code=400, detail="No pages to export")
            zoom = max(0.5, request.dpi / 72.0)
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            png_bytes = pix.tobytes("png")
            doc.close()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(png_bytes)
                png_path = tmp.name
            return FileResponse(
                png_path, media_type="image/png", filename="album.png",
                background=BackgroundTask(_cleanup, png_path),
            )

        elif fmt == "svg":
            import fitz
            pdf_bytes = generator.generate_to_bytes(album)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if doc.page_count == 0:
                doc.close()
                raise HTTPException(status_code=400, detail="No pages to export")
            svg_text = doc[0].get_svg_image()
            doc.close()
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w", encoding="utf-8") as tmp:
                tmp.write(svg_text)
                svg_path = tmp.name
            return FileResponse(
                svg_path, media_type="image/svg+xml", filename="album.svg",
                background=BackgroundTask(_cleanup, svg_path),
            )

        elif fmt == "html":
            gallery_html = _build_html_gallery(html_content, album)
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
                tmp.write(gallery_html)
                html_path = tmp.name
            return FileResponse(
                html_path, media_type="text/html", filename="album-gallery.html",
                background=BackgroundTask(_cleanup, html_path),
            )

        elif fmt == "epub":
            epub_html = _build_html_gallery(html_content, album)
            with tempfile.NamedTemporaryFile(suffix=".epub", delete=False, mode="w", encoding="utf-8") as tmp:
                tmp.write(epub_html)
                epub_path = tmp.name
            return FileResponse(
                epub_path, media_type="application/epub+zip", filename="album.epub",
                background=BackgroundTask(_cleanup, epub_path),
            )

    except ParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
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
# Direct Canvas State → Render/Export (bypasses DSL parser)
# ============================================================

class CanvasElementState(BaseModel):
    id: str = ""
    t: str = "stamp"
    s: str = "rectangle"
    x: float = 0
    y: float = 0
    w: float = 80
    h: float = 60
    lbl: str = ""
    font: str = "HN"
    fs: float = 12
    align: str = "left"
    bdr: str = "solid"
    bdrC: str = "#666"
    bdrW: float = 1
    fill: str = "#fff"
    fillA: int = 100
    img: str = ""


class CanvasStateRequest(BaseModel):
    elements: list[CanvasElementState]
    pages: list[list[CanvasElementState]] = []
    page_width_px: float = 595
    page_height_px: float = 842
    scale: float = 2.5
    source_path: str = "album.slbum"
    format: str = "html"
    title: str = "My Album"
    author: str = ""


def _canvas_state_to_album(req: CanvasStateRequest) -> "Album":
    """Convert canvas state directly to Album model, bypassing DSL text."""
    from stamp_album.core.models import (
        Album, Page, PageSetup, Stamp, StampShape, Color,
    )

    SCALE = req.scale
    w_mm = req.page_width_px / SCALE
    h_mm = req.page_height_px / SCALE

    shape_map = {
        "rectangle": StampShape.RECTANGLE,
        "oval": StampShape.OVAL,
        "diamond": StampShape.DIAMOND,
        "triangle": StampShape.TRIANGLE,
        "hexagon": StampShape.HEXAGON,
        "octagon": StampShape.OCTAGON,
        "pentagon": StampShape.PENTAGON,
    }
    def build_page(elements: list[CanvasElementState]) -> Page:
        page = Page()
        for el in elements:
            is_text = el.t == "text"
            stamp = Stamp(
                abs_x=el.x / SCALE,
                abs_y=el.y / SCALE,
                width=max(1.0, el.w / SCALE),
                height=max(1.0, el.h / SCALE),
                description=el.lbl or "",
                shape=shape_map.get(el.s, StampShape.RECTANGLE),
                image_path=el.img if el.img else None,
                is_text_element=is_text,
                font_id=el.font or "HN",
                font_size=el.fs or 12.0,
            )
            page.absolute_stamps.append(stamp)
        return page

    pages = [build_page(req.elements)]
    for pg in req.pages:
        pages.append(build_page(pg))

    album = Album(
        title=req.title or "My Album",
        author=req.author or "",
        source_path=req.source_path or "album.slbum",
        page_setup=PageSetup(width=w_mm, height=h_mm),
        pages=pages,
    )
    album.color_stamp_border = Color(r=0.5, g=0.5, b=0.5)
    album.color_stamp_background = Color(r=1.0, g=1.0, b=1.0)
    return album


@app.post("/render-from-state", response_class=HTMLResponse)
async def render_from_state(req: CanvasStateRequest):
    """Render canvas state directly to HTML preview (bypasses DSL)."""
    try:
        album = _canvas_state_to_album(req)
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
        raise HTTPException(status_code=500, detail=f"Render error: {e}")


@app.post("/export-from-state")
async def export_from_state(req: CanvasStateRequest):
    """Export canvas state directly to PDF, PNG, SVG, or HTML (bypasses DSL)."""
    from starlette.background import BackgroundTask

    fmt = req.format.lower()
    if fmt not in ("pdf", "png", "svg", "html"):
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    def _cleanup(path: str):
        try:
            os.unlink(path)
        except OSError:
            pass

    try:
        album = _canvas_state_to_album(req)
        generator = PDFGenerator()

        if fmt == "pdf":
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                pdf_path = tmp.name
                generator.generate(album, pdf_path, base_url="http://localhost:8080")
            filename = req.source_path.replace(".slbum", ".pdf").replace(".txt", ".pdf") or "album.pdf"
            return FileResponse(
                pdf_path, media_type="application/pdf", filename=filename,
                background=BackgroundTask(_cleanup, pdf_path),
            )
        elif fmt == "png":
            import fitz
            import tempfile
            pdf_bytes = generator.generate_to_bytes(album)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if doc.page_count == 0:
                doc.close()
                raise HTTPException(status_code=400, detail="No pages to export")
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
            png_bytes = pix.tobytes("png")
            doc.close()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(png_bytes)
                png_path = tmp.name
            filename = req.source_path.replace(".slbum", ".png").replace(".txt", ".png") or "album.png"
            return FileResponse(
                png_path, media_type="image/png", filename=filename,
                background=BackgroundTask(_cleanup, png_path),
            )
        elif fmt == "svg":
            import fitz
            import tempfile
            pdf_bytes = generator.generate_to_bytes(album)
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            if doc.page_count == 0:
                doc.close()
                raise HTTPException(status_code=400, detail="No pages to export")
            svg_text = doc[0].get_svg_image()
            doc.close()
            with tempfile.NamedTemporaryFile(suffix=".svg", delete=False, mode="w", encoding="utf-8") as tmp:
                tmp.write(svg_text)
                svg_path = tmp.name
            filename = req.source_path.replace(".slbum", ".svg").replace(".txt", ".svg") or "album.svg"
            return FileResponse(
                svg_path, media_type="image/svg+xml", filename=filename,
                background=BackgroundTask(_cleanup, svg_path),
            )
        else:  # html
            html = generator.get_html_preview(album)
            import re
            html = re.sub(
                r'src="([^\/"][^"]*\.(?:png|jpg|jpeg|gif|bmp|tiff|tif|webp))"',
                r'src="/images/\1"',
                html,
            )
            return HTMLResponse(html)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")


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



# ============================================================
# Version History API (P2-15)
# ============================================================

from stamp_album.version_history import (
    save_version, get_versions, get_version, delete_version,
)


class VersionSaveRequest(BaseModel):
    filename: str
    dsl: str
    comment: str = ""


@app.post("/api/version/save")
async def api_save_version(request: VersionSaveRequest):
    if not request.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    if not request.dsl.strip():
        raise HTTPException(status_code=400, detail="DSL content required")
    version = save_version(request.filename, request.dsl, request.comment)
    return version


@app.get("/api/version/list/{filename}")
async def api_get_versions(filename: str):
    versions = get_versions(filename)
    return {"versions": versions, "count": len(versions)}


@app.get("/api/version/get/{filename}/{version_id}")
async def api_get_version(filename: str, version_id: str):
    dsl = get_version(filename, version_id)
    if dsl is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"dsl": dsl, "filename": filename, "version_id": version_id}


@app.delete("/api/version/delete/{filename}/{version_id}")
async def api_delete_version(filename: str, version_id: str):
    if delete_version(filename, version_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Version not found")


# ============================================================
# Multi-User & Cloud Sync API (P2-14 + P2-16)
# ============================================================

from stamp_album.cloud_sync import (
    create_user, authenticate_user, get_user, list_users,
    create_session, validate_session, destroy_session,
    share_file, get_shared_files, get_my_shares, revoke_share,
)


class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class ShareRequest(BaseModel):
    filename: str
    shared_with: str
    permission: str = "read"


def _get_current_user(request: Request) -> Optional[str]:
    token = request.cookies.get("session_token")
    if token:
        return validate_session(token)
    return None


@app.post("/api/auth/register")
async def api_register(request: RegisterRequest):
    try:
        user = create_user(request.username, request.password, request.display_name)
        return {"status": "created", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login")
async def api_login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_session(request.username)
    return {"status": "logged_in", "user": user, "token": token}


@app.post("/api/auth/logout")
async def api_logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        destroy_session(token)
    return {"status": "logged_out"}


@app.get("/api/auth/me")
async def api_current_user(request: Request):
    username = _get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": get_user(username)}


@app.get("/api/users")
async def api_list_users(request: Request):
    if not _get_current_user(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"users": list_users()}


@app.post("/api/share")
async def api_share_file(request: ShareRequest, http_request: Request):
    username = _get_current_user(http_request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    share = share_file(username, request.filename, request.shared_with, request.permission)
    return {"status": "shared", "share": share}


@app.get("/api/share/received")
async def api_shared_with_me(request: Request):
    username = _get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"shares": get_shared_files(username)}


@app.get("/api/share/sent")
async def api_my_shares(request: Request):
    username = _get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"shares": get_my_shares(username)}


@app.delete("/api/share/{share_id}")
async def api_revoke_share(share_id: str, request: Request):
    username = _get_current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if revoke_share(share_id, username):
        return {"status": "revoked"}
    raise HTTPException(status_code=404, detail="Share not found")


# ── Templates API ──
@app.get("/api/templates")
async def list_templates():
    """List all available album templates."""
    return [
        {"id": t["id"], "name": t["name"], "description": t["description"], "category": t.get("category", "General")}
        for t in TEMPLATES
    ]


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """Get a specific template by ID."""
    for t in TEMPLATES:
        if t["id"] == template_id:
            return {"id": t["id"], "name": t["name"], "description": t["description"], "dsl": t["content"]}
    raise HTTPException(status_code=404, detail="Template not found")


# Catch-all: serve static JS/CSS/image files from the web directory.
# Must be LAST so that /files, /images, /render, /export, /api, etc. match first.
@app.get("/{static_file:path}")
async def serve_static(static_file: str):
    if not static_file or "/" in static_file:
        raise HTTPException(status_code=404)
    fp = WEB_DIR / static_file
    if fp.exists() and fp.is_file():
        mt = None
        if static_file.endswith(".css"):
            mt = "text/css"
        elif static_file.endswith(".js"):
            mt = "application/javascript"
        elif static_file.endswith(".html"):
            mt = "text/html"
        elif static_file.endswith((".png", ".jpg", ".jpeg", ".gif", ".svg")):
            mt = "image/png"
        return FileResponse(fp, media_type=mt)
    raise HTTPException(status_code=404)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
