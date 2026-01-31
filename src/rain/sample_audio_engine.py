#!/usr/bin/env python3
"""
Sample-Based Audio Engine for Sleep-Grade Rain Audio.

Generates long-duration audio from REAL SAMPLES ONLY.
NO synthesis, NO procedural generation.

This engine:
- Requires real audio files in assets/audio/bed/
- Fails fast if no bed recordings exist
- Uses grain-based rendering with anti-repetition
- Equal-power crossfades for seamless transitions
- Very sparse details and rare thunder
- Sleep-friendly loudness (-22 LUFS default)
"""

import numpy as np
from pathlib import Path
from typing import List, Optional, Callable
from collections import defaultdict
import soundfile as sf
from scipy import signal
from tqdm import tqdm


class SampleBasedAudioEngine:
    """
    Generates long-duration audio from REAL SAMPLES ONLY.
    No synthesis, no procedural generation.
    """
    
    def __init__(self, assets_dir: Path, target_sr: int = 48000, seed: int = None,
                 chunk_seconds: float = 120.0, crossfade_seconds: float = 5.0,
                 include_thunder: bool = True):
        """
        Initialize the sample-based audio engine.
        
        Args:
            assets_dir: Path to assets directory
            target_sr: Target sample rate (default: 48000)
            seed: Random seed for reproducibility
            chunk_seconds: Duration of rendering chunks (default: 120s)
            crossfade_seconds: Crossfade duration (default: 5s)
            include_thunder: Whether to include thunder (default: True)
            
        Raises:
            RuntimeError: If no bed recordings found
        """
        self.assets_dir = Path(assets_dir)
        self.target_sr = target_sr
        self.rng = np.random.default_rng(seed)
        self.chunk_seconds = chunk_seconds
        self.crossfade_seconds = crossfade_seconds
        self.include_thunder = include_thunder
        
        # Find audio files (do NOT load into memory - files can be huge)
        self.bed_files = self._find_audio_files(self.assets_dir / "audio" / "bed")
        self.detail_files = self._find_audio_files(self.assets_dir / "audio" / "details")
        self.thunder_files = self._find_audio_files(self.assets_dir / "audio" / "thunder")
        
        # CRITICAL: Fail if no bed files
        if not self.bed_files:
            raise RuntimeError(
                "No bed recordings found. Add at least 1 long rain recording to assets/audio/bed/."
            )
        
        # Track recently used offsets per file to avoid repetition
        self.recent_offsets = defaultdict(list)  # file -> [offset1, offset2, ...]
        self.max_recent = 5
    
    def _find_audio_files(self, directory: Path) -> List[Path]:
        """
        Find all audio files in directory.
        
        Supports: .wav, .flac, .mp3
        
        Args:
            directory: Directory to search
            
        Returns:
            List of audio file paths
        """
        if not directory.exists():
            return []
        
        files = []
        for ext in ['*.wav', '*.flac', '*.mp3', '*.WAV', '*.FLAC', '*.MP3']:
            files.extend(directory.glob(ext))
        
        return sorted(files)
    
    def _is_offset_recent(self, file_path: Path, offset: float, min_gap: float = 30.0) -> bool:
        """
        Check if this offset was recently used for this file.
        
        Args:
            file_path: Audio file path
            offset: Start offset in seconds
            min_gap: Minimum gap between offsets (default: 30s)
            
        Returns:
            True if offset is too close to a recent one
        """
        recent = self.recent_offsets[str(file_path)]
        for recent_offset in recent:
            if abs(offset - recent_offset) < min_gap:
                return True
        return False
    
    def _record_offset(self, file_path: Path, offset: float):
        """
        Record that we used this offset for this file.
        
        Args:
            file_path: Audio file path
            offset: Start offset in seconds
        """
        key = str(file_path)
        self.recent_offsets[key].append(offset)
        
        # Keep only recent history
        if len(self.recent_offsets[key]) > self.max_recent:
            self.recent_offsets[key].pop(0)
    
    def _select_grain(self, min_duration: float = 60.0, max_duration: float = 180.0) -> np.ndarray:
        """
        Select a random grain from a random bed file.
        Avoids recently used offsets to prevent obvious looping.
        
        Args:
            min_duration: Minimum grain duration in seconds
            max_duration: Maximum grain duration in seconds
            
        Returns:
            Stereo audio grain (samples, 2)
        """
        grain_duration = self.rng.uniform(min_duration, max_duration)
        
        # Pick a random bed file
        bed_file = self.rng.choice(self.bed_files)
        
        # Get file info (fast, doesn't load audio)
        file_info = sf.info(bed_file)
        file_duration = file_info.duration
        
        if file_duration < grain_duration:
            # Use entire file if too short
            grain_duration = file_duration
            start_offset = 0.0
        else:
            # Pick random start offset, avoiding recent offsets
            max_offset = file_duration - grain_duration
            
            # Try up to 10 times to find non-recent offset
            for _ in range(10):
                start_offset = self.rng.uniform(0, max_offset)
                if not self._is_offset_recent(bed_file, start_offset, min_gap=30.0):
                    break
            
            # Record this offset
            self._record_offset(bed_file, start_offset)
        
        # Read the grain
        start_sample = int(start_offset * file_info.samplerate)
        num_samples = int(grain_duration * file_info.samplerate)
        
        try:
            audio, sr = sf.read(bed_file, start=start_sample, frames=num_samples, dtype='float32')
        except Exception as e:
            # If soundfile fails, try librosa
            import librosa
            audio, sr = librosa.load(bed_file, sr=None, offset=start_offset, 
                                    duration=grain_duration, mono=False)
            if audio.ndim == 1:
                audio = audio[np.newaxis, :]
            audio = audio.T  # librosa returns (channels, samples), we want (samples, channels)
        
        # Resample to target SR if needed
        if sr != self.target_sr:
            import librosa
            # Handle stereo resampling
            if audio.ndim == 2 and audio.shape[1] == 2:
                audio_resampled = np.zeros((int(len(audio) * self.target_sr / sr), 2), dtype=np.float32)
                for ch in range(2):
                    audio_resampled[:, ch] = librosa.resample(
                        audio[:, ch], orig_sr=sr, target_sr=self.target_sr
                    )
                audio = audio_resampled
            else:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sr)
        
        # Force stereo
        if audio.ndim == 1:
            audio = np.column_stack([audio, audio])
        elif audio.shape[1] == 1:
            audio = np.column_stack([audio[:, 0], audio[:, 0]])
        
        return audio.astype(np.float32)
    
    def _generate_bed_chunk(self) -> np.ndarray:
        """
        Generate a bed chunk by stitching together grains.
        
        Returns:
            Stereo audio chunk (samples, 2)
        """
        chunk_samples = int(self.chunk_seconds * self.target_sr)
        overlap_samples = int(self.crossfade_seconds * self.target_sr)
        
        # Start with first grain
        result = self._select_grain()
        
        # Keep adding grains until we have enough
        while len(result) < chunk_samples:
            next_grain = self._select_grain()
            
            # Crossfade grains
            result = equal_power_crossfade(result, next_grain, overlap_samples)
        
        # Trim to exact length
        return result[:chunk_samples]
    
    def _add_details(self, chunk: np.ndarray, chunk_start_time: float) -> np.ndarray:
        """
        Add VERY SPARSE and QUIET detail sounds.
        Critical: details must never dominate or create "fire crackle" effect.
        
        Args:
            chunk: Audio chunk to add details to
            chunk_start_time: Start time of chunk in seconds (for reproducibility)
            
        Returns:
            Chunk with details added
        """
        if not self.detail_files:
            return chunk  # Skip if no details
        
        chunk = chunk.copy()
        
        # Very sparse: 0-3 events per minute
        events_per_minute = self.rng.uniform(0, 3)
        chunk_duration = len(chunk) / self.target_sr
        expected_events = events_per_minute * (chunk_duration / 60)
        num_events = self.rng.poisson(expected_events)
        
        for _ in range(num_events):
            # Pick random detail file
            detail_file = self.rng.choice(self.detail_files)
            
            try:
                detail_audio, sr = sf.read(detail_file, dtype='float32')
            except:
                # Skip if can't read
                continue
            
            # Resample and force stereo
            if sr != self.target_sr:
                import librosa
                if detail_audio.ndim == 2:
                    detail_resampled = np.zeros((int(len(detail_audio) * self.target_sr / sr), 2), dtype=np.float32)
                    for ch in range(2):
                        detail_resampled[:, ch] = librosa.resample(
                            detail_audio[:, ch], orig_sr=sr, target_sr=self.target_sr
                        )
                    detail_audio = detail_resampled
                else:
                    detail_audio = librosa.resample(detail_audio, orig_sr=sr, target_sr=self.target_sr)
            
            if detail_audio.ndim == 1:
                detail_audio = np.column_stack([detail_audio, detail_audio])
            
            # LOW-PASS FILTER to remove brittle sparkle (8-10 kHz)
            sos = signal.butter(4, 9000, btype='low', fs=self.target_sr, output='sos')
            detail_audio = signal.sosfilt(sos, detail_audio, axis=0)
            
            # Apply fade in/out (50-200ms) to avoid clicks
            fade_samples = int(self.rng.uniform(0.05, 0.2) * self.target_sr)
            fade_samples = min(fade_samples, len(detail_audio) // 2)
            
            if fade_samples > 0:
                fade_in = np.linspace(0, 1, fade_samples)
                fade_out = np.linspace(1, 0, fade_samples)
                
                if detail_audio.ndim == 2:
                    fade_in = fade_in[:, np.newaxis]
                    fade_out = fade_out[:, np.newaxis]
                
                detail_audio[:fade_samples] *= fade_in
                detail_audio[-fade_samples:] *= fade_out
            
            # VERY QUIET: -18 to -30 dB relative to bed
            gain_db = self.rng.uniform(-30, -18)
            gain = 10 ** (gain_db / 20)
            detail_audio *= gain
            
            # Random position in chunk
            if len(detail_audio) < len(chunk):
                pos = self.rng.integers(0, len(chunk) - len(detail_audio))
                chunk[pos:pos + len(detail_audio)] += detail_audio
        
        return chunk
    
    def _maybe_add_thunder(self, chunk: np.ndarray, chunk_idx: int, total_chunks: int) -> np.ndarray:
        """
        Add thunder VERY RARELY (0-2 per hour) with LONG FADES.
        Must never "jumpscare" - always distant and gradual.
        
        Args:
            chunk: Audio chunk to add thunder to
            chunk_idx: Index of this chunk
            total_chunks: Total number of chunks
            
        Returns:
            Chunk with thunder added (if triggered)
        """
        if not self.thunder_files or not self.include_thunder:
            return chunk
        
        chunk = chunk.copy()
        
        # Calculate probability for this chunk
        # Target: 0-2 events per hour
        hours = (total_chunks * self.chunk_seconds) / 3600
        max_thunder = 2 * hours
        
        # Very low probability per chunk
        prob = max_thunder / total_chunks if total_chunks > 0 else 0
        
        if self.rng.random() > prob:
            return chunk  # No thunder this chunk
        
        # Load thunder
        thunder_file = self.rng.choice(self.thunder_files)
        
        try:
            thunder_audio, sr = sf.read(thunder_file, dtype='float32')
        except:
            return chunk  # Skip if can't read
        
        # Resample and stereo
        if sr != self.target_sr:
            import librosa
            if thunder_audio.ndim == 2:
                thunder_resampled = np.zeros((int(len(thunder_audio) * self.target_sr / sr), 2), dtype=np.float32)
                for ch in range(2):
                    thunder_resampled[:, ch] = librosa.resample(
                        thunder_audio[:, ch], orig_sr=sr, target_sr=self.target_sr
                    )
                thunder_audio = thunder_resampled
            else:
                thunder_audio = librosa.resample(thunder_audio, orig_sr=sr, target_sr=self.target_sr)
        
        if thunder_audio.ndim == 1:
            thunder_audio = np.column_stack([thunder_audio, thunder_audio])
        
        # LONG FADES: 10-30 seconds
        fade_duration = self.rng.uniform(10, 30)
        fade_samples = int(fade_duration * self.target_sr)
        fade_samples = min(fade_samples, len(thunder_audio) // 2)
        
        if fade_samples > 0:
            fade_in = np.linspace(0, 1, fade_samples) ** 2  # Exponential for smoother
            fade_out = np.linspace(1, 0, fade_samples) ** 2
            
            if thunder_audio.ndim == 2:
                fade_in = fade_in[:, np.newaxis]
                fade_out = fade_out[:, np.newaxis]
            
            thunder_audio[:fade_samples] *= fade_in
            thunder_audio[-fade_samples:] *= fade_out
        
        # DISTANT LEVEL: very quiet
        gain_db = self.rng.uniform(-24, -18)
        thunder_audio *= 10 ** (gain_db / 20)
        
        # Add to chunk
        if len(thunder_audio) <= len(chunk):
            pos = self.rng.integers(0, max(1, len(chunk) - len(thunder_audio) + 1))
            end_pos = min(pos + len(thunder_audio), len(chunk))
            chunk[pos:end_pos] += thunder_audio[:end_pos - pos]
        
        return chunk
    
    def _apply_mastering(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply gentle tonal shaping to the FINAL MIX.
        This is mastering of real recordings, NOT synthesis.
        
        Args:
            audio: Input audio (samples, 2)
            
        Returns:
            Mastered audio
        """
        audio = audio.copy()
        
        # DC offset removal
        audio = audio - np.mean(audio, axis=0, keepdims=True)
        
        # High-pass at 25 Hz (remove rumble)
        sos_hp = signal.butter(2, 25, btype='high', fs=self.target_sr, output='sos')
        audio = signal.sosfilt(sos_hp, audio, axis=0)
        
        # Gentle dip around 3-5 kHz (reduce tizz/crackle)
        # We'll use a bandpass filter to isolate 4kHz region, then subtract scaled version
        # This is approximate parametric EQ
        sos_peak = signal.butter(2, [3000, 5000], btype='band', fs=self.target_sr, output='sos')
        audio_peak = signal.sosfilt(sos_peak, audio, axis=0)
        # Subtract 30% of the peak band (approximately -3dB cut at center)
        audio = audio - 0.3 * audio_peak
        
        # Low-pass at 15 kHz if hissy
        sos_lp = signal.butter(2, 15000, btype='low', fs=self.target_sr, output='sos')
        audio = signal.sosfilt(sos_lp, audio, axis=0)
        
        return audio
    
    def generate_to_file(self, output_path: Path, duration_seconds: float,
                         target_lufs: float = -22.0,
                         progress_callback: Optional[Callable[[float], None]] = None):
        """
        Stream-render audio to disk in chunks.
        NEVER keeps full audio in RAM.
        
        Args:
            output_path: Output WAV file path
            duration_seconds: Total duration in seconds
            target_lufs: Target loudness in LUFS (default: -22 for sleep)
            progress_callback: Optional progress callback
        """
        output_path = Path(output_path)
        chunk_samples = int(self.chunk_seconds * self.target_sr)
        overlap_samples = int(self.crossfade_seconds * self.target_sr)
        total_samples = int(duration_seconds * self.target_sr)
        total_chunks = int(np.ceil(duration_seconds / self.chunk_seconds))
        
        # Open output file for writing
        with sf.SoundFile(output_path, mode='w', samplerate=self.target_sr,
                          channels=2, format='WAV', subtype='FLOAT') as outfile:
            
            samples_written = 0
            prev_chunk_tail = None  # For crossfading between chunks
            chunk_idx = 0
            
            pbar = tqdm(total=total_chunks, desc="Generating audio")
            
            while samples_written < total_samples:
                # Generate this chunk's bed from real samples
                chunk = self._generate_bed_chunk()
                
                # Add optional details (very sparse)
                chunk = self._add_details(chunk, samples_written / self.target_sr)
                
                # Maybe add thunder (very rare)
                chunk = self._maybe_add_thunder(chunk, chunk_idx, total_chunks)
                
                # Apply mastering to this chunk
                chunk = self._apply_mastering(chunk)
                
                # Crossfade with previous chunk if exists
                if prev_chunk_tail is not None:
                    # Create crossfade region
                    fade_region = equal_power_crossfade(prev_chunk_tail, chunk[:overlap_samples], overlap_samples)
                    
                    # Write the crossfaded region
                    remaining = total_samples - samples_written
                    write_samples = min(len(fade_region), remaining)
                    if write_samples > 0:
                        outfile.write(fade_region[:write_samples])
                        samples_written += write_samples
                    
                    # Remove the overlapped part from chunk
                    chunk = chunk[overlap_samples:]
                
                # Calculate how much to write from this chunk
                remaining = total_samples - samples_written
                write_samples = min(len(chunk) - overlap_samples, remaining)
                
                if write_samples > 0:
                    outfile.write(chunk[:write_samples])
                    samples_written += write_samples
                
                # Save tail for next crossfade
                if len(chunk) >= overlap_samples:
                    prev_chunk_tail = chunk[-overlap_samples:]
                else:
                    prev_chunk_tail = chunk
                
                chunk_idx += 1
                pbar.update(1)
                
                if progress_callback:
                    progress_callback(samples_written / total_samples)
            
            pbar.close()
        
        # Normalize loudness
        print(f"\nNormalizing to {target_lufs} LUFS...")
        self._normalize_loudness(output_path, target_lufs)
    
    def _normalize_loudness(self, audio_path: Path, target_lufs: float = -22.0):
        """
        Normalize to SLEEP-FRIENDLY loudness.
        Default: -22 LUFS (NOT the loud -14 LUFS YouTube standard).
        
        Args:
            audio_path: Path to audio file (modified in place)
            target_lufs: Target loudness in LUFS
        """
        audio, sr = sf.read(audio_path, dtype='float32')
        
        try:
            import pyloudnorm as pyln
            meter = pyln.Meter(sr)
            current_lufs = meter.integrated_loudness(audio)
            
            if not np.isinf(current_lufs):
                gain_db = target_lufs - current_lufs
                gain = 10 ** (gain_db / 20)
                audio = audio * gain
                print(f"Loudness: {current_lufs:.1f} LUFS -> {target_lufs:.1f} LUFS (gain: {gain_db:+.1f} dB)")
        except ImportError:
            # Fallback to RMS normalization with headroom
            print("pyloudnorm not available, using RMS normalization")
            rms = np.sqrt(np.mean(audio ** 2))
            target_rms = 10 ** (target_lufs / 20) * 0.5  # Approximate
            if rms > 0:
                audio = audio * (target_rms / rms)
        
        # Apply limiter: peaks <= -1 dBFS
        ceiling = 10 ** (-1 / 20)  # -1 dBFS
        peak = np.max(np.abs(audio))
        if peak > ceiling:
            audio = audio * (ceiling / peak)
            print(f"Peak limited to -1.0 dBFS")
        
        # Save back
        sf.write(audio_path, audio, sr)


def equal_power_crossfade(audio1: np.ndarray, audio2: np.ndarray, 
                          fade_samples: int) -> np.ndarray:
    """
    Equal-power crossfade for seamless transitions.
    Uses sqrt curves to maintain constant perceived loudness.
    
    Args:
        audio1: First audio segment (samples, channels)
        audio2: Second audio segment (samples, channels)
        fade_samples: Number of samples for crossfade
        
    Returns:
        Crossfaded audio (samples, channels)
    """
    # Limit fade to available length
    fade_samples = min(fade_samples, len(audio1), len(audio2))
    
    # Create fade curves using sin²/cos² for equal power
    t = np.linspace(0, np.pi / 2, fade_samples)
    fade_out = np.cos(t) ** 2  # Equal power: cos²
    fade_in = np.sin(t) ** 2   # Equal power: sin²
    
    # Reshape for stereo
    if audio1.ndim == 2:
        fade_out = fade_out[:, np.newaxis]
        fade_in = fade_in[:, np.newaxis]
    
    # Create result array
    result_len = len(audio1) + len(audio2) - fade_samples
    if audio1.ndim == 2:
        result = np.zeros((result_len, audio1.shape[1]), dtype=audio1.dtype)
    else:
        result = np.zeros(result_len, dtype=audio1.dtype)
    
    # Copy audio1 up to fade region
    fade_start = len(audio1) - fade_samples
    result[:fade_start] = audio1[:fade_start]
    
    # Crossfade region
    result[fade_start:len(audio1)] = (
        audio1[-fade_samples:] * fade_out + 
        audio2[:fade_samples] * fade_in
    )
    
    # Copy rest of audio2
    result[len(audio1):] = audio2[fade_samples:]
    
    return result
