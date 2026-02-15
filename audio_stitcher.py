#!/usr/bin/env python3
"""
Advanced audio stitching module for creating natural-sounding rain audio
from real samples using multi-layer mixing and seamless transitions.
"""

import numpy as np
from scipy.io import wavfile
from scipy import signal
import soundfile as sf
import librosa
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import config
from tqdm import tqdm

class AudioStitcher:
    """Handles sophisticated audio stitching with zero-crossing loops and spectral matching."""
    
    def __init__(self, sample_rate: int = None):
        """
        Initialize AudioStitcher.
        
        Args:
            sample_rate: Target sample rate. If None, uses config default.
        """
        self.sample_rate = sample_rate or config.DEFAULT_SAMPLE_RATE
    
    def load_audio(self, file_path: Path) -> Tuple[np.ndarray, int]:
        """
        Load audio file and resample if necessary.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            # Load audio using soundfile (handles various formats)
            audio, sr = sf.read(str(file_path))
            
            # Convert stereo to mono if needed
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # Resample if necessary
            if sr != self.sample_rate:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
            
            return audio, self.sample_rate
            
        except Exception as e:
            print(f"Error loading audio file {file_path}: {e}")
            return np.array([]), self.sample_rate
    
    def find_zero_crossings(self, audio: np.ndarray, window_start: int, window_end: int) -> List[int]:
        """
        Find zero-crossing points within a window for seamless looping.
        
        Args:
            audio: Audio data
            window_start: Start of search window (in samples)
            window_end: End of search window (in samples)
            
        Returns:
            List of zero-crossing indices
        """
        if window_start >= window_end or window_end > len(audio):
            return []
        
        window = audio[window_start:window_end]
        
        # Find zero crossings (where signal changes sign)
        zero_crossings = np.where(np.diff(np.sign(window)))[0]
        
        # Convert to absolute indices
        return [window_start + zc for zc in zero_crossings]
    
    def find_best_loop_point(self, audio: np.ndarray, prefer_start: int, prefer_end: int, 
                             search_window: int = 4410) -> Tuple[int, int]:
        """
        Find the best loop points for seamless looping using zero-crossing detection.
        
        Args:
            audio: Audio data
            prefer_start: Preferred start point (in samples)
            prefer_end: Preferred end point (in samples)
            search_window: Size of search window around preferred points
            
        Returns:
            Tuple of (actual_start, actual_end) indices
        """
        # Search for zero crossings near preferred points
        start_search_begin = max(0, prefer_start - search_window // 2)
        start_search_end = min(len(audio), prefer_start + search_window // 2)
        
        end_search_begin = max(0, prefer_end - search_window // 2)
        end_search_end = min(len(audio), prefer_end + search_window // 2)
        
        start_crossings = self.find_zero_crossings(audio, start_search_begin, start_search_end)
        end_crossings = self.find_zero_crossings(audio, end_search_begin, end_search_end)
        
        # Find closest crossings to preferred points
        if not start_crossings:
            actual_start = prefer_start
        else:
            actual_start = min(start_crossings, key=lambda x: abs(x - prefer_start))
        
        if not end_crossings:
            actual_end = prefer_end
        else:
            actual_end = min(end_crossings, key=lambda x: abs(x - prefer_end))
        
        return actual_start, actual_end
    
    def create_crossfade(self, audio1: np.ndarray, audio2: np.ndarray, 
                        fade_duration: float) -> np.ndarray:
        """
        Create a smooth crossfade between two audio segments.
        
        Args:
            audio1: First audio segment (will fade out)
            audio2: Second audio segment (will fade in)
            fade_duration: Crossfade duration in seconds
            
        Returns:
            Crossfaded audio
        """
        fade_samples = int(fade_duration * self.sample_rate)
        
        # Ensure we don't exceed audio lengths
        fade_samples = min(fade_samples, len(audio1), len(audio2))
        
        if fade_samples <= 0:
            return np.concatenate([audio1, audio2])
        
        # Create fade curves (cosine curves for smooth fading)
        fade_out = np.cos(np.linspace(0, np.pi / 2, fade_samples)) ** 2
        fade_in = np.sin(np.linspace(0, np.pi / 2, fade_samples)) ** 2
        
        # Apply fades
        audio1_end = audio1[-fade_samples:] * fade_out
        audio2_start = audio2[:fade_samples] * fade_in
        
        # Mix the crossfade region
        crossfade = audio1_end + audio2_start
        
        # Concatenate: audio1 (without fade region) + crossfade + audio2 (without fade region)
        result = np.concatenate([
            audio1[:-fade_samples] if len(audio1) > fade_samples else np.array([]),
            crossfade,
            audio2[fade_samples:] if len(audio2) > fade_samples else np.array([])
        ])
        
        return result
    
    def compute_spectral_similarity(self, audio1: np.ndarray, audio2: np.ndarray) -> float:
        """
        Compute spectral similarity between two audio segments.
        
        Args:
            audio1: First audio segment
            audio2: Second audio segment
            
        Returns:
            Similarity score (0-1, higher is more similar)
        """
        # Compute spectral centroids
        try:
            centroid1 = librosa.feature.spectral_centroid(y=audio1, sr=self.sample_rate)[0]
            centroid2 = librosa.feature.spectral_centroid(y=audio2, sr=self.sample_rate)[0]
            
            # Compare mean centroids
            mean1 = np.mean(centroid1)
            mean2 = np.mean(centroid2)
            
            # Normalize difference to similarity score
            max_diff = max(mean1, mean2)
            if max_diff == 0:
                return 1.0
            
            diff = abs(mean1 - mean2)
            similarity = 1.0 - (diff / max_diff)
            
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            print(f"Error computing spectral similarity: {e}")
            return 0.5  # Default middle similarity
    
    def loop_audio(self, audio: np.ndarray, target_duration: float) -> np.ndarray:
        """
        Loop audio to reach target duration with seamless transitions.
        
        Args:
            audio: Source audio to loop
            target_duration: Target duration in seconds
            
        Returns:
            Looped audio
        """
        target_samples = int(target_duration * self.sample_rate)
        
        if len(audio) == 0:
            return np.zeros(target_samples)
        
        if len(audio) >= target_samples:
            return audio[:target_samples]
        
        # Find good loop points
        loop_start = int(len(audio) * 0.1)  # Skip first 10%
        loop_end = int(len(audio) * 0.9)  # Use up to 90%
        
        loop_start, loop_end = self.find_best_loop_point(audio, loop_start, loop_end)
        loop_segment = audio[loop_start:loop_end]
        
        # Build looped audio
        result = audio.copy()
        
        while len(result) < target_samples:
            # Use crossfade for seamless loop
            fade_duration = min(2.0, len(loop_segment) / self.sample_rate * 0.1)
            result = self.create_crossfade(result, loop_segment, fade_duration)
        
        return result[:target_samples]
    
    def apply_random_variation(self, audio: np.ndarray, variation: float = 0.1) -> np.ndarray:
        """
        Apply subtle random variations to avoid repetitive sound.
        
        Args:
            audio: Input audio
            variation: Amount of variation (0-1)
            
        Returns:
            Modified audio
        """
        # Apply very subtle pitch variation
        pitch_shift = np.random.uniform(-variation, variation)
        
        try:
            # Use librosa for pitch shifting
            if abs(pitch_shift) > 0.01:
                audio = librosa.effects.pitch_shift(audio, sr=self.sample_rate, n_steps=pitch_shift)
        except Exception:
            pass  # If pitch shift fails, return original
        
        # Apply subtle volume variation
        volume_mult = 1.0 + np.random.uniform(-variation * 0.2, variation * 0.2)
        audio = audio * volume_mult
        
        return audio

class MultiLayerMixer:
    """Handles multi-layer audio mixing with different sample categories."""
    
    def __init__(self, sample_rate: int = None):
        """Initialize mixer."""
        self.sample_rate = sample_rate or config.DEFAULT_SAMPLE_RATE
        self.stitcher = AudioStitcher(sample_rate)
    
    def generate_bed_layer(self, bed_samples: List[Path], duration: float, 
                          intensity_timeline: List[Dict]) -> np.ndarray:
        """
        Generate continuous bed layer using long samples.
        
        Args:
            bed_samples: List of paths to bed sample files
            duration: Target duration in seconds
            intensity_timeline: Timeline with intensity changes
            
        Returns:
            Generated bed layer audio
        """
        if not bed_samples:
            print("Warning: No bed samples available, returning silence")
            return np.zeros(int(duration * self.sample_rate))
        
        # Load all bed samples
        beds = []
        for sample_path in bed_samples:
            audio, _ = self.stitcher.load_audio(sample_path)
            if len(audio) > 0:
                beds.append(audio)
        
        if not beds:
            return np.zeros(int(duration * self.sample_rate))
        
        # For simplicity, use the longest bed and loop it
        longest_bed = max(beds, key=len)
        bed_layer = self.stitcher.loop_audio(longest_bed, duration)
        
        return bed_layer
    
    def generate_texture_layer(self, texture_samples: List[Path], duration: float) -> np.ndarray:
        """
        Generate texture layer with slowly fading variations.
        
        Args:
            texture_samples: List of paths to texture sample files
            duration: Target duration in seconds
            
        Returns:
            Generated texture layer audio
        """
        if not texture_samples:
            return np.zeros(int(duration * self.sample_rate))
        
        result = np.zeros(int(duration * self.sample_rate))
        
        # Load textures
        textures = []
        for sample_path in texture_samples:
            audio, _ = self.stitcher.load_audio(sample_path)
            if len(audio) > 0:
                textures.append(audio)
        
        if not textures:
            return result
        
        # Randomly place textures with long crossfades
        current_time = 0
        while current_time < duration:
            texture = np.random.choice(textures)
            texture_duration = len(texture) / self.sample_rate
            
            # Apply random variation
            texture = self.stitcher.apply_random_variation(texture, 0.05)
            
            # Place in result
            start_sample = int(current_time * self.sample_rate)
            end_sample = min(start_sample + len(texture), len(result))
            
            # Mix with existing audio
            mix_length = end_sample - start_sample
            result[start_sample:end_sample] += texture[:mix_length] * 0.5
            
            # Move to next position with overlap
            current_time += texture_duration * 0.7  # 30% overlap
        
        return result
    
    def generate_detail_layer(self, detail_samples: List[Path], duration: float,
                             frequency: float) -> np.ndarray:
        """
        Generate detail layer with scattered individual sounds.
        
        Args:
            detail_samples: List of paths to detail sample files
            duration: Target duration in seconds
            frequency: Number of detail sounds per second
            
        Returns:
            Generated detail layer audio
        """
        if not detail_samples:
            return np.zeros(int(duration * self.sample_rate))
        
        result = np.zeros(int(duration * self.sample_rate))
        
        # Load details
        details = []
        for sample_path in detail_samples:
            audio, _ = self.stitcher.load_audio(sample_path)
            if len(audio) > 0:
                details.append(audio)
        
        if not details:
            return result
        
        # Calculate number of details to place
        num_details = int(duration * frequency)
        
        for _ in range(num_details):
            detail = np.random.choice(details)
            detail = self.stitcher.apply_random_variation(detail, 0.15)
            
            # Random position
            max_start = max(0, len(result) - len(detail))
            start_sample = np.random.randint(0, max_start + 1) if max_start > 0 else 0
            end_sample = min(start_sample + len(detail), len(result))
            
            # Add to result
            mix_length = end_sample - start_sample
            result[start_sample:end_sample] += detail[:mix_length] * 0.3
        
        return result
    
    def generate_environmental_layer(self, environmental_samples: List[Path],
                                    duration: float, frequency: float) -> np.ndarray:
        """
        Generate environmental layer (thunder, wind, etc.).
        
        Args:
            environmental_samples: List of paths to environmental sample files
            duration: Target duration in seconds
            frequency: Number of environmental sounds per second
            
        Returns:
            Generated environmental layer audio
        """
        if not environmental_samples:
            return np.zeros(int(duration * self.sample_rate))
        
        result = np.zeros(int(duration * self.sample_rate))
        
        # Load environmental sounds
        environmental = []
        for sample_path in environmental_samples:
            audio, _ = self.stitcher.load_audio(sample_path)
            if len(audio) > 0:
                environmental.append(audio)
        
        if not environmental:
            return result
        
        # Place environmental sounds
        num_environmental = int(duration * frequency)
        
        for _ in range(num_environmental):
            sound = np.random.choice(environmental)
            
            # Random position
            max_start = max(0, len(result) - len(sound))
            start_sample = np.random.randint(0, max_start + 1) if max_start > 0 else 0
            end_sample = min(start_sample + len(sound), len(result))
            
            # Add to result with fade in/out
            mix_length = end_sample - start_sample
            envelope = np.ones(mix_length)
            fade_len = min(int(0.5 * self.sample_rate), mix_length // 4)
            if fade_len > 0:
                envelope[:fade_len] = np.linspace(0, 1, fade_len)
                envelope[-fade_len:] = np.linspace(1, 0, fade_len)
            
            result[start_sample:end_sample] += sound[:mix_length] * envelope * 0.4
        
        return result
    
    def mix_layers(self, layers: Dict[str, np.ndarray], volumes: Dict[str, float] = None) -> np.ndarray:
        """
        Mix multiple layers with specified volumes.
        
        Args:
            layers: Dictionary of layer_name -> audio_data
            volumes: Dictionary of layer_name -> volume (0-1)
            
        Returns:
            Mixed audio
        """
        if volumes is None:
            volumes = config.DEFAULT_LAYER_VOLUMES
        
        # Find maximum length
        max_length = max(len(audio) for audio in layers.values() if len(audio) > 0)
        
        if max_length == 0:
            return np.array([])
        
        # Initialize result
        result = np.zeros(max_length)
        
        # Mix each layer
        for layer_name, audio in layers.items():
            if len(audio) == 0:
                continue
            
            volume = volumes.get(layer_name, 0.5)
            
            # Pad if needed
            if len(audio) < max_length:
                audio = np.pad(audio, (0, max_length - len(audio)))
            
            result += audio[:max_length] * volume
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(result))
        if max_val > 0:
            result = result / max_val * 0.9
        
        return result

def test_audio_stitcher():
    """Test the audio stitcher."""
    print("Audio stitcher module loaded successfully")
    stitcher = AudioStitcher()
    print(f"Sample rate: {stitcher.sample_rate}")
    return True

if __name__ == '__main__':
    test_audio_stitcher()
