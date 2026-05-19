from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from PIL import Image

from compress_images import build_output_path, compress_image, iter_input_files


class CompressImagesTests(unittest.TestCase):
    def test_compress_image_writes_256_color_optimized_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.png"
            target = Path(tmp) / "target.png"
            Image.effect_noise((64, 64), 80).convert("RGBA").save(source)

            result = compress_image(source, target)
            compressed = Image.open(target)

            self.assertEqual(compressed.format, "PNG")
            self.assertEqual(compressed.mode, "P")
            self.assertLessEqual(len(compressed.getpalette() or []), 256 * 3)
            self.assertEqual(result.input_path, source)
            self.assertEqual(result.output_path, target)
            self.assertGreater(result.input_bytes, 0)
            self.assertGreater(result.output_bytes, 0)

    def test_directory_without_output_only_compresses_png_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            png = root / "image.png"
            jpg = root / "image.jpg"
            Image.new("RGBA", (4, 4), (255, 0, 0, 255)).save(png)
            Image.new("RGB", (4, 4), (0, 255, 0)).save(jpg)

            files = list(iter_input_files(root, in_place=True))

            self.assertEqual(files, [png])
            self.assertEqual(build_output_path(png, root, None), png)

    def test_non_png_single_file_requires_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.jpg"
            Image.new("RGB", (4, 4), (0, 0, 255)).save(source)

            with self.assertRaises(ValueError):
                list(iter_input_files(source, in_place=True))


if __name__ == "__main__":
    unittest.main()
