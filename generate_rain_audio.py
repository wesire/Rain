#!/usr/bin/env python3
"""
Generate realistic rain sound audio using procedural synthesis.
Creates a continuous rain sound by layering multiple randomized droplet sounds.
"""

import numpy as np
from scipy.io import wavfile
from scipy import signal
import argparse
from tqdm import tqdm


def generate_raindrop(sample_rate=44100, drop_type='light'):
    """
    Generate a single raindrop sound using filtered noise.
    
    Args:
        sample_rate: Audio sample rate in Hz
        drop_type: Type of raindrop ('light', 'medium', 'heavy')
    
    Returns:
        numpy array containing the raindrop audio
    """
    if drop_type == 'light':
        duration = np.random.uniform(0.02, 0.05)
        freq_range = (2000, 8000)
        amplitude = np.random.uniform(0.1, 0.3)
    elif drop_type == 'medium':
        duration = np.random.uniform(0.05, 0.1)
        freq_range = (1000, 6000)
        amplitude = np.random.uniform(0.2, 0.5)
    else:  # heavy
        duration = np.random.uniform(0.1, 0.2)
        freq_range = (500, 4000)
        amplitude = np.random.uniform(0.4, 0.7)
    
    # Generate white noise
    num_samples = int(duration * sample_rate)
    noise = np.random.randn(num_samples)
    
    # Apply bandpass filter
    nyquist = sample_rate / 2
    low = freq_range[0] / nyquist
    high = freq_range[1] / nyquist
    b, a = signal.butter(4, [low, high], btype='band')
    filtered = signal.filtfilt(b, a, noise)
    
    # Apply envelope (attack-decay)
    envelope = np.exp(-np.linspace(0, 10, num_samples))
    drop_sound = filtered * envelope * amplitude
    
    return drop_sound


def generate_rain_audio(duration_seconds, sample_rate=44100, intensity='medium', output_file='rain.wav'):
    """
    Generate continuous rain audio by layering multiple raindrops.
    
    Args:
        duration_seconds: Length of audio to generate in seconds
        sample_rate: Audio sample rate in Hz
        intensity: Rain intensity ('light', 'medium', 'heavy')
        output_file: Output WAV file path
    """
    print(f"Generating {duration_seconds} seconds of {intensity} rain audio...")
    
    # Determine drop rate based on intensity
    if intensity == 'light':
        drops_per_second = np.random.uniform(10, 30)
        drop_types = ['light'] * 7 + ['medium'] * 3
    elif intensity == 'heavy':
        drops_per_second = np.random.uniform(100, 200)
        drop_types = ['light'] * 3 + ['medium'] * 4 + ['heavy'] * 3
    else:  # medium
        drops_per_second = np.random.uniform(40, 80)
        drop_types = ['light'] * 5 + ['medium'] * 4 + ['heavy'] * 1
    
    # Initialize audio buffer
    total_samples = int(duration_seconds * sample_rate)
    audio = np.zeros(total_samples, dtype=np.float32)
    
    # Calculate total number of drops
    total_drops = int(duration_seconds * drops_per_second)
    
    # Generate and place raindrops
    for _ in tqdm(range(total_drops), desc="Generating raindrops"):
        # Random drop type and timing
        drop_type = np.random.choice(drop_types)
        drop_time = np.random.uniform(0, duration_seconds)
        start_sample = int(drop_time * sample_rate)
        
        # Generate drop
        drop = generate_raindrop(sample_rate, drop_type)
        end_sample = min(start_sample + len(drop), total_samples)
        
        # Add to audio buffer
        if start_sample < total_samples:
            audio[start_sample:end_sample] += drop[:end_sample - start_sample]
    
    # Add subtle background noise for continuous ambiance
    print("Adding ambient background...")
    background = np.random.randn(total_samples) * 0.01
    # Low-pass filter for background
    b, a = signal.butter(4, 500 / (sample_rate / 2), btype='low')
    background = signal.filtfilt(b, a, background)
    audio += background
    
    # Normalize audio to prevent clipping
    audio = audio / np.max(np.abs(audio)) * 0.9
    
    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Save to WAV file
    print(f"Saving to {output_file}...")
    wavfile.write(output_file, sample_rate, audio_int16)
    print("Audio generation complete!")


def main():
    parser = argparse.ArgumentParser(description='Generate realistic rain sound audio')
    parser.add_argument('--duration', type=int, default=60,
                        help='Duration in seconds (default: 60)')
    parser.add_argument('--intensity', choices=['light', 'medium', 'heavy'], default='medium',
                        help='Rain intensity (default: medium)')
    parser.add_argument('--output', type=str, default='rain.wav',
                        help='Output WAV file (default: rain.wav)')
    parser.add_argument('--sample-rate', type=int, default=44100,
                        help='Audio sample rate in Hz (default: 44100)')
    
    args = parser.parse_args()
    
    generate_rain_audio(
        duration_seconds=args.duration,
        sample_rate=args.sample_rate,
        intensity=args.intensity,
        output_file=args.output
    )


if __name__ == '__main__':
    main()
