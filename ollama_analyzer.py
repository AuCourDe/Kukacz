#!/usr/bin/env python3
"""
Moduł do integracji z Ollama dla analizy treści
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class OllamaAnalyzer:
    """Klasa do analizy treści za pomocą Ollama"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3:8b"):
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api/generate"
        
        logger.info(f"OllamaAnalyzer zainicjalizowany z modelem: {model}")
        logger.info(f"API URL: {self.api_url}")
    
    def test_connection(self) -> bool:
        """Test połączenia z serwerem Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model["name"] for model in models]
                logger.info(f"Dostępne modele Ollama: {available_models}")
                
                if self.model in available_models:
                    logger.info(f"Model {self.model} jest dostępny")
                    return True
                else:
                    logger.warning(f"Model {self.model} nie jest dostępny. Dostępne: {available_models}")
                    return False
            else:
                logger.error(f"Błąd połączenia z Ollama: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Błąd podczas testowania połączenia z Ollama: {e}")
            return False
    
    def analyze_content(self, text: str, analysis_type: str = "general") -> Dict[str, Any]:
        """
        Analiza treści za pomocą Ollama
        
        Args:
            text: Tekst do analizy
            analysis_type: Typ analizy ("general", "sentiment", "content_quality", "call_center", "custom")
        
        Returns:
            Słownik z wynikami analizy
        """
        try:
            # Import konfiguracji
            from config import OLLAMA_PROMPTS, OLLAMA_GENERATION_PARAMS
            
            # Przygotowanie promptu w zależności od typu analizy
            if analysis_type in OLLAMA_PROMPTS:
                # Użyj promptu z konfiguracji
                prompt = OLLAMA_PROMPTS[analysis_type].format(text=text)
            elif analysis_type == "call_center":
                prompt = self._create_call_center_prompt(text)
            elif analysis_type == "sentiment":
                prompt = self._create_sentiment_prompt(text)
            elif analysis_type == "content_quality":
                prompt = self._create_content_quality_prompt(text)
            else:
                prompt = self._create_general_prompt(text)
            
            # Wywołanie API Ollama
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": OLLAMA_GENERATION_PARAMS
            }
            
            logger.info(f"Wysyłanie zapytania do Ollama (typ: {analysis_type})")
            response = requests.post(self.api_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get("response", "").strip()
                
                # Parsowanie odpowiedzi
                parsed_result = self._parse_analysis_response(analysis_text, analysis_type)
                
                logger.info(f"Analiza zakończona pomyślnie (typ: {analysis_type})")
                return {
                    "success": True,
                    "analysis_type": analysis_type,
                    "raw_response": analysis_text,
                    "parsed_result": parsed_result,
                    "model_used": self.model
                }
            else:
                logger.error(f"Błąd API Ollama: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "analysis_type": analysis_type
                }
                
        except Exception as e:
            logger.error(f"Błąd podczas analizy treści: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_type": analysis_type
            }
    
    def _create_call_center_prompt(self, text: str) -> str:
        """Tworzenie promptu dla analizy rozmów call center"""
        return f"""Podsumuj rozmowę w dwóch krótkich zdaniach. W trzecim zdaniu oceń, czy była ona pozytywna, negatywna, czy przebiegła w miłym tonie. Jeżeli ktoś podczas rozmowy był agresywny lub wulgarny lub niemiły to podaj kto to był i co dokładnie powiedział.

Transkrypcja rozmowy:
{text}

Odpowiedź:"""

    def _create_sentiment_prompt(self, text: str) -> str:
        """Tworzenie promptu dla analizy sentymentu"""
        return f"""Przeanalizuj sentyment poniższego tekstu i zwróć odpowiedź w formacie JSON:

Tekst:
{text}

Odpowiedź w formacie JSON:
{{
    "sentiment": "positive/negative/neutral",
    "confidence": 0.85,
    "emotions": ["satisfaction", "frustration"],
    "intensity": "high/medium/low"
}}"""

    def _create_content_quality_prompt(self, text: str) -> str:
        """Tworzenie promptu dla analizy jakości treści"""
        return f"""Przeanalizuj jakość poniższego tekstu i zwróć odpowiedź w formacie JSON:

Tekst:
{text}

Odpowiedź w formacie JSON:
{{
    "readability": 7.5,
    "clarity": 8.0,
    "completeness": 6.5,
    "issues": ["grammar_errors", "unclear_phrases"],
    "suggestions": ["poprawić gramatykę", "dodać szczegóły"]
}}"""

    def _create_general_prompt(self, text: str) -> str:
        """Tworzenie ogólnego promptu analizy"""
        return f"""Przeanalizuj poniższy tekst i zwróć ogólne podsumowanie w formacie JSON:

Tekst:
{text}

Odpowiedź w formacie JSON:
{{
    "summary": "krótkie podsumowanie",
    "key_points": ["punkt 1", "punkt 2"],
    "tone": "formal/informal",
    "length_category": "short/medium/long"
}}"""

    def _parse_analysis_response(self, response_text: str, analysis_type: str) -> Dict[str, Any]:
        """Parsowanie odpowiedzi z Ollama"""
        try:
            # Próba wyodrębnienia JSON z odpowiedzi
            if "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
                return json.loads(json_str)
            else:
                # Jeśli nie ma JSON, zwróć surowy tekst
                return {
                    "raw_analysis": response_text,
                    "parsing_error": "Nie znaleziono formatu JSON"
                }
        except json.JSONDecodeError as e:
            logger.warning(f"Błąd parsowania JSON: {e}")
            return {
                "raw_analysis": response_text,
                "parsing_error": str(e)
            }
    
    def analyze_speaker_patterns(self, speakers_data: List[Dict]) -> Dict[str, Any]:
        """Analiza wzorców mówców"""
        if not speakers_data:
            return {"error": "Brak danych o mówcach"}
        
        try:
            # Statystyki mówców
            speaker_stats = {}
            total_duration = 0
            
            for speaker_info in speakers_data:
                speaker = speaker_info["speaker"]
                duration = speaker_info["duration"]
                
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = {
                        "total_time": 0,
                        "segments": 0,
                        "avg_segment_length": 0
                    }
                
                speaker_stats[speaker]["total_time"] += duration
                speaker_stats[speaker]["segments"] += 1
                total_duration += duration
            
            # Obliczenie średnich
            for speaker in speaker_stats:
                stats = speaker_stats[speaker]
                stats["avg_segment_length"] = stats["total_time"] / stats["segments"]
                stats["percentage"] = (stats["total_time"] / total_duration) * 100
            
            # Analiza wzorców
            dominant_speaker = max(speaker_stats.keys(), 
                                 key=lambda x: speaker_stats[x]["total_time"])
            
            return {
                "speaker_stats": speaker_stats,
                "total_duration": total_duration,
                "dominant_speaker": dominant_speaker,
                "speaker_count": len(speaker_stats),
                "analysis": {
                    "conversation_balance": "balanced" if len(speaker_stats) == 2 else "unbalanced",
                    "dominant_speaker_percentage": speaker_stats[dominant_speaker]["percentage"]
                }
            }
            
        except Exception as e:
            logger.error(f"Błąd podczas analizy wzorców mówców: {e}")
            return {"error": str(e)}

def test_ollama_integration():
    """Test integracji z Ollama"""
    print("🧪 Test integracji z Ollama")
    print("=" * 40)
    
    analyzer = OllamaAnalyzer()
    
    # Test połączenia
    print("1. Test połączenia z serwerem Ollama...")
    if analyzer.test_connection():
        print("✅ Połączenie z Ollama udane")
    else:
        print("❌ Błąd połączenia z Ollama")
        return False
    
    # Test analizy
    print("\n2. Test analizy treści...")
    test_text = "Klient dzwoni w sprawie reklamacji produktu. Doradca jest uprzejmy i profesjonalny."
    
    result = analyzer.analyze_content(test_text, "call_center")
    
    if result["success"]:
        print("✅ Analiza treści udana")
        print(f"Model: {result['model_used']}")
        print(f"Odpowiedź: {result['raw_response'][:200]}...")
    else:
        print(f"❌ Błąd analizy: {result['error']}")
        return False
    
    # Test analizy wzorców mówców
    print("\n3. Test analizy wzorców mówców...")
    test_speakers = [
        {"speaker": "SPEAKER_00", "start": 0, "end": 10, "duration": 10},
        {"speaker": "SPEAKER_01", "start": 10, "end": 15, "duration": 5},
        {"speaker": "SPEAKER_00", "start": 15, "end": 25, "duration": 10}
    ]
    
    pattern_result = analyzer.analyze_speaker_patterns(test_speakers)
    if "error" not in pattern_result:
        print("✅ Analiza wzorców mówców udana")
        print(f"Liczba mówców: {pattern_result['speaker_count']}")
        print(f"Dominujący mówca: {pattern_result['dominant_speaker']}")
    else:
        print(f"❌ Błąd analizy wzorców: {pattern_result['error']}")
    
    print("\n✅ Test integracji z Ollama zakończony pomyślnie!")
    return True

if __name__ == "__main__":
    test_ollama_integration() 