from __future__ import annotations

import pygame

from ..sprites.buildings import BuildingSprite
from ..sprites.units import UnitSprite
from ..sprites.effects import OneShotEffect

class SpriteFactory:
    """Creates sprites from templates and registers them with animation manager"""

    def __init__(self, template_manager, animation_manager) -> None:
        self.template_manager = template_manager
        self.animation_manager = animation_manager
        self.unit_sprites: dict[int, UnitSprite] = {}
        self.tower_sprites: dict[int, BuildingSprite] = {}
        self.units_group = None
        self.towers_group = None

    def configure_groups(self, units_group, towers_group, effects_group=None):
        self.units_group = units_group
        self.towers_group = towers_group
        self.effects_group = effects_group if effects_group else units_group

    def create_effect(self, x: float, y: float, effect_name: str) -> None:
        """Spawns a visual effect at the given position."""
        frames = self.template_manager.get_effect_template(effect_name)
        
        # Create the effect sprite
        effect = OneShotEffect(x, y, frames, fps=15.0)
        
        # Add to group and animation manager
        self.effects_group.add(effect)
        self.animation_manager.register(effect)

    def create_unit_sprite(
        self, entity_id: int, unit_type: str, player_id: str, x: float, y: float
    ) -> UnitSprite:
        # We expect a dict
        frames_dict = self.template_manager.get_unit_template(
            unit_type, player_id
        )

        # We create the dust immediately when the unit is created
        self.create_effect(x, y, "spawn_dust")

        # Pass dic to the sprite
        sprite = UnitSprite(x=x, y=y, anim_dict=frames_dict, entity_id=entity_id)

        def on_death_callback(pos_x, pos_y):
            self.create_effect(pos_x, pos_y, "explosion")

        sprite = UnitSprite(
            x=x, y=y, 
            anim_dict=frames_dict, 
            entity_id=entity_id,
            on_death=on_death_callback # <--- Passing the callback
        )

        self.units_group.add(sprite)
        self.unit_sprites[entity_id] = sprite
        self.animation_manager.register(sprite)
        return sprite

    def create_tower_sprite(
        self, entity_id: int, tower_type: str, x: float, y: float, range_px: float
    ) -> BuildingSprite | None:
        
        # Get the static image
        image = self.template_manager.get_tower_template(tower_type)
        
        if not image:
            return None
            
        # Create static sprite
        # Note: midbottom=(x, y) aligns the tower's base with the tile center
        sprite = BuildingSprite(
            x=x, y=y, 
            image=image, 
            entity_id=entity_id, 
            range_px=range_px
        )
        
        self.towers_group.add(sprite)
        self.tower_sprites[entity_id] = sprite
        
        # Note: We do NOT register towers with animation_manager because they are static
        return sprite

    def remove_unit_sprite(self, entity_id: int) -> None:
        sprite = self.unit_sprites.pop(entity_id, None)
        if sprite:
            sprite.trigger_base_attack()

    def remove_tower_sprite(self, entity_id: int) -> None:
        sprite = self.tower_sprites.pop(entity_id, None)
        if sprite:
            sprite.kill()

    def get_unit_sprite(self, entity_id: int) -> UnitSprite | None:
        return self.unit_sprites.get(entity_id)

    def get_tower_sprite(self, entity_id: int) -> BuildingSprite | None:
        return self.tower_sprites.get(entity_id)
