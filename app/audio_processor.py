#!/usr/bin/env python3
"""
Główny moduł do przetwarzania plików audio
==========================================

Zawiera główną klasę AudioProcessor która:
- Koordynuje wszystkie komponenty systemu
- Zarządza procesem transkrypcji i analizy
- Obsługuje przetwarzanie równoległe
- Integruje wszystkie moduły systemu z konfiguracją
"""

import logging
import shutil
import threading
from pathlib import Path
from typing import Optional, Union

from .config import (
    INPUT_FOLDER,
    OUTPUT_FOLDER,
    PROCESSED_FOLDER,
    ENABLE_SPEAKER_DIARIZATION,
    ENABLE_OLLAMA_ANALYSIS,
    MAX_CONCURRENT_PROCESSES,
)
from .file_loader import AudioFileLoader, FileWatcherManager
from .speech_transcriber import WhisperTranscriber
from .speaker_diarizer import SpeakerDiarizer, SimpleSpeakerDiarizer
from .content_analyzer import ContentAnalyzer
from .result_saver import ResultSaver

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Główna klasa do przetwarzania plików audio z integracją wszystkich komponentów"""
    
    def __init__(self, input_folder: Union[str, Path] = INPUT_FOLDER, 
                 output_folder: Union[str, Path] = OUTPUT_FOLDER, 
                 enable_speaker_diarization: bool = ENABLE_SPEAKER_DIARIZATION, 
                 enable_ollama_analysis: bool = ENABLE_OLLAMA_ANALYSIS):
        # Inicjalizacja komponentów
        input_folder_path = Path(input_folder)
        output_folder_path = Path(output_folder)

        self.file_loader = AudioFileLoader(input_folder_path)
        self.transcriber = WhisperTranscriber()
        self.speaker_diarizer = SpeakerDiarizer()
        self.content_analyzer = ContentAnalyzer()
        self.result_saver = ResultSaver(output_folder_path)
        self.file_watcher = FileWatcherManager(self, input_folder_path)
        self.processed_folder = Path(PROCESSED_FOLDER)
        self.processed_folder.mkdir(parents=True, exist_ok=True)
        
        # Konfiguracja funkcjonalności
        self.enable_speaker_diarization = enable_speaker_diarization
        self.enable_ollama_analysis = enable_ollama_analysis
        self.use_simple_diarization = False
        
        # Kontrola równoległości
        self.max_concurrent = MAX_CONCURRENT_PROCESSES
        self.semaphore = threading.Semaphore(self.max_concurrent)
        
        logger.info(f"AudioProcessor zainicjalizowany")
        logger.info(f"Rozpoznawanie mówców: {'Włączone' if enable_speaker_diarization else 'Wyłączone'}")
        logger.info(f"Analiza Ollama: {'Włączona' if enable_ollama_analysis else 'Wyłączona'}")
    
    def initialize_components(self, whisper_model: str = None, 
                            speaker_auth_token: Optional[str] = None,
                            ollama_model: str = None) -> None:
        """Inicjalizacja wszystkich komponentów systemu"""
        try:
            from .config import WHISPER_MODEL, OLLAMA_MODEL
            
            # Ładowanie modelu Whisper
            model_to_load = whisper_model if whisper_model else WHISPER_MODEL
            self.transcriber.load_model(model_to_load)
            
            # Inicjalizacja rozpoznawania mówców
            if self.enable_speaker_diarization:
                self.use_simple_diarization = False
                success = self.speaker_diarizer.initialize(speaker_auth_token)
                if not success:
                    logger.warning(
                        "Zaawansowane rozpoznawanie mówców niedostępne – "
                        "używam heurystycznego podziału na mówców."
                    )
                    self.use_simple_diarization = True
            
            # Inicjalizacja analizy Ollama
            if self.enable_ollama_analysis:
                model_to_use = ollama_model if ollama_model else OLLAMA_MODEL
                self.content_analyzer = ContentAnalyzer(model=model_to_use)
                success = self.content_analyzer.initialize()
                if not success:
                    logger.warning("Analiza Ollama będzie wyłączona")
                    self.enable_ollama_analysis = False
            
            logger.info("Wszystkie komponenty zainicjalizowane pomyślnie")
            
        except Exception as e:
            logger.error(f"Błąd podczas inicjalizacji komponentów: {e}")
            raise
    
    def transcribe_audio_with_speakers(self, audio_file_path: Path) -> Optional[dict]:
        """Transkrypcja pliku audio z rozpoznawaniem mówców"""
        try:
            # Transkrypcja audio na tekst
            transcription_data = self.transcriber.transcribe_audio(audio_file_path)
            if not transcription_data:
                return None
            
            # Rozpoznawanie mówców (jeśli włączone)
            speakers_data = None
            segments = transcription_data.get("segments", [])
            if self.enable_speaker_diarization:
                if not self.use_simple_diarization:
                    speakers_data = self.speaker_diarizer.diarize_speakers(audio_file_path)
                
                # Jeśli zaawansowane rozpoznawanie nie działa, użyj prostego algorytmu
                if not speakers_data:
                    logger.info("Używanie prostego rozpoznawania mówców...")
                    speakers_data = SimpleSpeakerDiarizer.diarize_speakers(segments)
            
            # Dodanie danych o mówcach do wyników transkrypcji
            transcription_data["speakers"] = speakers_data
            
            return transcription_data
            
        except Exception as e:
            logger.error(f"Błąd podczas transkrypcji z mówcami: {e}")
            return None
    
    def process_audio_file(self, audio_file_path: Path) -> None:
        """Przetwarzanie pojedynczego pliku audio z pełnym pipeline"""
        with self.semaphore:  # Ograniczenie liczby równoczesnych przetwarzań
            try:
                logger.info(f"Rozpoczęcie przetwarzania: {audio_file_path.name}")
                
                # Sprawdzenie czy plik jest już przetworzony
                if self.result_saver.is_file_processed(audio_file_path):
                    logger.info(f"Plik już przetworzony: {audio_file_path.name}")
                    return
                
                # Transkrypcja z rozpoznawaniem mówców
                transcription_data = self.transcribe_audio_with_speakers(audio_file_path)
                if transcription_data:
                    # Analiza treści za pomocą Ollama (jeśli włączona)
                    analysis_results = None
                    if self.enable_ollama_analysis:
                        analysis_results = self.content_analyzer.analyze_transcription_content(transcription_data)
                        logger.info(f"Analiza Ollama zakończona dla: {audio_file_path.name}")
                    else:
                        logger.info(f"Analiza Ollama wyłączona, pominięto analizę treści.")
                    
                    # Zapisanie wyników
                    self.result_saver.save_transcription_with_speakers(
                        audio_file_path, transcription_data, analysis_results
                    )
                    # Przeniesienie przetworzonego pliku do folderu processed
                    destination = self.processed_folder / audio_file_path.name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(audio_file_path), destination)
                    logger.info(
                        "Przetwarzanie zakończone pomyślnie: %s (przeniesiono do %s)",
                        audio_file_path.name,
                        destination,
                    )
                else:
                    logger.error(f"Nie udało się przetworzyć pliku: {audio_file_path.name}")
                
            except Exception as e:
                logger.error(f"Błąd podczas przetwarzania {audio_file_path.name}: {e}")
    
    def process_all_files(self) -> None:
        """Przetwarzanie wszystkich plików MP3 w folderze wejściowym"""
        try:
            # Pobranie nieprzetworzonych plików
            unprocessed_files = self.file_loader.get_unprocessed_files(self.result_saver.output_folder)
            
            if not unprocessed_files:
                logger.info("Brak plików MP3 do przetworzenia")
                return
            
            logger.info(f"Znaleziono {len(unprocessed_files)} plików MP3 do przetworzenia")
            
            # Przetwarzanie plików w puli wątków
            threads = []
            for audio_file in unprocessed_files:
                thread = threading.Thread(
                    target=self.process_audio_file,
                    args=(audio_file,)
                )
                threads.append(thread)
                thread.start()
            
            # Oczekiwanie na zakończenie wszystkich wątków
            for thread in threads:
                thread.join()
            
            logger.info("Przetwarzanie wszystkich plików zakończone")
            
        except Exception as e:
            logger.error(f"Błąd podczas przetwarzania plików: {e}")
    
    def start_file_watcher(self) -> None:
        """Uruchomienie obserwatora folderu"""
        self.file_watcher.start_watching()
    
    def stop_file_watcher(self) -> None:
        """Zatrzymanie obserwatora folderu"""
        self.file_watcher.stop_watching() 