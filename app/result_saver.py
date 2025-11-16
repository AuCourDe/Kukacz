#!/usr/bin/env python3
"""
Moduł do zapisywania wyników transkrypcji i analizy
===================================================

Zawiera funkcje do:
- Zapisywania transkrypcji z informacjami o mówcach
- Zapisywania analizy treści przez Ollama
- Zapisywania rozumowania modeli (opcjonalnie)
- Formatowania wyników w czytelny sposób
- Obsługi różnych formatów wyjściowych
"""

import copy
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Union

from .reasoning_filter import ReasoningFilter

logger = logging.getLogger(__name__)

class ResultSaver:
    """Zapisywanie wyników transkrypcji i analizy do plików"""
    
    def __init__(
        self,
        output_folder: Union[str, Path] = "output",
    ):
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.reasoning_filter = ReasoningFilter()
        logger.info(f"ResultSaver zainicjalizowany - folder: {self.output_folder}")
    
    def find_speaker_for_segment(self, segment_start: float, segment_end: float, 
                                speakers_data: List[Dict]) -> str:
        """Znajdowanie mówcy dla segmentu z ulepszonym algorytmem dopasowania"""
        if not speakers_data:
            return "Unknown"
        
        best_speaker = "Unknown"
        best_overlap = 0.0
        
        for speaker_info in speakers_data:
            speaker_start = speaker_info["start"]
            speaker_end = speaker_info["end"]
            
            # Obliczenie nakładania się segmentów
            overlap_start = max(segment_start, speaker_start)
            overlap_end = min(segment_end, speaker_end)
            
            if overlap_end > overlap_start:  # Jest nakładanie
                overlap_duration = overlap_end - overlap_start
                segment_duration = segment_end - segment_start
                
                # Procent nakładania względem segmentu
                overlap_ratio = overlap_duration / segment_duration
                
                if overlap_ratio > best_overlap:
                    best_overlap = overlap_ratio
                    best_speaker = speaker_info["speaker"]
        
        # Jeśli nakładanie jest mniejsze niż 50%, sprawdź najbliższy segment
        if best_overlap < 0.5:
            best_speaker = self._find_closest_speaker(segment_start, segment_end, speakers_data)
        
        return best_speaker
    
    def _find_closest_speaker(self, segment_start: float, segment_end: float, 
                             speakers_data: List[Dict]) -> str:
        """Znajdowanie najbliższego segmentu mówcy"""
        if not speakers_data:
            return "Unknown"
        
        segment_center = (segment_start + segment_end) / 2
        closest_speaker = "Unknown"
        min_distance = float('inf')
        
        for speaker_info in speakers_data:
            speaker_center = (speaker_info["start"] + speaker_info["end"]) / 2
            distance = abs(segment_center - speaker_center)
            
            if distance < min_distance:
                min_distance = distance
                closest_speaker = speaker_info["speaker"]
        
        return closest_speaker
    
    def merge_consecutive_speakers(self, segments_with_speakers: List[Dict]) -> List[Dict]:
        """Łączenie kolejnych segmentów tego samego mówcy"""
        if not segments_with_speakers:
            return segments_with_speakers
        
        merged = []
        current_group = {
            "speaker": segments_with_speakers[0]["speaker"],
            "start": segments_with_speakers[0]["start"],
            "end": segments_with_speakers[0]["end"],
            "text": segments_with_speakers[0]["text"]
        }
        
        for i in range(1, len(segments_with_speakers)):
            current_seg = segments_with_speakers[i]
            
            # Sprawdzenie czy można połączyć (ten sam mówca, mała pauza)
            if (current_seg["speaker"] == current_group["speaker"] and 
                current_seg["start"] - current_group["end"] < 1.0):  # Pauza < 1s
                
                # Rozszerzenie grupy
                current_group["end"] = current_seg["end"]
                current_group["text"] += " " + current_seg["text"]
            else:
                # Zapisanie grupy i rozpoczęcie nowej
                merged.append(current_group)
                current_group = {
                    "speaker": current_seg["speaker"],
                    "start": current_seg["start"],
                    "end": current_seg["end"],
                    "text": current_seg["text"]
                }
        
        # Dodanie ostatniej grupy
        merged.append(current_group)
        
        return merged
    
    def save_transcription_with_speakers(
        self,
        audio_file_path: Path,
        transcription_data: Dict,
        analysis_results: Optional[Dict] = None,
        timestamp: Optional[str] = None,
    ) -> str:
        """Zapisywanie transkrypcji z informacjami o mówcach i analizą Ollama."""
        try:
            effective_timestamp = timestamp or datetime.now().strftime("%Y%m%d%H%M%S")
            output_filename = f"{audio_file_path.stem} {effective_timestamp}.txt"
            output_path = self.output_folder / output_filename

            analysis_filename = f"{audio_file_path.stem} ANALIZA {effective_timestamp}.txt"
            analysis_path = self.output_folder / analysis_filename

            # Zapisanie transkrypcji tekstowej z rozpoznawaniem mówców
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Transkrypcja rozmowy: {audio_file_path.name}\n")
                f.write("=" * 60 + "\n\n")
                
                segments = transcription_data.get("segments", [])
                speakers_data = transcription_data.get("speakers", [])
                
                # Przygotowanie segmentów z przypisanymi mówcami
                segments_with_speakers = []
                for segment in segments:
                    segment_start = segment.get("start", 0)
                    segment_end = segment.get("end", 0)
                    
                    # Znajdź mówcę dla tego segmentu
                    speaker = self.find_speaker_for_segment(segment_start, segment_end, speakers_data)
                    
                    segments_with_speakers.append({
                        "speaker": speaker,
                        "start": segment_start,
                        "end": segment_end,
                        "text": segment.get("text", "").strip()
                    })
                
                # Łączenie kolejnych segmentów tego samego mówcy
                merged_segments = self.merge_consecutive_speakers(segments_with_speakers)
                
                # Zapisanie do pliku
                for segment in merged_segments:
                    start_time = f"{int(segment['start']//60):02d}:{int(segment['start']%60):02d}"
                    end_time = f"{int(segment['end']//60):02d}:{int(segment['end']%60):02d}"
                    f.write(f"[{start_time}-{end_time}] {segment['speaker']}: {segment['text']}\n")
                
                # Dodanie statystyk mówców
                f.write("\n" + "=" * 60 + "\n")
                f.write("STATYSTYKI MÓWCÓW:\n")
                f.write("=" * 60 + "\n")
                
                speaker_stats = {}
                for segment in merged_segments:
                    speaker = segment["speaker"]
                    duration = segment["end"] - segment["start"]
                    
                    if speaker not in speaker_stats:
                        speaker_stats[speaker] = {"total_time": 0, "segments": 0, "words": 0}
                    
                    speaker_stats[speaker]["total_time"] += duration
                    speaker_stats[speaker]["segments"] += 1
                    speaker_stats[speaker]["words"] += len(segment["text"].split())
                
                for speaker, stats in speaker_stats.items():
                    total_minutes = stats["total_time"] / 60
                    avg_words_per_segment = stats["words"] / stats["segments"] if stats["segments"] > 0 else 0
                    f.write(f"{speaker}:\n")
                    f.write(f"  - Czas mówienia: {stats['total_time']:.1f}s ({total_minutes:.1f}min)\n")
                    f.write(f"  - Liczba segmentów: {stats['segments']}\n")
                    f.write(f"  - Liczba słów: {stats['words']}\n")
                    f.write(f"  - Średnio słów/segment: {avg_words_per_segment:.1f}\n")
                    f.write("\n")
            
            analysis_text = self._prepare_analysis_text(analysis_results, audio_file_path)
            with open(analysis_path, "w", encoding="utf-8") as f:
                f.write(f"Analiza rozmowy: {audio_file_path.name}\n")
                f.write("=" * 60 + "\n\n")
                f.write(analysis_text)

            # Zapisywanie rozumowania do osobnego pliku (jeśli włączone)
            if (
                analysis_results
                and analysis_results.get("content_analysis", {}).get("filtered_reasoning")
            ):
                self.reasoning_filter.save_reasoning_to_file(
                    analysis_results["content_analysis"]["filtered_reasoning"],
                    self.output_folder,
                    audio_file_path.stem,
                )

            logger.success("Analiza zapisana: %s", analysis_path)

            logger.success(f"Transkrypcja zapisana: {output_path}")
            return effective_timestamp
            
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania transkrypcji: {e}")
            raise
    
    def _prepare_analysis_text(
        self, analysis_results: Optional[Dict], audio_file_path: Path
    ) -> str:
        """Tworzy tekst analizy nawet jeśli Ollama jest niedostępna."""
        if not analysis_results:
            return (
                "Analiza Ollama niedostępna. "
                "Sprawdź konfigurację serwera lub ustaw zmienną ENABLE_OLLAMA_ANALYSIS=false."
            )

        content_analysis = analysis_results.get("content_analysis")
        if content_analysis:
            if content_analysis.get("injection_detected"):
                warning = (
                    "⚠️ Wykryto potencjalną próbę manipulacji transkrypcją. "
                    f"Słowa-klucze: {', '.join(content_analysis.get('injection_matches', []))}\n\n"
                )
            else:
                warning = ""

            if not content_analysis.get("success"):
                error_detail = (
                    content_analysis.get("validation_error")
                    or content_analysis.get("error")
                    or "Nieznany błąd analizy"
                )
                return warning + f"Analiza Ollama zakończona błędem: {error_detail}"

            if content_analysis.get("raw_response"):
                return warning + content_analysis["raw_response"]

        if content_analysis and content_analysis.get("parsed_result"):
            try:
                parsed = content_analysis["parsed_result"]
                # Jeśli jest brief_summary, wyświetl je na początku
                if isinstance(parsed, dict) and "brief_summary" in parsed:
                    parsed_copy = copy.deepcopy(parsed)
                    brief = parsed_copy.pop("brief_summary")
                    result = f"📋 Krótkie podsumowanie rozmowy:\n{brief}\n\n"
                    result += "📊 Szczegółowa analiza:\n"
                    result += json.dumps(parsed_copy, ensure_ascii=False, indent=2)
                    return warning + result
                else:
                    return warning + json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                return warning + str(content_analysis["parsed_result"])

        return (
            f"Analiza Ollama niedostępna dla pliku {audio_file_path.name}. "
            f"Szczegóły: {analysis_results}"
        )
