from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pygame

from ..config import AssetPaths


class AssetLoader:
    """Centralized asset loader with caching.
    
    Provides methods for loading images and
    extracting frames from spritesheets.
    """
    
    def __init__(self, asset_paths: AssetPaths):
        """Init asset loader.
        
        Args:
            asset_paths: AssetPaths instance for path management
        """
        self.paths = asset_paths
        self._cache: Dict[str, pygame.Surface] = {}
    
    def scale_surface(
        self,
        surface: pygame.Surface,
        scale_factor: Optional[float] = None,
        scale_to_size: Optional[Tuple[int, int]] = None,
    ) -> pygame.Surface:
        """Scale a pygame.Surface by factor or to a specific size.
        
        Args:
            surface: Source surface to scale
            scale_factor: Optional scale factor (e.g., 0.5 for 50% size)
            scale_to_size: Optional explicit size (width, height)
        
        Returns:
            Scaled surface if scaling requested, otherwise the original surface.
        """
        if scale_to_size:
            return pygame.transform.scale(surface, scale_to_size)
        if scale_factor:
            original_size = surface.get_size()
            new_size = (
                int(original_size[0] * scale_factor),
                int(original_size[1] * scale_factor),
            )
            return pygame.transform.scale(surface, new_size)
        return surface
    
    def load_image(
        self,
        path: Path,
        *,
        scale_factor: Optional[float] = None,
        scale_to_size: Optional[Tuple[int, int]] = None,
    ) -> pygame.Surface:
        """Load an image with caching, optionally scale it.
        
        Args:
            path: Path to the image file
            scale_factor: Optional scale factor. If provided, the loaded image is scaled.
            scale_to_size: Optional explicit target size. Takes precedence over scale_factor.
        Returns:
            Loaded pygame.Surface (scaled if a scale parameter is provided)
            
        Raises:
            FileNotFoundError: If the asset file does not exist
        """
        path_str = str(path)
        
        if path_str in self._cache:
            base_image = self._cache[path_str]
            if not scale_factor and not scale_to_size:
                return base_image
            return self.scale_surface(base_image, scale_factor=scale_factor, scale_to_size=scale_to_size)
        
        if not path.exists():
            raise FileNotFoundError(f"Asset not found: {path}")
        
        image = pygame.image.load(path_str)
        # Auto-detect per-pixel alpha and convert accordingl
        if image.get_flags() & pygame.SRCALPHA:
            image = image.convert_alpha()
        else:
            image = image.convert()
        
        self._cache[path_str] = image
        return self.scale_surface(image, scale_factor=scale_factor, scale_to_size=scale_to_size)
    
    def load_spritesheet(
        self,
        path: Path,
        frame_count: int,
        frame_size: Optional[Tuple[int, int]] = None,
        direction: str = "horizontal",
        scale_factor: Optional[float] = None,
        scale_to_size: Optional[Tuple[int, int]] = None
    ) -> List[pygame.Surface]:
        """Load and slice a spritesheet into individual frames.
        
        Args:
            path: Path to the spritesheet file
            frame_count: Number of frames in the spritesheet
            frame_size: Optional (width, height) of each frame. If None, calculates automatically
            direction: "horizontal" or "vertical" frame layout
            scale_factor: Optional scale factor to apply to each frame (e.g., 0.5 for 50% size)
            scale_to_size: Optional target size (width, height) to scale each frame to
            
        Returns:
            List of pygame.Surface frames (scaled if scale_factor or scale_to_size provided)
            
        Raises:
            ValueError: If direction is invalid or frame_count is invalid
        """
        if frame_count <= 0:
            raise ValueError("frame_count must be positive")
        
        if direction not in ("horizontal", "vertical"):
            raise ValueError("direction must be 'horizontal' or 'vertical'")
        
        spritesheet = self.load_image(path)
        sheet_width, sheet_height = spritesheet.get_size()
        
        if frame_size:
            frame_width, frame_height = frame_size
        else:
            if direction == "horizontal":
                frame_width = sheet_width // frame_count
                frame_height = sheet_height
            else:
                frame_width = sheet_width
                frame_height = sheet_height // frame_count
        
        frames = []
        for i in range(frame_count):
            if direction == "horizontal":
                x = i * frame_width
                y = 0
            else:
                x = 0
                y = i * frame_height
            
            frame_rect = pygame.Rect(x, y, frame_width, frame_height)
            frame = spritesheet.subsurface(frame_rect).copy()
            frame = frame.convert_alpha()
            
            frame = self.scale_surface(frame, scale_factor=scale_factor, scale_to_size=scale_to_size)
            
            frames.append(frame)
        
        return frames
