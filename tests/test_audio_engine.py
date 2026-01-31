#!/usr/bin/env python3
"""
Tests for Rain audio generation system.

Tests cover:
- Crossfade continuity (no clicks)
- Output peak levels (no clipping)
- Stereo output verification
- Audio quality metrics
"""

import pytest
import numpy as np
import tempfile
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rain.audio_engine import (
    AudioAssetLoader, 
    RainAudioEngine, 
    equal_power_crossfade,
    overlap_add
)
from rain.loudness import apply_limiter, apply_fades, apply_filters


def test_crossfade_continuity():
    """Verify no large discontinuity at crossfade boundary."""
    # Create two test signals
    sr = 48000
    duration = 1.0
    samples = int(duration * sr)
    
    # Sine waves at different frequencies
    t = np.linspace(0, duration, samples)
    audio1 = np.sin(2 * np.pi * 440 * t)  # A4
    audio2 = np.sin(2 * np.pi * 880 * t)  # A5
    
    # Make stereo
    audio1 = np.stack([audio1, audio1], axis=1).astype(np.float32)
    audio2 = np.stack([audio2, audio2], axis=1).astype(np.float32)
    
    # Apply crossfade
    fade_samples = int(0.1 * sr)  # 100ms crossfade
    crossfaded = equal_power_crossfade(audio1, audio2, fade_samples)
    
    # Check for continuity at crossfade boundary
    # Calculate sample-to-sample differences
    diffs = np.abs(np.diff(crossfaded[:, 0]))
    max_diff = np.max(diffs)
    
    # Should have no large discontinuities (no clicks)
    # Normal sine wave has max diff ~0.002, allow 10x margin
    assert max_diff < 0.02, f"Large discontinuity detected: {max_diff}"
    
    print(f"✓ Crossfade continuity test passed (max diff: {max_diff:.6f})")


def test_output_peak_below_ceiling():
    """Verify output never exceeds -1 dBFS after limiting."""
    # Generate test signal with peaks above ceiling
    samples = 48000
    audio = np.random.randn(samples, 2).astype(np.float32) * 2.0  # Overloaded
    
    # Apply limiter
    limited = apply_limiter(audio, ceiling_db=-1.0)
    
    # Check peak
    peak = np.max(np.abs(limited))
    ceiling_linear = 10 ** (-1.0 / 20)  # -1 dBFS in linear
    
    assert peak <= ceiling_linear * 1.01, f"Peak {peak} exceeds ceiling {ceiling_linear}"
    
    peak_db = 20 * np.log10(peak) if peak > 0 else -np.inf
    print(f"✓ Peak limiting test passed (peak: {peak_db:.1f} dBFS)")


def test_no_clipping():
    """Verify no samples exceed 1.0 (0 dBFS)."""
    # Generate test audio
    sr = 48000
    duration = 0.5
    samples = int(duration * sr)
    
    # Create audio that might clip
    audio = np.random.randn(samples, 2).astype(np.float32) * 0.5
    
    # Apply processing
    audio = apply_filters(audio, sr, hpf_freq=25.0, lpf_freq=15000.0)
    audio = apply_fades(audio, sr, fade_in_sec=0.1, fade_out_sec=0.1)
    audio = apply_limiter(audio, ceiling_db=-1.0)
    
    # Check for clipping
    max_sample = np.max(np.abs(audio))
    assert max_sample < 1.0, f"Clipping detected: {max_sample}"
    
    print(f"✓ No clipping test passed (max sample: {max_sample:.4f})")


def test_stereo_output():
    """Verify output is stereo (2 channels)."""
    # Create a temporary assets directory
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = Path(tmpdir) / 'assets'
        assets_dir.mkdir()
        (assets_dir / 'audio').mkdir()
        (assets_dir / 'audio' / 'bed').mkdir()
        (assets_dir / 'audio' / 'details').mkdir()
        (assets_dir / 'audio' / 'thunder').mkdir()
        
        # Create loader (will use fallback since no assets)
        loader = AudioAssetLoader(assets_dir, target_sr=48000)
        loader.load_all()
        
        # Create engine
        engine = RainAudioEngine(
            loader=loader,
            chunk_seconds=1.0,
            overlap_seconds=0.2,
            include_thunder=False,
            seed=42
        )
        
        # Generate short audio
        output_path = Path(tmpdir) / 'test_output.wav'
        engine.generate_to_file(output_path, duration_seconds=2.0)
        
        # Load and check
        import soundfile as sf
        audio, sr = sf.read(output_path)
        
        # Verify stereo
        assert audio.ndim == 2, f"Expected 2D array, got {audio.ndim}D"
        assert audio.shape[1] == 2, f"Expected 2 channels, got {audio.shape[1]}"
        
        print(f"✓ Stereo output test passed (shape: {audio.shape})")


def test_equal_power_crossfade_energy():
    """Verify equal-power crossfade maintains roughly constant energy."""
    # Create two identical signals
    sr = 48000
    duration = 1.0
    samples = int(duration * sr)
    
    # Constant amplitude signal
    audio1 = np.ones((samples, 2), dtype=np.float32) * 0.5
    audio2 = np.ones((samples, 2), dtype=np.float32) * 0.5
    
    # Apply crossfade
    fade_samples = int(0.1 * sr)
    crossfaded = equal_power_crossfade(audio1, audio2, fade_samples)
    
    # Check energy in crossfade region
    # For equal-power crossfade of identical signals, energy should be roughly constant
    crossfade_region = crossfaded[-fade_samples:fade_samples, 0]
    energy = crossfade_region ** 2
    mean_energy = np.mean(energy)
    
    # Energy should be close to 0.25 (0.5^2)
    expected_energy = 0.25
    assert abs(mean_energy - expected_energy) < 0.05, \
        f"Energy deviation: {mean_energy} vs {expected_energy}"
    
    print(f"✓ Equal-power crossfade energy test passed (energy: {mean_energy:.4f})")


def test_overlap_add():
    """Test overlap-add functionality."""
    # Create test chunks
    sr = 48000
    chunk_samples = sr  # 1 second
    
    chunks = [
        np.ones((chunk_samples, 2), dtype=np.float32) * 0.3,
        np.ones((chunk_samples, 2), dtype=np.float32) * 0.4,
        np.ones((chunk_samples, 2), dtype=np.float32) * 0.5,
    ]
    
    # Overlap-add
    overlap_samples = int(0.1 * sr)
    result = overlap_add(chunks, overlap_samples)
    
    # Verify length (approximately sum of chunk lengths minus overlaps)
    expected_length = len(chunks) * chunk_samples - (len(chunks) - 1) * overlap_samples
    assert abs(len(result) - expected_length) < overlap_samples, \
        f"Unexpected length: {len(result)} vs {expected_length}"
    
    print(f"✓ Overlap-add test passed (length: {len(result)})")


if __name__ == '__main__':
    # Run tests
    print("Running audio engine tests...\n")
    
    try:
        test_crossfade_continuity()
        test_output_peak_below_ceiling()
        test_no_clipping()
        test_stereo_output()
        test_equal_power_crossfade_energy()
        test_overlap_add()
        
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
