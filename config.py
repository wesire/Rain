#!/usr/bin/env python3
"""
Configuration management for Rain Video Creator.
Handles API keys, paths, and default settings.
"""

import os
from pathlib import Path

# Freesound API Configuration
FREESOUND_API_KEY = os.environ.get('FREESOUND_API_KEY', '')
FREESOUND_API_BASE_URL = 'https://freesound.org/apiv2'

# Sample Library Paths
BASE_DIR = Path(__file__).parent
SAMPLES_DIR = BASE_DIR / 'samples'
BEDS_DIR = SAMPLES_DIR / 'beds'
TEXTURES_DIR = SAMPLES_DIR / 'textures'
DETAILS_DIR = SAMPLES_DIR / 'details'
ENVIRONMENTAL_DIR = SAMPLES_DIR / 'environmental'

# Audio Processing Settings
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_BIT_DEPTH = 16

# Normalization Settings
DEFAULT_DOWNLOAD_NORMALIZATION_DB = -3.0  # Target peak for downloads (leaves headroom)
DEFAULT_OUTPUT_NORMALIZATION_DB = -1.0    # Target peak for final output (YouTube standard)
AUTO_NORMALIZE_ENABLED = True             # Auto-normalize downloads by default

# Layer Configuration Defaults
DEFAULT_LAYER_VOLUMES = {
    'bed': 0.7,
    'texture': 0.5,
    'details': 0.4,
    'environmental': 0.3
}

# Crossfade Settings
MIN_CROSSFADE_DURATION = 10.0  # seconds
MAX_CROSSFADE_DURATION = 60.0  # seconds
DEFAULT_CROSSFADE_DURATION = 30.0  # seconds

# Detail Sound Settings
DEFAULT_DETAIL_FREQUENCY = 0.5  # sounds per second
DEFAULT_ENVIRONMENTAL_FREQUENCY = 0.1  # sounds per second

# Sample Requirements
MIN_BED_DURATION = 60  # seconds
MIN_TEXTURE_DURATION = 30  # seconds
MIN_DETAIL_DURATION = 1  # seconds
MIN_ENVIRONMENTAL_DURATION = 10  # seconds

# Freesound Search Defaults
DEFAULT_SEARCH_PAGE_SIZE = 15
SUPPORTED_AUDIO_FORMATS = ['.wav', '.mp3', '.ogg', '.flac']

def ensure_sample_directories():
    """Create sample library directory structure if it doesn't exist."""
    for directory in [BEDS_DIR, TEXTURES_DIR, DETAILS_DIR, ENVIRONMENTAL_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def get_config():
    """Get all configuration as a dictionary."""
    return {
        'freesound_api_key': FREESOUND_API_KEY,
        'samples_dir': str(SAMPLES_DIR),
        'layer_volumes': DEFAULT_LAYER_VOLUMES,
        'crossfade_duration': DEFAULT_CROSSFADE_DURATION,
        'detail_frequency': DEFAULT_DETAIL_FREQUENCY,
        'environmental_frequency': DEFAULT_ENVIRONMENTAL_FREQUENCY,
        'sample_rate': DEFAULT_SAMPLE_RATE,
        'normalization': {
            'auto_normalize': AUTO_NORMALIZE_ENABLED,
            'download_target_db': DEFAULT_DOWNLOAD_NORMALIZATION_DB,
            'output_target_db': DEFAULT_OUTPUT_NORMALIZATION_DB
        }
    }
