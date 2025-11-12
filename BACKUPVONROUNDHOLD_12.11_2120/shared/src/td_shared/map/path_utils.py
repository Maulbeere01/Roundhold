from __future__ import annotations

from typing import Dict, List, Tuple


def mirror_paths_for_width(paths: Dict[int, List[Tuple[int, int]]], width_tiles: int) -> Dict[int, List[Tuple[int, int]]]:
    """Mirror path column indices across a grid of width_tiles."""
    mirrored: Dict[int, List[Tuple[int, int]]] = {}
    for route, tiles in paths.items():
        mirrored[route] = [(int(r), (width_tiles - 1) - int(c)) for r, c in tiles]
    return mirrored


def infer_height_from_paths(paths: Dict[int, List[Tuple[int, int]]]) -> int:
    """Infer grid height from maximum row index in paths."""
    max_row = 0
    for tiles in paths.values():
        for r, _ in tiles:
            ir = int(r)
            if ir > max_row:
                max_row = ir
    return max_row + 1


