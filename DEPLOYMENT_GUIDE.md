# Instrukcja Wdrożenia Whisper Analyzer — Produkcja (CPU)

## 1. Wymagania systemowe

- Ubuntu 22.04+ (lub WSL2 na Windows 11)
- Python 3.12 (rekomendowany)
- FFmpeg (`sudo apt update && sudo apt install -y ffmpeg`)
- Ollama 0.12+ (`curl -fsSL https://ollama.com/install.sh | sh`)
- Dysk ~20 GB (modele Whisper + analiza)

## 2. Instalacja aplikacji

```bash
git clone <repo_url>
cd Whisper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Konfiguracja `.env`

Skopiuj wzorzec i uzupełnij wartości:

```bash
cp .env.example .env
```

Przykładowa konfiguracja (linia = `zmienna=wartość`):

```env
# Główne ścieżki
INPUT_FOLDER=input            # Folder z plikami wejściowymi
OUTPUT_FOLDER=output          # Folder wyników (transkrypcje, analizy)
PROCESSED_FOLDER=processed    # Folder przeniesionych nagrań
MODEL_CACHE_DIR=models        # Cache modeli Whisper

# Whisper
WHISPER_MODEL=base            # base/medium/large-v3 (CPU: base/small)
ENABLE_SPEAKER_DIARIZATION=false  # true = wymaga tokenu HF (Zob. sekcja 4)

# Ollama
OLLAMA_MODEL=gemma3:12b
OLLAMA_BASE_URL=http://localhost:11434

# Analiza
ENABLE_OLLAMA_ANALYSIS=true   # false aby pominąć analizę LLM

# Wykonanie
MAX_CONCURRENT_PROCESSES=1    # produkcja (CPU) – sekwencyjnie
LOG_LEVEL=INFO

# Opcjonalnie: plik logów (domyślnie whisper_analyzer.log)
# LOG_FILE=/var/log/whisper_analyzer.log
```

### Objaśnienia kluczowych opcji

| Zmienna                    | Wpływ / Zalecane wartości                                |
|---------------------------|-----------------------------------------------------------|
| `INPUT_FOLDER`            | Ścieżka wejściowa (relatywna lub absolutna).             |
| `OUTPUT_FOLDER`           | Gdzie trafią transkrypcje i analizy.                     |
| `PROCESSED_FOLDER`        | Nagrania po przetworzeniu.                               |
| `WHISPER_MODEL`           | `base` (CPU, szybki), `small`, `medium`, `large-v3` (GPU).|
| `ENABLE_SPEAKER_DIARIZATION` | `true` ⇒ używa PyAnnote (potrzebny token HF), `false` ⇒ heurystyka. |
| `OLLAMA_MODEL`            | Nazwa modelu dostępnego w `ollama list`.                 |
| `MAX_CONCURRENT_PROCESSES`| Liczba równoległych transkrypcji (`1` na CPU, >1 z GPU). |

## 4. Token HuggingFace (opcjonalny)

Chcesz dokładną diarizację mówców? Wykonaj:

1. Zaloguj się na HF, zaakceptuj licencje:
   - https://huggingface.co/pyannote/speaker-diarization-3.1  
   - https://huggingface.co/pyannote/segmentation-3.0
2. Utwórz token (`Settings → Access Tokens`), uprawnienie `read`.
3. Dodaj do `.env`:

```env
SPEAKER_DIARIZATION_TOKEN=hf_xxx
ENABLE_SPEAKER_DIARIZATION=true
```

Brak tokenu ⇒ aplikacja przełącza się na heurystyczny algorytm (`SimpleSpeakerDiarizer`).

## 5. Uruchomienie

### 5.1 Start jednorazowy

```bash
source .venv/bin/activate
APP_RUN_ONCE=true python -m app.main
```

### 5.2 Tryb ciągły (watcher)

```bash
source .venv/bin/activate
python -m app.main
# Przerwij Ctrl+C
```

### 5.3 Systemd (przykład)

`/etc/systemd/system/whisper.service`

```ini
[Unit]
Description=Whisper Analyzer
After=network.target

[Service]
Type=simple
User=whisper
WorkingDirectory=/opt/Whisper
Environment=PYTHONUNBUFFERED=1
Environment=CONFIG_ENV=/opt/Whisper/.env
ExecStart=/opt/Whisper/.venv/bin/python -m app.main
Restart=always

[Install]
WantedBy=multi-user.target
```

Potem:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now whisper
```

## 6. Weryfikacja działania

1. Umieść plik MP3 w `input/`.
2. Obserwuj `whisper_analyzer.log` – powinna pojawić się transkrypcja oraz analiza z flagą `integrity_alert` jeśli wykryto manipulację.
3. Wyniki w `output/`, nagranie trafia do `processed/`.

## 7. Aktualizacja / Deploy

```bash
git pull
source .venv/bin/activate
pip install -r requirements.txt
systemctl restart whisper   # jeśli używasz systemd
```

## 8. Najczęstsze wskazówki

- **CPU-only** – ustaw `WHISPER_MODEL=base` i `MAX_CONCURRENT_PROCESSES=1`.
- **GPU** – zainstaluj sterowniki CUDA, zwiększ `MAX_CONCURRENT_PROCESSES`, rozważ `large-v3`.
- **Brak Ollama** – ustaw `ENABLE_OLLAMA_ANALYSIS=false`.
- **Alerty bezpieczeństwa** – sprawdzaj `output/*. ANALIZA *.txt` (integrity flag + ostrzeżenia).



