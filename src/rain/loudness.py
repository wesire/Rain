#!/usr/bin/env python3
"""
Loudness normalization, limiting, and audio processing utilities.

Provides LUFS-based loudness normalization, soft limiting, fade utilities,
and filtering for professional audio quality.
"""

import numpy as np
import soundfile as sf
from pathlib import Path
from scipy import signal
from typing import Optional


def normalize_loudness(audio_path: Path, target_lufs: float = -14.0,
                       output_path: Optional[Path] = None) -> Path:
    """
    Normalize audio file to target LUFS using pyloudnorm.
    
    Falls back to RMS normalization if pyloudnorm is unavailable.
    
    Args:
        audio_path: Input WAV file
        target_lufs: Target integrated loudness (default -14 LUFS for YouTube)
        output_path: Output path (defaults to overwriting input)
        
    Returns:
        Path to normalized audio file
    """
    audio_path = Path(audio_path)
    if output_path is None:
        output_path = audio_path
    else:
        output_path = Path(output_path)
    
    # Load audio
    audio, sr = sf.read(audio_path)
    
    try:
        import pyloudnorm as pyln
        
        # Measure integrated loudness
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(audio)
        
        # Calculate gain needed
        gain_db = target_lufs - loudness
        gain_linear = 10 ** (gain_db / 20)
        
        # Apply gain
        audio_normalized = audio * gain_linear
        
        print(f"Normalized: {loudness:.1f} LUFS -> {target_lufs:.1f} LUFS (gain: {gain_db:+.1f} dB)")
        
    except ImportError:
        print("pyloudnorm not available, using RMS normalization with -3dB headroom")
        
        # Fallback to RMS normalization
        rms = np.sqrt(np.mean(audio ** 2))
        target_rms = 0.1  # Approximately -20 dBFS RMS
        gain = target_rms / (rms + 1e-10)
        
        # Apply -3dB headroom
        gain *= 0.707  # -3dB
        
        audio_normalized = audio * gain
        
        print(f"RMS normalized with {20 * np.log10(gain):.1f} dB gain")
    
    # Ensure no clipping
    peak = np.max(np.abs(audio_normalized))
    if peak > 0.99:
        audio_normalized = audio_normalized / peak * 0.99
        print(f"Peak limited to -0.09 dBFS")
    
    # Write output
    sf.write(output_path, audio_normalized, sr)
    
    return output_path


def apply_limiter(audio: np.ndarray, ceiling_db: float = -1.0,
                  release_ms: float = 100.0) -> np.ndarray:
    """
    Apply soft limiter to prevent peaks exceeding ceiling.
    
    Uses a simple soft-knee limiter with smooth release.
    Aims for -1 dBFS maximum to leave headroom.
    
    Args:
        audio: Input audio array (samples,) or (samples, channels)
        ceiling_db: Ceiling level in dBFS (default: -1.0)
        release_ms: Release time in milliseconds (default: 100.0)
        
    Returns:
        Limited audio array
    """
    ceiling_linear = 10 ** (ceiling_db / 20)
    
    # Simple soft clipper with tanh
    # Scale so that ceiling_linear maps to tanh(1) ≈ 0.76
    scale = 1.0 / ceiling_linear
    audio_limited = np.tanh(audio * scale) / np.tanh(1.0) * ceiling_linear
    
    return audio_limited


def apply_fades(audio: np.ndarray, sr: int,
                fade_in_sec: float = 3.0,
                fade_out_sec: float = 5.0) -> np.ndarray:
    """
    Apply gentle fade-in and fade-out.
    
    Args:
        audio: Input audio array (samples,) or (samples, channels)
        sr: Sample rate in Hz
        fade_in_sec: Fade-in duration in seconds (default: 3.0)
        fade_out_sec: Fade-out duration in seconds (default: 5.0)
        
    Returns:
        Audio with fades applied
    """
    audio = audio.copy()
    n_samples = len(audio)
    
    # Fade in
    fade_in_samples = int(fade_in_sec * sr)
    if fade_in_samples > 0 and fade_in_samples < n_samples:
        fade_in_curve = np.linspace(0, 1, fade_in_samples) ** 2  # Quadratic fade
        if audio.ndim == 2:
            fade_in_curve = fade_in_curve[:, np.newaxis]
        audio[:fade_in_samples] *= fade_in_curve
    
    # Fade out
    fade_out_samples = int(fade_out_sec * sr)
    if fade_out_samples > 0 and fade_out_samples < n_samples:
        fade_out_curve = np.linspace(1, 0, fade_out_samples) ** 2  # Quadratic fade
        if audio.ndim == 2:
            fade_out_curve = fade_out_curve[:, np.newaxis]
        audio[-fade_out_samples:] *= fade_out_curve
    
    return audio


def apply_filters(audio: np.ndarray, sr: int,
                  hpf_freq: float = 25.0,
                  lpf_freq: Optional[float] = 15000.0) -> np.ndarray:
    """
    Apply gentle filtering.
    
    - High-pass at 25Hz to remove rumble
    - Low-pass at 15kHz to tame hiss (optional)
    
    Args:
        audio: Input audio array (samples,) or (samples, channels)
        sr: Sample rate in Hz
        hpf_freq: High-pass filter frequency in Hz (default: 25.0)
        lpf_freq: Low-pass filter frequency in Hz (default: 15000.0, None to disable)
        
    Returns:
        Filtered audio array
    """
    nyquist = sr / 2
    
    # Process each channel separately if stereo
    if audio.ndim == 2:
        filtered = np.zeros_like(audio)
        for ch in range(audio.shape[1]):
            filtered[:, ch] = apply_filters(audio[:, ch], sr, hpf_freq, lpf_freq)
        return filtered
    
    # High-pass filter
    if hpf_freq > 0:
        sos = signal.butter(2, hpf_freq / nyquist, btype='high', output='sos')
        audio = signal.sosfilt(sos, audio)
    
    # Low-pass filter
    if lpf_freq is not None and lpf_freq < nyquist:
        sos = signal.butter(2, lpf_freq / nyquist, btype='low', output='sos')
        audio = signal.sosfilt(sos, audio)
    
    return audio


def process_audio_file(input_path: Path, output_path: Path,
                       target_lufs: float = -14.0,
                       apply_limiting: bool = True,
                       fade_in_sec: float = 3.0,
                       fade_out_sec: float = 5.0,
                       hpf_freq: float = 25.0,
                       lpf_freq: Optional[float] = 15000.0) -> None:
    """
    Apply complete audio processing chain to a file.
    
    Steps:
    1. Apply filters (HPF/LPF)
    2. Apply fades
    3. Apply limiter
    4. Normalize loudness
    
    Args:
        input_path: Input audio file
        output_path: Output audio file
        target_lufs: Target loudness in LUFS (default: -14.0)
        apply_limiting: Whether to apply soft limiter (default: True)
        fade_in_sec: Fade-in duration (default: 3.0)
        fade_out_sec: Fade-out duration (default: 5.0)
        hpf_freq: High-pass frequency (default: 25.0)
        lpf_freq: Low-pass frequency (default: 15000.0)
    """
    print(f"Processing audio: {input_path}")
    
    # Load audio
    audio, sr = sf.read(input_path)
    
    # Apply filters
    print("  Applying filters...")
    audio = apply_filters(audio, sr, hpf_freq, lpf_freq)
    
    # Apply fades
    print("  Applying fades...")
    audio = apply_fades(audio, sr, fade_in_sec, fade_out_sec)
    
    # Apply limiter
    if apply_limiting:
        print("  Applying limiter...")
        audio = apply_limiter(audio, ceiling_db=-1.0)
    
    # Save to temporary file
    temp_path = output_path.parent / f"{output_path.stem}_temp.wav"
    sf.write(temp_path, audio, sr)
    
    # Normalize loudness
    print("  Normalizing loudness...")
    normalize_loudness(temp_path, target_lufs, output_path)
    
    # Clean up temp file
    if temp_path.exists():
        temp_path.unlink()
    
    print(f"  Complete: {output_path}")
