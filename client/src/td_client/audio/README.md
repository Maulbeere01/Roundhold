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

UI Sounds (z.B. Button clicks)<br>
`audio.play_ui_sound("click")`  # spielt sounds/ui/click.wav

Unit Sounds<br>
`audio.play_unit_sound("archer", "attack")`  # sounds/units/archer/attack.wav

Environment<br>
`audio.play_environment_sound("wind")`  # sounds/environment/wind.ogg

Generic / Custom Path<br>
`audio.play_audio("custom/path/sound")`

## Musik

Musik starten (loopt default endlos)<br>
`audio.play_music("battle_theme")`

Einmal abspielen<br>
`audio.play_music("victory", loops=0)`

Stoppen<br>
`audio.stop_music()`

## Lautstärke

Sound Effects (0.0 - 1.0)<br>
`audio.set_sound_volume(0.5)`

Musik (0.0 - 1.0)<br>
`audio.set_music_volume(0.3)`

## APIs nutzen

In Screens -> `self.app.audio...`<br>
In Controller -> `game.audio...`<br>
In Simulation -> `self.audio...`<br>
