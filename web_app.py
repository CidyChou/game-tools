from __future__ import annotations

from argparse import ArgumentTypeError
from collections.abc import Sequence
from io import BytesIO
from pathlib import Path
import re
import zipfile

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
FILENAME_SAFE_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")

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


def _crop_box(
    source_width: int,
    source_height: int,
    crop_x: int,
    crop_y: int,
    crop_width: int,
    crop_height: int,
) -> tuple[int, int, int, int]:
    if crop_width <= 0 or crop_height <= 0:
        raise ValueError("crop width and height are required")
    if crop_x < 0 or crop_y < 0:
        raise ValueError("crop x and y must be greater than or equal to 0")
    if crop_x + crop_width > source_width or crop_y + crop_height > source_height:
        raise ValueError("crop box must stay inside the image")

    return crop_x, crop_y, crop_x + crop_width, crop_y + crop_height


def process_image_bytes(
    raw: bytes,
    *,
    crop_enabled: bool = False,
    crop_x: int = 0,
    crop_y: int = 0,
    crop_width: int = 0,
    crop_height: int = 0,
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
    applied_crop = (0, 0, source_width, source_height)

    if crop_enabled:
        applied_crop = _crop_box(
            source_width,
            source_height,
            crop_x,
            crop_y,
            crop_width,
            crop_height,
        )
        result = source.crop(applied_crop)

    if resize_enabled:
        output_size = _resize_dimensions(
            result.size[0],
            result.size[1],
            target_width,
            target_height,
            keep_aspect_ratio,
        )
        result = result.resize(output_size, Image.Resampling.LANCZOS)

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
        "crop_x": str(applied_crop[0]),
        "crop_y": str(applied_crop[1]),
        "crop_width": str(applied_crop[2] - applied_crop[0]),
        "crop_height": str(applied_crop[3] - applied_crop[1]),
        "source_bytes": str(len(raw)),
        "output_bytes": str(len(processed)),
        "palette_colors": str(palette_colors if compress_enabled and png_mode == "palette" else 0),
    }


def _validate_remove_options(mode: str, threshold: int, tolerance: int) -> None:
    if mode not in {"edge", "all"}:
        raise ValueError("mode must be 'edge' or 'all'")
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be between 0 and 255")
    if not 0 <= tolerance <= 255:
        raise ValueError("tolerance must be between 0 and 255")


def _validate_image_suffix(filename: str | None) -> None:
    suffix = Path(filename or "").suffix.lower()
    if suffix and suffix not in IMAGE_EXTENSIONS:
        raise ValueError("unsupported image format")


def _zip_output_name(filename: str | None, index: int, used_names: set[str]) -> str:
    stem = Path(filename or "").stem or f"image-{index}"
    safe_stem = FILENAME_SAFE_PATTERN.sub("_", stem).strip("._-") or f"image-{index}"
    base_name = f"{safe_stem}-transparent"
    output_name = f"{base_name}.png"
    suffix = 2
    while output_name in used_names:
        output_name = f"{base_name}-{suffix}.png"
        suffix += 1
    used_names.add(output_name)
    return output_name


def remove_background_bytes(
    raw: bytes,
    *,
    mode: str,
    threshold: int,
    bg_color: str,
    tolerance: int,
) -> tuple[bytes, dict[str, str]]:
    _validate_remove_options(mode, threshold, tolerance)
    source = _open_uploaded_image(raw)

    try:
        parsed_bg_color = parse_color(bg_color) if bg_color.strip() else None
    except ArgumentTypeError as exc:
        raise ValueError(str(exc)) from exc

    background_matcher, effective_threshold = build_background_matcher(
        source,
        threshold,
        parsed_bg_color,
        tolerance,
    )
    result, removed = remove_background_from_image(source, mode, background_matcher)
    output = BytesIO()
    result.save(output, format="PNG")
    return output.getvalue(), {
        "pixels_removed": str(removed),
        "effective_threshold": str(effective_threshold),
    }


def build_remove_background_zip(
    uploads: Sequence[tuple[str | None, bytes]],
    *,
    mode: str,
    threshold: int,
    bg_color: str,
    tolerance: int,
) -> tuple[bytes, dict[str, str]]:
    _validate_remove_options(mode, threshold, tolerance)
    if not uploads:
        raise ValueError("at least one image is required")

    archive = BytesIO()
    used_names: set[str] = set()
    total_removed = 0

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for index, (filename, raw) in enumerate(uploads, start=1):
            _validate_image_suffix(filename)
            processed, metadata = remove_background_bytes(
                raw,
                mode=mode,
                threshold=threshold,
                bg_color=bg_color,
                tolerance=tolerance,
            )
            total_removed += int(metadata["pixels_removed"])
            zip_file.writestr(_zip_output_name(filename, index, used_names), processed)

    return archive.getvalue(), {
        "images_processed": str(len(uploads)),
        "pixels_removed": str(total_removed),
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
    try:
        _validate_image_suffix(image.filename)
        result, metadata = remove_background_bytes(
            await image.read(),
            mode=mode,
            threshold=threshold,
            bg_color=bg_color,
            tolerance=tolerance,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=result,
        media_type="image/png",
        headers={
            "Content-Disposition": 'attachment; filename="removed-background.png"',
            "X-Pixels-Removed": metadata["pixels_removed"],
            "X-Effective-Threshold": metadata["effective_threshold"],
        },
    )


@app.post("/api/remove-background/batch")
async def remove_background_batch(
    images: list[UploadFile] = File(...),
    mode: str = Form("edge"),
    threshold: int = Form(245),
    bg_color: str = Form(""),
    tolerance: int = Form(12),
) -> Response:
    try:
        uploads = [(image.filename, await image.read()) for image in images]
        archive, metadata = build_remove_background_zip(
            uploads,
            mode=mode,
            threshold=threshold,
            bg_color=bg_color,
            tolerance=tolerance,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=archive,
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="removed-background-batch.zip"',
            "X-Images-Processed": metadata["images_processed"],
            "X-Pixels-Removed": metadata["pixels_removed"],
        },
    )


@app.post("/api/process-image")
async def process_image(
    image: UploadFile = File(...),
    compress_enabled: bool = Form(True),
    crop_enabled: bool = Form(False),
    crop_x: int = Form(0),
    crop_y: int = Form(0),
    crop_width: int = Form(0),
    crop_height: int = Form(0),
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
            crop_enabled=crop_enabled,
            crop_x=crop_x,
            crop_y=crop_y,
            crop_width=crop_width,
            crop_height=crop_height,
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
            "X-Crop-X": metadata["crop_x"],
            "X-Crop-Y": metadata["crop_y"],
            "X-Crop-Width": metadata["crop_width"],
            "X-Crop-Height": metadata["crop_height"],
            "X-Source-Bytes": metadata["source_bytes"],
            "X-Output-Bytes": metadata["output_bytes"],
            "X-Palette-Colors": metadata["palette_colors"],
        },
    )
