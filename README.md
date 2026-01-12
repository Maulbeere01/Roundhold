# Roundhold – Installations- und Einrichtungsanleitung

Diese Dokumentation beschreibt die Installation von Python, die Einrichtung der Entwicklungsumgebung sowie den Start des Projekts. Die Anleitung deckt sowohl Windows als auch Linux (bzw. WSL2) ab.

## 1. Voraussetzungen

### Python Installation
Für das Projekt wird **Python 3.12** benötigt.

> **Hinweis:** Es wird explizit Python 3.12 empfohlen, da neuere Versionen (z. B. 3.14) in Tests Kompatibilitätsprobleme mit Pygame hatten.

*   **Windows:**
    *   Download: [Python 3.12.0 (Windows x64)](https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe)
    *   **Wichtig:** Während der Installation muss die Option **"Add Python.exe to PATH"** aktiviert werden.
*   **Linux / WSL2:**
    *   Installation über den Paketmanager (z. B. `sudo apt install python3 python3-venv`).

---

## 2. Projekt klonen

Repository lokal klonen:

```bash
# Über HTTPS
git clone https://gitlab.reutlingen-university.de/wehrberb/Roundhold.git

# ODER über SSH
git clone ssh://git@gitlab.reutlingen-university.de:2224/wehrberb/Roundhold.git

# Dann:
cd Roundhold
```

---

## 3. Entwicklungsumgebung einrichten (Virtual Environment)

Zur Isolierung der Abhängigkeiten wird ein Virtual Environment (`.venv`) verwendet.

### Erstellung und Aktivierung

1.  **Erstellung des Environments:**
    ```bash
    # Windows und Linux
    python -m venv .venv
    ```
    *(Sollte unter Linux `python` nicht auf Version 3.xx zeigen, sollte man `python3` verwenden.)*

2.  **Aktivierung des Environments:**

    *   **Linux / WSL / Git Bash:**
        ```bash
        source .venv/bin/activate
        ```

    *   **Windows (CMD):**
        ```cmd
        .venv/Scripts/activate.bat
        ```

    *   **Windows (PowerShell):**
        ```powershell
        .venv/Scripts/Activate.ps1
        ```
        
        **Hinweis:** Falls Fehler "Ausführung von Skripts ist auf diesem System deaktiviert":
        ```powershell
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
        ```

### Konfiguration in VS Code
Falls Visual Studio Code genutzt wird, muss der korrekte Python-Interpreter für das Projekt ausgewählt werden:

1.  Eine beliebige `.py`-Datei im Projekt öffnen.
2.  In der unteren Statusleiste auf die angezeigte Python-Version klicken.
3.  Den Interpreter auswählen, der auf das virtuelle Environment verweist:
    *   Linux/WSL: `./.venv/bin/python`
    *   Windows: `./.venv/Scripts/python.exe`

Nach erfolgter Auswahl wird das Environment in neuen Terminals innerhalb von VS Code automatisch aktiviert.

---

## 4. Abhängigkeiten installieren

Nach der Aktivierung des Environments (erkennbar am Präfix `(.venv)` in der Konsole) erfolgt die Installation der Pakete.

**Hinweis:** Die Reihenfolge der Installation der lokalen Module (`shared`, `server`, `client`) bitte einhalten.

```bash
# 1. Entwickler-Tools und Pygame installieren
pip install -r requirements-dev.txt

# 2. Projekt-Module installieren (Reihenfolge beachten!)
pip install -e ./shared
pip install -e ./server
pip install -e ./client
```

---

## 5. Systemprüfung

Zur Verifizierung der Installation können folgende Befehle genutzt werden:

```bash
# Prüfen der Python-Version (Sollte 3.12.x anzeigen)
python --version

# Prüfen, ob pip korrekt installiert ist
pip --version
```

---

## 6. Spiel starten

### Windows (PowerShell)
Zum Starten steht ein PowerShell-Skript bereit:

```powershell
./run_game.ps1
```

**Fehlerbehebung:**
Sollte die Ausführung von Skripten blockiert sein, kann das Skript mit folgendem Befehl gestartet werden:
```powershell
powershell -ExecutionPolicy Bypass -File ./run_game.ps1
```

### Linux / WSL (Bash)

```bash
./run_game.sh
```

---

## 7. Tests ausführen

Um die Testsuite (163 Tests) auszuführen:

```bash
python -m pytest tests/
```

## Zusammenfassung der Befehle

| Ziel | Befehl (Linux/WSL) | Befehl (Windows PowerShell) |
| :--- | :--- | :--- |
| **Venv erstellen** | `python3 -m venv .venv` | `python -m venv .venv` |
| **Venv aktivieren** | `source .venv/bin/activate` | `./.venv/Scripts/Activate.ps1` |
| **Abhängigkeiten** | `pip install -r requirements-dev.txt` | *(identisch)* |
| **Module linken** | `pip install -e ./shared` (usw.) | *(identisch)* |
| **Starten** | `./run_game.sh` | `./run_game.ps1` |