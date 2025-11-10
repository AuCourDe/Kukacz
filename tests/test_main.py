import importlib
import sys

import pytest


def reload_main():
    for module in ("app.main", "app.config"):
        if module in sys.modules:
            del sys.modules[module]
    return importlib.import_module("app.main")


def test_main_requires_hf_token(monkeypatch, capsys):
    monkeypatch.delenv("SPEAKER_DIARIZATION_TOKEN", raising=False)
    monkeypatch.setenv("ENABLE_SPEAKER_DIARIZATION", "true")

    main_module = reload_main()

    with pytest.raises(SystemExit):
        main_module.main()

    captured = capsys.readouterr()
    assert "SPEAKER_DIARIZATION_TOKEN" in captured.err
    assert "https://huggingface.co/pyannote/speaker-diarization-3.1" in captured.err


def test_main_allows_disabled_diarization(monkeypatch):
    monkeypatch.delenv("SPEAKER_DIARIZATION_TOKEN", raising=False)
    monkeypatch.setenv("ENABLE_SPEAKER_DIARIZATION", "false")
    monkeypatch.setenv("ENABLE_OLLAMA_ANALYSIS", "false")

    class DummyProcessor:
        def __init__(self, *args, **kwargs):
            self.initialize_called = False
            self.process_called = False
            self.watcher_started = False
            self.watcher_stopped = False
            self.file_loader = type(
                "Loader", (), {"input_folder": "input"}
            )()

        def initialize_components(self, **kwargs):
            self.initialize_called = True

        def process_all_files(self):
            self.process_called = True

        def start_file_watcher(self):
            self.watcher_started = True

        def stop_file_watcher(self):
            self.watcher_stopped = True

    for module in ("app.main", "app.config", "app.audio_processor"):
        if module in sys.modules:
            del sys.modules[module]

    import app.audio_processor as audio_processor  # noqa: E402

    dummy = DummyProcessor()
    monkeypatch.setattr(audio_processor, "AudioProcessor", lambda *a, **k: dummy)

    main_module = importlib.import_module("app.main")

    def fake_sleep(_):
        raise KeyboardInterrupt

    monkeypatch.setattr(main_module.time, "sleep", fake_sleep)

    main_module.main()

    assert dummy.initialize_called
    assert dummy.process_called
    assert dummy.watcher_started
    assert dummy.watcher_stopped

