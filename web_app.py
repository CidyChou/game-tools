from __future__ import annotations

from argparse import ArgumentTypeError
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from remove_bg import (
    IMAGE_EXTENSIONS,
    build_background_matcher,
    parse_color,
    remove_background_from_image,
)


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "web_static"

app = FastAPI(title="PNG Tools Web")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/remove-background")
async def remove_background(
    image: UploadFile = File(...),
    mode: str = Form("edge"),
    threshold: int = Form(245),
    bg_color: str = Form(""),
    tolerance: int = Form(12),
) -> Response:
    if mode not in {"edge", "all"}:
        raise HTTPException(status_code=400, detail="mode must be 'edge' or 'all'")
    if not 0 <= threshold <= 255:
        raise HTTPException(status_code=400, detail="threshold must be between 0 and 255")
    if not 0 <= tolerance <= 255:
        raise HTTPException(status_code=400, detail="tolerance must be between 0 and 255")

    suffix = Path(image.filename or "").suffix.lower()
    if suffix and suffix not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="unsupported image format")

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="empty image upload")

    try:
        source = Image.open(BytesIO(raw))
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="image could not be decoded") from exc

    try:
        parsed_bg_color = parse_color(bg_color) if bg_color.strip() else None
    except ArgumentTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    background_matcher, effective_threshold = build_background_matcher(
        source,
        threshold,
        parsed_bg_color,
        tolerance,
    )
    result, removed = remove_background_from_image(source, mode, background_matcher)
    output = BytesIO()
    result.save(output, format="PNG")

    return Response(
        content=output.getvalue(),
        media_type="image/png",
        headers={
            "Content-Disposition": 'attachment; filename="removed-background.png"',
            "X-Pixels-Removed": str(removed),
            "X-Effective-Threshold": str(effective_threshold),
        },
    )
