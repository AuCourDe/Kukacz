from pathlib import Path

import pytest

from app.file_loader import AudioFileLoader, AudioFileValidator


def _write_dummy_audio(file_path: Path, size: int = 4) -> None:
    file_path.write_bytes(b"\x00" * size)


def test_supported_extensions_cover_common_formats():
    expected = {".mp3", ".wav", ".mp4", ".m4a", ".ogg", ".aac", ".flac"}
    assert expected.issubset(AudioFileValidator.SUPPORTED_EXTENSIONS)

    description = AudioFileValidator.describe_supported_extensions()
    for ext in expected:
        assert ext.lstrip(".") in description


@pytest.mark.parametrize(
    "extension",
    [
        ".mp3",
        ".wav",
        ".mp4",
        ".m4a",
        ".ogg",
        ".aac",
        ".flac",
        ".acc",
    ],
)
def test_is_supported_extension(extension):
    dummy_path = Path(f"dummy{extension}")
    assert AudioFileValidator.is_supported_extension(dummy_path)


def test_loader_filters_invalid_and_empty_files(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    valid_files = [
        "clip_mp3.mp3",
        "clip_wav.wav",
        "clip_mp4.mp4",
        "clip_m4a.m4a",
        "clip_ogg.ogg",
        "clip_aac.aac",
        "clip_flac.flac",
        "clip_acc.acc",
    ]

    for filename in valid_files:
        _write_dummy_audio(input_dir / filename)

    # Unsupported extension
    (input_dir / "notes.txt").write_text("test")
    # Empty file even with supported extension should be filtered out
    (input_dir / "empty.wav").touch()

    loader = AudioFileLoader(input_dir)
    detected = sorted(path.name for path in loader.get_audio_files())

    assert detected == sorted(valid_files)



