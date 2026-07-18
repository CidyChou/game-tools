from pathlib import Path
import unittest


BASE_DIR = Path(__file__).resolve().parents[1]


class AudioEditorUiTests(unittest.TestCase):
    def test_audio_tool_exposes_waveform_trim_controls(self) -> None:
        html = (BASE_DIR / "web_static" / "index.html").read_text()

        for element_id in (
            "audioEditor",
            "audioWaveformCanvas",
            "audioSelection",
            "audioStartHandle",
            "audioEndHandle",
            "audioStartInput",
            "audioEndInput",
            "playAudioSelectionButton",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'id="{element_id}"', html)

        self.assertIn(".wav", html)
        self.assertIn(".flac", html)
        self.assertIn(".m4a", html)

    def test_conversion_submits_selected_audio_range(self) -> None:
        script = (BASE_DIR / "web_static" / "app.js").read_text()

        self.assertIn('form.append("start_time"', script)
        self.assertIn('form.append("end_time"', script)


if __name__ == "__main__":
    unittest.main()
