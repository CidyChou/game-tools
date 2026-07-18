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


def build_test_wav(duration: float = 2.0) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "tone.wav"
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=440:duration={duration}",
                "-ac",
                "1",
                str(output),
            ],
            check=True,
        )
        return output.read_bytes()


def build_test_audio(suffix: str, encoder: str, *, channels: int = 1) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / f"tone{suffix}"
        encoder_flags = ["-strict", "-2"] if encoder == "vorbis" else []
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
                str(channels),
                "-c:a",
                encoder,
                *encoder_flags,
                str(output),
            ],
            check=True,
        )
        return output.read_bytes()


def probe_ogg(raw: bytes) -> dict[str, str]:
    return probe_audio(raw, ".ogg")


def probe_audio(raw: bytes, suffix: str) -> dict[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / f"output{suffix}"
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


def probe_duration(raw: bytes, suffix: str) -> float:
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / f"output{suffix}"
        source.write_bytes(raw)
        completed = subprocess.run(
            [
                "ffprobe",
                "-hide_banner",
                "-loglevel",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nw=1:nk=1",
                str(source),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    return float(completed.stdout.strip())


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

    def test_validate_audio_suffix_accepts_common_audio_formats(self) -> None:
        for suffix in ("mp3", "wav", "flac", "m4a", "aac", "ogg", "opus"):
            with self.subTest(suffix=suffix):
                web_app.validate_audio_upload(f"effect.{suffix}", b"abc")

        with self.assertRaises(ValueError):
            web_app.validate_audio_upload("effect.txt", b"abc")

        with self.assertRaises(ValueError):
            web_app.validate_audio_upload("effect.mp3", b"")

    def test_missing_ffmpeg_returns_clear_error(self) -> None:
        with patch.object(web_app.shutil, "which", return_value=None):
            with self.assertRaises(ValueError) as context:
                web_app.convert_mp3_to_ogg_bytes(b"not empty", quality="small")

        self.assertIn("ffmpeg", str(context.exception))

    def test_converts_and_trims_wav_to_selected_ogg_segment(self) -> None:
        source = build_test_wav()

        converted, metadata = web_app.convert_audio_to_ogg_bytes(
            source,
            input_suffix=".wav",
            quality="balanced",
            start_time=0.4,
            end_time=1.2,
        )

        self.assertAlmostEqual(probe_duration(converted, ".ogg"), 0.8, delta=0.08)
        self.assertEqual(metadata["trim_start"], "0.400")
        self.assertEqual(metadata["trim_end"], "1.200")

    def test_trims_and_preserves_each_supported_audio_format(self) -> None:
        vorbis_encoder, _ = web_app._select_vorbis_encoder(shutil.which("ffmpeg") or "ffmpeg")
        formats = {
            ".mp3": ("libmp3lame", "mp3", "mp3", 1),
            ".wav": ("pcm_s16le", "wav", "pcm_s16le", 1),
            ".flac": ("flac", "flac", "flac", 1),
            ".m4a": ("aac", "m4a", "aac", 1),
            ".aac": ("aac", "aac", "aac", 1),
            ".ogg": (vorbis_encoder, "ogg", "vorbis", 2),
            ".oga": (vorbis_encoder, "ogg", "vorbis", 2),
            ".opus": ("libopus", "ogg", "opus", 1),
        }

        for suffix, (source_encoder, expected_container, expected_codec, channels) in formats.items():
            with self.subTest(suffix=suffix):
                source = build_test_audio(suffix, source_encoder, channels=channels)
                trimmed, metadata = web_app.trim_audio_bytes(
                    source,
                    input_suffix=suffix,
                    quality="balanced",
                    start_time=0.2,
                    end_time=0.7,
                )
                probed = probe_audio(trimmed, suffix)

                self.assertIn(expected_container, probed["format_name"])
                self.assertEqual(probed["codec_name"], expected_codec)
                self.assertAlmostEqual(probe_duration(trimmed, suffix), 0.5, delta=0.1)
                self.assertEqual(metadata["audio_format"], suffix.removeprefix(".").upper())
                self.assertEqual(metadata["audio_codec"], expected_codec)

    def test_rejects_invalid_audio_trim_range(self) -> None:
        source = build_test_wav()

        for start_time, end_time in ((-0.1, 1.0), (1.0, 1.0), (1.5, 1.0)):
            with self.subTest(start_time=start_time, end_time=end_time):
                with self.assertRaises(ValueError):
                    web_app.convert_audio_to_ogg_bytes(
                        source,
                        input_suffix=".wav",
                        quality="small",
                        start_time=start_time,
                        end_time=end_time,
                    )

    def test_builds_normalized_waveform_for_audio_editor(self) -> None:
        source = build_test_wav()

        waveform = web_app.build_audio_waveform(source, input_suffix=".wav", points=120)

        self.assertAlmostEqual(waveform["duration"], 2.0, delta=0.05)
        self.assertEqual(len(waveform["peaks"]), 120)
        self.assertGreater(max(waveform["peaks"]), 0.9)
        self.assertTrue(all(0 <= peak <= 1 for peak in waveform["peaks"]))


if __name__ == "__main__":
    unittest.main()
