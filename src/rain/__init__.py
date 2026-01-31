"""Rain audio and video generation system."""

__version__ = "2.0.0"

from .audio_engine import AudioAssetLoader, RainAudioEngine, equal_power_crossfade
from .loudness import normalize_loudness, apply_limiter, apply_fades, apply_filters

__all__ = [
    'AudioAssetLoader',
    'RainAudioEngine', 
    'equal_power_crossfade',
    'normalize_loudness',
    'apply_limiter',
    'apply_fades',
    'apply_filters',
]
