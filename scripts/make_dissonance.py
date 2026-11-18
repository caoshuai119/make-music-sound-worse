#!/usr/bin/env python3
"""Render recognizable dissonance previews from a supplied audio file."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

import librosa
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, iirpeak, lfilter, resample_poly, sosfiltfilt


def read_pcm(path: Path) -> tuple[int, np.ndarray]:
    """Decode common audio formats locally and return float32 stereo audio."""
    temp_context = None
    decoded = path
    if path.suffix.lower() not in {".wav", ".wave"}:
        temp_context = tempfile.TemporaryDirectory(prefix="dissonance_audio_")
        decoded = Path(temp_context.name) / "decoded.wav"
        ffmpeg = shutil.which("ffmpeg")
        afconvert = shutil.which("afconvert")
        if ffmpeg:
            command = [ffmpeg, "-v", "error", "-y", "-i", str(path), "-ac", "2", "-ar", "44100", str(decoded)]
        elif afconvert:
            command = [afconvert, "-f", "WAVE", "-d", "LEI16", "-c", "2", str(path), str(decoded)]
        else:
            temp_context.cleanup()
            raise RuntimeError("For MP3/M4A input, install no packages automatically; use local ffmpeg or macOS afconvert to decode it.")
        subprocess.run(command, check=True, capture_output=True)

    try:
        sr, data = wavfile.read(decoded)
        if np.issubdtype(data.dtype, np.integer):
            scale = float(max(abs(np.iinfo(data.dtype).min), np.iinfo(data.dtype).max))
            audio = data.astype(np.float32) / scale
        else:
            audio = data.astype(np.float32)
    finally:
        if temp_context:
            temp_context.cleanup()

    if audio.ndim == 1:
        audio = np.column_stack((audio, audio))
    elif audio.shape[1] > 2:
        audio = audio[:, :2]
    if sr != 44100:
        from math import gcd

        factor = gcd(44100, sr)
        audio = resample_poly(audio, 44100 // factor, sr // factor, axis=0).astype(np.float32)
        sr = 44100
    return sr, np.nan_to_num(audio)


def shift_channels(audio: np.ndarray, sr: int, semitones: float) -> np.ndarray:
    return np.stack(
        [librosa.effects.pitch_shift(audio[:, channel], sr=sr, n_steps=semitones) for channel in range(audio.shape[1])],
        axis=1,
    ).astype(np.float32)


def distort_small_speaker(audio: np.ndarray, sr: int, intensity: float) -> np.ndarray:
    mono = audio.mean(axis=1)
    band = butter(4, [420, 4700], btype="bandpass", fs=sr, output="sos")
    result = sosfiltfilt(band, mono)
    for frequency, quality, gain in ((2250, 6, 1.35), (3350, 7, 1.10)):
        b, a = iirpeak(frequency, Q=quality, fs=sr)
        result = result + lfilter(b, a, result) * gain * intensity
    result = resample_poly(result, 1, 5)
    result = resample_poly(result, 5, 1)[: len(mono)]
    result = np.clip(result * (2.8 + 1.0 * intensity) + 0.04, -0.38, 0.38)
    result = np.tanh(result * (1.8 + 0.8 * intensity))
    return np.column_stack((result, result)).astype(np.float32)


def process(audio: np.ndarray, sr: int, effect: str, intensity: float) -> np.ndarray:
    strength = float(np.clip(intensity, 0.25, 1.75))
    if effect == "offkey-shadow":
        up = shift_channels(audio, sr, 1.0)
        down = shift_channels(audio, sr, -1.0)
        result = audio * 0.78 + up * (0.34 * strength) + down * (0.25 * strength)
    elif effect == "microdetune":
        shifted = shift_channels(audio, sr, 0.25)
        delay = int(0.040 * sr)
        delayed = np.pad(shifted, ((delay, 0), (0, 0)))[: len(audio)]
        result = audio * 0.78 + delayed * (0.38 * strength)
    elif effect == "rhythm-offset":
        delay = int(0.070 * sr)
        delayed = np.pad(audio, ((delay, 0), (0, 0)))[: len(audio)]
        result = audio * 0.78 + delayed * (0.40 * strength)
    elif effect == "harsh-speaker":
        up = shift_channels(audio, sr, 1.0)
        down = shift_channels(audio, sr, -1.0)
        dissonant = audio * 0.76 + up * (0.40 * strength) + down * (0.30 * strength)
        result = distort_small_speaker(dissonant, sr, strength)
    else:
        raise ValueError(f"Unknown effect: {effect}")

    peak = float(np.max(np.abs(result)))
    if peak > 1e-9:
        result = result * min(0.96 / peak, 1.0)
    return np.clip(result, -0.98, 0.98)


def save_outputs(audio: np.ndarray, sr: int, stem: str, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / f"{stem}.wav"
    wavfile.write(wav_path, sr, (audio * 32767).astype(np.int16))
    outputs = [wav_path]
    converter = shutil.which("afconvert")
    ffmpeg = shutil.which("ffmpeg")
    m4a_path = output_dir / f"{stem}.m4a"
    if converter:
        subprocess.run([converter, "-f", "m4af", "-d", "aac", "-b", "256000", str(wav_path), str(m4a_path)], check=True)
        outputs.append(m4a_path)
    elif ffmpeg:
        subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(wav_path), "-c:a", "aac", "-b:a", "256k", str(m4a_path)], check=True)
        outputs.append(m4a_path)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Source audio; the source is never modified")
    parser.add_argument("--effect", choices=("offkey-shadow", "microdetune", "rhythm-offset", "harsh-speaker", "all"), default="harsh-speaker")
    parser.add_argument("--start", type=float, default=20.0, help="Preview start time in seconds (default: 20; clamped for short files)")
    parser.add_argument("--duration", type=float, default=12.0, help="Preview length in seconds")
    parser.add_argument("--intensity", type=float, default=1.0, help="Effect strength, normally 0.5 to 1.5")
    parser.add_argument("--output-dir", type=Path, default=None, help="Defaults to a sibling <source>_dissonance folder")
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"Input file not found: {args.input}")
    if args.duration <= 0:
        parser.error("--duration must be positive")

    sr, full_audio = read_pcm(args.input)
    start = max(0.0, min(args.start, max(0.0, len(full_audio) / sr - 0.1)))
    begin = int(start * sr)
    end = min(len(full_audio), begin + int(args.duration * sr))
    excerpt = full_audio[begin:end]
    if len(excerpt) < sr:
        parser.error("The selected excerpt must contain at least one second of audio")

    output_dir = args.output_dir or args.input.parent / f"{args.input.stem}_dissonance"
    effects = ("offkey-shadow", "microdetune", "rhythm-offset", "harsh-speaker") if args.effect == "all" else (args.effect,)
    for effect in effects:
        stem = f"{args.input.stem}_{effect}"
        paths = save_outputs(process(excerpt, sr, effect, args.intensity), sr, stem, output_dir)
        print("\n".join(str(path) for path in paths))


if __name__ == "__main__":
    main()
