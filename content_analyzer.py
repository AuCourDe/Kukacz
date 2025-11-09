#!/usr/bin/env python3
"""
Moduł do analizy treści przez Ollama
====================================

Zawiera funkcje do:
- Analizy treści transkrypcji rozmów
- Analizy wzorców mówców i ich zachowań
- Analizy sentymentu i emocji w rozmowie
- Integracji z serwerem Ollama z filtrowaniem rozumowania
"""

import logging
from typing import Dict, Any
from config import OLLAMA_MODEL, OLLAMA_BASE_URL, CONTENT_ANALYSIS_TYPE, OLLAMA_PROMPTS
from reasoning_filter import ReasoningFilter

# Import OllamaAnalyzer
try:
    from ollama_analyzer import OllamaAnalyzer
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("OllamaAnalyzer nie jest dostępny. Analiza treści będzie wyłączona.")

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """Analiza treści transkrypcji za pomocą modeli Ollama z filtrowaniem rozumowania"""
    
    def __init__(self, model: str = OLLAMA_MODEL, base_url: str = OLLAMA_BASE_URL):
        self.ollama_analyzer = None
        self.model = model
        self.base_url = base_url
        self.initialized = False
        self.reasoning_filter = ReasoningFilter()
        logger.info("ContentAnalyzer zainicjalizowany")
    
    def initialize(self) -> bool:
        """Inicjalizacja analizy Ollama z testem połączenia"""
        if not OLLAMA_AVAILABLE:
            logger.warning("OllamaAnalyzer nie jest dostępny")
            return False
        
        try:
            self.ollama_analyzer = OllamaAnalyzer(base_url=self.base_url, model=self.model)
            if self.ollama_analyzer.test_connection():
                logger.info(f"Analiza Ollama zainicjalizowana z modelem: {self.model}")
                self.initialized = True
                return True
            else:
                logger.warning("Nie udało się połączyć z serwerem Ollama")
                return False
        except Exception as e:
            logger.error(f"Błąd podczas inicjalizacji Ollama: {e}")
            return False
    
    def analyze_transcription_content(self, transcription_data: Dict) -> Dict[str, Any]:
        """Kompleksowa analiza treści transkrypcji z analizą wzorców mówców i sentymentu"""
        if not self.initialized or not self.ollama_analyzer:
            return {"error": "Analiza Ollama nie jest dostępna"}
        
        try:
            text = transcription_data.get("text", "")
            speakers_data = transcription_data.get("speakers", [])
            
            analysis_results = {}
            
            # Analiza treści rozmowy (z wyborem typu z konfiguracji)
            logger.info(f"Rozpoczęcie analizy treści przez Ollama (typ: {CONTENT_ANALYSIS_TYPE})...")
            content_analysis = self.ollama_analyzer.analyze_content(text, CONTENT_ANALYSIS_TYPE)
            # Filtrowanie rozumowania z odpowiedzi
            content_analysis = self.reasoning_filter.process_ollama_response(content_analysis)
            analysis_results["content_analysis"] = content_analysis
            
            # Analiza wzorców mówców
            if speakers_data:
                logger.info("Analiza wzorców mówców...")
                speaker_analysis = self.ollama_analyzer.analyze_speaker_patterns(speakers_data)
                speaker_analysis = self.reasoning_filter.process_ollama_response(speaker_analysis)
                analysis_results["speaker_analysis"] = speaker_analysis
            
            # Analiza sentymentu
            sentiment_analysis = self.ollama_analyzer.analyze_content(text, "sentiment")
            sentiment_analysis = self.reasoning_filter.process_ollama_response(sentiment_analysis)
            analysis_results["sentiment_analysis"] = sentiment_analysis
            
            logger.info("Analiza treści zakończona pomyślnie")
            return analysis_results
            
        except Exception as e:
            logger.error(f"Błąd podczas analizy treści: {e}")
            return {"error": str(e)}
    
    def is_available(self) -> bool:
        """Sprawdzenie czy analiza Ollama jest dostępna"""
        return self.initialized and OLLAMA_AVAILABLE 