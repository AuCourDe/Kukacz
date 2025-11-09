#!/usr/bin/env python3
"""
"""

import sys
import logging
import time
from config import (
    WHISPER_MODEL, SPEAKER_DIARIZATION_TOKEN, OLLAMA_MODEL,
    LOG_LEVEL, LOG_FILE, ENABLE_SPEAKER_DIARIZATION, ENABLE_OLLAMA_ANALYSIS
)

from audio_processor import AudioProcessor

# Konfiguracja logowania
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(LOG_FILE)),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Główna funkcja aplikacji z pełną inicjalizacją i uruchomieniem systemu"""
    try:
        if ENABLE_SPEAKER_DIARIZATION and not SPEAKER_DIARIZATION_TOKEN:
            message = (
                "Brak tokenu Hugging Face dla rozpoznawania mówców. "
                "Dodaj wartość zmiennej SPEAKER_DIARIZATION_TOKEN do pliku .env "
                "i uruchom ponownie aplikację."
            )
            logger.error(message)
            print(message, file=sys.stderr)
            sys.exit(1)

        logger.info("=== Uruchamianie aplikacji Whisper Analyzer ===")
        
        # Inicjalizacja procesora audio
        processor = AudioProcessor(
            enable_speaker_diarization=ENABLE_SPEAKER_DIARIZATION, 
            enable_ollama_analysis=ENABLE_OLLAMA_ANALYSIS
        )
        
        # Inicjalizacja wszystkich komponentów
        processor.initialize_components(
            whisper_model=WHISPER_MODEL,
            speaker_auth_token=SPEAKER_DIARIZATION_TOKEN,
            ollama_model=OLLAMA_MODEL
        )
        
        # Przetwarzanie istniejących plików
        logger.info("Przetwarzanie istniejących plików...")
        processor.process_all_files()
        
        # Uruchomienie obserwatora folderu
        logger.info("Uruchamianie obserwatora folderu...")
        processor.start_file_watcher()
        
        logger.info("Aplikacja uruchomiona. Oczekiwanie na nowe pliki...")
        logger.info(f"Umieść pliki MP3 w folderze: {processor.file_loader.input_folder}")
        logger.info("Naciśnij Ctrl+C aby zatrzymać")
        
        # Pętla główna aplikacji
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Otrzymano sygnał zatrzymania...")
            processor.stop_file_watcher()
            logger.info("Aplikacja zatrzymana")
        
    except Exception as e:
        logger.error(f"Błąd krytyczny: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 