from __future__ import annotations

from io import BytesIO
import unittest

from PIL import Image

from web_app import process_image_bytes


def png_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class ProcessImageTests(unittest.TestCase):
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
