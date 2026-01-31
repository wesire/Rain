#!/usr/bin/env python3
"""
Analyze audio file and print quality metrics.

Usage: python scripts/analyze_audio.py output.wav

Output:
    Peak: -1.2 dBFS ✓
    Integrated Loudness: -14.1 LUFS ✓
    Clipping: None detected ✓
    Duration: 8:00:00
    Sample Rate: 48000 Hz
    Channels: 2 (stereo)
"""

import sys
import numpy as np
from pathlib import Path


def analyze(audio_path: str):
    """
    Analyze audio file and print quality metrics.
    
    Args:
        audio_path: Path to audio file
    """
    try:
        import soundfile as sf
    except ImportError:
        print("Error: soundfile not installed. Install with: pip install soundfile")
        sys.exit(1)
    
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)
    
    print(f"Analyzing: {audio_path}\n")
    
    # Load audio
    try:
        audio, sr = sf.read(audio_path)
    except Exception as e:
        print(f"Error loading audio: {e}")
        sys.exit(1)
    
    # Basic info
    duration_seconds = len(audio) / sr
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)
    seconds = int(duration_seconds % 60)
    
    channels = audio.shape[1] if audio.ndim == 2 else 1
    channel_str = "stereo" if channels == 2 else "mono"
    
    # Peak analysis
    peak = np.max(np.abs(audio))
    peak_db = 20 * np.log10(peak) if peak > 0 else -np.inf
    
    # Peak status
    if peak_db > -0.5:
        peak_status = "⚠️  (may clip)"
    elif peak_db > -1.5:
        peak_status = "✓"
    else:
        peak_status = "✓ (conservative)"
    
    # Clipping detection
    num_clipped = np.sum(np.abs(audio) >= 0.99)
    if num_clipped > 0:
        clip_status = f"✗ {num_clipped} samples clipped"
    else:
        clip_status = "✓ None detected"
    
    # RMS level
    rms = np.sqrt(np.mean(audio ** 2))
    rms_db = 20 * np.log10(rms) if rms > 0 else -np.inf
    
    # LUFS (if pyloudnorm available)
    loudness = None
    try:
        import pyloudnorm as pyln
        meter = pyln.Meter(sr)
        loudness = meter.integrated_loudness(audio)
        
        # Loudness status
        if -15.0 <= loudness <= -13.0:
            loudness_status = "✓ (YouTube standard)"
        elif -16.0 <= loudness <= -12.0:
            loudness_status = "✓"
        else:
            loudness_status = "⚠️  (outside typical range)"
            
    except ImportError:
        loudness_status = "(pyloudnorm not available)"
    
    # Dynamic range
    if audio.ndim == 2:
        dynamic_range_l = np.max(audio[:, 0]) - np.min(audio[:, 0])
        dynamic_range_r = np.max(audio[:, 1]) - np.min(audio[:, 1])
        dynamic_range = (dynamic_range_l + dynamic_range_r) / 2
    else:
        dynamic_range = np.max(audio) - np.min(audio)
    
    dynamic_range_db = 20 * np.log10(dynamic_range) if dynamic_range > 0 else -np.inf
    
    # Band energy analysis (detect "tinny" or "fire crackle" sound)
    bands = {
        'low (<500Hz)': (20, 500),
        'mid (500-2kHz)': (500, 2000),
        'high-mid (2-8kHz)': (2000, 8000),
        'high (>8kHz)': (8000, sr // 2)
    }
    
    band_energies = {}
    from scipy import signal as scipy_signal
    for name, (low, high) in bands.items():
        try:
            sos = scipy_signal.butter(4, [low, min(high, sr // 2 - 1)], btype='band', fs=sr, output='sos')
            if audio.ndim == 2:
                filtered = scipy_signal.sosfilt(sos, audio[:, 0])
            else:
                filtered = scipy_signal.sosfilt(sos, audio)
            energy = np.mean(filtered ** 2)
            band_energies[name] = energy
        except:
            band_energies[name] = 0.0
    
    total_energy = sum(band_energies.values())
    if total_energy > 0:
        band_ratios = {k: v / total_energy * 100 for k, v in band_energies.items()}
    else:
        band_ratios = {k: 0.0 for k in band_energies.keys()}
    
    # Print results
    print("=" * 50)
    print("AUDIO QUALITY METRICS")
    print("=" * 50)
    print()
    
    print(f"Peak:                 {peak_db:>7.1f} dBFS {peak_status}")
    print(f"RMS Level:            {rms_db:>7.1f} dBFS")
    
    if loudness is not None:
        print(f"Integrated Loudness:  {loudness:>7.1f} LUFS {loudness_status}")
    else:
        print(f"Integrated Loudness:  {loudness_status}")
    
    print(f"Dynamic Range:        {dynamic_range_db:>7.1f} dB")
    print(f"Clipping:             {clip_status}")
    print()
    
    # Band energy distribution
    print("=" * 50)
    print("FREQUENCY BAND ENERGY")
    print("=" * 50)
    print()
    
    for band, ratio in band_ratios.items():
        warning = ""
        if "2-8kHz" in band and ratio > 35:
            warning = " ⚠️  HIGH - may sound tinny/crackly"
        elif "2-8kHz" in band and ratio > 25:
            warning = " ⚠️  Elevated"
        elif "2-8kHz" in band and ratio < 20:
            warning = " ✓ Good for sleep"
        print(f"  {band:20s}: {ratio:>5.1f}%{warning}")
    print()
    
    print("=" * 50)
    print("FILE INFORMATION")
    print("=" * 50)
    print()
    
    print(f"Duration:             {hours}:{minutes:02d}:{seconds:02d}")
    print(f"Sample Rate:          {sr} Hz")
    print(f"Channels:             {channels} ({channel_str})")
    print(f"Bit Depth:            {audio.dtype}")
    
    # File size
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    print(f"File Size:            {file_size_mb:.1f} MB")
    print()
    
    # Stereo analysis
    if channels == 2:
        print("=" * 50)
        print("STEREO ANALYSIS")
        print("=" * 50)
        print()
        
        peak_l = np.max(np.abs(audio[:, 0]))
        peak_r = np.max(np.abs(audio[:, 1]))
        peak_l_db = 20 * np.log10(peak_l) if peak_l > 0 else -np.inf
        peak_r_db = 20 * np.log10(peak_r) if peak_r > 0 else -np.inf
        
        print(f"Left Peak:            {peak_l_db:>7.1f} dBFS")
        print(f"Right Peak:           {peak_r_db:>7.1f} dBFS")
        
        # Correlation
        correlation = np.corrcoef(audio[:, 0], audio[:, 1])[0, 1]
        print(f"Stereo Correlation:   {correlation:>7.3f}")
        
        if correlation > 0.95:
            print("                      (⚠️  nearly mono)")
        elif correlation > 0.7:
            print("                      (✓ good stereo image)")
        else:
            print("                      (✓ wide stereo image)")
        
        print()
    
    print("=" * 50)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_audio.py <audio_file>")
        print()
        print("Example: python scripts/analyze_audio.py output.wav")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    analyze(audio_path)


if __name__ == '__main__':
    main()
