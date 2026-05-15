#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from collections import deque
from itertools import chain
from pathlib import Path
from typing import Callable, Iterable

from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
Pixel = tuple[int, int, int, int]
PixelMatcher = Callable[[Pixel], bool]


def parse_color(value: str) -> tuple[int, int, int]:
    value = value.strip()
    if value.startswith("#"):
        value = value[1:]
        if len(value) != 6:
            raise argparse.ArgumentTypeError("颜色需要是 #RRGGBB 格式")
        try:
            return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
        except ValueError as exc:
            raise argparse.ArgumentTypeError("颜色需要是 #RRGGBB 格式") from exc

    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("颜色需要是 #RRGGBB 或 R,G,B 格式")

    try:
        rgb = tuple(int(part) for part in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("RGB 颜色值必须是整数") from exc

    if any(channel < 0 or channel > 255 for channel in rgb):
        raise argparse.ArgumentTypeError("RGB 颜色值范围必须是 0-255")
    return rgb  # type: ignore[return-value]


def is_whiteish(threshold: int) -> PixelMatcher:
    return lambda px: px[3] == 0 or (
        px[0] >= threshold and px[1] >= threshold and px[2] >= threshold
    )


def is_near_color(
    bg_color: tuple[int, int, int],
    tolerance: int,
) -> PixelMatcher:
    br, bg, bb = bg_color

    def match(px: Pixel) -> bool:
        r, g, b, a = px
        if a == 0:
            return True
        return max(abs(r - br), abs(g - bg), abs(b - bb)) <= tolerance

    return match


def iter_border_pixels(img: Image.Image) -> Iterable[Pixel]:
    pixels = img.load()
    width, height = img.size

    for x in range(width):
        yield pixels[x, 0]
        if height > 1:
            yield pixels[x, height - 1]

    for y in range(1, max(1, height - 1)):
        yield pixels[0, y]
        if width > 1:
            yield pixels[width - 1, y]


def iter_transparency_frontier_pixels(img: Image.Image) -> Iterable[Pixel]:
    pixels = img.load()
    width, height = img.size

    for y in range(height):
        for x in range(width):
            px = pixels[x, y]
            if px[3] == 0:
                continue

            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < width and 0 <= ny < height and pixels[nx, ny][3] == 0:
                    yield px
                    break


def percentile(sorted_values: list[int], fraction: float) -> int:
    if not sorted_values:
        raise ValueError("percentile requires at least one value")
    index = round((len(sorted_values) - 1) * fraction)
    return sorted_values[index]


def infer_white_threshold(img: Image.Image, threshold: int) -> int:
    """Relax the white threshold when background-adjacent pixels are off-white."""
    rgba = img.convert("RGBA")
    min_candidate = max(0, threshold - 35)
    candidate_min_channels = sorted(
        min(r, g, b)
        for r, g, b, a in chain(
            iter_border_pixels(rgba),
            iter_transparency_frontier_pixels(rgba),
        )
        if a > 0 and min(r, g, b) >= min_candidate
    )
    if not candidate_min_channels:
        return threshold

    edge_floor = percentile(candidate_min_channels, 0.05)
    if edge_floor >= threshold:
        return threshold

    return max(0, edge_floor - 1)


def build_background_matcher(
    img: Image.Image,
    threshold: int,
    bg_color: tuple[int, int, int] | None = None,
    tolerance: int = 12,
) -> tuple[PixelMatcher, int]:
    if bg_color is not None:
        return is_near_color(bg_color, tolerance), threshold

    effective_threshold = infer_white_threshold(img, threshold)
    return is_whiteish(effective_threshold), effective_threshold


def iter_image_files(input_path: Path) -> Iterable[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() in IMAGE_EXTENSIONS:
            yield input_path
        return

    for path in sorted(input_path.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def build_output_path(input_file: Path, input_root: Path, output_path: Path) -> Path:
    if input_root.is_file():
        if output_path.suffix.lower() == ".png":
            return output_path
        return output_path / f"{input_file.stem}.png"

    return output_path / f"{input_file.stem}.png"


def remove_matching_pixels_everywhere(
    img: Image.Image,
    matches_background: PixelMatcher,
) -> int:
    pixels = img.load()
    width, height = img.size
    removed = 0

    for y in range(height):
        for x in range(width):
            if matches_background(pixels[x, y]):
                r, g, b, a = pixels[x, y]
                if a != 0:
                    pixels[x, y] = (r, g, b, 0)
                    removed += 1

    return removed


def remove_edge_connected_background(
    img: Image.Image,
    matches_background: PixelMatcher,
) -> int:
    pixels = img.load()
    width, height = img.size
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    def enqueue_if_background(x: int, y: int) -> None:
        point = (x, y)
        if point not in visited and matches_background(pixels[x, y]):
            visited.add(point)
            queue.append(point)

    for x in range(width):
        enqueue_if_background(x, 0)
        enqueue_if_background(x, height - 1)
    for y in range(height):
        enqueue_if_background(0, y)
        enqueue_if_background(width - 1, y)

    removed = 0
    while queue:
        x, y = queue.popleft()
        r, g, b, a = pixels[x, y]
        if a != 0:
            pixels[x, y] = (r, g, b, 0)
            removed += 1

        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height:
                enqueue_if_background(nx, ny)

    return removed


def process_image(
    input_file: Path,
    output_file: Path,
    mode: str,
    threshold: int,
    bg_color: tuple[int, int, int] | None,
    tolerance: int,
) -> tuple[int, int]:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(input_file).convert("RGBA")
    matches_background, effective_threshold = build_background_matcher(
        img,
        threshold,
        bg_color,
        tolerance,
    )
    result, removed = remove_background_from_image(img, mode, matches_background)
    result.save(output_file)
    return removed, effective_threshold


def remove_background_from_image(
    img: Image.Image,
    mode: str,
    matches_background: PixelMatcher,
) -> tuple[Image.Image, int]:
    if mode not in {"edge", "all"}:
        raise ValueError("mode must be 'edge' or 'all'")

    img = img.convert("RGBA")
    if mode == "all":
        removed = remove_matching_pixels_everywhere(img, matches_background)
    else:
        removed = remove_edge_connected_background(img, matches_background)

    return img, removed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把图片背景抠成透明背景，支持单张图片或整个目录批处理。",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="input",
        type=Path,
        help="输入图片或输入目录，默认 input",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="output",
        type=Path,
        help="输出图片或输出目录，默认 output",
    )
    parser.add_argument(
        "--mode",
        choices=("edge", "all"),
        default="edge",
        help="edge 只抠除和图片边缘连通的背景；all 抠除全图匹配背景色的像素。默认 edge",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=245,
        help="白色背景阈值，越低抠除越多。默认 245",
    )
    parser.add_argument(
        "--bg-color",
        type=parse_color,
        help="指定背景色，例如 #ffffff 或 255,255,255。不填则按白色阈值判断",
    )
    parser.add_argument(
        "--tolerance",
        type=int,
        default=12,
        help="指定 --bg-color 后允许的颜色误差。默认 12",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.input.exists():
        raise SystemExit(f"输入路径不存在: {args.input}")
    if args.threshold < 0 or args.threshold > 255:
        raise SystemExit("--threshold 必须在 0-255 之间")
    if args.tolerance < 0 or args.tolerance > 255:
        raise SystemExit("--tolerance 必须在 0-255 之间")

    image_files = list(iter_image_files(args.input))
    if not image_files:
        raise SystemExit("没有找到可处理的图片文件")

    os.makedirs(args.output if args.input.is_dir() else args.output.parent, exist_ok=True)

    for input_file in image_files:
        output_file = build_output_path(input_file, args.input, args.output)
        removed, effective_threshold = process_image(
            input_file,
            output_file,
            args.mode,
            args.threshold,
            args.bg_color,
            args.tolerance,
        )
        suffix = (
            f", effective threshold {effective_threshold}"
            if args.bg_color is None and effective_threshold != args.threshold
            else ""
        )
        print(f"{input_file} -> {output_file} ({removed} pixels removed{suffix})")

    print("Done!")


if __name__ == "__main__":
    main()
