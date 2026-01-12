from pathlib import Path

import pygame

# Config
BASE_PATH = Path(__file__).parent / "sounds"
FILE_EXTENSIONS = (".wav", ".mp3", ".ogg")

# Channel configuration
CHANNEL_UI = 0
CHANNEL_UNITS = 1
CHANNEL_ENVIRONMENT = 2


class AudioService:
    _initialized = False  # init flag

    def __init__(self):
        if not AudioService._initialized:
            try:
                pygame.mixer.init()
                pygame.mixer.set_num_channels(8)  
                AudioService._initialized = True
            except pygame.error:
                AudioService._initialized = False

        self._BASE_PATH = BASE_PATH
        self._cache: dict[str, pygame.mixer.Sound] = {}
        self._sound_volume = 1.0  # Default volume

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
            self._play_on_channel(sound, CHANNEL_UI)

    # Unit Sounds
    def play_unit_sound(self, unit_type: str, sound_name: str) -> None:
        path = self._BASE_PATH / "units" / unit_type / sound_name
        if sound := self._get_sound(path):
            self._play_on_channel(sound, CHANNEL_UNITS)

    # Environment Sounds
    def play_environment_sound(self, sound_name: str) -> None:
        path = self._BASE_PATH / "environment" / sound_name
        if sound := self._get_sound(path):
            self._play_on_channel(sound, CHANNEL_ENVIRONMENT)

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

    def _play_on_channel(self, sound: pygame.mixer.Sound, channel_id: int) -> None:
        """Play sound on specific channel, new sound automatically stops and replaces the old one."""
        channel = pygame.mixer.Channel(channel_id)
        channel.play(sound) 

    def _get_sound(self, path: Path) -> pygame.mixer.Sound | None:
        if not AudioService._initialized:
            return None

        key = str(path)

        if key in self._cache:
            return self._cache[key]

        full_path = self._find_file(path)
        if not full_path:
            return None

        sound = pygame.mixer.Sound(full_path)
        sound.set_volume(self._sound_volume)
        self._cache[key] = sound
        return sound

    def _find_file(self, path: Path) -> Path | None:
        for ext in FILE_EXTENSIONS:
            full_path = path.with_suffix(ext)
            if full_path.exists():
                return full_path
        return None
