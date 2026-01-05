# AudioService API
Audio System für Tower Defense Game.

## Setup
`audio = AudioService()`

## Folder Structure

```md
sounds/
├── ui/
├── units/
│   ├── archer/
│   ├── knight/
│   └── ...
├── environment/
└── music/
```

Unterstützte Formate: `.wav, .mp3, .ogg`

## APIs

UI Sounds (z.B. Button clicks)
`audio.play_ui_sound("click")`  # spielt sounds/ui/click.wav

Unit Sounds
`audio.play_unit_sound("archer", "attack")`  # sounds/units/archer/attack.wav

Environment
`audio.play_environment_sound("wind")`  # sounds/environment/wind.ogg

Generic / Custom Path
`audio.play_audio("custom/path/sound")`

## Musik

Musik starten (loopt default endlos)
`audio.play_music("battle_theme")`

Einmal abspielen
`audio.play_music("victory", loops=0)`

Stoppen
`audio.stop_music()`

## Lautstärke

Sound Effects (0.0 - 1.0)
`audio.set_sound_volume(0.5)`

Musik (0.0 - 1.0)
`audio.set_music_volume(0.3)`
