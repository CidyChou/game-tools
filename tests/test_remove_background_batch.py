from __future__ import annotations

from io import BytesIO
import unittest
import zipfile

from PIL import Image

from web_app import build_remove_background_zip


def png_bytes(image: Image.Image) -> bytes:
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class RemoveBackgroundBatchTests(unittest.TestCase):
    def test_builds_zip_with_processed_pngs_and_unique_names(self) -> None:
        first = Image.new("RGBA", (3, 3), (255, 255, 255, 255))
        first.putpixel((1, 1), (20, 80, 160, 255))
        second = Image.new("RGBA", (2, 2), (255, 255, 255, 255))
        second.putpixel((0, 0), (180, 30, 40, 255))

        archive, metadata = build_remove_background_zip(
            [
                ("sprite.png", png_bytes(first)),
                ("sprite.png", png_bytes(second)),
            ],
            mode="edge",
            threshold=245,
            bg_color="",
            tolerance=12,
        )

        self.assertEqual(metadata["images_processed"], "2")
        self.assertEqual(metadata["pixels_removed"], "11")

        with zipfile.ZipFile(BytesIO(archive)) as zip_file:
            self.assertEqual(
                zip_file.namelist(),
                ["sprite-transparent.png", "sprite-transparent-2.png"],
            )
            first_output = Image.open(BytesIO(zip_file.read("sprite-transparent.png")))
            second_output = Image.open(BytesIO(zip_file.read("sprite-transparent-2.png")))

        self.assertEqual(first_output.getpixel((0, 0))[3], 0)
        self.assertEqual(first_output.getpixel((1, 1))[3], 255)
        self.assertEqual(second_output.getpixel((1, 1))[3], 0)
        self.assertEqual(second_output.getpixel((0, 0))[3], 255)


if __name__ == "__main__":
    unittest.main()
