# Architectural Overview: Deterministic Lockstep TD

## Das Gameplay-Konzept (Das "Big Picture")

**Roundhold** ist ein 1v1-Netzwerk-Tower-Defense-Spiel, bei dem das Ziel darin besteht, die gegnerische Basis zu zerstören, während man die eigene Basis verteidigt.

**SplitMap-Design:** Die Karte ist symmetrisch in zwei Hälften geteilt. Jeder Spieler spielt auf seiner eigenen Spielfeldhälfte und greift die Basis des Gegners auf der anderen Hälfte an.

**Basis-Leben:** Jede Basis hat 20 Lebenspunkte. Wenn eine feindliche Einheit die gegnerische Basis erreicht, verliert der betroffene Spieler 1 Leben. Das Spiel endet, wenn ein Spieler 0 Leben erreicht.

**5 Routen:** Auf jeder Spielfeldhälfte gibt es 5 feste Angriffsrouten, die Einheiten folgen können. Diese Routen sind vordefiniert und statisch.

**Wirtschaftssystem:** 
- Spieler erhalten Gold automatisch über Zeit
- Gold wird für das Töten von Einheiten belohnt
- Mit Gold können Spieler Türme bauen, Türme verbessern oder Angriffseinheiten kaufen
- Es gibt auch reine Gold-Produktionsgebäude

**Turm-Typen (Beispiele):**
- Normaler Turm (20g)
- Verlangsamungsturm (30g)
- Scharfschütze (45g)

**Einheiten-Typen (Beispiele):**
- Standard (5g)
- Tank (15g)
- Späher (25g)

**Kasernen-Mechanik:** Auf der eigenen Spielfeldhälfte gibt es 5 "Kasernen" (Barracks), die jeweils einer der 5 Routen auf der Gegnerseite zugeordnet sind. Hier wählt der Spieler die Einheiten aus, die den Gegner angreifen sollen.

## Pre-Game & LAN-Verbindung (Der "Find Game" Screen)

**LAN-Verbindung:** Das Spiel ist für lokale Netzwerke (LAN) ausgelegt. Es gibt keine zentrale Matchmaking-Instanz.

**Host (Server):** Ein Spieler agiert als Host. Er startet die `rpc_server.py`-Anwendung. Diese Anwendung ist der autoritative Spieleserver, der den gesamten Game State verwaltet.

**Join (Client):** Der zweite Spieler (und auch der Host selbst) startet den `td_client`. Beide Spieler verwenden die Client-Anwendung, um sich mit dem Server zu verbinden.

**Find Game Screen:** Im Client gibt es einen "Find Game" (o.ä.) Bildschirm. Hier muss der Spieler die IP-Adresse des Hosts im LAN eingeben, um sich zu verbinden.

**Spielstart:** Der `rpc_server.py` wartet, bis sich zwei Clients verbunden haben, und initiiert dann den Start des Spiels (Phase 1: Vorbereitung).

## Das Kernprinzip: Server-Autorität

Das Fundament unserer Architektur ist, dass der **Server die alleinige Quelle der Wahrheit ("Source of Truth")** ist.

- Der Server verwaltet den **globalen Game State**: die 20 Leben, das Gold, die aktuelle Runde sowie Position und Level aller Türme beider Spieler.
- Der Client (`td_client`) ist primär eine **Rendering-Engine** und eine **Input-Schnittstelle**. Er visualisiert den Spielzustand und sendet Spieleraktionen an den Server.

## Die zwei Welten: Simulation vs. Rendering

Eine strikte Entkopplung von Spiellogik (Simulation) und Grafik (Rendering) ist essentiell. Diese beiden "Loops" laufen parallel auf dem Client:

**Der Render-Loop (ca. 60 FPS):**
- Gesteuert von `td_client/main.py` und dem `RenderManager`
- Er ist nur für die Grafik zuständig
- Nutzt einen variablen `dt` (Delta Time), der von der tatsächlichen Framerate abhängt
- Zeichnet Sprites, Animationen, Effekte und UI-Elemente

**Der Simulations-Loop (Feste 20 Hz):**
- Gesteuert vom `td_client/wave_simulator.py`
- Läuft mit einer festen, deterministischen Tickrate (z. B. 20 Ticks/Sekunde)
- Nutzt einen festen `SIM_DT` (z. B. $1.0 / 20.0 = 0.05s$)
- Berechnet Bewegungen, Kollisionen, Schaden und alle anderen Spiellogik-Aspekte

Diese Trennung stellt sicher, dass die Simulation unabhängig von der Framerate deterministisch bleibt, während das Rendering flüssig und responsiv bleibt.

## Das "Shared Kernel": `shared/sim_core.py`

Das Modul `shared/sim_core.py` ist das **"Gehirn"** des Spiels. Es enthält die gesamte deterministische Spiellogik.

**Kritische Eigenschaft:** Dieses Modul wird **exakt identisch** vom Server (für die "echte" Berechnung) und vom Client (für die "visuelle" Berechnung) importiert. Es ist Teil des `td_shared`-Pakets, das sowohl vom Server als auch vom Client als Abhängigkeit verwendet wird.

**Wichtig:** Dieses Modul darf **niemals** Pygame oder anderen Rendering-Code enthalten. Es ist reine, plattformunabhängige Spiellogik.

**Deterministische Regeln:**

- **Bewegung:** Verwendet $\Delta x = velocity \times dt$, wobei `dt` der feste `SIM_DT` ist. Keine Gleitkomma-Rundungsfehler durch variable Zeitstufen.
- **Pfadfindung:** Es gibt keine dynamische Pfadfindung. Einheiten folgen ausschließlich den vordefinierten, festen Pfaden, die als Koordinatenlisten gespeichert sind.
- **Turm-Logik:** Zielerfassung folgt festen Prioritäten (z. B. "first", "closest"). Die Reihenfolge der Einheiten in der Liste ist deterministisch.
- **Cooldowns:** Werden in ganzen Simulationsticks gespeichert, nicht in Sekunden. Beispiel: Ein Turm hat einen Cooldown von 10 Ticks, nicht von 0.5 Sekunden.
- **Schaden/HP:** Werden nur als `int` (Ganzzahlen) gespeichert und berechnet, um Gleitkomma-Rundungsfehler zu vermeiden.

## Der Phasen-Ablauf: Der "Lockstep"-Zyklus

Das Spiel läuft in einem wiederholten Zyklus von 4 Phasen ab:

### Phase 1: Vorbereitung (30 Sekunden) (Client → Server)

**Gameplay:** 
- Spieler bauen/verbessern Türme
- Spieler wählen Angriffseinheiten an den 5 Kasernen aus

**Netzwerk:** Client → Server

**Nachrichten:** 
- `BuildTower` (Position, Turm-Typ)
- `SendUnitsForRoute3` (Route-Nummer, Einheiten-Typ, Anzahl)
- Weitere Aktionen wie Turm-Upgrades

**Server-Aktion:** Der Server validiert jede Aktion:
- Hat der Spieler genug Gold?
- Ist die Position frei?
- Ist die Aktion in der aktuellen Phase erlaubt?

Bei erfolgreicher Validierung wird der Game State aktualisiert (Gold abgezogen, Turm hinzugefügt, etc.).

### Phase 2: Rundenstart (Server → Client)

**Was passiert:** Die 30 Sekunden Vorbereitungszeit sind abgelaufen.

**Netzwerk:** Server → Client

**Nachricht:** `RoundStart`

**Inhalt:** Alle Daten, die für die Simulation benötigt werden:
- Eine Liste aller Türme (beider Spieler) mit Position, Typ, Level
- Eine Liste aller Einheiten (beider Spieler), die spawnen werden (Typ, Route, Spawn-Zeit in Ticks)
- Die Simulationsparameter: `tick_rate` (z. B. 20) und der `seed` für Zufallsereignisse

### Phase 3: Simulation (Kein Netzwerkverkehr)

**Was passiert:** Die Welle läuft. Es findet **kein Netzwerkverkehr** statt.

**Server-Aktion:** 
- Der Server startet seine interne Simulation (`combat_sim.py`)
- Rechnet die Welle "im Dunkeln" durch (mit `shared/sim_core.py` und `SIM_DT`)
- Berechnet alle Bewegungen, Angriffe, Schaden, Tod von Einheiten

**Client-Aktion:** 
- Der Client startet parallel seine lokale Simulation (`wave_simulator.py`)
- Verwendet dieselben Daten, dieselbe Logik (`shared/sim_core.py`) und denselben `SIM_DT`
- Visualisiert die Simulation in Echtzeit (60 FPS Rendering)

**Das "Lockstep":** 
- Da Server und Client mit identischen Daten, identischer Logik und identischem `SIM_DT` starten, müssen sie **exakt dasselbe Ergebnis** berechnen.
- Die Simulation ist deterministisch: Gleiche Eingaben führen immer zu gleichen Ausgaben.
- Der Client "sieht" die Welle in Echtzeit, während der Server sie im Hintergrund berechnet. Beide kommen zum selben Ergebnis.

### Phase 4: Rundenende (Server → Client)

**Was passiert:** Die Simulation ist beendet.

**Netzwerk:** Server → Client

**Nachricht:** `RoundResult`

**Inhalt:** Nur das Endergebnis:
- `lives_lost_player_A: 2`
- `gold_earned_player_A: 30`
- `lives_lost_player_B: 1`
- `gold_earned_player_B: 25`
- Aktualisierter Game State (neue Turm-Level, etc.)

**Client-Aktion:** 
- Der Client stoppt seine lokale Simulation
- Überschreibt seinen lokalen Zustand (Leben, Gold) mit den **autoritativen Werten** aus dem `RoundResult`
- Das Spiel kehrt zu Phase 1 (Vorbereitung) zurück

## Cheating & Optionale Features (Fog of War)

**Resilienz gegen Manipulation:** 
Dieses Modell erschwert Cheating erheblich. Selbst wenn ein Hacker seinen Client-Code (`sim_core.py`) ändert, um z. B. mehr Schaden zu verursachen, ist das irrelevant. Die Simulation des Servers ("die Wahrheit") berechnet den Schaden korrekt, und der `RoundResult` des Servers wird dem Hacker am Ende trotzdem die korrekten Leben abziehen. Der Hacker sieht zwar auf seinem Bildschirm vielleicht falsche Werte, aber der Server-State ist unveränderlich.

**Fog of War (Optional):** 
"Fog of War" (Nebel des Krieges) ist ein optionales Feature, das nicht Teil des Kern-MVPs ist. Wenn implementiert, würde der Client nur die Einheiten und Türme auf seiner eigenen Spielfeldhälfte sehen, während die gegnerische Hälfte verdeckt wäre.

**Map Hack (Schwachstelle):** 
Falls Fog of War implementiert würde, müsste die `RoundStart`-Nachricht alle Turmpositionen enthalten (damit die Simulation korrekt funktioniert). Ein Hacker könnte diese Daten auslesen, um den Nebel zu umgehen. Dies ist ein bekannter Kompromiss dieser Architektur: Die deterministische Simulation erfordert vollständige Zustandsinformationen.

## Technologie-Stack

**Netzwerk:** 
- Die Kommunikation erfolgt über **gRPC**
- gRPC bietet typsichere, effiziente Kommunikation zwischen Client und Server

**Datenformat:** 
- Der Datenaustausch wird durch die in gRPC definierten Service- und Message-Strukturen (via `.proto`-Dateien) abgewickelt
- Diese Definitionen befinden sich in `shared/` und werden von beiden Seiten verwendet

**Client:** 
- **Pygame** für Rendering, Input-Handling und Fensterverwaltung
- Python für die gesamte Client-Logik

**Server:** 
- Python (Back-End)
- gRPC-Server für Netzwerkkommunikation

**Shared Code:** 
- Python-Module, die sowohl vom Server als auch vom Client importiert werden
- Enthält deterministische Spiellogik und Protobuf-Definitionen

## Ziel-Modul-Struktur

Die finale Projektstruktur ist in drei Hauptverzeichnisse aufgeteilt:

```
Roundhold/
├── server/              # Autoritative Server-Logik
│   ├── rpc_server.py    # gRPC-Server, Netzwerk-Endpunkte
│   ├── game_state.py    # Verwaltung des globalen Game States
│   ├── round_manager.py # Orchestriert Phasen 1-4
│   └── combat_sim.py    # Führt die autoritative Simulation aus
│
├── client/              # Rendering & Input
│   ├── main.py          # Entry Point, Render-Loop (60 FPS)
│   ├── rendering/       # RenderManager, Sprite-System, etc.
│   ├── network.py       # gRPC-Client, Nachrichten senden/empfangen
│   └── wave_simulator.py # Lokale Simulation (20 Hz) für Visualisierung
│
└── shared/              # Gemeinsamer Code
    ├── sim_core.py      # Deterministische Spiellogik (wird von beiden importiert)
    ├── game_defs.py     # Turm-Kosten, Einheiten-Stats, etc.
    └── protocol.py      # gRPC-Definitionen (.proto-Dateien)
```

Diese Struktur stellt sicher, dass:
- Die Spiellogik zentralisiert und deterministisch ist
- Server und Client dieselbe Logik verwenden
- Rendering und Simulation sauber getrennt sind
- Netzwerkkommunikation typsicher und wartbar ist

