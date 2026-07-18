from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APP_JS = ROOT / "web_static" / "app.js"
INDEX_HTML = ROOT / "web_static" / "index.html"


def _function_body(source: str, name: str) -> str:
    signature = f"function {name}"
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[brace + 1:index]
    raise AssertionError(f"Could not find end of {name}")


class SpriteExportTests(unittest.TestCase):
    def test_repaired_sprite_export_preserves_original_frame_pixels(self) -> None:
        source = APP_JS.read_text(encoding="utf-8")
        body = _function_body(source, "drawAdvancedAlignedFrame")

        self.assertNotIn("makeTransparentFrame", body)
        self.assertLess(body.index("fillAlignedFrameBackground"), body.index("targetContext.drawImage(frameCanvas, analysis.dx, analysis.dy)"))
        self.assertIn("targetContext.drawImage(frameCanvas, analysis.dx, analysis.dy)", body)

    def test_app_script_url_is_versioned_to_avoid_stale_export_logic(self) -> None:
        source = INDEX_HTML.read_text(encoding="utf-8")

        self.assertRegex(source, r'<script src="/static/app\.js\?v=[^"]+" defer></script>')

    def test_removed_background_result_can_be_imported_to_compression_tool(self) -> None:
        html = INDEX_HTML.read_text(encoding="utf-8")
        script = APP_JS.read_text(encoding="utf-8")

        self.assertIn('id="importRemovedToProcess"', html)
        self.assertIn("导入到压缩", html)
        self.assertIn('/static/app.js?v=20260716-audio-editor', html)
        self.assertIn('const importRemovedToProcess = $("importRemovedToProcess");', script)
        self.assertIn("function importRemovedResultToProcess()", script)
        self.assertIn("new File([blob]", script)
        self.assertIn('document.getElementById("tool-process").scrollIntoView', script)
        self.assertIn('importRemovedToProcess.addEventListener("click", importRemovedResultToProcess);', script)


if __name__ == "__main__":
    unittest.main()
