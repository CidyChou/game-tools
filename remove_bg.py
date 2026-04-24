#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from collections import deque
from pathlib import Path
from typing import Callable, Iterable

from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


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


def is_whiteish(threshold: int) -> Callable[[tuple[int, int, int, int]], bool]:
    return lambda px: px[0] >= threshold and px[1] >= threshold and px[2] >= threshold


def is_near_color(
    bg_color: tuple[int, int, int],
    tolerance: int,
) -> Callable[[tuple[int, int, int, int]], bool]:
    br, bg, bb = bg_color

    def match(px: tuple[int, int, int, int]) -> bool:
        r, g, b, _ = px
        return max(abs(r - br), abs(g - bg), abs(b - bb)) <= tolerance

    return match


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
    matches_background: Callable[[tuple[int, int, int, int]], bool],
) -> int:
    pixels = img.load()
    width, height = img.size
    removed = 0

    for y in range(height):
        for x in range(width):
            if matches_background(pixels[x, y]):
                r, g, b, _ = pixels[x, y]
                pixels[x, y] = (r, g, b, 0)
                removed += 1

    return removed


def remove_edge_connected_background(
    img: Image.Image,
    matches_background: Callable[[tuple[int, int, int, int]], bool],
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
        r, g, b, _ = pixels[x, y]
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
    matches_background: Callable[[tuple[int, int, int, int]], bool],
) -> int:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(input_file).convert("RGBA")

    if mode == "all":
        removed = remove_matching_pixels_everywhere(img, matches_background)
    else:
        removed = remove_edge_connected_background(img, matches_background)

    img.save(output_file)
    return removed


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

    matches_background = (
        is_near_color(args.bg_color, args.tolerance)
        if args.bg_color
        else is_whiteish(args.threshold)
    )

    image_files = list(iter_image_files(args.input))
    if not image_files:
        raise SystemExit("没有找到可处理的图片文件")

    os.makedirs(args.output if args.input.is_dir() else args.output.parent, exist_ok=True)

    for input_file in image_files:
        output_file = build_output_path(input_file, args.input, args.output)
        removed = process_image(input_file, output_file, args.mode, matches_background)
        print(f"{input_file} -> {output_file} ({removed} pixels removed)")

    print("Done!")


if __name__ == "__main__":
    main()
