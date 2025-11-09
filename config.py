#!/usr/bin/env python3
"""
Plik konfiguracyjny aplikacji Whisper Analyzer
==============================================

Zawiera wszystkie ustawienia aplikacji podzielone na kategorie:
- Ustawienia kluczowe (tokeny, modele)
- Ustawienia Ollama (prompty, parametry generowania)
- Ustawienia filtrowania rozumowania
- Ustawienia ogólne aplikacji
"""

from __future__ import annotations

import os
from pathlib import Path
# Próba załadowania zmiennych środowiskowych z pliku .env (jeśli dostępny)
try:
    from dotenv import load_dotenv  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - opcjonalna zależność
    load_dotenv = None  # type: ignore

# Katalog bazowy projektu
BASE_DIR: Path = Path(__file__).resolve().parent

if load_dotenv:
    # Ładowanie .env z katalogu projektu (ignorowane jeśli plik nie istnieje)
    load_dotenv(BASE_DIR / ".env")


# ============================================================================
# USTAWIENIA KLUCZOWE
# ============================================================================

# Token autoryzacji dla pyannote.audio (rozpoznawanie mówców)
SPEAKER_DIARIZATION_TOKEN: str = os.getenv("SPEAKER_DIARIZATION_TOKEN", "")

# Model Whisper do transkrypcji
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "large-v3")

# Model Ollama do analizy treści
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")

# Adres bazowy serwera Ollama
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ============================================================================
# USTAWIENIA OLLAMA - PROMPTY
# ============================================================================

# Wybór typu analizy treści
# Dostępne opcje: "call_center", "sentiment", "custom"
CONTENT_ANALYSIS_TYPE = "call_center"

# Prompty do różnych typów analizy
OLLAMA_PROMPTS = {
    "call_center": """
Przeanalizuj poniższą transkrypcję rozmowy z call center. 
Zwróć uwagę na:
- Główny problem klienta
- Jakość obsługi
- Rozwiązanie problemu
- Emocje klienta
- Sugestie poprawy

Transkrypcja:
{text}

Analiza:
""",
    
    "sentiment": """
Przeanalizuj sentyment poniższego tekstu. 
Określ:
- Ogólny nastrój (pozytywny/negatywny/neutralny)
- Intensywność emocji (niska/średnia/wysoka)
- Główne emocje
- Sugestie działania

Tekst:
{text}

Analiza sentymentu:
""",
    
    "custom": """
Przeanalizuj poniższy tekst według własnych kryteriów.
Zwróć uwagę na:
- Główne tematy
- Kluczowe informacje
- Wnioski i obserwacje
- Rekomendacje

Tekst:
{text}

Analiza:
"""
}

# Prompt do analizy wzorców mówców (zawsze używany jeśli włączone rozpoznawanie mówców)
SPEAKER_PATTERNS_PROMPT = """
Przeanalizuj wzorce mówców w poniższej rozmowie.
Zwróć uwagę na:
- Dominację mówców
- Długość wypowiedzi
- Przeplatanie się mówców
- Dynamikę rozmowy

Dane o mówcach:
{speakers_data}

Analiza wzorców:
"""

# ============================================================================
# USTAWIENIA OLLAMA - PARAMETRY GENEROWANIA
# ============================================================================

# Parametry generowania dla Ollama
OLLAMA_GENERATION_PARAMS = {
    "temperature": 0.7,      # Kreatywność (0.0-1.0)
    "top_p": 0.9,           # Jakość generowania
    "top_k": 40,            # Liczba tokenów do rozważenia
    "repeat_penalty": 1.1,  # Kara za powtarzanie
    "max_tokens": 2048,     # Maksymalna długość odpowiedzi
    "stop": None            # Tokeny zatrzymujące
}

# ============================================================================
# USTAWIENIA FILTROWANIA ROZUMOWANIA
# ============================================================================

# Czy zapisywać rozumowanie modelu do pliku
SAVE_REASONING = False

# Tagi rozumowania do filtrowania (XML tags)
REASONING_TAGS = [
    "<think>", "</think>",
    "<reasoning>", "</reasoning>",
    "<thought>", "</thought>",
    "<analysis>", "</analysis>",
    "<process>", "</process>",
    "<step>", "</step>",
    "<consider>", "</consider>"
]

# ============================================================================
# USTAWIENIA OGÓLNE APLIKACJI
# ============================================================================

# Foldery wejściowe i wyjściowe
INPUT_FOLDER: Path = BASE_DIR / os.getenv("INPUT_FOLDER", "input")
OUTPUT_FOLDER: Path = BASE_DIR / os.getenv("OUTPUT_FOLDER", "output")

# Folder modeli Whisper
MODEL_CACHE_DIR: Path = BASE_DIR / os.getenv("MODEL_CACHE_DIR", "models")

# Włączanie/wyłączanie funkcjonalności
ENABLE_SPEAKER_DIARIZATION: bool = os.getenv("ENABLE_SPEAKER_DIARIZATION", "true").lower() == "true"
ENABLE_OLLAMA_ANALYSIS: bool = os.getenv("ENABLE_OLLAMA_ANALYSIS", "true").lower() == "true"

# Ustawienia przetwarzania równoległego
MAX_CONCURRENT_PROCESSES: int = int(os.getenv("MAX_CONCURRENT_PROCESSES", "4"))

# Ustawienia logowania
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
_log_file_env = os.getenv("LOG_FILE")
if _log_file_env:
    LOG_FILE: Path = Path(_log_file_env)
    if not LOG_FILE.is_absolute():
        LOG_FILE = BASE_DIR / LOG_FILE
else:
    LOG_FILE = BASE_DIR / "whisper_analyzer.log"

# Ustawienia retry dla transkrypcji
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY_BASE: int = int(os.getenv("RETRY_DELAY_BASE", "2"))  # sekundy

# Ustawienia bezpieczeństwa
ENABLE_FILE_ENCRYPTION: bool = os.getenv("ENABLE_FILE_ENCRYPTION", "true").lower() == "true"
TEMPORARY_FILE_CLEANUP: bool = os.getenv("TEMPORARY_FILE_CLEANUP", "true").lower() == "true"