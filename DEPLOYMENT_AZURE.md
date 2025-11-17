# Instrukcja Deploymentu Whisper Analyzer na Azure Ubuntu 24.04

## Spis treści
1. [Wymagania systemowe](#1-wymagania-systemowe)
2. [Instalacja aplikacji](#2-instalacja-aplikacji)
3. [Konfiguracja zmiennych środowiskowych](#3-konfiguracja-zmiennych-środowiskowych)
4. [Token HuggingFace](#4-token-huggingface)
5. [Konfiguracja Azure - Otwieranie portów](#5-konfiguracja-azure---otwieranie-portów)
6. [Uruchomienie aplikacji](#6-uruchomienie-aplikacji)
7. [Konfiguracja w kodzie](#7-konfiguracja-w-kodzie)
8. [Systemd Service (opcjonalnie)](#8-systemd-service-opcjonalnie)
9. [Monitoring i logi](#9-monitoring-i-logi)
10. [Rozwiązywanie problemów](#10-rozwiązywanie-problemów)

---

## 1. Wymagania systemowe

### Minimalne wymagania:
- **System operacyjny**: Ubuntu 24.04 LTS
- **Python**: 3.12+ (zainstalowany domyślnie w Ubuntu 24.04)
- **RAM**: minimum 4 GB (rekomendowane 8 GB+)
- **Dysk**: minimum 30 GB wolnego miejsca (modele Whisper + cache)
- **FFmpeg**: do przetwarzania plików audio
- **Ollama**: opcjonalnie, jeśli włączona analiza LLM

### Rozmiar Azure VM:
- **Dla CPU-only**: Standard_B2s (2 vCPU, 4 GB RAM) lub większy
- **Dla GPU (opcjonalnie)**: Standard_NC6s_v3 lub podobny z GPU NVIDIA

---

## 2. Instalacja aplikacji

### 2.1 Szybka instalacja (gotowe komendy)

Wszystkie komendy w jednym pliku: zobacz `deployment.txt` lub wykonaj:

```bash
# Przejście do folderu projektów i klonowanie repozytorium
cd ~/projekty
git clone https://github.com/AuCourDe/Kukacz.git Whisper
cd Whisper

# Instalacja zależności systemowych
sudo apt update
sudo apt install -y python3 python3-pip python3-venv ffmpeg git

# Instalacja Ollama (jeśli potrzebne - opcjonalnie)
curl -fsSL https://ollama.com/install.sh | sh

# Utworzenie i aktywacja wirtualnego środowiska + instalacja requirements
python3 -m venv venv_python310_new
source venv_python310_new/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Konfiguracja środowiska (kopiuj wzorzec i edytuj)
cp env.example .env
nano .env  # lub użyj vim/vi
```

### 2.2 Instalacja Ollama (opcjonalnie)

Ollama jest wymagane tylko jeśli `ENABLE_OLLAMA_ANALYSIS=true` w `.env`.

```bash
# Instalacja Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Uruchomienie Ollama jako serwis (w tle)
ollama serve

# Pobranie wymaganego modelu (np. gemma3:12b)
ollama pull gemma3:12b

# Sprawdzenie dostępnych modeli
ollama list
```

**Uwaga**: Jeśli uruchamiasz Ollama w tle, dodaj do `.env`:
```env
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 3. Konfiguracja zmiennych środowiskowych

### 3.1 Podstawowa konfiguracja

Skopiuj wzorzec i edytuj:
```bash
cp env.example .env
nano .env
```

### 3.2 Najważniejsze zmienne (minimalna konfiguracja)

```env
# Model Whisper (dla CPU użyj 'base' lub 'small')
WHISPER_MODEL=base

# Rozpoznawanie mówców (true wymaga tokenu HF - patrz sekcja 4)
ENABLE_SPEAKER_DIARIZATION=false

# Analiza Ollama (false jeśli nie używasz Ollama)
ENABLE_OLLAMA_ANALYSIS=false

# Konfiguracja webowego interfejsu (WAŻNE dla Azure!)
WEB_HOST=0.0.0.0        # MUSI być 0.0.0.0 dla dostępu z zewnątrz
WEB_PORT=8080           # Port, który otworzysz w Azure (domyślnie 8080)

# Hasło i login (ZMIEŃ PRZY WDROŻENIU!)
WEB_LOGIN=admin
WEB_PASSWORD=TwojeSilneHaslo123!

# Klucz sesji (ZMIEŃ!)
WEB_SECRET_KEY=losowy_klucz_co_ma_minimum_32_znaki
```

### 3.3 Kompletny przykład .env dla produkcji (CPU-only)

```env
# Modele
WHISPER_MODEL=base
ENABLE_SPEAKER_DIARIZATION=false
ENABLE_OLLAMA_ANALYSIS=false

# Interfejs webowy
WEB_HOST=0.0.0.0
WEB_PORT=8080
WEB_LOGIN=admin
WEB_PASSWORD=ZmienToHaslo123!
WEB_SECRET_KEY=twoj_losowy_klucz_sesji_minimum_32_znaki_dlugie

# Foldery
INPUT_FOLDER=input
OUTPUT_FOLDER=output
PROCESSED_FOLDER=processed
MODEL_CACHE_DIR=models

# Logi
LOG_LEVEL=INFO
LOG_FILE=whisper_analyzer.log

# Przetwarzanie
MAX_CONCURRENT_PROCESSES=1
```

---

## 4. Token HuggingFace

### Czy potrzebny jest token?

**Token HuggingFace jest wymagany TYLKO jeśli:**
- `ENABLE_SPEAKER_DIARIZATION=true` w `.env`
- Chcesz używać precyzyjnego rozpoznawania mówców (pyannote.audio)

**Jeśli `ENABLE_SPEAKER_DIARIZATION=false`:**
- Aplikacja używa heurystycznego algorytmu (nie wymaga tokenu)
- Działa od razu bez konfiguracji
- Mniej precyzyjne, ale szybsze

### Jak uzyskać token (jeśli potrzebny):

1. **Zaloguj się na HuggingFace**:
   - Wejdź na https://huggingface.co/
   - Utwórz konto lub zaloguj się

2. **Zaakceptuj licencje modeli**:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
   - Kliknij "Agree and access repository" na każdym

3. **Utwórz token**:
   - Settings → Access Tokens → New token
   - Nazwa: np. "whisper-analyzer"
   - Typ: **Read** (wystarczy)
   - Skopiuj token (zaczyna się od `hf_...`)

4. **Dodaj do `.env`**:
   ```env
   SPEAKER_DIARIZATION_TOKEN=hf_xxx_twoj_token_tutaj
   ENABLE_SPEAKER_DIARIZATION=true
   ```

---

## 5. Konfiguracja Azure - Otwieranie portów

### 5.1 Porty wymagane

Aplikacja używa **JEDNEGO portu** - portu Flask (domyślnie `8080`).

**WAŻNE**: Nie musisz otwierać osobnego portu dla "backendu" - Flask **JEST** backendem i frontendem w jednym. Aplikacja działa jako monolityczny serwer webowy.

### 5.2 Otwieranie portu w Azure Portal

1. **Przejdź do Azure Portal**:
   - Zaloguj się na https://portal.azure.com
   - Znajdź swoją maszynę wirtualną (VM)

2. **Konfiguracja Network Security Group (NSG)**:
   - W sekcji **Networking** VM
   - Kliknij **Inbound port rules**
   - Kliknij **Add inbound port rule**

3. **Dodaj regułę dla portu 8080**:
   ```
   Name: whisper-http
   Priority: 1000
   Source: Any (lub konkretny IP)
   Service: Custom
   Destination port ranges: 8080
   Protocol: TCP
   Action: Allow
   ```

4. **Zapisz regułę**

### 5.3 Otwieranie portu przez Azure CLI

```bash
# Zainstaluj Azure CLI jeśli nie masz
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Logowanie
az login

# Pobierz nazwę grupy zasobów i VM
RESOURCE_GROUP="nazwa-grupy-zasobow"
VM_NAME="nazwa-vm"
NSG_NAME=$(az vm show --resource-group $RESOURCE_GROUP --name $VM_NAME --query networkProfile.networkInterfaces[0].id -o tsv | xargs -I {} az network nic show --ids {} --query networkSecurityGroup.id -o tsv | xargs basename)

# Dodaj regułę
az network nsg rule create \
  --resource-group $RESOURCE_GROUP \
  --nsg-name $NSG_NAME \
  --name whisper-http \
  --priority 1000 \
  --protocol Tcp \
  --destination-port-ranges 8080 \
  --access Allow \
  --direction Inbound
```

### 5.4 Sprawdzenie zapory systemowej (Ubuntu Firewall)

```bash
# Sprawdź czy ufw jest aktywny
sudo ufw status

# Jeśli aktywny, otwórz port 8080
sudo ufw allow 8080/tcp

# Weryfikacja
sudo ufw status
```

### 5.5 Adres aplikacji

Po otwarciu portu, aplikacja będzie dostępna pod adresem:
```
http://<publiczne-ip-azure-vm>:8080
```

**Publiczne IP znajdziesz w Azure Portal**:
- VM → Overview → Public IP address

---

## 6. Uruchomienie aplikacji

### 6.1 Uruchomienie przez skrypt run.sh (REKOMENDOWANE)

Skrypt `run.sh` automatycznie:
- Aktywuje wirtualne środowisko
- Instaluje zależności (jeśli potrzeba)
- Uruchamia aplikację webową (Flask + Backend)

```bash
cd ~/projekty/Whisper
chmod +x run.sh
./run.sh
```

### 6.2 Ręczne uruchomienie

```bash
cd ~/projekty/Whisper
source venv_python310_new/bin/activate
python3 -m app.web_server
```

### 6.3 Uruchomienie w tle (z nohup)

```bash
cd ~/projekty/Whisper
source venv_python310_new/bin/activate
nohup python3 -m app.web_server > web_server.log 2>&1 &
```

Sprawdzenie procesu:
```bash
ps aux | grep web_server
```

Zatrzymanie:
```bash
pkill -f "app.web_server"
```

### 6.4 Uruchomienie z systemd (produkcja)

Patrz sekcja [8. Systemd Service](#8-systemd-service-opcjonalnie)

---

## 7. Konfiguracja w kodzie

### 7.1 Gdzie zmieniać konfigurację?

**Główny plik konfiguracyjny**: `app/config.py`

**NIE edytuj bezpośrednio `app/config.py` jeśli nie musisz!**

Zamiast tego używaj pliku **`.env`** - wszystkie zmienne są odczytywane przez `config.py` z zmiennych środowiskowych.

### 7.2 Zmienne konfiguracyjne (plik `app/config.py`)

Wszystkie zmienne można nadpisać przez `.env`:

| Zmienna w kodzie | Zmienna .env | Opis |
|-----------------|--------------|------|
| `WEB_HOST` | `WEB_HOST` | Host Flask (0.0.0.0 dla zewnętrznego dostępu) |
| `WEB_PORT` | `WEB_PORT` | Port Flask |
| `WEB_LOGIN` | `WEB_LOGIN` | Login do panelu webowego |
| `WEB_PASSWORD` | `WEB_PASSWORD` | Hasło do panelu webowego |
| `WHISPER_MODEL` | `WHISPER_MODEL` | Model Whisper (base/small/medium/large-v3) |
| `OLLAMA_MODEL` | `OLLAMA_MODEL` | Model Ollama |
| `OLLAMA_BASE_URL` | `OLLAMA_BASE_URL` | URL serwera Ollama |
| `ENABLE_SPEAKER_DIARIZATION` | `ENABLE_SPEAKER_DIARIZATION` | Włącz/wyłącz rozpoznawanie mówców |
| `ENABLE_OLLAMA_ANALYSIS` | `ENABLE_OLLAMA_ANALYSIS` | Włącz/wyłącz analizę Ollama |

### 7.3 Zmiana domyślnych wartości w kodzie

Jeśli chcesz zmienić domyślne wartości w kodzie (nie przez .env):

1. Edytuj `app/config.py`
2. Znajdź odpowiednią zmienną, np.:
   ```python
   WEB_PORT: int = int(os.getenv("WEB_PORT", "8080"))
   ```
3. Zmień wartość domyślną:
   ```python
   WEB_PORT: int = int(os.getenv("WEB_PORT", "5000"))  # zmiana z 8080 na 5000
   ```

**Uwaga**: Zmiany w kodzie będą nadpisywane przez `.env`!

### 7.4 Właściwa kolejność nadpisywania

1. **Wartość w `.env`** (najwyższy priorytet)
2. **Wartość domyślna w `config.py`** (jeśli brak w .env)
3. **Hardkodowana wartość w kodzie** (tylko jeśli brak obu powyższych)

---

## 8. Systemd Service (opcjonalnie)

### 8.1 Utworzenie pliku service

```bash
sudo nano /etc/systemd/system/whisper-analyzer.service
```

### 8.2 Zawartość pliku service

```ini
[Unit]
Description=Whisper Analyzer Web Server
After=network.target

[Service]
Type=simple
User=azureuser
Group=azureuser
WorkingDirectory=/home/azureuser/projekty/Whisper
Environment="PATH=/home/azureuser/projekty/Whisper/venv_python310_new/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/home/azureuser/projekty/Whisper/venv_python310_new/bin/python -m app.web_server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Uwaga**: Zamień `azureuser` na swojego użytkownika i popraw ścieżki!

### 8.3 Aktywacja i uruchomienie

```bash
# Przeładowanie systemd
sudo systemctl daemon-reload

# Włączenie automatycznego startu
sudo systemctl enable whisper-analyzer

# Uruchomienie serwisu
sudo systemctl start whisper-analyzer

# Sprawdzenie statusu
sudo systemctl status whisper-analyzer

# Logi
sudo journalctl -u whisper-analyzer -f
```

---

## 9. Monitoring i logi

### 9.1 Logi aplikacji

```bash
# Główny plik logów (domyślnie)
tail -f ~/projekty/Whisper/whisper_analyzer.log

# Jeśli zmieniono w .env
tail -f $(grep LOG_FILE ~/projekty/Whisper/.env | cut -d'=' -f2)
```

### 9.2 Sprawdzenie czy aplikacja działa

```bash
# Sprawdzenie procesu
ps aux | grep web_server

# Sprawdzenie portu
netstat -tlnp | grep 8080
# lub
ss -tlnp | grep 8080

# Test HTTP
curl http://localhost:8080/login
```

### 9.3 Monitorowanie (opcjonalnie)

Utworzony został skrypt `monitor_web_server.sh` do monitorowania statusu co 2 minuty:

```bash
cd ~/projekty/Whisper
./monitor_web_server.sh > /dev/null 2>&1 &
```

Logi monitora:
```bash
tail -f ~/projekty/Whisper/web_server_monitor.log
```

---

## 10. Rozwiązywanie problemów

### 10.1 Aplikacja nie startuje

```bash
# Sprawdź logi
tail -50 ~/projekty/Whisper/whisper_analyzer.log

# Sprawdź czy .env istnieje
ls -la ~/projekty/Whisper/.env

# Sprawdź czy venv jest aktywny
which python3

# Test uruchomienia z verbose
cd ~/projekty/Whisper
source venv_python310_new/bin/activate
python3 -m app.web_server
```

### 10.2 Port już zajęty

```bash
# Znajdź proces używający portu 8080
sudo lsof -i :8080
# lub
sudo netstat -tlnp | grep 8080

# Zabij proces (UWAGA: zamień PID!)
sudo kill -9 <PID>
```

Albo zmień port w `.env`:
```env
WEB_PORT=5000
```

### 10.3 Błąd "ModuleNotFoundError: No module named 'flask'"

```bash
# Upewnij się, że venv jest aktywny
source ~/projekty/Whisper/venv_python310_new/bin/activate

# Zainstaluj zależności ponownie
pip install -r ~/projekty/Whisper/requirements.txt
```

### 10.4 Brak dostępu z zewnątrz (Azure)

1. **Sprawdź NSG w Azure Portal** - czy port 8080 jest otwarty
2. **Sprawdź ufw**:
   ```bash
   sudo ufw status
   sudo ufw allow 8080/tcp
   ```
3. **Sprawdź WEB_HOST w .env** - musi być `0.0.0.0`:
   ```env
   WEB_HOST=0.0.0.0
   ```
4. **Sprawdź publiczne IP VM** w Azure Portal
5. **Test lokalnie**:
   ```bash
   curl http://localhost:8080/login
   ```

### 10.5 Ollama nie działa

```bash
# Sprawdź czy Ollama działa
curl http://localhost:11434/api/tags

# Uruchom Ollama
ollama serve

# Sprawdź modele
ollama list

# W .env wyłącz analizę jeśli nie używasz
ENABLE_OLLAMA_ANALYSIS=false
```

### 10.6 Błąd z tokenem HuggingFace

```bash
# Wyłącz rozpoznawanie mówców jeśli nie masz tokenu
# W .env:
ENABLE_SPEAKER_DIARIZATION=false
```

---

## Podsumowanie - Szybki Start

1. **Sklonuj repo**: `cd ~/projekty && git clone https://github.com/AuCourDe/Kukacz.git Whisper`
2. **Zainstaluj**: `cd Whisper && python3 -m venv venv_python310_new && source venv_python310_new/bin/activate && pip install -r requirements.txt`
3. **Skonfiguruj**: `cp env.example .env && nano .env` (ustaw `WEB_HOST=0.0.0.0`, zmień hasło)
4. **Otwórz port 8080** w Azure NSG
5. **Uruchom**: `./run.sh` lub `python3 -m app.web_server`
6. **Dostęp**: `http://<publiczne-ip>:8080`

**Gotowe komendy w pliku `deployment.txt`!**

---

## Dodatkowe zasoby

- **GitHub Repo**: https://github.com/AuCourDe/Kukacz
- **Azure VM Documentation**: https://docs.microsoft.com/azure/virtual-machines/
- **Ollama Documentation**: https://ollama.com/docs
- **Flask Documentation**: https://flask.palletsprojects.com/

