#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
PNG_EXTENSION = ".png"


@dataclass(frozen=True)
class CompressionResult:
    input_path: Path
    output_path: Path
    input_bytes: int
    output_bytes: int


def iter_input_files(input_path: Path, *, in_place: bool) -> Iterable[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() not in IMAGE_EXTENSIONS:
            return
        if in_place and input_path.suffix.lower() != PNG_EXTENSION:
            raise ValueError("原地压缩只支持 PNG；非 PNG 图片请指定输出路径")
        yield input_path
        return

    for path in sorted(input_path.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in IMAGE_EXTENSIONS:
            continue
        if in_place and suffix != PNG_EXTENSION:
            continue
        yield path


def build_output_path(
    input_file: Path,
    input_root: Path,
    output_path: Path | None,
) -> Path:
    if output_path is None:
        if input_file.suffix.lower() != PNG_EXTENSION:
            raise ValueError("原地压缩只支持 PNG；非 PNG 图片请指定输出路径")
        return input_file

    if input_root.is_file():
        if output_path.suffix.lower() == PNG_EXTENSION:
            return output_path
        return output_path / f"{input_file.stem}.png"

    if output_path.suffix:
        raise ValueError("批量压缩目录时，输出路径必须是目录")

    relative = input_file.relative_to(input_root)
    return output_path / relative.with_suffix(".png")


def quantize_to_256_color_png(image: Image.Image) -> Image.Image:
    return image.convert("RGBA").quantize(
        colors=256,
        method=Image.Quantize.FASTOCTREE,
        dither=Image.Dither.NONE,
    )


def compress_image(input_file: Path, output_file: Path) -> CompressionResult:
    input_bytes = input_file.stat().st_size
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(input_file) as image:
        compressed = quantize_to_256_color_png(image)

    if input_file.resolve() == output_file.resolve():
        temp_output = output_file.with_name(f".{output_file.name}.tmp-compress.png")
        try:
            compressed.save(temp_output, format="PNG", optimize=True, compress_level=9)
            temp_output.replace(output_file)
        finally:
            if temp_output.exists():
                temp_output.unlink()
    else:
        compressed.save(output_file, format="PNG", optimize=True, compress_level=9)

    return CompressionResult(
        input_path=input_file,
        output_path=output_file,
        input_bytes=input_bytes,
        output_bytes=output_file.stat().st_size,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="使用最多 256 色调色板有损量化压缩 PNG 图片。",
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
        type=Path,
        help="输出 PNG 文件或输出目录；不填时原地压缩 PNG",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"输入路径不存在: {args.input}")

    in_place = args.output is None
    try:
        image_files = list(iter_input_files(args.input, in_place=in_place))
        if not image_files:
            raise SystemExit("没有找到可压缩的图片文件")

        for input_file in image_files:
            output_file = build_output_path(input_file, args.input, args.output)
            result = compress_image(input_file, output_file)
            saved = result.input_bytes - result.output_bytes
            print(
                f"{result.input_path} -> {result.output_path} "
                f"({result.input_bytes} -> {result.output_bytes} bytes, saved {saved})"
            )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    print("Done!")


if __name__ == "__main__":
    main()
