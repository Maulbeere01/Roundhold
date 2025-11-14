from __future__ import annotations

import pygame

from ..sprites.buildings import BuildingSprite
from ..sprites.units import UnitSprite


class SpriteFactory:
    """Creates sprites from templates and registers them with animation manager"""

    def __init__(self, template_manager, animation_manager) -> None:
        self.template_manager = template_manager
        self.animation_manager = animation_manager
        self.unit_sprites: dict[int, UnitSprite] = {}
        self.tower_sprites: dict[int, BuildingSprite] = {}
        self.units_group = None
        self.towers_group = None

    def configure_groups(self, units_group, towers_group) -> None:
        self.units_group = units_group
        self.towers_group = towers_group

    def create_unit_sprite(
        self, entity_id: int, unit_type: str, player_id: str, x: float, y: float
    ) -> UnitSprite:
        frames: list[pygame.Surface] = self.template_manager.get_unit_template(
            unit_type, player_id
        )
        sprite = UnitSprite(x=x, y=y, frames=frames, entity_id=entity_id)
        self.units_group.add(sprite)
        self.unit_sprites[entity_id] = sprite
        self.animation_manager.register(sprite)
        return sprite

    def create_tower_sprite(
        self, entity_id: int, tower_type: str, x: float, y: float, range_px: float
    ) -> BuildingSprite | None:
        image = self.template_manager.get_tower_template(tower_type)
        if not image:
            return None
        sprite = BuildingSprite(
            x=x, y=y, image=image, entity_id=entity_id, range_px=range_px
        )
        self.towers_group.add(sprite)
        self.tower_sprites[entity_id] = sprite
        return sprite

    def remove_unit_sprite(self, entity_id: int) -> None:
        sprite = self.unit_sprites.pop(entity_id, None)
        if sprite:
            sprite.kill()
            self.animation_manager.unregister(sprite)

    def remove_tower_sprite(self, entity_id: int) -> None:
        sprite = self.tower_sprites.pop(entity_id, None)
        if sprite:
            sprite.kill()

    def get_unit_sprite(self, entity_id: int) -> UnitSprite | None:
        return self.unit_sprites.get(entity_id)

    def get_tower_sprite(self, entity_id: int) -> BuildingSprite | None:
        return self.tower_sprites.get(entity_id)
