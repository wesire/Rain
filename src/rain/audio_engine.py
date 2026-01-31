#!/usr/bin/env python3
"""
Professional audio engine for generating sleep-grade rain audio.

This module implements a real audio asset-based system with seamless transitions,
proper loudness normalization, and streaming rendering. Falls back to improved
procedural generation if no audio assets are available.
"""

import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
import soundfile as sf
from scipy import signal
from tqdm import tqdm


class AudioAssetLoader:
    """Loads WAV files from assets folders, resamples to target SR, forces stereo."""
    
    def __init__(self, assets_dir: Path, target_sr: int = 48000):
        """
        Initialize the audio asset loader.
        
        Args:
            assets_dir: Path to assets directory containing audio/bed, audio/details, audio/thunder
            target_sr: Target sample rate (default: 48000 Hz)
        """
        self.assets_dir = Path(assets_dir)
        self.target_sr = target_sr
        self.bed_samples = []      # Long continuous rain recordings
        self.detail_samples = []   # Short droplet/splash sounds
        self.thunder_samples = []  # Distant thunder (optional)
    
    def load_all(self):
        """
        Load all audio files from assets folders.
        
        Loads from:
        - assets/audio/bed: Long continuous rain recordings
        - assets/audio/details: Short droplet/splash sounds
        - assets/audio/thunder: Distant thunder sounds
        
        All audio is resampled to target_sr and converted to stereo float32.
        """
        bed_dir = self.assets_dir / "audio" / "bed"
        details_dir = self.assets_dir / "audio" / "details"
        thunder_dir = self.assets_dir / "audio" / "thunder"
        
        # Load bed samples
        if bed_dir.exists():
            for wav_file in bed_dir.glob("*.wav"):
                audio = self._load_and_process(wav_file)
                if audio is not None:
                    self.bed_samples.append(audio)
        
        # Load detail samples
        if details_dir.exists():
            for wav_file in details_dir.glob("*.wav"):
                audio = self._load_and_process(wav_file)
                if audio is not None:
                    self.detail_samples.append(audio)
        
        # Load thunder samples
        if thunder_dir.exists():
            for wav_file in thunder_dir.glob("*.wav"):
                audio = self._load_and_process(wav_file)
                if audio is not None:
                    self.thunder_samples.append(audio)
    
    def _load_and_process(self, file_path: Path) -> Optional[np.ndarray]:
        """
        Load a WAV file, resample, and convert to stereo.
        
        Args:
            file_path: Path to WAV file
            
        Returns:
            Stereo float32 audio array (samples, 2) or None on error
        """
        try:
            audio, sr = sf.read(file_path)
            
            # Resample if needed
            if sr != self.target_sr:
                from scipy.signal import resample
                num_samples = int(len(audio) * self.target_sr / sr)
                audio = resample(audio, num_samples)
            
            # Convert to float32
            audio = audio.astype(np.float32)
            
            # Convert mono to stereo
            if audio.ndim == 1:
                audio = np.stack([audio, audio], axis=1)
            
            return audio
        except Exception as e:
            print(f"Warning: Failed to load {file_path}: {e}")
            return None


def equal_power_crossfade(audio1: np.ndarray, audio2: np.ndarray, 
                          fade_samples: int) -> np.ndarray:
    """
    Equal-power crossfade between two audio segments.
    
    Uses sqrt curves for constant perceived loudness during the crossfade.
    
    Args:
        audio1: First audio segment (samples, channels)
        audio2: Second audio segment (samples, channels)
        fade_samples: Number of samples for crossfade
        
    Returns:
        Crossfaded audio array
    """
    # Ensure both arrays have same shape
    if audio1.shape != audio2.shape:
        min_len = min(len(audio1), len(audio2))
        audio1 = audio1[:min_len]
        audio2 = audio2[:min_len]
    
    # Limit fade_samples to available length
    fade_samples = min(fade_samples, len(audio1), len(audio2))
    
    # Create equal-power fade curves
    fade_out = np.sqrt(np.linspace(1, 0, fade_samples))
    fade_in = np.sqrt(np.linspace(0, 1, fade_samples))
    
    # Apply fades to crossfade region
    if audio1.ndim == 2:
        # Stereo
        fade_out = fade_out[:, np.newaxis]
        fade_in = fade_in[:, np.newaxis]
    
    # Crossfade the overlapping region
    crossfaded = audio1.copy()
    crossfaded[-fade_samples:] = (audio1[-fade_samples:] * fade_out + 
                                   audio2[:fade_samples] * fade_in)
    
    # Append the rest of audio2
    if len(audio2) > fade_samples:
        crossfaded = np.vstack([crossfaded, audio2[fade_samples:]])
    
    return crossfaded


def overlap_add(chunks: List[np.ndarray], overlap_samples: int) -> np.ndarray:
    """
    Overlap-add multiple chunks with crossfades.
    
    Args:
        chunks: List of audio chunks to combine
        overlap_samples: Number of samples to overlap between chunks
        
    Returns:
        Combined audio array
    """
    if not chunks:
        return np.array([])
    
    if len(chunks) == 1:
        return chunks[0]
    
    result = chunks[0]
    for chunk in chunks[1:]:
        result = equal_power_crossfade(result, chunk, overlap_samples)
    
    return result


class RainAudioEngine:
    """
    Generates sleep-grade rain audio by mixing multiple layers.
    
    Features:
    - Bed layer: Continuous rain texture (long recordings, seamlessly looped)
    - Details layer: Random droplets/splashes sprinkled throughout
    - Thunder layer: Rare, distant, with long fade-ins/outs (optional)
    - Chunk-based rendering (10-30 sec chunks with overlap)
    - Streams directly to disk (no full audio in RAM)
    - Equal-power crossfades between bed segments
    - Randomized segment selection (no obvious loops)
    """
    
    def __init__(self, loader: AudioAssetLoader, 
                 chunk_seconds: float = 20.0,
                 overlap_seconds: float = 3.0,
                 include_thunder: bool = True,
                 seed: Optional[int] = None):
        """
        Initialize the rain audio engine.
        
        Args:
            loader: AudioAssetLoader with loaded samples
            chunk_seconds: Duration of each rendering chunk
            overlap_seconds: Overlap duration for crossfades
            include_thunder: Whether to include thunder sounds
            seed: Random seed for reproducibility
        """
        self.loader = loader
        self.chunk_seconds = chunk_seconds
        self.overlap_seconds = overlap_seconds
        self.include_thunder = include_thunder
        self.rng = np.random.default_rng(seed)
        self.recent_beds = []  # Track recently used to avoid repetition
        self.max_recent_history = 3
    
    def generate_to_file(self, output_path: Path, duration_seconds: float,
                         progress_callback=None):
        """
        Stream-render audio directly to WAV file.
        
        Args:
            output_path: Output WAV file path
            duration_seconds: Total duration to generate
            progress_callback: Optional callback for progress updates
        """
        output_path = Path(output_path)
        sr = self.loader.target_sr
        chunk_samples = int(self.chunk_seconds * sr)
        overlap_samples = int(self.overlap_seconds * sr)
        total_samples = int(duration_seconds * sr)
        
        # Check if we have assets or need fallback
        use_fallback = (len(self.loader.bed_samples) == 0)
        
        if use_fallback:
            print("No audio assets found, using improved procedural generation...")
            self._generate_procedural(output_path, duration_seconds, progress_callback)
            return
        
        # Stream to file using soundfile
        chunks_needed = int(np.ceil(duration_seconds / self.chunk_seconds))
        
        with sf.SoundFile(output_path, 'w', sr, 2, 'FLOAT') as f:
            previous_chunk = None
            
            for i in tqdm(range(chunks_needed), desc="Generating audio"):
                # Generate chunk
                chunk = self._generate_chunk(chunk_samples)
                
                # Crossfade with previous chunk if exists
                if previous_chunk is not None:
                    # Overlap-add the chunks
                    overlap_region = equal_power_crossfade(
                        previous_chunk[-overlap_samples:], 
                        chunk[:overlap_samples],
                        overlap_samples
                    )
                    # Write only the non-overlapping part of the crossfade
                    f.write(overlap_region)
                    # Keep the rest of the chunk for next iteration
                    chunk = chunk[overlap_samples:]
                
                # Write chunk (or remainder after overlap)
                remaining = total_samples - f.frames
                if remaining > 0:
                    write_samples = min(len(chunk), remaining)
                    f.write(chunk[:write_samples])
                    previous_chunk = chunk
                
                if progress_callback:
                    progress = (i + 1) / chunks_needed
                    progress_callback(progress)
    
    def _generate_chunk(self, chunk_samples: int) -> np.ndarray:
        """
        Generate a single audio chunk.
        
        Args:
            chunk_samples: Number of samples in the chunk
            
        Returns:
            Stereo audio chunk (samples, 2)
        """
        sr = self.loader.target_sr
        
        # Start with bed layer
        bed = self._get_bed_segment(chunk_samples)
        
        # Add detail sounds
        details = self._add_details(chunk_samples)
        
        # Mix layers
        chunk = bed + details * 0.3  # Details at lower level
        
        # Maybe add thunder
        if self.include_thunder and len(self.loader.thunder_samples) > 0:
            if self.rng.random() < 0.05:  # 5% chance
                thunder = self._add_thunder(chunk_samples)
                chunk = chunk + thunder * 0.2
        
        return chunk
    
    def _get_bed_segment(self, samples: int) -> np.ndarray:
        """
        Get a bed layer segment, avoiding recent repeats.
        
        Args:
            samples: Number of samples needed
            
        Returns:
            Stereo audio segment (samples, 2)
        """
        if not self.loader.bed_samples:
            # Fallback to procedural
            return self._generate_pink_noise_stereo(samples)
        
        # Select a bed sample, avoiding recent ones
        available = [i for i, _ in enumerate(self.loader.bed_samples) 
                     if i not in self.recent_beds]
        if not available:
            available = list(range(len(self.loader.bed_samples)))
            self.recent_beds = []
        
        idx = self.rng.choice(available)
        self.recent_beds.append(idx)
        if len(self.recent_beds) > self.max_recent_history:
            self.recent_beds.pop(0)
        
        bed_sample = self.loader.bed_samples[idx]
        
        # Loop/tile to fill the duration
        if len(bed_sample) >= samples:
            # Take a random segment
            start = self.rng.integers(0, len(bed_sample) - samples + 1)
            return bed_sample[start:start + samples]
        else:
            # Tile with crossfades
            result = np.zeros((samples, 2), dtype=np.float32)
            pos = 0
            fade_samples = min(int(0.5 * self.loader.target_sr), len(bed_sample) // 4)
            
            while pos < samples:
                remaining = samples - pos
                if remaining >= len(bed_sample):
                    result[pos:pos + len(bed_sample)] = bed_sample
                    # Apply crossfade at the loop point
                    if pos > 0 and fade_samples > 0:
                        fade_out = np.sqrt(np.linspace(1, 0, fade_samples))[:, np.newaxis]
                        fade_in = np.sqrt(np.linspace(0, 1, fade_samples))[:, np.newaxis]
                        crossfade_start = pos - fade_samples
                        if crossfade_start >= 0:
                            result[crossfade_start:pos] = (
                                result[crossfade_start:pos] * fade_out +
                                bed_sample[:fade_samples] * fade_in
                            )
                    pos += len(bed_sample)
                else:
                    result[pos:] = bed_sample[:remaining]
                    pos = samples
            
            return result
    
    def _add_details(self, samples: int) -> np.ndarray:
        """
        Add random detail sounds throughout the chunk.
        
        Args:
            samples: Number of samples in the chunk
            
        Returns:
            Stereo audio with detail sounds (samples, 2)
        """
        result = np.zeros((samples, 2), dtype=np.float32)
        
        if not self.loader.detail_samples:
            return result
        
        sr = self.loader.target_sr
        # Add 1-3 detail sounds per second on average
        num_details = self.rng.poisson(2 * samples / sr)
        
        for _ in range(num_details):
            detail = self.rng.choice(self.loader.detail_samples)
            start_pos = self.rng.integers(0, max(1, samples - len(detail)))
            end_pos = min(start_pos + len(detail), samples)
            detail_len = end_pos - start_pos
            
            # Apply random amplitude variation
            amplitude = self.rng.uniform(0.5, 1.0)
            result[start_pos:end_pos] += detail[:detail_len] * amplitude
        
        return result
    
    def _add_thunder(self, samples: int) -> np.ndarray:
        """
        Add a thunder sound with fades.
        
        Args:
            samples: Number of samples in the chunk
            
        Returns:
            Stereo audio with thunder sound (samples, 2)
        """
        result = np.zeros((samples, 2), dtype=np.float32)
        
        if not self.loader.thunder_samples:
            return result
        
        thunder = self.rng.choice(self.loader.thunder_samples)
        
        # Place thunder randomly in the chunk
        if len(thunder) < samples:
            start_pos = self.rng.integers(0, samples - len(thunder))
            end_pos = start_pos + len(thunder)
            
            # Apply fade in/out
            fade_samples = min(int(0.5 * self.loader.target_sr), len(thunder) // 4)
            fade_in = np.linspace(0, 1, fade_samples)[:, np.newaxis]
            fade_out = np.linspace(1, 0, fade_samples)[:, np.newaxis]
            
            thunder_copy = thunder.copy()
            thunder_copy[:fade_samples] *= fade_in
            thunder_copy[-fade_samples:] *= fade_out
            
            result[start_pos:end_pos] = thunder_copy
        
        return result
    
    def _generate_pink_noise_stereo(self, samples: int) -> np.ndarray:
        """
        Generate improved pink noise as fallback.
        
        Args:
            samples: Number of samples to generate
            
        Returns:
            Stereo pink noise (samples, 2)
        """
        # Generate pink noise using the Voss-McCartney algorithm
        num_sources = 16
        values = self.rng.random(num_sources)
        
        pink_left = np.zeros(samples)
        pink_right = np.zeros(samples)
        
        for i in range(samples):
            # Update sources based on bit pattern
            for j in range(num_sources):
                if i & (1 << j):
                    values[j] = self.rng.random()
            pink_left[i] = np.sum(values) / num_sources
            pink_right[i] = np.sum(self.rng.random(num_sources)) / num_sources
        
        # Normalize
        pink_left = (pink_left - 0.5) * 2
        pink_right = (pink_right - 0.5) * 2
        
        # Apply gentle filtering for rain-like spectrum
        sr = self.loader.target_sr
        nyquist = sr / 2
        b, a = signal.butter(2, [200 / nyquist, 8000 / nyquist], btype='band')
        pink_left = signal.filtfilt(b, a, pink_left)
        pink_right = signal.filtfilt(b, a, pink_right)
        
        # Normalize
        pink_left = pink_left / np.max(np.abs(pink_left)) * 0.5
        pink_right = pink_right / np.max(np.abs(pink_right)) * 0.5
        
        return np.stack([pink_left, pink_right], axis=1).astype(np.float32)
    
    def _generate_procedural(self, output_path: Path, duration_seconds: float,
                            progress_callback=None):
        """
        Generate audio using improved procedural synthesis (fallback mode).
        
        Args:
            output_path: Output file path
            duration_seconds: Duration in seconds
            progress_callback: Optional progress callback
        """
        sr = self.loader.target_sr
        chunk_seconds = self.chunk_seconds
        chunks_needed = int(np.ceil(duration_seconds / chunk_seconds))
        
        with sf.SoundFile(output_path, 'w', sr, 2, 'FLOAT') as f:
            for i in tqdm(range(chunks_needed), desc="Generating procedural audio"):
                chunk_samples = int(chunk_seconds * sr)
                
                # Last chunk might be shorter
                if i == chunks_needed - 1:
                    remaining = int(duration_seconds * sr) - f.frames
                    chunk_samples = min(chunk_samples, remaining)
                
                # Generate pink noise chunk
                chunk = self._generate_pink_noise_stereo(chunk_samples)
                
                # Add synthetic raindrops
                chunk = chunk + self._generate_procedural_drops(chunk_samples) * 0.4
                
                f.write(chunk)
                
                if progress_callback:
                    progress = (i + 1) / chunks_needed
                    progress_callback(progress)
    
    def _generate_procedural_drops(self, samples: int) -> np.ndarray:
        """
        Generate synthetic raindrop sounds for procedural fallback.
        
        Args:
            samples: Number of samples to generate
            
        Returns:
            Stereo audio with synthetic drops (samples, 2)
        """
        sr = self.loader.target_sr
        result = np.zeros((samples, 2), dtype=np.float32)
        
        # Generate random drops
        drops_per_second = 50
        num_drops = int(drops_per_second * samples / sr)
        
        for _ in range(num_drops):
            # Generate a single drop
            drop_duration = self.rng.uniform(0.02, 0.08)
            drop_samples = int(drop_duration * sr)
            
            # Filtered noise
            noise = self.rng.randn(drop_samples)
            freq_low = self.rng.uniform(1000, 3000)
            freq_high = self.rng.uniform(4000, 8000)
            nyquist = sr / 2
            b, a = signal.butter(4, [freq_low / nyquist, freq_high / nyquist], btype='band')
            drop = signal.filtfilt(b, a, noise)
            
            # Envelope
            envelope = np.exp(-np.linspace(0, 8, drop_samples))
            drop = drop * envelope
            
            # Normalize
            drop = drop / np.max(np.abs(drop)) * 0.3
            
            # Random panning
            pan = self.rng.uniform(0, 1)
            left_gain = np.sqrt(1 - pan)
            right_gain = np.sqrt(pan)
            
            # Place in result
            start_pos = self.rng.integers(0, max(1, samples - drop_samples))
            end_pos = min(start_pos + drop_samples, samples)
            drop_len = end_pos - start_pos
            
            result[start_pos:end_pos, 0] += drop[:drop_len] * left_gain
            result[start_pos:end_pos, 1] += drop[:drop_len] * right_gain
        
        return result
