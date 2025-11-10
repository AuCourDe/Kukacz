#!/usr/bin/env python3
"""End-to-end smoke test for Whisper Analyzer."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / "tmp_test"


def _copy_project(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    ignore = shutil.ignore_patterns(
        ".git",
        ".venv",
        "venv",
        "venv_*",
        "venvpython*",
        "venv_python310_new",
        "trash",
        "tmp_test",
        "models",
        "__pycache__",
        "*.pyc",
        "*.log",
    )
    shutil.copytree(ROOT, destination, ignore=ignore)


def _prepare_environment(test_root: Path) -> None:
    for folder_name in ("input", "output", "processed", "models"):
        folder = test_root / folder_name
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)

    sample_src = ROOT / "MEDIA_FILES" / "sample.mp3"
    if not sample_src.exists():
        raise FileNotFoundError("Brak pliku testowego MEDIA_FILES/sample.mp3")
    shutil.copy(sample_src, test_root / "input" / sample_src.name)


def _run_application(test_root: Path) -> None:
    env = os.environ.copy()
    env.update(
        {
            "WHISPER_MODEL": env.get("WHISPER_MODEL", "tiny"),
            "ENABLE_SPEAKER_DIARIZATION": "false",
            "ENABLE_OLLAMA_ANALYSIS": env.get("ENABLE_OLLAMA_ANALYSIS", "false"),
            "APP_RUN_ONCE": "true",
            "MODEL_CACHE_DIR": str(test_root / "models"),
            "PROCESSED_FOLDER": str(test_root / "processed"),
            "INPUT_FOLDER": str(test_root / "input"),
            "OUTPUT_FOLDER": str(test_root / "output"),
            "LOG_FILE": str(test_root / "whisper_analyzer_test.log"),
        }
    )

    subprocess.run(
        [sys.executable, "-m", "app.main"],
        cwd=test_root,
        env=env,
        check=True,
        timeout=600,
    )


def _ensure_results(test_root: Path) -> None:
    output_dir = test_root / "output"
    processed_dir = test_root / "processed"

    transcripts = sorted(output_dir.glob("sample *.txt"))
    analysis = sorted(output_dir.glob("sample ANALIZA *.txt"))

    if not transcripts:
        raise AssertionError("Nie znaleziono pliku z transkrypcją w katalogu output")
    if not analysis:
        raise AssertionError("Nie znaleziono pliku z analizą w katalogu output")

    processed_file = processed_dir / "sample.mp3"
    if not processed_file.exists():
        raise AssertionError("Plik audio nie został przeniesiony do katalogu processed")


def main() -> None:
    _copy_project(TMP_DIR)
    try:
        _prepare_environment(TMP_DIR)
        _run_application(TMP_DIR)
        _ensure_results(TMP_DIR)
        print("✅ Test E2E zakończony pomyślnie")
    finally:
        shutil.rmtree(TMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
