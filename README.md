# Installations- und Einrichtungsanleitung (macOS)

## 1. Voraussetzungen

### Python Installation

Für das Projekt wird **Python 3.12** benötigt.

> **Hinweis:** Es wird explizit Python 3.12 empfohlen, da neuere Versionen (z. B. 3.14) in Tests Kompatibilitätsprobleme mit Pygame hatten.

## 2. Projekt klonen

```bash
# Über HTTPS
git clone https://gitlab.reutlingen-university.de/wehrberb/Roundhold.git

# ODER über SSH
git clone ssh://git@gitlab.reutlingen-university.de:2224/wehrberb/Roundhold.git

# Dann:
cd Roundhold
```

---

## 3. Entwicklungsumgebung einrichten

1. **Erstellung des Environments:**

   ```bash
   python3.12 -m venv .venv
   ```

2. **Aktivierung des Environments:**

   ```bash
   source .venv/bin/activate
   ```

### Konfiguration in VS Code

Falls Visual Studio Code genutzt wird, muss der korrekte Python-Interpreter für das Projekt ausgewählt werden:

1. Eine beliebige `.py`-Datei im Projekt öffnen.
2. In der unteren Statusleiste auf die angezeigte Python-Version klicken.
3. Den Interpreter auswählen, der auf das virtuelle Environment verweist: `./.venv/bin/python`

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

## 5. prüfen

```bash
# Prüfen der Python-Version (Sollte 3.12.x anzeigen)
python --version

# Prüfen, ob pip korrekt installiert ist
pip --version
```

---

## 6. Spiel starten

### Via Shell-Skript

```bash
./run_game.sh
```

Falls das Skript nicht ausführbar ist:

```bash
chmod +x run_game.sh
./run_game.sh
```

### Manueller Start (ohne Shell-Skript)

Falls das Shell-Skript nicht verwendet werden soll, kann das Spiel auch manuell gestartet werden:

```bash
# Sicherstellen, dass das venv aktiviert ist
source .venv/bin/activate

# Server starten (in einem separaten Terminal)
python -m server

# Client starten (in einem anderen Terminal)
python -m client
```

---

## 7. Tests ausführen


```bash
python -m pytest tests/
```

---

## Zusammenfassung der Befehle

| Ziel | Befehl |
| :--- | :--- |
| **Venv erstellen** | `python3.12 -m venv .venv` |
| **Venv aktivieren** | `source .venv/bin/activate` |
| **Abhängigkeiten** | `pip install -r requirements-dev.txt` |
| **Module linken** | `pip install -e ./shared && pip install -e ./server && pip install -e ./client` |
| **Starten** | `./run_game.sh` |
| **Manuell starten** | `python -m server` / `python -m client` |
