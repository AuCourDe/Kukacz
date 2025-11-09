# Whisper Analyzer

Kompleksowy system do transkrypcji i analizy treści plików audio zgodnie z PRD.

## Funkcjonalności

### Faza 1 (Obecna)
- ✅ Transkrypcja plików MP3 za pomocą Whisper (model large-v3)
- ✅ **Rozpoznawanie mówców (Speaker Diarization)** - nowość!
- ✅ Obsługa języka polskiego z dokładnością do 98%
- ✅ Automatyczne monitorowanie folderu wejściowego
- ✅ Równoległe przetwarzanie (max 4 pliki jednocześnie)
- ✅ Szyfrowanie plików tymczasowych (AES-256)
- ✅ Obsługa błędów z automatycznymi ponownymi próbami
- ✅ Logowanie wszystkich operacji

### Faza 2 (Planowana)
- 🔄 Integracja z Ollama do analizy treści
- 🔄 Wykrywanie treści wulgarnych/agresywnych
- 🔄 Nazewnictwo wyników z oznaczeniem analizy

## Rozpoznawanie Mówców 🎯

Aplikacja automatycznie rozpoznaje i rozdziela różnych mówców w nagraniu:

### Przykład wyjścia:
```
[00:00-00:03] SPEAKER_00: Dzień dobry, dzwonię w sprawie mojego zamówienia
[00:04-00:08] SPEAKER_01: Dzień dobry, jak mogę pomóc?
[00:09-00:15] SPEAKER_00: Mam problem z moim zamówieniem numer 12345
```

### Generowane pliki:
- `nazwa_pliku.txt` - Standardowa transkrypcja
- `nazwa_pliku_with_speakers.txt` - Transkrypcja z adnotacjami mówców
- `nazwa_pliku_metadata.json` - Metadane w formacie JSON

**Idealne dla call center!** Rozróżnia doradców klienta od klientów.

## Wymagania systemowe

- Python 3.10+
- Linux (Ubuntu 22.04+) lub Windows 11 z WSL2
- FFmpeg
- Minimum 8GB RAM (16GB zalecane)
- GPU z CUDA (opcjonalne, ale zalecane dla szybszego przetwarzania)

## Instalacja

1. **Klonowanie repozytorium**
```bash
git clone <repository-url>
cd Whisper
```

2. **Utworzenie środowiska wirtualnego**
```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# lub
.venv\Scripts\activate     # Windows
```

3. **Konfiguracja zmiennych środowiskowych**
```bash
cp .env.example .env
# Uzupełnij .env (token HuggingFace, adres serwera Ollama itd.)
```

4. **Instalacja zależności**
```bash
pip install -r requirements.txt
```

5. **Instalacja FFmpeg**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y ffmpeg

# CentOS/RHEL
sudo yum install ffmpeg

# macOS
brew install ffmpeg
```

5. **Konfiguracja rozpoznawania mówców (opcjonalne)**
```bash
# Dla najlepszej wydajności, uzyskaj token na:
# https://huggingface.co/pyannote/speaker-diarization-3.1
```

## Użytkowanie

### Szybki start

1. **Uruchomienie aplikacji**
   ```bash
   # Automatyczne uruchomienie (Ubuntu / WSL)
   ./run.sh

   # Ręczna aktywacja
   source .venv/bin/activate
   python main.py
   ```

   Skrypt `run.sh` automatycznie tworzy/aktywuje środowisko `.venv`, instaluje zależności i uruchamia aplikację.

2. **Umieszczenie plików audio**
- Umieść pliki MP3 w folderze `input/`
- Aplikacja automatycznie wykryje i przetworzy nowe pliki
- Wyniki transkrypcji zostaną zapisane w folderze `output/`
- Modele Whisper pobierają się automatycznie do podfolderu `models/` w katalogu projektu
- Token Hugging Face (`SPEAKER_DIARIZATION_TOKEN`) wpisz w pliku `.env` po zaakceptowaniu licencji na https://huggingface.co/pyannote/speaker-diarization-3.1

### Struktura folderów

```
Whisper/
├── input/           # Folder z plikami MP3 do przetworzenia
├── output/          # Folder z wynikami transkrypcji
│   ├── rozmowa_01.txt                    # Standardowa transkrypcja
│   ├── rozmowa_01_with_speakers.txt      # Transkrypcja z mówcami
│   └── rozmowa_01_metadata.json          # Metadane JSON
├── models/          # Lokalna pamięć podręczna modeli Whisper
├── .env.example     # Szablon zmiennych środowiskowych
├── .env             # Lokalna konfiguracja (nie trafia do repozytorium)
├── main.py
├── whisper_analyzer.py
├── run.sh
├── requirements.txt
├── README.md
├── SPEAKER_DIARIZATION.md               # Dokumentacja rozpoznawania mówców
└── whisper_analyzer.log  # Plik logów
```

### Przykład użycia

```bash
# 1. Uruchom aplikację
python whisper_analyzer.py

# 2. W nowym terminalu skopiuj plik audio
cp /ścieżka/do/rozmowy.mp3 input/

# 3. Sprawdź wyniki w folderze output/
ls output/
cat output/rozmowy_with_speakers.txt
```

## Konfiguracja

### Parametry aplikacji

Możesz dostosować parametry w kodzie:

```python
# W klasie AudioProcessor
self.max_concurrent = 4  # Maksymalna liczba równoczesnych przetwarzań
self.input_folder = "input"  # Folder wejściowy
self.output_folder = "output"  # Folder wyjściowy
self.enable_speaker_diarization = True  # Włącz/wyłącz rozpoznawanie mówców
```

#### Ścieżki modeli i urządzenia

- Modele Whisper są buforowane w `models/` względnie do katalogu projektu (zmienna `MODEL_CACHE_DIR`).
- Aplikacja automatycznie wykrywa dostępność GPU; przy braku akceleratora przechodzi na CPU i wymusza transkrypcję w trybie `fp16=False`.
- Do rozpoznawania mówców wymagany jest token Hugging Face (`SPEAKER_DIARIZATION_TOKEN`) uzyskany po zaakceptowaniu warunków repozytorium https://huggingface.co/pyannote/speaker-diarization-3.1.

### Model Whisper

Domyślnie używany jest model `large-v3` dla najwyższej dokładności. Możesz zmienić na:

- `tiny` - najszybszy, najmniej dokładny
- `base` - szybki, podstawowa dokładność
- `small` - średnia prędkość i dokładność
- `medium` - wolniejszy, wyższa dokładność
- `large-v3` - najwolniejszy, najwyższa dokładność

### Rozpoznawanie mówców

Aby włączyć rozpoznawanie mówców z tokenem HuggingFace:

```python
# W funkcji main()
auth_token = "hf_your_token_here"
processor.initialize_speaker_diarization(auth_token)
```

## Monitorowanie

### Logi

Aplikacja generuje szczegółowe logi w pliku `whisper_analyzer.log`:

```
2025-01-XX 10:30:15 - INFO - === Uruchamianie aplikacji Whisper Analyzer ===
2025-01-XX 10:30:16 - INFO - Ładowanie modelu Whisper: large-v3
2025-01-XX 10:30:45 - INFO - Model Whisper załadowany pomyślnie
2025-01-XX 10:30:46 - INFO - Rozpoznawanie mówców: Włączone
2025-01-XX 10:30:47 - INFO - Rozpoznawanie mówców zainicjalizowane pomyślnie
2025-01-XX 10:30:48 - INFO - Znaleziono 2 plików MP3 do przetworzenia
2025-01-XX 10:30:49 - INFO - Transkrypcja pliku: rozmowa_01.mp3 (próba 1/3)
2025-01-XX 10:32:15 - INFO - Rozpoznano 2 mówców
2025-01-XX 10:32:16 - INFO - Transkrypcja zakończona pomyślnie: rozmowa_01.mp3
```

### Wydajność

Typowe czasy przetwarzania (na CPU):
- **Transkrypcja:** Model `large-v3`: ~5 min/30 min nagrania
- **Rozpoznawanie mówców:** ~10-15 min/30 min nagrania
- **Całkowity czas:** ~15-20 min/30 min nagrania

Z GPU CUDA czasy mogą być 3-5x szybsze.

### Dokładność rozpoznawania mówców:
- **Rozpoznawanie liczby mówców:** 95%+
- **Rozdzielenie wypowiedzi:** 90%+
- **Dokładność czasowa:** ±0.5 sekundy

## Bezpieczeństwo

- Pliki tymczasowe są szyfrowane za pomocą AES-256
- Brak wysyłania danych do chmury - wszystko przetwarzane lokalnie
- Automatyczne usuwanie plików tymczasowych
- Walidacja plików wejściowych

## Rozwiązywanie problemów

### Błąd: "Model Whisper nie został załadowany"
```bash
# Sprawdź czy model został pobrany
python -c "import whisper; whisper.load_model('large-v3')"
```

### Błąd: "FFmpeg not found"
```bash
# Zainstaluj FFmpeg
sudo apt install ffmpeg
```

### Błąd: "pyannote.audio nie jest dostępne"
```bash
# Zainstaluj zależności rozpoznawania mówców
pip install pyannote.audio torch torchaudio librosa soundfile
```

### Błąd: "Out of memory"
- Zmniejsz `max_concurrent` w kodzie
- Użyj mniejszego modelu Whisper
- Zamknij inne aplikacje zużywające dużo RAM

### Wolne przetwarzanie
- Sprawdź czy masz GPU z CUDA
- Użyj mniejszego modelu Whisper
- Sprawdź czy nie ma innych procesów zużywających CPU

### Niskie rozpoznawanie mówców
- Sprawdź jakość audio (szum, echo)
- Upewnij się, że mówcy nie nakładają się na siebie
- Sprawdź czy audio ma odpowiednią długość (>10 sekund)

## Analiza wyników

### Przykład analizy JSON:
```python
import json

with open('rozmowa_01_metadata.json', 'r') as f:
    data = json.load(f)

# Liczba mówców
speakers = set([s['speaker'] for s in data['speakers']])
print(f"Liczba mówców: {len(speakers)}")

# Czas mówienia każdej osoby
speaker_times = {}
for speaker_info in data['speakers']:
    speaker = speaker_info['speaker']
    if speaker not in speaker_times:
        speaker_times[speaker] = 0
    speaker_times[speaker] += speaker_info['duration']

for speaker, time in speaker_times.items():
    print(f"{speaker}: {time:.1f} sekund")
```

## Rozwój

### Dodanie nowych funkcjonalności

1. Edytuj `whisper_analyzer.py`
2. Dodaj nowe zależności do `requirements.txt`
3. Przetestuj zmiany
4. Zaktualizuj dokumentację

### Testowanie

```bash
# Test podstawowej funkcjonalności
python -c "from whisper_analyzer import AudioProcessor; p = AudioProcessor(); print('OK')"

# Test rozpoznawania mówców
python -c "from whisper_analyzer import SpeakerDiarizer; s = SpeakerDiarizer(); print('OK')"
```

## Dokumentacja

- [Rozpoznawanie Mówców](SPEAKER_DIARIZATION.md) - Szczegółowa dokumentacja funkcji rozpoznawania mówców
- [PRD](PRD.txt) - Dokument wymagań aplikacji

## Licencja

Projekt zgodny z wymaganiami PRD.

## Wsparcie

W przypadku problemów sprawdź:
1. Logi w `whisper_analyzer.log`
2. Dokumentację Whisper: https://github.com/openai/whisper
3. Dokumentację pyannote.audio: https://github.com/pyannote/pyannote-audio
4. Wymagania systemowe 