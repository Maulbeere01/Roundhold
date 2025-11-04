**Projet aufsetzen**

Ich mach das ganze mit VSC, da bessere WSL2 Unterstützung, je nach IDE müsst ihr den Interpreter anders auswählen.

Wenn keine WSL2 oder Python, das zuerst installieren.

**Alles auf der WSL machen:**
1. Projekt klonen
```bash
    git clone ssh://git@gitlab.reutlingen-university.de:2224/wehrberb/Roundhold.git
    cd Roundhold
```
2. Umgebung
```bash
    python -m venv .venv
```

3.  **Interpreter auswählen (in VS Code):**
    * Öffne eine beliebige `.py`-Datei
    * Klicke unten rechts in der blauen Leiste auf die Python-Version.
    * Es sollte der Interpreter: **`./.venv/bin/python`** ausgewählt sein.
    * Wir brauchen den Interpreter aus roundhold/.venv/bin/python

4. In VSC sollte automatisch das env aktiv sein, ansonsten:
```bash
    source .venv/bin/activate
```

5. Dependencies

    **Dev Tools:**
    ```bash
    pip install -r requirements-dev.txt
    ```
    **Installiere die Projekt Pakete (DIE REIHENFOLGE IST WICHTIG):**
    ```bash
    # 1.
    pip install -e ./shared
    
    # 2. 
    pip install -e ./server

    # 3.
    pip install -e ./client
    ```

6. Git Hooks aktivieren
    ```bash
    pre-commit install
    ```
