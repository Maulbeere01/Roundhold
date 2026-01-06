import io
import logging
from pathlib import Path

import pygame

logger = logging

# Config
_CURRENT_DIR = Path(__file__).parent.absolute()
BASE_PATH = _CURRENT_DIR / "sounds"

FILE_EXTENSIONS = (".wav", ".mp3", ".ogg")


class AudioService:
    _initialized = False  # init flag

    def __init__(self):
        if not AudioService._initialized:
            try:
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.mixer.init()
                AudioService._initialized = True
            except Exception as e:
                logger.error("AudioService initialization error: %s", e)

        self._BASE_PATH = BASE_PATH
        self._cache = {}
        self._sound_volume = 1.0

    # ---- Public APIs ----

    # Generic audio play method
    def play_audio(self, file_path: str) -> None:
        path = Path(file_path)
        if sound := self._get_sound(path):
            pygame.mixer.find_channel(True).play(sound)

    # UI Sounds
    def play_ui_sound(self, sound_name: str) -> None:
        path = self._BASE_PATH / "ui" / sound_name
        if sound := self._get_sound(path):
            sound.play()

    # Unit Sounds
    def play_unit_sound(self, unit_type: str, sound_name: str) -> None:
        path = self._BASE_PATH / "units" / unit_type / sound_name
        if sound := self._get_sound(path):
            pygame.mixer.find_channel(True).play(sound)

    # Environment Sounds
    def play_environment_sound(self, sound_name: str) -> None:
        path = self._BASE_PATH / "environment" / sound_name
        if sound := self._get_sound(path):
            pygame.mixer.find_channel(True).play(sound)

    # Music
    def play_music(self, music_name: str, loops: int = -1) -> None:
        path = self._BASE_PATH / "music" / music_name
        full_path = self._find_file(path)

        if not full_path:
            return

        pygame.mixer.music.load(full_path)
        pygame.mixer.music.play(loops)

    def stop_music(self) -> None:
        pygame.mixer.music.stop()

    # Volume Controls
    def set_music_volume(self, volume: float) -> None:
        pygame.mixer.music.set_volume(volume)

    def set_sound_volume(self, volume: float) -> None:
        self._sound_volume = max(0.0, min(1.0, volume))
        for sound in self._cache.values():
            sound.set_volume(self._sound_volume)

    # ---- Private Utilities ----

    def _find_file(self, path: Path) -> Path | None:
        for ext in FILE_EXTENSIONS:
            p = path.with_suffix(ext)
            if p.exists():
                return p
        return None

    def _get_sound(self, path: Path) -> pygame.mixer.Sound | None:
        if not AudioService._initialized:
            return None

        # Suche Datei
        full_path = None
        for ext in FILE_EXTENSIONS:
            p = path.with_suffix(ext)
            if p.exists():
                full_path = p
                break

        if not full_path:
            return None

        key = str(full_path)
        if key in self._cache:
            return self._cache[key]

        try:
            sound_data = full_path.read_bytes()
            sound = pygame.mixer.Sound(io.BytesIO(sound_data))

            sound.set_volume(self._sound_volume)
            self._cache[key] = sound
            return sound
        except Exception as e:
            logger.error("Loading sound failed (%s): %s", full_path.name, e)
            return None
