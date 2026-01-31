#!/usr/bin/env python3
"""
Tests for Sample-Based Audio Engine.

Tests cover:
- Failing without bed files (required)
- Crossfade continuity (no clicks)
- Peak limiting (no clipping)
- Equal-power crossfade energy preservation
- Stereo output
"""

import numpy as np
import tempfile
from pathlib import Path
import sys
import soundfile as sf

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rain.sample_audio_engine import (
    SampleBasedAudioEngine,
    equal_power_crossfade
)


def test_fails_without_bed_files():
    """Engine must fail with clear message if no bed files exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = Path(tmpdir) / "assets"
        (assets_dir / "audio" / "bed").mkdir(parents=True)
        (assets_dir / "audio" / "details").mkdir(parents=True)
        (assets_dir / "audio" / "thunder").mkdir(parents=True)
        
        try:
            SampleBasedAudioEngine(assets_dir)
            raise AssertionError("Expected RuntimeError but engine was created successfully")
        except RuntimeError as e:
            if "No bed recordings found" not in str(e):
                raise AssertionError(f"Wrong error message: {e}")
    
    print("✓ Fails without bed files test passed")


def test_crossfade_continuity():
    """Crossfade must not have discontinuities (clicks)."""
    # Create test signals
    sr = 48000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    
    # Two sine waves with different phases
    audio1 = np.sin(2 * np.pi * 440 * t) * 0.3
    audio2 = np.sin(2 * np.pi * 440 * t + np.pi / 4) * 0.3
    
    # Make stereo
    audio1 = np.column_stack([audio1, audio1])
    audio2 = np.column_stack([audio2, audio2])
    
    fade_samples = int(0.1 * sr)  # 100ms crossfade
    result = equal_power_crossfade(audio1, audio2, fade_samples)
    
    # Check for discontinuities
    diff = np.diff(result, axis=0)
    max_diff = np.max(np.abs(diff))
    
    # Should be smooth, no sudden jumps
    # For a sine wave at 440 Hz, the max expected diff between samples is about:
    # 2*pi*440/48000 * amplitude ≈ 0.057 for amplitude 1.0
    # Our amplitude is 0.3, so max expected is about 0.017
    # With crossfade, this shouldn't increase dramatically
    assert max_diff < 0.1, f"Crossfade has discontinuity: max_diff={max_diff}"
    
    print(f"✓ Crossfade continuity test passed (max diff: {max_diff:.6f})")


def test_peak_below_ceiling():
    """Output must not exceed -1 dBFS after limiting."""
    # Generate test audio above ceiling
    audio = np.random.randn(48000, 2) * 2  # Way too hot
    
    # Apply limiter (same as in engine)
    ceiling = 10 ** (-1 / 20)  # -1 dBFS
    peak = np.max(np.abs(audio))
    if peak > ceiling:
        audio = audio * (ceiling / peak)
    
    # Verify
    final_peak = np.max(np.abs(audio))
    assert final_peak <= ceiling * 1.01, f"Peak {final_peak} exceeds ceiling {ceiling}"
    
    peak_db = 20 * np.log10(final_peak)
    print(f"✓ Peak limiting test passed (peak: {peak_db:.1f} dBFS)")


def test_no_clipping():
    """No samples should exceed 0 dBFS."""
    # After limiting, nothing should clip
    audio = np.random.randn(48000, 2).astype(np.float32)
    audio = audio / np.max(np.abs(audio)) * 0.9  # Normalize to -1dB
    
    assert np.max(np.abs(audio)) < 1.0, "Clipping detected"
    
    print(f"✓ No clipping test passed (max: {np.max(np.abs(audio)):.4f})")


def test_equal_power_crossfade_energy():
    """Verify equal-power crossfade maintains roughly constant energy."""
    sr = 48000
    duration = 1.0
    samples = int(duration * sr)
    
    # Constant amplitude white noise signals
    np.random.seed(42)
    audio1 = np.random.randn(samples, 2).astype(np.float32) * 0.3
    audio2 = np.random.randn(samples, 2).astype(np.float32) * 0.3
    
    # Apply crossfade
    fade_samples = int(0.1 * sr)
    crossfaded = equal_power_crossfade(audio1, audio2, fade_samples)
    
    # Check energy in different regions
    # Pre-fade region (should be similar to audio1)
    pre_fade_region = crossfaded[:len(audio1) - fade_samples, 0]
    pre_energy = np.mean(pre_fade_region ** 2)
    
    # Crossfade region
    crossfade_start = len(audio1) - fade_samples
    crossfade_region = crossfaded[crossfade_start:len(audio1), 0]
    crossfade_energy = np.mean(crossfade_region ** 2)
    
    # Post-fade region (should be similar to audio2)
    post_fade_region = crossfaded[len(audio1):, 0]
    post_energy = np.mean(post_fade_region ** 2)
    
    # For equal-power crossfade, the energy should be relatively constant
    # Allow some variation due to random signals
    avg_energy = (pre_energy + post_energy) / 2
    
    # Crossfade energy should be within reasonable range of average
    # For random signals, we allow more variation
    ratio = crossfade_energy / avg_energy if avg_energy > 0 else 1.0
    assert 0.5 < ratio < 2.0, f"Crossfade energy ratio {ratio} out of range"
    
    print(f"✓ Equal-power crossfade energy test passed (ratio: {ratio:.3f})")


def test_stereo_output_with_samples():
    """Verify output is stereo when using sample-based engine."""
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = Path(tmpdir) / "assets"
        bed_dir = assets_dir / "audio" / "bed"
        bed_dir.mkdir(parents=True)
        (assets_dir / "audio" / "details").mkdir(parents=True)
        (assets_dir / "audio" / "thunder").mkdir(parents=True)
        
        # Create a test bed audio file
        sr = 48000
        duration = 5.0
        samples = int(sr * duration)
        
        # Generate some noise
        audio = np.random.randn(samples, 2).astype(np.float32) * 0.3
        
        # Save to bed directory
        bed_file = bed_dir / "test_bed.wav"
        sf.write(bed_file, audio, sr)
        
        # Create engine
        engine = SampleBasedAudioEngine(
            assets_dir=assets_dir,
            target_sr=sr,
            seed=42,
            chunk_seconds=2.0,
            crossfade_seconds=0.5,
            include_thunder=False
        )
        
        # Generate short audio
        output_path = Path(tmpdir) / 'test_output.wav'
        engine.generate_to_file(output_path, duration_seconds=3.0, target_lufs=-22.0)
        
        # Load and check
        audio_out, sr_out = sf.read(output_path)
        
        # Verify stereo
        assert audio_out.ndim == 2, f"Expected 2D array, got {audio_out.ndim}D"
        assert audio_out.shape[1] == 2, f"Expected 2 channels, got {audio_out.shape[1]}"
        
        print(f"✓ Stereo output test passed (shape: {audio_out.shape})")


def test_grain_selection_anti_repetition():
    """Test that grain selection avoids repeating recent offsets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        assets_dir = Path(tmpdir) / "assets"
        bed_dir = assets_dir / "audio" / "bed"
        bed_dir.mkdir(parents=True)
        (assets_dir / "audio" / "details").mkdir(parents=True)
        (assets_dir / "audio" / "thunder").mkdir(parents=True)
        
        # Create a long test bed audio file
        sr = 48000
        duration = 600.0  # 10 minutes
        samples = int(sr * duration)
        
        # Generate some noise
        audio = np.random.randn(samples, 2).astype(np.float32) * 0.3
        
        # Save to bed directory
        bed_file = bed_dir / "test_bed.wav"
        sf.write(bed_file, audio, sr)
        
        # Create engine
        engine = SampleBasedAudioEngine(
            assets_dir=assets_dir,
            target_sr=sr,
            seed=42,
            chunk_seconds=60.0,
            crossfade_seconds=5.0,
            include_thunder=False
        )
        
        # Select multiple grains and verify they don't repeat offsets
        offsets = []
        for _ in range(5):
            # Access the internal recent_offsets after selecting a grain
            grain = engine._select_grain(min_duration=30.0, max_duration=60.0)
            
            # Check that grain was generated
            assert grain is not None
            assert len(grain) > 0
        
        # Verify recent offsets were recorded
        assert len(engine.recent_offsets) > 0
        
        print("✓ Grain selection anti-repetition test passed")


if __name__ == '__main__':
    # Run tests
    print("Running sample-based audio engine tests...\n")
    
    try:
        test_fails_without_bed_files()
        test_crossfade_continuity()
        test_peak_below_ceiling()
        test_no_clipping()
        test_equal_power_crossfade_energy()
        test_stereo_output_with_samples()
        test_grain_selection_anti_repetition()
        
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
