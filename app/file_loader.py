#!/usr/bin/env python3
"""
Moduł do wczytywania i walidacji plików audio
==============================================

Zawiera funkcje do:
- Sprawdzania poprawności plików MP3
- Wczytywania plików z folderu wejściowego
- Filtrowania plików według kryteriów
- Obserwowania zmian w folderze wejściowym
"""

import os
import logging
import time
import threading
from pathlib import Path
from typing import List, Optional, Union
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class AudioFileValidator:
    """Walidacja plików audio MP3"""
    
    @staticmethod
    def is_valid_audio_file(file_path: Path) -> bool:
        """Sprawdzenie czy plik jest poprawnym plikiem audio MP3"""
        if not file_path.exists():
            return False
        
        # Sprawdzenie rozszerzenia
        if file_path.suffix.lower() != '.mp3':
            return False
        
        # Sprawdzenie czy plik nie jest pusty
        if file_path.stat().st_size == 0:
            return False
        
        return True

class AudioFileLoader:
    """Wczytywanie plików audio z folderu wejściowego"""
    
    def __init__(self, input_folder: Union[str, Path] = "input"):
        self.input_folder = Path(input_folder)
        self.input_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"AudioFileLoader zainicjalizowany - folder: {self.input_folder}")
    
    def get_audio_files(self) -> List[Path]:
        """Pobranie wszystkich plików MP3 z folderu wejściowego"""
        mp3_files = list(self.input_folder.glob("*.mp3"))
        valid_files = [f for f in mp3_files if AudioFileValidator.is_valid_audio_file(f)]
        
        logger.info(f"Znaleziono {len(valid_files)} poprawnych plików MP3")
        return valid_files
    
    def get_unprocessed_files(self, output_folder: Path) -> List[Path]:
        """Pobranie plików MP3 które nie zostały jeszcze przetworzone"""
        audio_files = self.get_audio_files()
        unprocessed = []
        
        for audio_file in audio_files:
            transcript_pattern = f"{audio_file.stem} *.txt"
            if not any(output_folder.glob(transcript_pattern)):
                unprocessed.append(audio_file)
        
        logger.info(f"Znaleziono {len(unprocessed)} nieprzetworzonych plików")
        return unprocessed

class FileWatcher(FileSystemEventHandler):
    """Obserwator folderu do automatycznego przetwarzania nowych plików"""
    
    def __init__(self, processor, input_folder: Path):
        self.processor = processor
        self.input_folder = input_folder
        logger.info("FileWatcher zainicjalizowany")
    
    def on_created(self, event):
        """Obsługa zdarzenia utworzenia nowego pliku"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() == '.mp3':
                logger.info(f"Wykryto nowy plik MP3: {file_path.name}")
                # Krótkie opóźnienie aby plik został w pełni zapisany
                time.sleep(1)
                if AudioFileValidator.is_valid_audio_file(file_path):
                    threading.Thread(
                        target=self.processor.process_audio_file,
                        args=(file_path,)
                    ).start()
                else:
                    logger.warning(f"Pominięto niepoprawny plik: {file_path.name}")

class FileWatcherManager:
    """Zarządzanie obserwatorem folderu"""
    
    def __init__(self, processor, input_folder: Path):
        self.processor = processor
        self.input_folder = input_folder
        self.observer = None
        self.event_handler = None
    
    def start_watching(self):
        """Uruchomienie obserwacji folderu"""
        self.event_handler = FileWatcher(self.processor, self.input_folder)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, str(self.input_folder), recursive=False)
        self.observer.start()
        logger.info("Obserwator folderu uruchomiony")
    
    def stop_watching(self):
        """Zatrzymanie obserwacji folderu"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Obserwator folderu zatrzymany") 