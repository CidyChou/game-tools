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


def _open_uploaded_image(raw: bytes) -> Image.Image:
    if not raw:
        raise ValueError("empty image upload")

    try:
        image = Image.open(BytesIO(raw))
        image.load()
    except UnidentifiedImageError as exc:
        raise ValueError("image could not be decoded") from exc

    return image.convert("RGBA")


def _resize_dimensions(
    source_width: int,
    source_height: int,
    target_width: int,
    target_height: int,
    keep_aspect_ratio: bool,
) -> tuple[int, int]:
    if target_width <= 0 or target_height <= 0:
        raise ValueError("target width and height are required")

    if keep_aspect_ratio:
        return target_width, target_height

    return target_width, target_height


def process_image_bytes(
    raw: bytes,
    *,
    resize_enabled: bool,
    target_width: int,
    target_height: int,
    keep_aspect_ratio: bool,
    png_mode: str,
    compress_enabled: bool = True,
    palette_colors: int = 256,
) -> tuple[bytes, dict[str, str]]:
    if png_mode not in {"lossless", "palette"}:
        raise ValueError("png_mode must be 'lossless' or 'palette'")
    if palette_colors not in {64, 128, 256}:
        raise ValueError("palette_colors must be 64, 128, or 256")

    source = _open_uploaded_image(raw)
    source_width, source_height = source.size
    result = source

    if resize_enabled:
        output_size = _resize_dimensions(
            source_width,
            source_height,
            target_width,
            target_height,
            keep_aspect_ratio,
        )
        result = source.resize(output_size, Image.Resampling.LANCZOS)

    output = BytesIO()
    if compress_enabled and png_mode == "palette":
        quantized = result.quantize(
            colors=palette_colors,
            method=Image.Quantize.FASTOCTREE,
            dither=Image.Dither.NONE,
        )
        quantized.save(output, format="PNG", optimize=True, compress_level=9)
    else:
        result.save(output, format="PNG", optimize=True, compress_level=9)

    processed = output.getvalue()
    output_width, output_height = result.size
    return processed, {
        "source_width": str(source_width),
        "source_height": str(source_height),
        "output_width": str(output_width),
        "output_height": str(output_height),
        "source_bytes": str(len(raw)),
        "output_bytes": str(len(processed)),
        "palette_colors": str(palette_colors if compress_enabled and png_mode == "palette" else 0),
    }


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


@app.post("/api/process-image")
async def process_image(
    image: UploadFile = File(...),
    compress_enabled: bool = Form(True),
    resize_enabled: bool = Form(False),
    target_width: int = Form(0),
    target_height: int = Form(0),
    keep_aspect_ratio: bool = Form(True),
    png_mode: str = Form("palette"),
    palette_colors: int = Form(256),
) -> Response:
    suffix = Path(image.filename or "").suffix.lower()
    if suffix and suffix not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="unsupported image format")

    raw = await image.read()
    try:
        result, metadata = process_image_bytes(
            raw,
            compress_enabled=compress_enabled,
            resize_enabled=resize_enabled,
            target_width=target_width,
            target_height=target_height,
            keep_aspect_ratio=keep_aspect_ratio,
            png_mode=png_mode,
            palette_colors=palette_colors,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=result,
        media_type="image/png",
        headers={
            "Content-Disposition": 'attachment; filename="processed-image.png"',
            "X-Source-Width": metadata["source_width"],
            "X-Source-Height": metadata["source_height"],
            "X-Output-Width": metadata["output_width"],
            "X-Output-Height": metadata["output_height"],
            "X-Source-Bytes": metadata["source_bytes"],
            "X-Output-Bytes": metadata["output_bytes"],
            "X-Palette-Colors": metadata["palette_colors"],
        },
    )
