import unittest

from PIL import Image

from remove_bg import build_background_matcher, remove_background_from_image


class RemoveBackgroundTests(unittest.TestCase):
    def test_adaptive_threshold_removes_off_white_edge_background(self) -> None:
        img = Image.new("RGBA", (5, 5), (243, 243, 243, 255))
        img.putpixel((2, 2), (40, 120, 40, 255))

        matcher, effective_threshold = build_background_matcher(img, threshold=245)
        result, removed = remove_background_from_image(img, "edge", matcher)

        self.assertEqual(effective_threshold, 242)
        self.assertEqual(removed, 24)
        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertEqual(result.getpixel((2, 2))[3], 255)

    def test_existing_transparency_is_traversable_but_not_counted(self) -> None:
        img = Image.new("RGBA", (5, 1), (20, 20, 20, 255))
        img.putpixel((0, 0), (255, 255, 255, 0))
        img.putpixel((1, 0), (255, 255, 255, 0))
        img.putpixel((2, 0), (243, 243, 243, 255))

        matcher, effective_threshold = build_background_matcher(img, threshold=245)
        result, removed = remove_background_from_image(img, "edge", matcher)

        self.assertEqual(effective_threshold, 242)
        self.assertEqual(removed, 1)
        self.assertEqual(result.getpixel((2, 0))[3], 0)
        self.assertEqual(result.getpixel((3, 0))[3], 255)


if __name__ == "__main__":
    unittest.main()
