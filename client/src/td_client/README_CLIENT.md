# TD Client Architecture

## Struktur

td_client/
├── config/           # Konfiguration
│   ├── settings.py   # Game-Einstellungen
│   └── paths.py      # Asset-Pfade
├── assets/           # Asset-Management
│   └── loader.py     # Asset-Loader mit Caching
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
│   ├── render_manager.py # Haupt-Renderer (Orchestriert alle Rendering-Logik)
│   ├── foam_renderer.py # Wasser-Foam Animationen
│   ├── elevation_renderer.py # Klippen/Elevation Rendering
│   └── road_renderer.py # Weg/Straßen Rendering
├── debug/            # Debug-Tooling
│   └── debug.py      # Debug-Rendering (Grid, Koordinaten, Info-Text)
└── main.py           # Entry Point
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

### Unter-Map Assets (Stein-Wände, Wasser)

render_manager.initialize_sprites(
    center_x, center_y, left_map_width, vertical_offset
)
```

## Architektur

- **Display**: Window-Management und Frame Presentation (`display/`)
- **Rendering**: Was wird gezeichnet (`rendering/`)
- **Map**: Map-Daten und TileMap-Definition (`map/`)
- **Sprites**: Sprite-Klassen und -Hierarchie (`sprites/`)
- **Debug**: Development-Tooling (`debug/`)


