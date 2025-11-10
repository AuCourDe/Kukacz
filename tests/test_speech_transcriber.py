import importlib
import sys
from pathlib import Path


def reload_transcriber(monkeypatch, env=None):
    env = env or {}
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    for module in ("app.speech_transcriber", "app.config"):
        if module in sys.modules:
            del sys.modules[module]
    return importlib.import_module("app.speech_transcriber")


def test_load_model_uses_project_models_dir(monkeypatch, tmp_path):
    env = {"MODEL_CACHE_DIR": str(tmp_path / "models")}
    st_module = reload_transcriber(monkeypatch, env)

    monkeypatch.setattr(st_module.torch.cuda, "is_available", lambda: False)

    captured = {}

    class DummyModel:
        def transcribe(self, *args, **kwargs):
            return {"text": "", "segments": []}

    def fake_load_model(name, download_root=None, device=None):
        captured["download_root"] = download_root
        captured["device"] = device
        return DummyModel()

    monkeypatch.setattr(st_module.whisper, "load_model", fake_load_model)

    transcriber = st_module.WhisperTranscriber()
    transcriber.load_model("base")

    expected_dir = Path(env["MODEL_CACHE_DIR"])
    assert Path(captured["download_root"]) == expected_dir
    assert captured["device"] == "cpu"
    assert not transcriber._fp16
    assert expected_dir.exists()


def test_load_model_prefers_cuda(monkeypatch, tmp_path):
    env = {"MODEL_CACHE_DIR": str(tmp_path / "models")}
    st_module = reload_transcriber(monkeypatch, env)

    monkeypatch.setattr(st_module.torch.cuda, "is_available", lambda: True)

    captured = {}

    class DummyModel:
        def transcribe(self, *args, **kwargs):
            return {"text": "", "segments": []}

    def fake_load_model(name, download_root=None, device=None):
        captured["device"] = device
        return DummyModel()

    monkeypatch.setattr(st_module.whisper, "load_model", fake_load_model)

    transcriber = st_module.WhisperTranscriber()
    transcriber.load_model("base")

    assert captured["device"] == "cuda"
    assert transcriber._fp16

