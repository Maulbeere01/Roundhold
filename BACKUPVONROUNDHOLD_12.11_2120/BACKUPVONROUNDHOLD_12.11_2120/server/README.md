# Server-Architektur: Autoritative Simulation & Concurrency

 Der Server implementiert ein deterministisches Lockstep-Modell. Er ist die alleinige Autorität über den dynamischen Spielzustand, managed die Spielphasen und gewährleistet Thread-Sicherheit bei nebenläufigen Anfragen.

---

## Kernprinzipien

### Server-Autorität (Single Source of Truth)

- **Autoritative Zustandsverwaltung**: Der Server ist die einzige Quelle der Wahrheit für alle dynamischen Zustände:
  - Spieler-Leben und Gold
  - Turmpositionen und -upgrades
  - Einheiten-Queues für die nächste Welle
  
- **Client als Visualisierer**: Clients führen eine lokale Visualisierung derselben Welle aus, jedoch ohne Autorität. Abweichungen (z. B. durch Lags oder Render-Tickdrift) werden vom Client stillschweigend korrigiert, sobald der Server autoritative Ergebnisse liefert.

- **Deterministische Simulation**: Server und Client nutzen exakt denselben deterministischen Simulationskern aus `td_shared`. Der Server berechnet das autoritative Ergebnis, der Client spiegelt nur.

### Lockstep-Mechanismus

Der Server verwendet ein **Lockstep-Modell**, bei dem:
- Alle Spieleraktionen in der Vorbereitungsphase gesammelt werden
- Die Simulation deterministisch auf dem Server läuft
- Ergebnisse erst nach Abschluss der Simulation an Clients gesendet werden
- Clients ihre lokale Simulation synchronisieren, sobald autoritative Ergebnisse eintreffen

---

## Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                      gRPC Server Layer                      │
│  (GameRpcServer - Request/Response Handler)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Game State Manager                        │
│  (Thread-safe, autoritative Zustandsverwaltung)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Economy    │  │  Placement   │  │  Wave Queue  │       │
│  │   Manager    │  │   Service    │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐                                           │
│  │  Snapshot    │                                           │
│  │   Builder    │                                           │
│  └──────────────┘                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Round Manager                            │
│  (Phasen-Orchestrierung: Prepare → Combat → Repeat)         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Combat Simulation                          │
│  (Autoritative Simulation mit td_shared/simulation)         │
└─────────────────────────────────────────────────────────────┘
```

---
### Repo Strutkur

```
server/
├── src/
│   └── td_server/
│       ├── __init__.py          # Package-Exports
│       ├── main.py              # Entry Point
│       ├── core/                # Kern-Logik
│       │   ├── game_state_manager.py  # Autoritative Zustandsverwaltung
│       │   ├── round_manager.py      # Phasen-Orchestrierung
│       │   └── combat_sim.py          # Autoritative Simulation
│       ├── network/             # Netzwerk-Schicht
│       │   └── rpc_server.py     # gRPC Server & Handler
│       └── services/             # Service-Komponenten
│           ├── economy.py        # Gold & Leben-Verwaltung
│           ├── placement.py      # Turm-Platzierung
│           ├── wave_queue.py     # Einheiten-Queue
│           └── snapshot.py       # Simulations-Snapshot-Builder
└──  pyproject.toml               # Projekt-Konfiguration
```

---

## Phasen-Modell und Datenfluss

Der Server steuert zwei Hauptphasen, die sich in einem kontinuierlichen Zyklus wiederholen:

### 1. Vorbereitungsphase (Preparation Phase)

**Dauer**: Konfigurierbar (Standard: `PREP_SECONDS`)

**Client → Server Kommunikation**:
- Clients senden gRPC-Requests:
  - `BuildTower`: Turm platzieren
  - `SendUnits`: Einheiten für nächste Welle kaufen
- **Gatekeeper-Rolle**: Der Server validiert alle Anfragen:
  - **Gold-Validierung**: Reicht das Gold des Spielers?
  - **Platzierungs-Validierung**: Ist die Zielkachel bebaubar und der richtigen Spielfeldhälfte zugeordnet?
  - **Phasen-Validierung**: Sind Timing-/Rundenrestriktionen erfüllt?
- **Transaktionale Updates**: Nur nach erfolgreicher Validierung werden:
  - Gold abgezogen
  - Türme platziert
  - Einheiten zur Queue hinzugefügt

**Thread-Sicherheit**: Alle mutierenden Operationen sind durch `threading.Lock` geschützt.

### 2. Simulationsphase (Combat Phase)

**Ablauf**:

1. **Rundenstart (RoundStart)**:
   - Der Server friert den vorbereiteten Zustand ein:
     - Alle platzierten Türme
     - Alle gekauften Einheiten
   - Erstellt einen `SimulationData`-Snapshot
   - Sendet `RoundStart`-Nachricht an beide Clients

2. **Interne Simulation**:
   - Der Server startet seine eigene autoritative Simulation
   - Verwendet denselben deterministischen Kern aus `td_shared/simulation`
   - Führt `update_tick()` in einer Schleife aus, bis `is_simulation_complete()` true ergibt
   - Läuft in einem separaten Worker-Thread

3. **Rundenende (RoundResult)**:
   - Nach Abschluss der Simulation:
     - Aggregiert autoritative Ergebnisse (verlorene Leben, verdientes Gold)
     - Wendet Ergebnisse auf den GameState an
     - Räumt die Wave-Queue auf
   - Wartet auf `RoundAck` von beiden Clients (Bestätigung, dass Rendering abgeschlossen ist)
   - Sendet `RoundResult` an beide Clients
   - Clients passen ihre UI/Local-State stillschweigend an

**Kein Echtzeit-Streaming**: Während des Kampfes sendet der Server keine Frame-by-Frame-Updates. Die Simulation läuft vollständig serverseitig.

---

## Nebenläufigkeit und Thread-Sicherheit

gRPC verarbeitet eingehende RPC-Aufrufe in einem Thread-Pool. Der Server muss daher Requests von:
- Spieler A und Spieler B (gleichzeitig)
- Mehreren schnellen Klicks desselben Spielers (Dopelklick)

nebenläufig korrekt behandeln.

Die Klasse `GameStateManager` hält ein `threading.Lock`. Jede gRPC-Methode, die den Zustand ändert, muss:

1. Das Lock akquirieren (`with self._lock:`)
2. In einem unteilbaren, kritischen Abschnitt:
   - Den relevanten Zustand lesen
   - Die Validierung durchführen
   - Den Zustand schreiben (Gold abziehen, Turm platzieren)
3. Das Lock wieder freigeben

### Wichtige Regeln

- **Kritische Abschnitte klein halten**: Nur den minimal nötigen Code zwischen Lock-Akquisition und -Freigabe ausführen
- **Keine blockierenden I/O-Operationen im Lock**: Netzwerkzugriffe, Datei-I/O etc. sollten außerhalb des Locks erfolgen
- **Lock-freie Lesezugriffe**: Reine Lesezugriffe können lock-frei sein, sofern sie konsistente Snapshots verwenden

---

## API-Endpoints

### gRPC Service: `YourGameService`

#### `QueueForMatch` (Server-Streaming)

**Zweck**: Matchmaking und persistenter Event-Stream

**Ablauf**:
1. Client tritt der Warteschlange bei
2. Wenn 2+ Spieler in Queue: Match wird erstellt
3. Beide Clients erhalten `MatchFound`-Event mit:
   - Zugewiesene Player-ID ("A" oder "B")
   - Gegner-Name
   - Initialer `RoundStart` mit aktuellem Spielzustand
4. Persistenter Stream: Clients erhalten kontinuierlich Events:
   - `RoundStart`: Neue Runde beginnt
   - `RoundResult`: Runde beendet, autoritative Ergebnisse
   - `TowerPlaced`: Turm wurde von einem Spieler platziert

**Thread-Sicherheit**: Matchmaking-Operationen sind durch `_match_lock` geschützt.

#### `BuildTower` (Unary)

**Zweck**: Turm platzieren

**Validierungen**:
- Ausreichend Gold vorhanden?
- Platzierung gültig (bebaubare Kachel, richtige Spielfeldhälfte)?
- In Vorbereitungsphase?

**Thread-Sicherheit**: Verwendet `GameStateManager._lock` für atomare Gold-Abzug und Platzierung.

**Broadcast**: Bei erfolgreicher Platzierung wird `TowerPlaced`-Event an beide Clients gesendet.

#### `SendUnits` (Unary)

**Zweck**: Einheiten für nächste Welle kaufen

**Validierungen**:
- Ausreichend Gold für alle Einheiten?
- In Vorbereitungsphase?
- Gültige Einheiten-Typen?

**Thread-Sicherheit**: Verwendet `GameStateManager._lock` für atomare Gold-Abzug und Queue-Update.

**Spawn-Tick-Zuweisung**: `WaveQueue` weist automatisch deterministische Spawn-Ticks zu, falls nicht spezifiziert.

#### `RoundAck` (Unary)

**Zweck**: Client signalisiert, dass Rendering der Runde abgeschlossen ist

**Verwendung**: `RoundManager` wartet auf ACKs von beiden Spielern, bevor `RoundResult` gesendet wird.

**Timeout**: Konfigurierbar (`ROUND_ACK_TIMEOUT`), Standard: 30 Sekunden

---

## Services

### EconomyManager (`services/economy.py`)

**Zweck**: Verwaltung von Gold und Leben für beide Spieler

**Funktionen**:
- `get_gold(player_id)`: Aktuelles Gold abrufen
- `get_lives(player_id)`: Aktuelle Leben abrufen
- `spend_gold(player_id, amount)`: Gold ausgeben (mit Validierung)
- `add_gold(player_id, amount)`: Gold hinzufügen
- `lose_lives(player_id, amount)`: Leben verlieren
- `apply_round_result(result)`: Runden-Ergebnisse anwenden

**Thread-Sicherheit**: Wird durch `GameStateManager._lock` geschützt.

### TowerPlacementService (`services/placement.py`)

**Zweck**: Validierung und Verwaltung von Turm-Platzierungen

**Funktionen**:
- `place_tower(...)`: Turm platzieren mit Validierung
- `get_sim_towers()`: Alle Türme als `SimTowerData`-Liste

**Validierungen**:
- Kachel ist bebaubar (`PlacementGrid.is_buildable()`)
- Kachel gehört zur richtigen Spielfeldhälfte
- Koordinaten-Transformation für Spieler B (gespiegelt)

**Datenstruktur**: `TowerPlacement` (Dataclass) speichert Platzierungen.

### WaveQueue (`services/wave_queue.py`)

**Zweck**: Queue für Einheiten der nächsten Welle mit deterministischer Spawn-Tick-Zuweisung

**Funktionen**:
- `prepare_units(player_id, units)`: Normalisiert Einheiten und berechnet Gesamtkosten
- `enqueue_units(units, tick_rate)`: Fügt Einheiten zur Queue hinzu, weist Spawn-Ticks zu
- `get_units()`: Gibt alle gequeueten Einheiten zurück
- `clear()`: Räumt Queue auf (nach Runde)

**Spawn-Tick-Logik**:
- Gruppiert Einheiten nach Route
- Bestimmt letzten Spawn-Tick pro Route aus bereits gequeueten Einheiten
- Weist neue Spawn-Ticks mit konfigurierbarem Delay zu (Standard: 0.5 * tick_rate)

### SnapshotBuilder (`services/snapshot.py`)

**Zweck**: Erstellt `SimulationData`-Snapshots für Rundenstart

**Funktionen**:
- `build(tick_rate)`: Erstellt vollständigen Snapshot mit:
  - Allen platzierten Türmen
  - Allen gequeueten Einheiten
  - Tick-Rate

**Verwendung**: Wird von `GameStateManager.get_current_state_snapshot()` aufgerufen.

---

## Core-Module

### GameStateManager (`core/game_state_manager.py`)

**Zweck**: Autoritative, thread-sichere Verwaltung des globalen Spielzustands

**Verantwortlichkeiten**:
- Enthält das zentrale `threading.Lock` für alle Zustandsänderungen
- Bietet API-Methoden für gRPC-Handler:
  - `build_tower()`: Turm bauen (atomar)
  - `add_units_to_wave()`: Einheiten zur Queue hinzufügen (atomar)
  - `get_current_state_snapshot()`: Snapshot für Rundenstart erstellen
  - `apply_round_result()`: Runden-Ergebnisse anwenden
  - `clear_wave_data()`: Queue nach Runde aufräumen

**Services**:
- `EconomyManager`: Gold & Leben
- `TowerPlacementService`: Turm-Platzierungen
- `WaveQueue`: Einheiten-Queue
- `SnapshotBuilder`: Snapshot-Erstellung

**PlacementGrids**: Separate Grids für Spieler A und B (gespiegelt).

### RoundManager (`core/round_manager.py`)

**Zweck**: Timer-gesteuerte Phasen-Orchestrierung (Prepare → Combat → Repeat)

**Haupt-Loop** (`run_game_loop()`):
1. **Vorbereitungsphase**:
   - Setzt `_in_preparation = True`
   - Wartet konfigurierbare Dauer (`prepare_duration_seconds`)
   - Währenddessen können Clients `BuildTower` und `SendUnits` senden

2. **Rundenstart**:
   - Erstellt Snapshot via `GameStateManager.get_current_state_snapshot()`
   - Sendet `RoundStart`-Event an beide Clients
   - Setzt `_in_preparation = False`

3. **Kampfphase**:
   - Startet Worker-Thread für Simulation
   - `_run_combat_and_callback()`:
     - Führt autoritative Simulation aus
     - Wendet Ergebnisse an
     - Räumt Queue auf
     - Speichert `RoundResult` als pending

4. **Rundenende**:
   - Wartet auf `RoundAck` von beiden Clients
   - Sendet `RoundResult`-Event an beide Clients
   - Wiederholt Zyklus

**Thread-Sicherheit**: Phasen-Status ist durch `_phase_lock` geschützt.

### CombatSim (`core/combat_sim.py`)

**Zweck**: Autoritative Kampf-Simulation

**Funktion**: `run_combat_simulation(simulation_data)`

**Ablauf**:
1. Erstellt `GameState` aus `SimulationData`
2. Führt Simulations-Loop aus:
   ```python
   while not game_state.is_simulation_complete():
       game_state.update_tick()
   ```
3. Aggregiert Ergebnisse:
   - Verlorene Leben pro Spieler
   - Verdientes Gold pro Spieler (basierend auf Kills)
4. Gibt `RoundResultData` zurück

**Determinismus**: Verwendet exakt denselben Simulationskern wie Client (`td_shared/simulation`).

### GameRpcServer (`network/rpc_server.py`)

**Zweck**: gRPC Server-Implementierung

**Komponenten**:
- `GameRpcServer`: gRPC Servicer-Implementierung
- `serve()`: Server-Bootstrap-Funktion

**Initialisierung**:
1. Erstellt `GameStateManager`
2. Erstellt `RoundManager`
3. Erstellt `GameRpcServer`-Instanz
4. Startet gRPC Server mit Thread-Pool
5. Startet Round-Loop (lazy, beim ersten Match)

**Matchmaking**:
- Verwaltet Warteschlange (`_waiting_clients`)
- Matched Spieler, wenn 2+ in Queue
- Weist Player-IDs zu ("A" und "B")
- Startet Round-Loop beim ersten Match

**Event-Streaming**:

Das Event-Streaming-System ermöglicht eine asynchrone, thread-sichere Kommunikation zwischen Server-Komponenten und Client-Streams:

- **Outbox-Prinzip**: Jeder Client hat eine eigene `outbox` (Python-Liste von `MatchEvent`-Objekten), die als Puffer zwischen Event-Produzenten (RoundManager, RPC-Handler) und Event-Consumer (QueueForMatch-Stream) dient. Diese Outbox wird beim Matchmaking erstellt (Zeile 100 in `rpc_server.py`) und bleibt während der gesamten Match-Dauer bestehen.

- **Event-Produktion**: Verschiedene Server-Komponenten pushen Events in die Outboxes:
  - **RoundManager** (Zeilen 79-81, 116-118): Pusht `RoundStart`-Events zu Rundenbeginn und `RoundResult`-Events nach Rundenende in beide Client-Outboxes
  - **GameRpcServer.BuildTower** (Zeilen 59-61): Broadcastet `TowerPlaced`-Events an beide Clients, wenn ein Turm platziert wird
  - **Matchmaking** (Zeilen 115-120): Fügt initiale `MatchFound`-Events hinzu

- **Event-Signalisierung**: Nach dem Hinzufügen eines Events wird ein `threading.Event` gesetzt (`ev.set()`), um den wartenden Stream-Thread zu wecken. Dies ermöglicht sofortige Reaktion auf neue Events, ohne ständiges Polling.

- **Event-Consumption**: Der `QueueForMatch`-Stream (Zeilen 141-151) läuft in einem persistenten Loop:
  - Wartet auf das Signal-Event (`ready.wait(timeout=1.0)`)
  - Leert die Outbox (`while outbox: ... outbox.pop(0)`)
  - Streamt jedes Event via `yield` an den Client
  - Setzt das Event zurück (`ready.clear()`) für das nächste Signal

- **Thread-Sicherheit**: Die Outbox-Operationen sind thread-sicher, da:
  - `RoundManager` läuft in einem separaten Thread
  - gRPC-Handler laufen im gRPC Thread-Pool
  - `QueueForMatch` läuft im Stream-Thread
  - Die Outbox-Liste wird durch das `_match_lock` geschützt (bei Matchmaking) und durch die sequenzielle Natur der Event-Signalisierung (bei Round-Events)

Dieses Design ermöglicht eine lose Kopplung zwischen Event-Produzenten und Consumern, ohne dass der Stream-Thread blockiert werden muss.

---

## Installation und Ausführung

```bash
python -m td_server.main
```

Der Server startet standardmäßig auf:
- **Host**: `0.0.0.0` (alle Interfaces)
- **Port**: `42069`

### Konfiguration

Die `serve()`-Funktion akzeptiert Parameter:
- `host`: Server-Host (Standard: `"0.0.0.0"`)
- `port`: Server-Port (Standard: `42069`)
- `max_workers`: gRPC Thread-Pool Größe (Standard: `10`)

### Logging

Der Server verwendet Python's `logging`-Modul mit INFO-Level. Logs enthalten:
- Server-Start/Stop
- Matchmaking-Events
- RPC-Requests und -Responses
- Phasen-Übergänge
- Simulations-Ergebnisse
