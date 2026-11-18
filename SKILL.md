---
name: make-music-sound-worse
description: Create deliberately dissonant, off-key audio previews that preserve a song's recognizable melody. Use when the user wants to alter supplied music with detuning, timing clashes, harsh resonance, or broken-speaker distortion.
---

# Recognizable Dissonance Audio

Make short, listenable concept previews that keep the original tune perceptible while adding controlled musical discomfort. Work from the user's supplied audio and save new outputs beside the requested destination; never overwrite the source.

## Workflow

1. Confirm the source file exists and inspect its duration and format. If the user supplied a passage or intensity, follow it. Otherwise use a 12-second excerpt starting around 20 seconds, falling back to the beginning for shorter tracks.
2. Choose a treatment that matches the request, or render a small set of clearly named alternatives when the user asks to compare approaches. Prefer the included script for repeatable renders:

   ```sh
   python scripts/make_dissonance.py /path/to/song.mp3 --effect all --output-dir /path/to/output
   ```

   Supported effects: `offkey-shadow` (semitone-shifted melodic copies), `microdetune` (25-cent copy with a short offset), `rhythm-offset` (delayed copy), `harsh-speaker` (detuned layers, narrow-band resonance, and clipping), and `all`.

3. Keep the original audible under the effect. Increase discomfort through pitch conflict, beating, timing smear, resonance, or saturation before making the track unrecognizable. Avoid relying only on high notes; broad-band or midrange processing works on songs with different vocal ranges.
4. If the source is a mixed master, describe the render as an overlay or whole-mix treatment. Do not claim that only the accompaniment, vocals, or chords changed unless stems were actually separated and processed independently.
5. Export a WAV and, when `afconvert` or `ffmpeg` is available, a convenient M4A preview. Provide the exact file links and briefly describe the audible difference. Keep the source untouched.

## Audio constraints

- The distortion and dissonance are exploratory design stimuli, not validated driving-safety alerts. Do not imply that a harsher sound improves attention or safety.
- Do not make sudden full-volume jumps. Normalize peaks conservatively and retain the recognizability of the supplied song.
- If stem separation would materially improve the requested result, explain that a mixed master cannot isolate accompaniment and ask for stems only if the next step depends on them. Continue with a clearly labeled whole-mix approximation when useful.
- Do not install dependencies or upload audio to third-party services without the user's explicit request. If local processing dependencies are unavailable, explain the limitation and offer a local workflow.

## Included processor

`scripts/make_dissonance.py` renders the treatments above from common audio files. It uses local decoding (`afconvert` on macOS or `ffmpeg`) and Python packages `numpy`, `scipy`, and `librosa`; check availability before running and do not install packages unless asked.
