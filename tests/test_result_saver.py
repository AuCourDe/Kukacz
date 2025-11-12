import pytest

from app.result_saver import ResultSaver


def _sample_transcription():
    return {
        "segments": [
            {"start": 0.0, "end": 1.5, "text": "Hello world"}
        ],
        "speakers": [
            {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.5, "duration": 1.5}
        ],
    }


def test_save_transcription_respects_provided_timestamp(tmp_path):
    output_dir = tmp_path / "output"
    saver = ResultSaver(output_dir)

    audio_file = tmp_path / "sample.mp3"
    audio_file.write_bytes(b"dummy audio content")

    provided_timestamp = "20250101010101"
    returned_timestamp = saver.save_transcription_with_speakers(
        audio_file,
        _sample_transcription(),
        analysis_results=None,
        timestamp=provided_timestamp,
    )

    assert returned_timestamp == provided_timestamp
    assert (output_dir / f"sample {provided_timestamp}.txt").exists()
    assert (output_dir / f"sample ANALIZA {provided_timestamp}.txt").exists()


def test_save_transcription_generates_timestamp(tmp_path):
    output_dir = tmp_path / "output"
    saver = ResultSaver(output_dir)

    audio_file = tmp_path / "sample.mp3"
    audio_file.write_bytes(b"dummy audio content")

    generated_timestamp = saver.save_transcription_with_speakers(
        audio_file,
        _sample_transcription(),
        analysis_results=None,
    )

    assert len(generated_timestamp) == 14  # YYYYMMDDHHMMSS
    assert (output_dir / f"sample {generated_timestamp}.txt").exists()
    assert (output_dir / f"sample ANALIZA {generated_timestamp}.txt").exists()

