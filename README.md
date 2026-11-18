# 可以把音乐变难听的 Skill

A Codex skill for making short, intentionally dissonant audio previews while keeping a melody recognizable.

## Twinkle Twinkle Little Star demo

Both clips are synthetic performances of the traditional public-domain melody. No commercial song or copyrighted recording is included.

- [Clean synthetic reference](examples/twinkle-clean-reference.m4a)
- [Sharper, dissonant broken-speaker treatment](examples/twinkle-sharper-dissonant.m4a)
- Open [the comparison player](examples/index.html) in a browser for side-by-side playback.

## Install

Copy this directory to `~/.codex/skills/make-music-sound-worse`.

## Render a preview

```sh
python scripts/make_dissonance.py /path/to/song.mp3 --effect harsh-speaker --start 20 --duration 12 --output-dir ./preview
```

Available effects: `offkey-shadow`, `microdetune`, `rhythm-offset`, `harsh-speaker`, and `all`.

The processor leaves the input untouched. It requires Python packages `numpy`, `scipy`, and `librosa`; local `ffmpeg` or macOS `afconvert` is used for MP3/M4A decoding and M4A export when available. Outputs are exploratory listening demos, not validated driving-safety alerts.
