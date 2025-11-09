import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _reload_config(monkeypatch, env: Dict[str, str] | None = None):
    """Reload the config module with a clean environment."""
    env = env or {}
    keys_to_clear = [
        "SPEAKER_DIARIZATION_TOKEN",
        "WHISPER_MODEL",
        "OLLAMA_MODEL",
        "OLLAMA_BASE_URL",
        "ENABLE_SPEAKER_DIARIZATION",
        "ENABLE_OLLAMA_ANALYSIS",
        "INPUT_FOLDER",
        "OUTPUT_FOLDER",
        "LOG_LEVEL",
        "LOG_FILE",
        "MODEL_CACHE_DIR",
    ]

    for key in keys_to_clear:
        monkeypatch.delenv(key, raising=False)

    for key, value in env.items():
        monkeypatch.setenv(key, value)

    if "config" in sys.modules:
        del sys.modules["config"]

    return importlib.import_module("config")


def test_config_defaults(monkeypatch):
    config = _reload_config(monkeypatch)

    assert config.SPEAKER_DIARIZATION_TOKEN == ""
    assert config.INPUT_FOLDER.is_absolute()
    assert config.INPUT_FOLDER.name == "input"
    assert config.OUTPUT_FOLDER.is_absolute()
    assert config.OUTPUT_FOLDER.name == "output"
    assert config.LOG_FILE.is_absolute()
    assert config.LOG_FILE.name == "whisper_analyzer.log"
    assert config.MODEL_CACHE_DIR.is_absolute()
    assert config.MODEL_CACHE_DIR.name == "models"


def test_config_environment_overrides(monkeypatch):
    env = {
        "SPEAKER_DIARIZATION_TOKEN": "token123",
        "WHISPER_MODEL": "base",
        "OLLAMA_MODEL": "llama3",
        "OLLAMA_BASE_URL": "http://example.com:11435",
        "ENABLE_SPEAKER_DIARIZATION": "false",
        "ENABLE_OLLAMA_ANALYSIS": "false",
        "INPUT_FOLDER": "custom_input",
        "OUTPUT_FOLDER": "custom_output",
        "LOG_FILE": "logs/custom.log",
        "MODEL_CACHE_DIR": "custom_models",
    }
    config = _reload_config(monkeypatch, env)

    assert config.SPEAKER_DIARIZATION_TOKEN == "token123"
    assert config.WHISPER_MODEL == "base"
    assert config.OLLAMA_MODEL == "llama3"
    assert config.OLLAMA_BASE_URL == "http://example.com:11435"
    assert config.ENABLE_SPEAKER_DIARIZATION is False
    assert config.ENABLE_OLLAMA_ANALYSIS is False
    assert config.INPUT_FOLDER == config.BASE_DIR / "custom_input"
    assert config.OUTPUT_FOLDER == config.BASE_DIR / "custom_output"
    assert config.LOG_FILE == config.BASE_DIR / "logs/custom.log"
    assert config.MODEL_CACHE_DIR == config.BASE_DIR / "custom_models"


def test_config_absolute_log_file(monkeypatch, tmp_path):
    custom_log = tmp_path / "absolute.log"
    config = _reload_config(monkeypatch, {"LOG_FILE": str(custom_log)})

    assert config.LOG_FILE == custom_log


def test_run_script_skip_modes(tmp_path):
    script_path = PROJECT_ROOT / "run.sh"
    env = os.environ.copy()
    env.update(
        {
            "SKIP_VENV_SETUP": "1",
            "SKIP_REQUIREMENTS_INSTALL": "1",
            "SKIP_APP_EXECUTION": "1",
            "VENV_DIR": str(tmp_path / "venv"),
        }
    )

    completed = subprocess.run(
        ["bash", str(script_path)],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    stdout = completed.stdout
    assert "Skipping virtual environment setup" in stdout
    assert "Skipping dependency installation" in stdout
    assert "Skipping application execution" in stdout

