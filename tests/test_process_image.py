from __future__ import annotations

from io import BytesIO
from pathlib import Path
import unittest

from PIL import Image

from web_app import process_image_bytes


BASE_DIR = Path(__file__).resolve().parents[1]


def png_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class ProcessImageTests(unittest.TestCase):
    def test_expand_controls_are_exposed_and_submitted(self) -> None:
        html = (BASE_DIR / "web_static" / "index.html").read_text()
        script = (BASE_DIR / "web_static" / "app.js").read_text()

        self.assertIn('id="processExpandInput"', html)
        self.assertIn("扩图（透明画布）", html)
        self.assertIn('form.append("expand_enabled"', script)
        self.assertIn("drawTransparencyGrid", script)

    def test_resizes_uploaded_png_to_target_dimensions(self) -> None:
        image = Image.new("RGBA", (12, 8), (40, 120, 220, 255))

        result, metadata = process_image_bytes(
            png_bytes(image),
            resize_enabled=True,
            target_width=6,
            target_height=4,
            keep_aspect_ratio=True,
            png_mode="lossless",
        )

        resized = Image.open(BytesIO(result))
        self.assertEqual(resized.size, (6, 4))
        self.assertEqual(metadata["source_width"], "12")
        self.assertEqual(metadata["source_height"], "8")
        self.assertEqual(metadata["output_width"], "6")
        self.assertEqual(metadata["output_height"], "4")

    def test_crops_uploaded_png_to_requested_box(self) -> None:
        image = Image.new("RGBA", (8, 6), (0, 0, 0, 0))
        image.putpixel((2, 1), (255, 0, 0, 255))
        image.putpixel((5, 4), (0, 0, 255, 255))

        result, metadata = process_image_bytes(
            png_bytes(image),
            crop_enabled=True,
            crop_x=2,
            crop_y=1,
            crop_width=4,
            crop_height=4,
            resize_enabled=False,
            target_width=0,
            target_height=0,
            keep_aspect_ratio=True,
            png_mode="lossless",
        )

        output = Image.open(BytesIO(result)).convert("RGBA")
        self.assertEqual(output.size, (4, 4))
        self.assertEqual(metadata["crop_x"], "2")
        self.assertEqual(metadata["crop_y"], "1")
        self.assertEqual(metadata["crop_width"], "4")
        self.assertEqual(metadata["crop_height"], "4")
        self.assertEqual(output.getpixel((0, 0)), (255, 0, 0, 255))
        self.assertEqual(output.getpixel((3, 3)), (0, 0, 255, 255))

    def test_resizes_cropped_region_instead_of_original_image(self) -> None:
        image = Image.new("RGBA", (8, 8), (0, 0, 255, 255))
        for y in range(2, 6):
            for x in range(2, 6):
                image.putpixel((x, y), (255, 0, 0, 255))

        result, metadata = process_image_bytes(
            png_bytes(image),
            crop_enabled=True,
            crop_x=2,
            crop_y=2,
            crop_width=4,
            crop_height=4,
            resize_enabled=True,
            target_width=2,
            target_height=2,
            keep_aspect_ratio=True,
            png_mode="lossless",
        )

        output = Image.open(BytesIO(result)).convert("RGBA")
        self.assertEqual(output.size, (2, 2))
        self.assertEqual(metadata["output_width"], "2")
        self.assertEqual(metadata["output_height"], "2")
        pixels = output.load()
        for y in range(output.height):
            for x in range(output.width):
                pixel = pixels[x, y]
                self.assertGreater(pixel[0], 240)
                self.assertLess(pixel[2], 15)

    def test_expands_crop_box_with_transparent_pixels_outside_source(self) -> None:
        image = Image.new("RGBA", (2, 2), (20, 80, 160, 255))

        result, metadata = process_image_bytes(
            png_bytes(image),
            crop_enabled=True,
            expand_enabled=True,
            crop_x=-1,
            crop_y=-2,
            crop_width=4,
            crop_height=5,
            resize_enabled=False,
            target_width=0,
            target_height=0,
            keep_aspect_ratio=True,
            png_mode="palette",
        )

        output = Image.open(BytesIO(result)).convert("RGBA")
        self.assertEqual(output.size, (4, 5))
        self.assertEqual(output.getpixel((0, 0)), (0, 0, 0, 0))
        self.assertEqual(output.getpixel((1, 2)), (20, 80, 160, 255))
        self.assertEqual(output.getpixel((2, 3)), (20, 80, 160, 255))
        self.assertEqual(metadata["crop_x"], "-1")
        self.assertEqual(metadata["crop_y"], "-2")
        self.assertEqual(metadata["expanded"], "1")

    def test_expansion_requires_crop_box_to_overlap_source(self) -> None:
        image = Image.new("RGBA", (5, 5), (0, 0, 0, 255))

        with self.assertRaises(ValueError):
            process_image_bytes(
                png_bytes(image),
                crop_enabled=True,
                expand_enabled=True,
                crop_x=6,
                crop_y=0,
                crop_width=3,
                crop_height=3,
                resize_enabled=False,
                target_width=0,
                target_height=0,
                keep_aspect_ratio=True,
                png_mode="lossless",
            )

    def test_lossless_png_mode_preserves_dimensions_and_png_format(self) -> None:
        image = Image.new("RGBA", (5, 3), (255, 0, 0, 128))

        result, metadata = process_image_bytes(
            png_bytes(image),
            resize_enabled=False,
            target_width=0,
            target_height=0,
            keep_aspect_ratio=True,
            png_mode="lossless",
        )

        output = Image.open(BytesIO(result))
        self.assertEqual(output.format, "PNG")
        self.assertEqual(output.size, (5, 3))
        self.assertEqual(metadata["output_width"], "5")
        self.assertEqual(metadata["output_height"], "3")

    def test_palette_mode_keeps_dimensions_and_reduces_png_size(self) -> None:
        image = Image.effect_noise((64, 64), 80).convert("RGBA")
        raw = png_bytes(image)

        result, metadata = process_image_bytes(
            raw,
            resize_enabled=False,
            target_width=0,
            target_height=0,
            keep_aspect_ratio=True,
            png_mode="palette",
        )

        output = Image.open(BytesIO(result))
        self.assertEqual(output.size, (64, 64))
        self.assertLess(len(result), len(raw))
        self.assertEqual(metadata["source_bytes"], str(len(raw)))
        self.assertEqual(metadata["output_bytes"], str(len(result)))

    def test_palette_compression_strength_controls_color_count(self) -> None:
        image = Image.effect_noise((96, 96), 90).convert("RGBA")
        raw = png_bytes(image)

        detailed, detailed_metadata = process_image_bytes(
            raw,
            resize_enabled=False,
            target_width=0,
            target_height=0,
            keep_aspect_ratio=True,
            png_mode="palette",
            palette_colors=256,
        )
        strong, strong_metadata = process_image_bytes(
            raw,
            resize_enabled=False,
            target_width=0,
            target_height=0,
            keep_aspect_ratio=True,
            png_mode="palette",
            palette_colors=64,
        )

        self.assertLess(len(strong), len(detailed))
        self.assertEqual(detailed_metadata["palette_colors"], "256")
        self.assertEqual(strong_metadata["palette_colors"], "64")

        with self.assertRaises(ValueError):
            process_image_bytes(
                raw,
                resize_enabled=False,
                target_width=0,
                target_height=0,
                keep_aspect_ratio=True,
                png_mode="palette",
                palette_colors=32,
            )

    def test_invalid_dimensions_empty_upload_and_non_image_are_rejected(self) -> None:
        image = Image.new("RGBA", (5, 5), (0, 0, 0, 255))

        with self.assertRaises(ValueError):
            process_image_bytes(
                png_bytes(image),
                crop_enabled=True,
                crop_x=3,
                crop_y=0,
                crop_width=3,
                crop_height=3,
                resize_enabled=True,
                target_width=0,
                target_height=10,
                keep_aspect_ratio=True,
                png_mode="lossless",
            )

        with self.assertRaises(ValueError):
            process_image_bytes(
                b"",
                resize_enabled=False,
                target_width=0,
                target_height=0,
                keep_aspect_ratio=True,
                png_mode="lossless",
            )

        with self.assertRaises(ValueError):
            process_image_bytes(
                b"not an image",
                resize_enabled=False,
                target_width=0,
                target_height=0,
                keep_aspect_ratio=True,
                png_mode="lossless",
            )


if __name__ == "__main__":
    unittest.main()
