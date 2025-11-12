# TD Client Architecture

## Struktur

```
td_client/
├── config/           # Konfiguration
│   ├── settings.py   # Game-Einstellungen
│   └── paths.py      # Asset-Pfade
├── assets/           # Asset-Management
│   ├── loader.py     # Asset-Loader mit Caching
│   └── template_manager.py # Erstellt & cached Sprite-/Tile-Templates
├── display/          # Display & Window Management
│   └── display_manager.py # Window, Render Surface, Frame Presentation
├── sprites/          # Sprite-Klassen
│   ├── base.py       # Basis-Sprite-Klassen
│   ├── buildings.py  # Gebäude-Sprites
│   ├── units.py      # Einheiten-Sprites
│   ├── decor.py      # Deko-Sprites
│   └── animated.py   # Animierte Sprites
├── map/              # Map-Management
│   ├── map_data.py   # Map-Daten
│   └── map_renderer.py # Map-Rendering
├── rendering/        # Rendering-System
│   ├── render_manager.py     # Orchestriert alle Rendering-Schichten
│   ├── coordinate_translator.py # Simulation → Bildschirmkoordinaten
│   ├── sprite_factory.py     # Erzeugt Unit- & Tower-Sprites aus Templates
│   ├── map_layer_renderer.py # Zeichnet Wasser, Wege, Foam
│   ├── foam_renderer.py      # Wasser-Foam Animationen
│   ├── elevation_renderer.py # Klippen/Elevation Rendering
│   └── road_renderer.py      # Weg/Straßen Rendering
├── debug/            # Debug-Tooling
│   └── debug.py      # Debug-Rendering (Grid, Koordinaten, Info-Text)
├── ui/               # Client-seitige Controller
│   ├── input_controller.py # Ereignisverarbeitung (Mouse/Keyboard)
│   ├── build_controller.py # Optimistisches Bauen & Rollback
│   └── hud_renderer.py     # UI/HUD Rendering
└── main.py           # Entry Point & GameSimulation-Komposition
```

### Neue Sprite-Typen hinzufügen

1. Erstelle neue Klasse in `sprites/`:
```python
from .base import YSortableSprite

class MyNewSprite(YSortableSprite):
    def __init__(self, x, y, image):
        super().__init__(x, y, image)
```

2. In `sprites/__init__.py` exportieren:
```python
from .my_new_sprite import MyNewSprite
__all__ = [..., 'MyNewSprite']
```

3. In `render_manager.py`:
   - Neue Sprite-Gruppe in `__init__` hinzufügen:
   ```python
   self.my_sprites = pygame.sprite.Group()
   ```
   
   - In `_draw_sorted_sprites()` hinzufügen:
   ```python
   all_sprites = (
       list(self.buildings)
       + list(self.units)
       + list(self.decor)
       + list(self.effects)
       + list(self.my_sprites)  # Neue Gruppe hinzufügen
   )
   ```
   
   - Falls animiert, in `update()` hinzufügen:
   ```python
   self.my_sprites.update(dt)
   ```

4. Sprites zur Gruppe hinzufügen:
```python
my_sprite = MyNewSprite(x, y, image)
render_manager.my_sprites.add(my_sprite)
```

### Animierte Sprites (z.B. Wasser)

```python
from sprites.animated import AnimatedSprite

# Frames laden
frames = [loader.load_image(path) for path in water_frames]
water = AnimatedSprite(x, y, frames, frame_duration=0.1)
render_manager.effects.add(water)
```

### Neue Layer hinzufügen

In `rendering/layers.py`:
```python
class RenderLayer(IntEnum):
    # ... bestehende Layer
    NEW_LAYER = 500
```

## Architektur
### High-Level Komponenten
- **Display** (`display/`): kümmert sich um Fenster, Render-Surface und Present.
- **GameSimulation** (`main.py`): Komponiert alle Services und delegiert an Controller/Renderer.
- **Controller-Layer** (`ui/`):
  - `InputController` verarbeitet Eingaben und ruft bei Bedarf Build/HUD-Aktionen auf.
  - `BuildController` managt optimistische Tower-Platzierung, Rollback und lokale Sprites.
  - `HUDRenderer` zeichnet Buttons, Gold/Leben-Anzeige und Rundentimer.
- **Rendering-System** (`rendering/`):
  - `TemplateManager` (aus `assets/`) lädt Assets und liefert Sprite-/Tile-Templates (Single Source of Truth).
  - `SpriteFactory` erzeugt konkrete Unit-/Tower-Sprites und registriert Animationen.
  - `CoordinateTranslator` übersetzt Simulationskoordinaten in Bildschirmpositionen (inkl. Spiegelung für Spieler B).
  - `MapLayerRenderer` zeichnet Wasser, Wege und Foam-Overlays.
  - `RenderManager` orchestriert die Layer (Wasser → Terrain → Wege → Ranges → Y-sortierte Sprites).
- **Maps** (`map/`): Map-Daten, TileMap-Instanzen und statische Hintergründe.
- **Sprites** (`sprites/`): Y-sortierbare Basisklassen sowie konkrete Unit-/Tower-Sprites.
- **Debug** (`debug/`): Overlays für Entwicklungszwecke.

### Rendering Pipeline (SRP-Aufteilung)
1. **TemplateManager** lädt beim Start alle benötigten Assets (Units, Towers, Wasser, Wege, Schlösser) und stellt Factory-Methoden bereit.
2. **SpriteFactory** erzeugt aus Templates konkrete `UnitSprite`-/`BuildingSprite`-Instanzen, hängt sie an die passenden Gruppen und registriert Animations-Updates.
3. **CoordinateTranslator** fragt die aktuellen TileMaps ab und berechnet Bildschirmkoordinaten (inkl. Spiegelung der rechten Map).
4. **MapLayerRenderer** zeichnet Wasser-Tiles, das Foam-Overlay und das Weg-Overlay (aus `RoadRenderer`) auf die gemeinsame Render-Surface.
5. **RenderManager**:
   - initialisiert Wasser, Foam und Wege (inkl. Übergabe des `RoadRenderer` an den `MapLayerRenderer`),
   - synchronisiert Simulationszustand → Sprites über die `SpriteFactory`,
   - sortiert alle Sprites nach Y und blit’t sie gemeinsam.

### Ablauf im Spiel
1. `GameApp` empfängt Server-Events und wandelt sie mithilfe von `_convert_proto_to_sim_data` in interne Datenstrukturen.
2. `GameSimulation` aktualisiert Placement-Grids, steuert Gold/Leben für den Client und delegiert an:
   - `InputController` für Eventhandling,
   - `BuildController` für Tower-Build-Requests und lokale Effekte,
   - `HUDRenderer` für UI,
   - `RenderManager` für das eigentliche Zeichnen.
3. `RenderManager` nutzt `CoordinateTranslator` und `SpriteFactory`, um die Sprites auf Basis des aktuellen Simulationszustands zu platzieren und zu rendern.
4. Der Frame wird über den `DisplayManager` präsentiert.


