from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import web_app


def build_test_mp3() -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "tone.mp3"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=440:duration=1",
                "-ac",
                "2",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "192k",
                str(output),
            ],
            check=True,
        )
        return output.read_bytes()


def probe_ogg(raw: bytes) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "output.ogg"
        source.write_bytes(raw)
        completed = subprocess.run(
            [
                "ffprobe",
                "-hide_banner",
                "-loglevel",
                "error",
                "-show_entries",
                "format=format_name",
                "-show_entries",
                "stream=codec_name,channels",
                "-of",
                "default=nw=1",
                str(source),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    values: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        key, value = line.split("=", 1)
        values[key] = value
    return values


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"),
    "ffmpeg and ffprobe are required for audio conversion tests",
)
class ConvertAudioTests(unittest.TestCase):
    def test_converts_high_bitrate_mp3_to_smaller_vorbis_ogg(self) -> None:
        source = build_test_mp3()

        converted, metadata = web_app.convert_mp3_to_ogg_bytes(source, quality="small")

        probed = probe_ogg(converted)
        self.assertIn("ogg", probed["format_name"])
        self.assertEqual(probed["codec_name"], "vorbis")
        self.assertEqual(probed["channels"], "2")
        self.assertLess(len(converted), len(source))
        self.assertEqual(metadata["source_bytes"], str(len(source)))
        self.assertEqual(metadata["output_bytes"], str(len(converted)))
        self.assertEqual(metadata["audio_codec"], "vorbis")
        self.assertEqual(metadata["audio_quality"], "small")

    def test_rejects_empty_upload_and_invalid_quality(self) -> None:
        with self.assertRaises(ValueError):
            web_app.convert_mp3_to_ogg_bytes(b"", quality="small")

        with self.assertRaises(ValueError):
            web_app.convert_mp3_to_ogg_bytes(b"not really mp3", quality="tiny")

    def test_validate_audio_suffix_only_accepts_mp3(self) -> None:
        web_app.validate_audio_upload("effect.mp3", b"abc")

        with self.assertRaises(ValueError):
            web_app.validate_audio_upload("effect.wav", b"abc")

        with self.assertRaises(ValueError):
            web_app.validate_audio_upload("effect.mp3", b"")

    def test_missing_ffmpeg_returns_clear_error(self) -> None:
        with patch.object(web_app.shutil, "which", return_value=None):
            with self.assertRaises(ValueError) as context:
                web_app.convert_mp3_to_ogg_bytes(b"not empty", quality="small")

        self.assertIn("ffmpeg", str(context.exception))


if __name__ == "__main__":
    unittest.main()
