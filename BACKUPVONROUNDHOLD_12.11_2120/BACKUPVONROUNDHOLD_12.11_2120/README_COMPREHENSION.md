### Roundhold – Ausführliche Codebase-Zusammenfassung (Comprehension README)

Diese Datei beschreibt die gesamte Projektstruktur, alle wesentlichen Module und deren konkrete Implementierung. Sie dient als präzise Referenz für Entwicklerinnen und Entwickler, die schnell verstehen möchten, wie Client, Server und Shared-Layer zusammenarbeiten.


## Überblick

- **Ziel**: 1v1 Tower-Defense mit deterministischer Simulation (Lockstep). Der Server ist autoritativ; der Client rendert und interagiert.
- **Technologien**: Python, gRPC, Pygame, geteilte Spiellogik im Paket `td_shared`.
- **Kerneigenschaft**: Die Simulationslogik ist in `shared/src/td_shared/sim_core.py` zentralisiert und wird identisch von Client und Server genutzt.


## Repository-Struktur

```
Roundhold/
├── ARCHITECTURE.md                    # Architektonischer Überblick (Konzept, Phasen, Ziele)
├── README.md                          # Setup/Entwicklungsanleitung (WSL/venv, Installation)
├── README_COMPREHENSION.md            # Diese Datei: detailliertes Codebase-Exposé
├── pyproject.toml                     # (Root) ggf. projektweite Metadaten
├── requirements-dev.txt               # Dev-Tools (pre-commit etc.)
│
├── shared/                            # Geteilte, deterministische Spiellogik & Protobuf
│   ├── pyproject.toml
│   └── src/td_shared/
│       ├── __init__.py
│       ├── game_defs.py               # Stats (Towers/Units), Pfade, Tile-Konvertierung
│       ├── game.proto                 # gRPC-Schnittstellen (BuildTower, SendUnits)
│       ├── game_pb2.py                # Generierter Protobuf-Code
│       ├── game_pb2_grpc.py           # Generierte gRPC-Stubs
│       ├── protocol.py                # TypedDict-Datenverträge (Simulation/Round)
│       └── sim_core.py                # Deterministische Simulationsengine
│
├── server/                            # Autoritative Server-Seite
│   ├── pyproject.toml
│   ├── README.md
│   ├── main.py                        # Server-Entry; Prozess-/Signalsteuerung
│   ├── rpc_server.py                  # gRPC-Server, Service-Impl, Bootstrapping
│   ├── game_state_manager.py          # Gold/Leben/Towers/Units (prä-Runde) + Snapshot
│   ├── round_manager.py               # Rundensteuerung (Vorbereitung -> Kampf)
│   └── combat_sim.py                  # Startet sim_core.GameState, ermittelt Ergebnis
│
└── client/                            # Rendering- und Input-Client
    ├── pyproject.toml
    ├── assets/                        # Art-/Asset-Dateien
    └── src/td_client/
        ├── __init__.py
        ├── README_CLIENT.md
        ├── main.py                    # Game-Loop (Pygame), Input, Rendering-Koordinator
        ├── network.py                 # gRPC-Client (asynchron per Thread)
        ├── wave_simulator.py          # Lokale Visualisierungssimulation (nutzt shared)
        ├── assets/                    # Asset-Loader/Verwaltung
        ├── config/                    # Einstellungen/Pfade
        ├── debug/                     # Debug-Overlay/Grid
        ├── display/                   # Fenster- und Surface-Management
        ├── map/                       # TileMap, Terrain (inkl. Offsets, TILE_SIZE)
        ├── rendering/                 # RenderManager, Draw-Pipeline
        └── sprites/                   # Sprite-/Entity-Visuals
```


## Shared-Layer (`td_shared`)

- `protocol.py`:
  - Definiert TypedDicts als stabile Verträge zwischen Client und Server.
  - Wichtige Typen:
    - `PlayerID = Literal["A", "B"]`
    - `SimTowerData`: Tower am Rundenstart (Besitzer, Typ, Position, Level)
    - `SimUnitData`: Einheiten, die in der Runde spawnen (Besitzer, Typ, Route, Spawn-Tick)
    - `SimulationData`: Komplettpaket für eine Runde (Towers, Units, tick_rate, seed)
    - `RoundStartData`: Wrapper mit `simulation_data`
    - `RoundResultData`: Endergebnis einer Runde (verlorene Leben, Goldgewinne)

- `game_defs.py`:
  - Zentrale Spieldefinitionen: `TILE_SIZE_PX`, `tile_to_pixel(row, col)`, `UNIT_STATS`, `TOWER_STATS`, `GAME_PATHS`.
  - `UNIT_STATS["standard"]`: cost=5, health=10, speed=50 px/s.
  - `TOWER_STATS["standard"]`: cost=20, damage=25, range_px=120, cooldown_ticks=10.
  - `GAME_PATHS`: Feste Routen als Tile-Koordinatenlisten (5 Routen). Der Client ist für Spiegelung/Translation in der Anzeige verantwortlich.

- `game.proto`:
  - gRPC-Service `YourGameService` mit zwei RPCs:
    - `BuildTower(BuildTowerRequest) -> BuildTowerResponse`
    - `SendUnits(SendUnitsRequest) -> SendUnitsResponse`
  - Nachrichten u. a.: `SimUnitData` (für `SendUnitsRequest.units`), einfache Erfolgs-Flags.

- `sim_core.py`:
  - Herzstück der deterministischen Simulation. Läuft identisch auf Server und Client.
  - Konstanten/Utilities:
    - `DEFAULT_TICK_RATE = 20`, `calculate_sim_dt(tick_rate)`.
  - Basisklassen:
    - `SimEntity`: id, `player_id`, Position, `is_active`, `distance_to(...)`.
  - Einheiten:
    - `SimUnit`: besitzt `unit_type`, `route`, `path` (aus `GAME_PATHS`), `speed`, `health`.
    - `update()`: deterministisches Bewegen entlang Wegpunkten; setzt `_reached_base`/`is_active` am Ende.
  - Türme:
    - `SimTower`: konstruiert aus `TOWER_STATS` (damage, range, cooldown).
    - `update(enemy_units)`: Cooldown-Handling, Zielauswahl mit `_find_target` (nächste gegnerische Unit in Range), `_shoot()` reduziert HP.
  - Spielzustand pro Runde:
    - `GameState(simulation_data)`: baut Listen von `SimTower` und `SimUnit` (Units starten inaktiv bis `spawn_tick`).
    - Tick-Update:
      - Spawnt Units bei Erreichen ihres `spawn_tick`
      - Aktualisiert aktive Units und alle Türme
      - Entfernt inaktive Units; setzt `last_unit_inactive_tick`, wenn keine aktiven/pending Units mehr existieren
    - Abschlussbedingungen:
      - Mindestens 5 Sekunden Laufzeit, danach 3 Sekunden Verzögerung nach letzter Inaktivität
    - Ergebnisse/Hilfen:
      - `get_units_reached_base(player_id)`: zählt gegnerische Units, die die Basis dieses Spielers erreichten
      - `is_simulation_complete()`: prüft oben beschriebene Zeitregeln


## Server

- `rpc_server.py`:
  - Implementiert den gRPC-Servicer `GameRpcServer` (erbt aus `game_pb2_grpc.YourGameServiceServicer`).
  - `BuildTower(req)`: validiert und delegiert an `GameStateManager.build_tower(...)`; antwortet mit `success`.
  - `SendUnits(req)`: normalisiert ankommende Units und delegiert an `GameStateManager.add_units_to_wave(...)`; antwortet mit `success`.
  - `serve(host, port, max_workers)`: erstellt gRPC-Server, initialisiert `GameStateManager` und `RoundManager`, startet beide (RoundManager in Hintergrund-Thread).

- `game_state_manager.py`:
  - Verantwortlich für autoritativen Zustand vor/zwischen Runden: Gold/Leben, platzierte Türme, vorbereitete Units.
  - Thread-sicher via Lock.
  - Wichtige Methoden:
    - `get_current_state_snapshot() -> SimulationData`: übersetzt platzierte Türme (Tile -> Pixel, Centering um 0.5 * TILE_SIZE_PX) und queued Units in ein Snapshot-Objekt; vergibt Seed.
    - `build_tower(player_id, tower_type, tile_row, tile_col, level=1) -> Optional[SimTowerData]`:
      - Prüft Kosten, Occupancy; zieht Gold ab; registriert Placement, liefert SimTowerData (mit zentrierter Pixel-Position) oder `None`.
    - `add_units_to_wave(player_id, units)`:
      - Normalisiert eingehende Unit-Daten (Route/Spawn als int), ergänzt `player_id` bei Bedarf.
    - `apply_round_result(result)`: reduziert Leben (min 0) und addiert Gold nach Kampfrunde.
    - `clear_wave_data()`: leert die Units-Warteschlange für die nächste Runde.

- `round_manager.py`:
  - Orchestriert Rundenzyklus: Vorbereitung -> Kampf -> Cleanup.
  - `run_game_loop()`:
    - Vorbereitung: wartet `prepare_duration_seconds` (Default 30s) in Halbschritten (responsiv stoppbar)
    - Erzeugt `snapshot = GameStateManager.get_current_state_snapshot()`
    - Startet Combat-Worker-Thread, der `_run_combat_and_callback(snapshot)` ausführt, wartet mit `join()`
  - `_run_combat_and_callback(snapshot)`:
    - `run_combat_simulation(snapshot)` aufrufen
    - `apply_round_result(result)` und `clear_wave_data()` am `GameStateManager`
    - TODO-Kommentar: spätere Pushes an Clients (RoundResult Broadcast)

- `combat_sim.py`:
  - `run_combat_simulation(simulation_data) -> RoundResultData`:
    - Konstruiert `sim_core.GameState`, tickt bis `is_simulation_complete()`
    - Leitet `lives_lost_player_A/B` aus `get_units_reached_base(...)` ab
    - Gibt Ergebnis mit beiden `gold_earned_* = 0` (Platzhalter) zurück

- `main.py`:
  - Startet `serve()` und blockiert mit sauberer Signalbehandlung (SIGINT/SIGTERM), stoppt gRPC-Server am Ende.


## Client

- `src/td_client/main.py` (Entry und Game-Loop):
  - Initialisiert Pygame, `DisplayManager`, Assets/Maps, `RenderManager` (inkl. Wasser/Umgebung/Sprites), `WaveSimulator`, `NetworkClient`.
  - Setzt testweise `player_id = "A"` und erzeugt Dummy-Wave (`_start_dummy_wave()`), die `wave_simulator` lädt.
  - Event-Handling (z. B. Taste G für Grid, ESC zum Beenden, Linksklick für Towerbau über `NetworkClient.build_tower(...)`).
  - `update(dt)`: aktualisiert `wave_simulator` und `render_manager` und synchronisiert Sprites zum `wave_simulator.game_state`.
  - `render()`: zeichnet Welt, Grid/Debug, präsentiert über `DisplayManager`.

- `src/td_client/network.py` (gRPC-Client-Wrapper):
  - Nicht-blockierende RPC-Aufrufe in Hintergrund-Threads, um den Render-Loop nicht zu stören.
  - Erwartet generierte Stubs aus `td_shared.game_pb2(_grpc)` (Hinweis im Kopfkommentar zur protoc-Generierung).
  - `build_tower(..., on_done)`: baut Request, ruft `stub.BuildTower`, callt Callback mit Bool-Success.
  - `send_units(..., on_done)`: mappt Python-`dict`-Units auf `game_pb2.SimUnitData`, ruft `stub.SendUnits`.

- Rendering-/Asset-/UI-Subsysteme
  - `display`, `rendering`, `sprites`, `map`, `assets`, `debug` enthalten die Darstellungslogik. Der `RenderManager` erhält Karte(n), Assets, Größen (z. B. `TILE_SIZE`) und Bildschirmmaße, initialisiert Wasser- und Umwelteffekte und Sprite-Instanzen. Die konkrete Darstellung ist bewusst vom `sim_core` getrennt.

- `wave_simulator.py`
  - Lädt `SimulationData` (z. B. aus `RoundStartData`) und führt lokale, deterministische Ticks für die Visualisierung aus. Nutzt dafür die Engine aus `td_shared.sim_core`. Dient zur synchronen Anzeige dessen, was der Server rechnet.


## gRPC-API

- Service: `YourGameService` (siehe `shared/src/td_shared/game.proto`)
  - `BuildTower(BuildTowerRequest) -> BuildTowerResponse`
    - Felder: `player_id`, `tower_type`, `tile_row`, `tile_col`, `level`
    - Antwort: `success: bool`
  - `SendUnits(SendUnitsRequest) -> SendUnitsResponse`
    - Felder: `player_id`, `units: repeated SimUnitData(player_id, unit_type, route, spawn_tick)`
    - Antwort: `success: bool`
- Generierung (wenn erforderlich):
  - Ausführen aus dem Projektroot (Beispiel):
    - `python -m grpc_tools.protoc -I shared/src --python_out=shared/src --grpc_python_out=shared/src td_shared/game.proto`


## Datenfluss einer Runde (End-to-End)

1. Vorbereitung (Client → Server):
   - Client sendet Aktionen über `NetworkClient` an gRPC-Server (`BuildTower`, `SendUnits`).
   - Server validiert und aktualisiert Zustand im `GameStateManager`.
2. RoundStart (Server intern → Client zukünftig):
   - `RoundManager` erzeugt `SimulationData` via `GameStateManager.get_current_state_snapshot()`.
   - Server und Client starten jeweils ihre Simulation mit denselben Daten.
3. Simulation (keine Netzwerknachrichten):
   - Server: `combat_sim.run_combat_simulation` tickt `sim_core.GameState` bis Abschluss.
   - Client: `wave_simulator` tickt und rendert mit `RenderManager`.
4. RoundResult (Server → Client):
   - Server gibt autoritatives Ergebnis zurück; Client überschreibt lokale Werte und geht zurück zur Vorbereitung.


## Wichtige Klassen/Funktionen und ihre Implementierung (Kurzreferenz)

- Server
  - `GameRpcServer.BuildTower/SendUnits` (in `server/rpc_server.py`): dünne RPC-Schicht, delegiert an `GameStateManager`.
  - `GameStateManager` (in `server/game_state_manager.py`):
    - Gold/Leben, Lock-geschützt, Occupancy-Check, Tower-Kauf/Kostenabzug, Unit-Queue.
    - `get_current_state_snapshot()`: baut deterministisches `SimulationData` inkl. Seed.
  - `RoundManager` (in `server/round_manager.py`): Taktet Vorbereitungsfenster, startet Simulation und schreibt Resultate zurück.
  - `run_combat_simulation` (in `server/combat_sim.py`): führt die Runde mit `sim_core.GameState` aus und fasst Resultate zusammen.

- Shared
  - `SimUnit.update()` und `SimTower.update()` (in `shared/src/td_shared/sim_core.py`): deterministische Bewegung, Zielwahl, Schaden, Cooldowns.
  - `GameState.update_tick()`/`is_simulation_complete()`/`get_units_reached_base()`:
    - Spawns bei `spawn_tick`, Listenpflege aktiver Units, Ende nach Mindestdauer + Nachlauf.

- Client
  - `Game` (in `client/src/td_client/main.py`): Pygame-Loop (Events → Update → Render), Integration von `WaveSimulator` und `RenderManager`, Test-Welle, RPC-Aufrufe bei Input.
  - `NetworkClient` (in `client/src/td_client/network.py`): asynchrones gRPC; serialisiert Requests, führt Callbacks aus.


## Setup, Build und Start (Kurz)

Siehe `README.md`. Wichtig: Reihenfolge der Installation
1) `./shared`, 2) `./server`, 3) `./client`. Dev-Tools via `requirements-dev.txt`. gRPC-Stubs bei Bedarf generieren (siehe oben).


## Erweiterungspunkte und Roadmap (Hint)

- RoundResult-Broadcast an Clients (TODO im Server) und UI-Anzeige/Aktualisierung.
- Wirtschaft: Gold über Zeit, Belohnungen (`gold_earned_*`) in `combat_sim.py` berechnen.
- Weitere Towers/Units und Balancing in `game_defs.py`.
- Fog of War (optional) mit bekannter Trade-off-Problematik in deterministischen Setups.


