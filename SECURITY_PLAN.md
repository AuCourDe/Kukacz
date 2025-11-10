# Plan poprawek bezpieczeństwa – Whisper Analyzer

## Cele
- Zablokować możliwość wpływania transkrypcji na instrukcje systemowe modeli językowych (prompt injection).
- Zapewnić walidację odpowiedzi modeli przed zapisaniem wyników.
- Utrzymać integralność i poufność danych audio oraz logów.

## Kroki realizacji
1. **Wzmocnienie promptu systemowego**
   - Dodać stały kontekst systemowy w `OllamaAnalyzer`, który explicite zabrania wykonywania poleceń z transkrypcji.
   - Umieścić treść rozmowy w polu danych (np. JSON) i jasno oznaczyć, że to dane wejściowe, nie instrukcje.

2. **Sanityzacja i walidacja transkryptów**
   - Normalizować transkrypcję przed wysłaniem (usunąć kontrolne znaki, ograniczyć długość).
   - Rejestrować nietypowe wzorce (np. frazy “ignore previous instructions”) i oznaczać analizę do ręcznej weryfikacji.

3. **Walidacja odpowiedzi modelu**
   - Wymusić format JSON i zwracać błąd, jeśli wynik nie przejdzie walidacji schematu.
   - W przypadku niepowodzenia zapisywać komunikat w logach i oznaczać plik jako “analiza nie powiodła się”.

4. **Monitorowanie i audyt**
   - Logować wykryte próby prompt injection z identyfikatorem pliku.
   - Uzupełnić testy automatyczne o scenariusze z wstrzykiwaniem instrukcji.

5. **Procedury operacyjne**
   - Zaktualizować dokumentację (README/PRD) o nowe zasady obsługi.
   - Upewnić się, że środowiska (lokalne, produkcyjne) mają ustawione zmienne środowiskowe wymuszające nowe zabezpieczenia (np. `ENABLE_STRICT_VALIDATION=true`).

## Wyniki
- Po wdrożeniu przeprowadzić testy e2e oraz scenariusze z próbą wstrzyknięcia.
- Wyniki testów zapisać w pliku `test20251110.txt`.
- Po pozytywnych testach zgłosić zmiany (PR/commit).

