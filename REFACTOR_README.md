# Refactor Whisper Analyzer - Nowa Struktura

## Przegląd zmian

Kod został podzielony na logiczne moduły zgodnie z zasadami Single Responsibility Principle. Każdy moduł ma jasno określoną odpowiedzialność i jest niezależny od innych.

## Struktura plików

### 1. `main.py` - Główny punkt wejścia
- Inicjalizacja wszystkich komponentów
- Uruchomienie aplikacji
- Obsługa sygnałów zatrzymania

### 2. `file_loader.py` - Wczytywanie plików
- **AudioFileValidator**: Walidacja plików MP3
- **AudioFileLoader**: Wczytywanie plików z folderu wejściowego
- **FileWatcher**: Obserwator zmian w folderze
- **FileWatcherManager**: Zarządzanie obserwatorem

### 3. `speech_transcriber.py` - Transkrypcja mowy
- **WhisperTranscriber**: Transkrypcja audio na tekst
- Ładowanie modelu Whisper
- Obsługa błędów i ponownych prób
- Szyfrowanie tymczasowych plików

### 4. `speaker_diarizer.py` - Rozpoznawanie mówców
- **SpeakerDiarizer**: Zaawansowane rozpoznawanie z pyannote.audio
- **SimpleSpeakerDiarizer**: Prosty algorytm na podstawie segmentów
- Obsługa różnych metod autoryzacji
- Automatyczne przełączanie między algorytmami

### 5. `content_analyzer.py` - Analiza treści
- **ContentAnalyzer**: Integracja z Ollama
- Analiza treści rozmów z promptami z konfiguracji
- Analiza wzorców mówców
- Analiza sentymentu
- Filtrowanie rozumowania modeli

### 6. `reasoning_filter.py` - Filtrowanie rozumowania
- **ReasoningFilter**: Wykrywanie i filtrowanie tagów rozumowania
- Obsługa różnych tagów XML (<think>, <reasoning>, etc.)
- Zapisywanie rozumowania do osobnych plików
- Konfigurowalne tagi rozumowania

### 7. `result_saver.py` - Zapisywanie wyników
- **ResultSaver**: Zapisywanie transkrypcji i analiz
- Formatowanie wyników
- Sprawdzanie czy pliki są już przetworzone
- Zapisywanie rozumowania do osobnych plików

### 8. `audio_processor.py` - Główny koordynator
- **AudioProcessor**: Integracja wszystkich komponentów
- Zarządzanie pipeline przetwarzania
- Kontrola równoległości
- Koordynacja między modułami
- Używanie konfiguracji z config.py

## Korzyści z refactoru

### 1. Modularność
- Każdy moduł ma jedną odpowiedzialność
- Łatwe testowanie poszczególnych komponentów
- Możliwość wymiany implementacji

### 2. Czytelność
- Jasna struktura kodu
- Komentarze w formie bezokoliczników
- Szczegółowe opisy funkcji

### 3. Utrzymywalność
- Łatwe dodawanie nowych funkcjonalności
- Izolacja błędów
- Proste debugowanie

### 4. Skalowalność
- Możliwość dodawania nowych modułów
- Elastyczna architektura
- Rozszerzalne API

## Uruchomienie

```bash
python3 main.py
```

## Konfiguracja

Wszystkie ustawienia znajdują się w `config.py`:

### Ustawienia kluczowe
- Model Whisper: `WHISPER_MODEL = "large-v3"`
- Token autoryzacji: `SPEAKER_DIARIZATION_TOKEN`
- Model Ollama: `OLLAMA_MODEL = "gemma3:12b"`

### Ustawienia Ollama
- Prompty do analizy treści, sentymentu i wzorców mówców
- Parametry generowania (temperature, top_p, max_tokens)
- Filtrowanie rozumowania modeli

### Ustawienia filtrowania rozumowania
- `SAVE_REASONING = False` - czy zapisywać rozumowanie
- `REASONING_TAGS` - tagi XML do wykrywania rozumowania

## Logi

Aplikacja generuje szczegółowe logi w pliku `whisper_analyzer.log` oraz wyświetla je w konsoli.

## Struktura folderów

```
Whisper/
├── main.py                 # Główny punkt wejścia
├── config.py               # Plik konfiguracyjny
├── audio_processor.py      # Główny koordynator
├── file_loader.py          # Wczytywanie plików
├── speech_transcriber.py   # Transkrypcja mowy
├── speaker_diarizer.py     # Rozpoznawanie mówców
├── content_analyzer.py     # Analiza treści
├── reasoning_filter.py     # Filtrowanie rozumowania
├── result_saver.py         # Zapisywanie wyników
├── ollama_analyzer.py      # Integracja z Ollama
├── input/                  # Pliki wejściowe MP3
├── output/                 # Wyniki transkrypcji
└── checkpoint2/            # Backup kodu
```

## Komentarze i dokumentacja

- Wszystkie komentarze w formie bezokoliczników
- Szczegółowe opisy funkcji na początku każdej klasy
- Jasne wyjaśnienia logiki działania
- Usunięte oczywiste komentarze 