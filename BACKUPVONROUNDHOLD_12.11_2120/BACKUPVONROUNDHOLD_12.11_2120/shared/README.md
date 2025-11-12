# Shared-Paket: Deterministische Simulation & Gemeinsame Definitionen

Enthält Code, der sowohl vom Server als auch vom Client verwendet wird, um sicherzustellen, dass beide Seiten identische deterministische Simulationen durchführen.

## Kernprinzipien

### Single Source of Truth für Spiel Logik

Das `td_shared`-Paket ist die single source of truth für:
- **Balance**: Türme- und Einheiten-Stats, Gold, Leben
- **Simulations Logik**: Deterministische Bewegungs-, Kampf- und Targeting-Regeln
- **Map-Definitionen**: Pfade, Tile-Größen, Platzierungs-Grids
- **Protokoll-Strukturen**: Datenformate für Client-Server-Kommunikation

### Deterministische Simulation

 Die Simulation muss auf Server und Client identische Ergebnisse produzieren.

- **Fixed Timesteps**: Alle Berechnungen basieren auf festen Tick-Raten (`SIM_DT`)
- **Reine Funktionen**: Keine Seiteneffekte, keine Abhängigkeiten von System-Zeit oder externen Zuständen
- **Plattform-Unabhängigkeit**: Keine Pygame- oder Rendering-Imports im Simulationskern

### Code-Sharing zwischen Server und Client

- **Server**: Verwendet `td_shared` für autoritative Simulation
- **Client**: Verwendet `td_shared` für lokale Visualisierung (Lockstep)
==> Beide Seiten verwenden denselben deterministischen Code, und produzieren daher identische Ergebnisse

---

### Repo Struktur

```
shared/
├── src/
│   └── td_shared/
│       ├── __init__.py          # Package-Exports
│       ├── game/                # Spiel-Definitionen
│       │   ├── game_balance.py  # Balance-Werte, Stats, Pfade, Tile-Größen
│       │   └── protocol.py      # TypedDict-Definitionen für Kommunikation
│       ├── simulation/          # Simulationskern
│       │   └── sim_core.py      # Deterministische Simulations-Logik
│       ├── map/                 # Karten-Logik
│       │   ├── placement_grid.py  # Turm-Platzierungs-Validierung
│       │   ├── grid_defs.py       # Grid-Zell-Zustände
│       │   └── path_utils.py      # Pfad-Utilities
│       └── protobuf/            # gRPC-Integration
│           ├── game.proto       # Protobuf-Definitionen
│           ├── game_pb2.py      # Generierte Protobuf-Klassen
│           ├── game_pb2_grpc.py # Generierte gRPC-Stubs
│           └── protobuf_utils.py # Konvertierungs-Utilities
└── pyproject.toml
```

---

## Deterministische Simulation

### Simulationskern (`simulation/sim_core.py`)

**Zweck**: Reine, deterministische Spiel-Logik ohne Seiteneffekte

**Kern-Komponenten**:

#### `GameState`
- **Zweck**: Verwaltet den Zustand einer einzelnen Runde
- **Initialisierung**: Erstellt aus `SimulationData` (Türme, Einheiten, Tick-Rate)
- **Haupt-Methode**: `update_tick()` - Führt einen Simulations-Tick aus
- **Beendigung**: `is_simulation_complete()` - Prüft Rundenende-Bedingungen

**Simulations-Loop**:
```python
game_state = GameState(simulation_data)
while not game_state.is_simulation_complete():
    game_state.update_tick()
```

#### `SimUnit`
- **Zweck**: Angreifende Einheit, die einem Pfad folgt
- **Bewegung**: Deterministische Bewegung entlang vordefinierter Pfade
- **Schaden**: Nimmt Schaden von Türmen, stirbt bei 0 HP
- **Base-Raech**: Zählt Leben-Verlust, wenn Base erreicht wird

#### `SimTower`
- **Zweck**: Defensive Struktur, die Einheiten angreift
- **Targeting**: Findet nächste feindliche Einheit in Reichweite
- **Angriff**: Schießt mit Cooldown-Mechanismus
- **Schaden**: Verursacht festen Schaden pro Angriff

**Determinismus-Garantien**:
- Fixed Timesteps (`sim_dt = 1.0 / tick_rate`)
- Deterministische Targeting-Regeln (nächste Einheit in Reichweite)
- Identische Berechnungen auf Server und Client

### Tick-basierte Simulation

**Timestep-Berechnung**:
```python
sim_dt = calculate_sim_dt(tick_rate)  # z.B. 1.0 / 20 = 0.05 Sekunden
```

**Bewegung pro Tick**:
```python
distance = speed * sim_dt  # z.B. 120.0 * 0.05 = 6 Pixel pro Tick
```

- Türme haben `cooldown_ticks` (z.B. 10 Ticks)
- `current_cooldown` wird pro Tick dekrementiert
- Angriff nur wenn `current_cooldown == 0`

---

## Spiel-Definitionen

### Game Balance (`game/game_balance.py`)

**Zweck**: Zentrale Konfiguration für das gesamte Spiel

**Enthält**:
- Balance-Werte (Gold, Leben, Tick-Rate, Phasen-Dauer)
- Unit- und Tower-Stats
- Karten-Geometrie (Tile-Größe, Map-Dimensionen)
- Pfad-Definitionen (`GAME_PATHS`)
- Koordinaten-Konvertierungen (`tile_to_pixel`)

### Map Logic (`map/placement_grid.py`)

**Zweck**: Validierung von Turm-Platzierungen

**PlacementGrid**:
- Verwaltet ein logisches Grid für Turm-Platzierungen
- `PATH`
- `EMPTY`
- `OCCUPIED`

---

## Protokoll-Definitionen

### Protocol Types (`game/protocol.py`)

**Zweck**: Typesafe Datenstrukturen für Client-Server-Kommunikation

**TypedDict-Definitionen**:

#### `SimulationData`
Vollständige Daten für eine Runde:
```python
{
    "towers": List[SimTowerData],
    "units": List[SimUnitData],
    "tick_rate": int,
}
```

#### `SimTowerData`
Daten für einen Turm:
```python
{
    "player_id": "A" | "B",
    "tower_type": str,
    "position_x": float,
    "position_y": float,
    "level": int,
}
```

#### `SimUnitData`
Daten für eine Einheit:
```python
{
    "player_id": "A" | "B",
    "unit_type": str,
    "route": int,
    "spawn_tick": int,
}
```

#### `RoundResultData`
Autoritative Runden-Ergebnisse:
```python
{
    "lives_lost_player_A": int,
    "gold_earned_player_A": int,
    "lives_lost_player_B": int,
    "gold_earned_player_B": int,
}
```

**PlayerID**:
```python
PlayerID = Literal["A", "B"]
```

---

## Protobuf-Integration

### Protobuf-Definitionen (`protobuf/game.proto`)

**Zweck**: gRPC-Protobuf-Definitionen für Netzwerk-Kommunikation

**Haupt-Messages**:
- `SimulationData`: Runden-Start-Daten
- `RoundResultData`: Runden-Ergebnisse
- `BuildTowerRequest/Response`: Turm-Platzierung
- `SendUnitsRequest/Response`: Einheiten-Kauf
- `MatchEvent`: Server-Streaming-Events

**Generierung**:
```bash
python -m grpc_tools.protoc -I shared/src \
    --python_out=shared/src \
    --grpc_python_out=shared/src \
    shared/src/td_shared/protobuf/game.proto
```

### Protobuf-Utilities (`protobuf/protobuf_utils.py`)

**Zweck**: Konvertierung zwischen internen TypedDicts und Protobuf-Messages

**Funktionen**:

#### `sim_data_to_proto(sim: SimulationData) -> game_pb2.SimulationData`
- Konvertiert internes `SimulationData` (TypedDict) zu Protobuf-Message
- Wird vom Server verwendet, um Daten an Clients zu senden

#### `proto_to_sim_data(sim_proto: game_pb2.SimulationData) -> SimulationData`
- Konvertiert Protobuf-Message zu internem `SimulationData` (TypedDict)
- Wird vom Client verwendet, um empfangene Daten zu verarbeiten

**Warum beide Formate?**:
- **TypedDict**: Type-safe, Python-native, für interne Verarbeitung
- **Protobuf**: Effiziente Serialisierung, plattform-übergreifend, für Netzwerk

---

## Erweiterungen und Anpassungen

### Neue Turm-Typen hinzufügen

1. `game/game_balance.py`: Stats zu `TOWER_STATS` hinzufügen
2. Server/Client: Verwendung der neuen Stats

### Neue Einheiten-Typen hinzufügen

1. `game/game_balance.py`: Stats zu `UNIT_STATS` hinzufügen
2. Server/Client: Verwendung der neuen Stats

### Balance-Anpassungen

Alle Balance-Werte in `game/game_balance.py`:
- `PLAYER_LIVES`
- `START_GOLD`
- `GOLD_PER_KILL`
- `TOWER_STATS` Werte
- `UNIT_STATS` Werte

### Protobuf-Änderungen

1. `protobuf/game.proto` bearbeiten
2. Protobuf-Dateien neu generieren
```bash
cd shared
python -m grpc_tools.protoc -I src \
    --python_out=src \
    --grpc_python_out=src \
    src/td_shared/protobuf/game.proto
```
3. `protobuf_utils.py` anpassen, falls nötig


