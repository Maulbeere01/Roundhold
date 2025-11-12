# TODOs 

## Tests

## Sync between TypedDicts and Protobuf
- `game.proto` ist die Source of Truth für gRPC-Definitionen
- `shared/src/td_shared/game/protocol.py` spiegelt die Strukturen als `TypedDict` wider.
==> pytest-Test schreiben, der Feldnamen (`SimulationData`, `SimTowerData`, etc.) zwischen Proto und TypedDict vergleicht, damit sie nicht auseinanderlaufen.

## Cheat-Prevention 
==> Integrationstest mit Pytest schreiben: manipulierter Client (z. B. 500 Gold) darf keine illegalen Aktionen auf dem Server durchbringen.


