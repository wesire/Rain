# Rain Sound Video Generator 🌧️

Generate professional, sleep-grade rain sound videos perfect for YouTube channels focused on sleep, relaxation, and study content.

## Overview

This project provides a complete solution for creating professional rain sound videos similar to popular sleep/relaxation content on YouTube. Version 2.0 features a completely rewritten audio engine with:

- **Professional audio quality**: Sleep-grade audio with LUFS normalization, soft limiting, and seamless crossfades
- **Asset-based or procedural**: Use your own rain recordings or high-quality procedural generation
- **Memory efficient**: Stream-renders long videos without memory issues
- **Calming visuals**: Procedural rain animation or custom background videos
- **Long duration**: Generate videos up to 12 hours or more
- **YouTube-ready**: Optimized output format with proper loudness standards

## Features

### Audio Engine v2.0
- 🎵 **Asset-Based Generation**: Use real rain recordings for natural, authentic sound
- 🔄 **Seamless Looping**: Equal-power crossfades eliminate clicks and pops
- 📊 **LUFS Normalization**: Consistent loudness at -14 LUFS (YouTube standard)
- 🎚️ **Professional Processing**: Soft limiting, filtering, and fade-ins/outs
- 🌧️ **Multi-Layer Mixing**: Bed layer + detail sounds + optional thunder
- 💾 **Memory Efficient**: Chunk-based streaming for 8+ hour videos
- 🎲 **Smart Randomization**: Avoids obvious repetition in loops

### Video Generation
- 🎨 **Procedural Rain Animation**: Generated rain drops with OpenCV
- 🎬 **Background Video Loop**: Use custom background videos
- 📹 **Streaming Rendering**: Memory-efficient for long durations

### Legacy Features
- 🌊 **Dynamic Intensity**: Interactive timeline editor (via Web UI)
- 🎛️ **Beautiful Web UI**: Modern interface for variable intensity videos
- 📦 **Fallback Mode**: High-quality procedural audio if no assets available

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg (required for video encoding)

### Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

### New Audio Engine (Recommended)

The new audio engine provides professional, sleep-grade audio quality:

#### 10-minute preview (fast test)
```bash
python -m rain generate --preview-minutes 10 --out preview.mp4 --mode procedural
```

#### Full 8-hour video with procedural visuals
```bash
python -m rain generate --duration-hours 8 --out rain_8hr.mp4 --mode procedural
```

#### With custom background video
```bash
python -m rain generate --duration-hours 8 --out rain_8hr.mp4 \
    --mode video_loop --background-video my_background.mp4
```

#### Audio only (for testing or separate use)
```bash
python -m rain generate --duration-hours 1 --out rain_1hr.wav --audio-only
```

### Asset Folder Setup (Optional)

For the best quality, provide your own rain audio recordings:

```
assets/audio/
├── bed/          # Long continuous rain (WAV, 48kHz, stereo, 60+ seconds each)
│   ├── rain_light_01.wav
│   ├── rain_medium_01.wav
│   └── rain_heavy_01.wav
├── details/      # Short sounds (WAV, 48kHz, stereo, 1-5 seconds)
│   ├── droplet_01.wav
│   └── splash_01.wav
└── thunder/      # Distant thunder (WAV, 48kHz, stereo, 5-30 seconds)
    └── thunder_distant_01.wav
```

**Note:** If no assets are provided, the system uses improved pink noise generation with proper stereo field.

### Legacy Web UI

The original web UI with dynamic intensity control is still available:

```bash
python web_ui.py
```

Then open your browser to **http://localhost:5000**

See [WEB_UI_README.md](WEB_UI_README.md) for detailed UI documentation.
- Processing time: 1-3 hours (depending on your system)
- File size: ~2-5 GB
- RAM usage: ~2-4 GB

## CLI Reference

### Main Command: `python -m rain generate`

Generate professional rain audio/video with the new audio engine.

**Options:**

```
--duration-hours FLOAT        Duration in hours (default: 8.0)
--preview-minutes FLOAT       Quick preview duration in minutes (overrides duration-hours)
--out PATH                    Output file path (required)
--assets-dir PATH             Assets directory (default: assets)
--sample-rate INTEGER         Audio sample rate in Hz (default: 48000)
--lufs FLOAT                  Target loudness in LUFS (default: -14.0)
--mode [video_loop|procedural] Video mode (default: procedural)
--background-video PATH       Background video for video_loop mode
--no-thunder                  Disable thunder sounds
--audio-only                  Generate audio only, no video
--video-fps INTEGER           Video frame rate (default: 30)
--video-resolution TEXT       Video resolution (default: 1920x1080)
--seed INTEGER                Random seed for reproducibility
```

**Examples:**

```bash
# 1-hour audio with pink noise fallback
python -m rain generate --duration-hours 1 --out rain_1hr.wav --audio-only

# 10-minute preview video
python -m rain generate --preview-minutes 10 --out preview.mp4

# Full 8-hour video, procedural animation
python -m rain generate --duration-hours 8 --out rain_8hr.mp4 --mode procedural

# 12-hour video with custom background (requires background.mp4)
python -m rain generate --duration-hours 12 --out rain_12hr.mp4 \
    --mode video_loop --background-video background.mp4

# Disable thunder, custom seed for reproducibility
python -m rain generate --duration-hours 2 --out rain_2hr.mp4 \
    --no-thunder --seed 42

# Custom video settings
python -m rain generate --preview-minutes 5 --out test.mp4 \
    --video-fps 24 --video-resolution 1280x720
```

### Audio Analysis Tool

Analyze generated audio for quality metrics:

```bash
python scripts/analyze_audio.py output.wav
```

**Output includes:**
- Peak level (dBFS)
- Integrated loudness (LUFS) 
- Clipping detection
- RMS level
- Dynamic range
- Stereo correlation
- Duration, sample rate, channels

### Legacy Commands

The original simple scripts are still available:

```bash
# Generate audio only (legacy)
python generate_rain_audio.py --duration 3600 --intensity medium --output rain.wav

# Create complete video (legacy)
python create_rain_video.py --duration 8 --intensity medium
```

## How It Works

### Audio Engine v2.0

The new audio engine generates professional sleep-grade audio through a sophisticated pipeline:

#### 1. Asset Loading & Preparation
- Loads WAV files from assets/audio/ folders
- Resamples all audio to target sample rate (48kHz by default)
- Converts mono to stereo for proper stereo field
- Stores audio as float32 arrays in memory

#### 2. Chunk-Based Rendering
- Generates audio in 20-second chunks with 3-second overlaps
- Keeps memory usage constant regardless of total duration
- Enables 8+ hour renders without RAM issues

#### 3. Multi-Layer Mixing
- **Bed Layer**: Continuous rain texture from long recordings
  - Randomized segment selection to avoid obvious loops
  - Tracks recently used segments to prevent repetition
  - Equal-power crossfades at loop points for seamless transitions
- **Details Layer**: Random droplet/splash sounds
  - Poisson distribution for natural timing (1-3 per second)
  - Random amplitude variation for realism
- **Thunder Layer** (optional): Rare distant thunder
  - 5% probability per chunk
  - Long fade-ins and fade-outs for natural sound

#### 4. Crossfading & Overlap-Add
- Equal-power crossfades use √ curves for constant perceived loudness
- Smooth transitions between chunks eliminate clicks
- Overlap regions are blended seamlessly

#### 5. Audio Processing Pipeline
- **Filtering**: 
  - High-pass at 25Hz to remove rumble
  - Low-pass at 15kHz to tame hiss (optional)
- **Fades**: Gentle fade-in (3s) and fade-out (5s)
- **Limiting**: Soft limiter with ceiling at -1 dBFS
- **Loudness Normalization**: 
  - Measures integrated loudness with pyloudnorm
  - Adjusts gain to target -14 LUFS (YouTube standard)
  - Falls back to RMS normalization if pyloudnorm unavailable

#### 6. Fallback Mode
If no audio assets are provided:
- Generates improved pink noise using Voss-McCartney algorithm
- Proper stereo field with independent left/right channels
- Band-pass filtering (200-8000 Hz) for rain-like spectrum
- Synthetic raindrop sounds with randomized panning
- Still applies full processing chain (limiting, LUFS, etc.)

### Video Generation

#### Procedural Mode
- Dark gradient background (night sky colors)
- Animated rain streaks using particle system
- Rendered with OpenCV frame-by-frame
- Memory-efficient chunk-based rendering

#### Video Loop Mode
- Uses FFmpeg to loop an existing background video
- Scales to target resolution
- Drops original audio
- Efficient for long durations

### Final Muxing
- Combines silent video + processed audio
- Uses FFmpeg with AAC audio codec
- H.264 video codec for YouTube compatibility
- Properly maps audio/video streams

## YouTube Upload Tips

### Recommended Settings

- **Resolution**: 1920x1080 (Full HD)
- **Duration**: 8-12 hours for sleep content
- **Title Examples**:
  - "Rain Sounds for Sleeping - 12 Hours of Relaxing Rain"
  - "Heavy Rain & Thunder Sounds - 10 Hours Sleep Aid"
  - "Gentle Rain Sounds - 8 Hours of Peaceful Rainfall"

### Description Template

```
🌧️ 12 Hours of Relaxing Rain Sounds for Sleep, Study, or Meditation

Peaceful rain sounds to help you fall asleep, stay asleep, and wake up refreshed. 
Perfect for insomnia, studying, reading, meditation, or just relaxing.

This video features high-quality rain audio with a calming dark background - 
perfect for overnight use.

⏰ Timestamps:
0:00 - Start
12:00:00 - End

🎧 Best experienced with headphones or quality speakers

#rainsounds #sleepsounds #whitenoise #rainforsleep #relaxing
```

### Thumbnail Tips

- Use dark, calming colors (blues, grays)
- Include text: "12 HOURS" or "RAIN SOUNDS"
- Show rain droplets or stormy imagery
- Keep it simple and easy to read

## Technical Details

### Audio Specifications (v2.0)

- **Format**: WAV (float32) → AAC in final video
- **Sample Rate**: 48,000 Hz (configurable)
- **Bit Depth**: 32-bit float during processing, 16-bit in final output
- **Channels**: Stereo (2 channels)
- **Loudness**: -14 LUFS (YouTube standard)
- **Peak Level**: -1 dBFS maximum
- **Filtering**: HPF @ 25Hz, optional LPF @ 15kHz

### Video Specifications

- **Resolution**: 1920x1080 (1080p, configurable)
- **Codec**: H.264 (libx264)
- **Frame Rate**: 30 fps (configurable)
- **Bitrate**: Adaptive based on content
- **Pixel Format**: yuv420p (maximum compatibility)

### Performance & File Sizes

#### Memory Usage
- **Chunk-based rendering**: ~200-500 MB RAM regardless of duration
- **Asset loading**: ~50-100 MB per minute of loaded audio
- **Video rendering**: ~500 MB-1 GB for OpenCV

#### Processing Time (approximate, on modern CPU)
- Audio generation: ~1-2 minutes per hour of output
- Video rendering (procedural): ~5-10 minutes per hour @ 30fps
- Video loop: ~1-2 minutes per hour
- Total for 8-hour video: ~40-80 minutes

#### File Sizes (approximate)

| Duration | Audio (WAV) | Video (MP4) | Notes |
|----------|-------------|-------------|-------|
| 10 min   | ~55 MB      | ~180 MB     | Preview |
| 1 hour   | ~330 MB     | ~1.1 GB     | Test |
| 8 hours  | ~2.6 GB     | ~8.5 GB     | Standard |
| 12 hours | ~3.9 GB     | ~12.7 GB    | Extended |

*MP4 sizes with 192k AAC audio + medium quality H.264 video*

## Customization

### Using Your Own Audio Assets

For best results, provide your own rain recordings:

1. **Bed samples** (assets/audio/bed/):
   - Long continuous rain recordings (60+ seconds)
   - High quality: 48kHz, stereo, 24-bit or higher
   - Natural ambience, consistent rain texture
   - Multiple variations for randomization

2. **Detail samples** (assets/audio/details/):
   - Short droplet or splash sounds (1-5 seconds)
   - Individual rain drops, water impacts
   - High quality: 48kHz, stereo
   - Variety helps avoid repetition

3. **Thunder samples** (assets/audio/thunder/) [optional]:
   - Distant thunder recordings (5-30 seconds)
   - Low rumble, not too loud or scary
   - Multiple variations for variety

**Recording tips:**
- Use a quality stereo microphone
- Record in quiet environment (minimize wind, traffic)
- Avoid clipping - leave headroom
- Natural recordings sound better than synthetic

### Adjusting Audio Settings

Edit CLI parameters or modify the code:

```python
# In src/rain/audio_engine.py
engine = RainAudioEngine(
    loader=loader,
    chunk_seconds=20.0,      # Chunk size for rendering
    overlap_seconds=3.0,     # Crossfade duration
    include_thunder=True,    # Enable/disable thunder
    seed=42                  # For reproducibility
)

# Adjust detail sound frequency
# In _add_details() method, change:
num_details = self.rng.poisson(2 * samples / sr)  # 2 = average per second
```

### Customizing Video Visuals

For procedural rain animation, edit `src/rain/video.py`:

```python
# Modify background colors
top_color = np.array([40, 35, 30], dtype=np.uint8)     # Dark blue-gray
bottom_color = np.array([20, 18, 15], dtype=np.uint8)  # Darker

# Adjust raindrop parameters
num_drops = 300              # Number of visible drops
raindrops[:, 2] = np.random.uniform(15, 30, num_drops)  # Speed range
raindrops[:, 3] = np.random.uniform(20, 50, num_drops)  # Length range
```

### Adjusting Audio Processing

Modify processing parameters in CLI or code:

```bash
# Different loudness target (e.g., for podcasts)
python -m rain generate --duration-hours 1 --out rain.wav \
    --audio-only --lufs -16.0

# Different sample rate
python -m rain generate --duration-hours 1 --out rain.wav \
    --audio-only --sample-rate 44100
```

Or edit `src/rain/loudness.py`:

```python
# Adjust limiter ceiling
audio = apply_limiter(audio, ceiling_db=-0.5)  # Less headroom

# Adjust filter frequencies
audio = apply_filters(audio, sr, hpf_freq=30.0, lpf_freq=12000.0)

# Adjust fade durations
audio = apply_fades(audio, sr, fade_in_sec=5.0, fade_out_sec=10.0)
```

## Troubleshooting

### FFmpeg not found

**Error**: "FFmpeg is required but not found"

**Solution**: Install FFmpeg:
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html and add to PATH
```

After installation, restart your terminal.

### Memory errors with long videos

**Problem**: Out of memory when generating 8+ hour videos

**Solutions**:
1. The new audio engine should handle this automatically with chunk-based rendering
2. If still having issues, try generating audio and video separately:
   ```bash
   # Generate audio only
   python -m rain generate --duration-hours 8 --out audio.wav --audio-only
   
   # Generate silent video
   python -m rain generate --duration-hours 8 --out video_silent.mp4 \
       --mode procedural
   
   # Combine manually with FFmpeg
   ffmpeg -i video_silent.mp4 -i audio.wav -c:v copy -c:a aac \
       -b:a 192k -map 0:v:0 -map 1:a:0 -shortest final.mp4
   ```

### Audio quality issues

**Problem**: Audio sounds harsh, has clicks, or inconsistent volume

**Solutions**:
1. Check LUFS normalization is working:
   ```bash
   python scripts/analyze_audio.py output.wav
   ```
2. Ensure you have pyloudnorm installed:
   ```bash
   pip install pyloudnorm
   ```
3. Verify no clipping in analysis output
4. Try adjusting the limiter ceiling in code if needed

### OpenCV not found (procedural video mode)

**Error**: "OpenCV not available"

**Solution**: Install OpenCV:
```bash
pip install opencv-python
```

### No audio assets warning

**Message**: "No audio assets found, using improved procedural generation..."

This is normal if you haven't added audio files to assets/audio/. The system will use high-quality pink noise generation as fallback. For best results, add your own rain recordings to assets/audio/bed/.

### Video rendering is slow

**Problem**: Video generation takes too long

**Solutions**:
1. Use video_loop mode with a short background video (faster than procedural)
2. Reduce frame rate: `--video-fps 24` or even `--video-fps 15`
3. Reduce resolution: `--video-resolution 1280x720`
4. For 8+ hour videos, expect ~1 hour rendering time on modern hardware

### Audio-video sync issues

**Problem**: Audio and video durations don't match

**Solution**: This shouldn't happen with the new system, but if it does:
1. Check both files with:
   ```bash
   ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 video.mp4
   ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 audio.wav
   ```
2. The muxer uses `-shortest` flag to handle mismatches automatically

## Project Structure

```
Rain/
├── src/
│   └── rain/
│       ├── __init__.py          # Package initialization
│       ├── __main__.py          # CLI entry point (python -m rain)
│       ├── audio_engine.py      # Core audio generation engine
│       ├── loudness.py          # LUFS normalization & processing
│       ├── video.py             # Video generation utilities
│       └── muxer.py             # FFmpeg wrapper for muxing
├── assets/
│   └── audio/
│       ├── bed/                 # Long rain recordings (60s+)
│       │   └── .gitkeep
│       ├── details/             # Short droplet sounds (1-5s)
│       │   └── .gitkeep
│       └── thunder/             # Distant thunder (optional)
│           └── .gitkeep
├── scripts/
│   └── analyze_audio.py         # Audio quality analysis tool
├── tests/
│   ├── __init__.py
│   └── test_audio_engine.py    # Audio engine tests
├── templates/                   # Web UI templates
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── web_ui.py                    # Legacy web UI with intensity editor
├── generate_rain_audio.py       # Legacy audio generator
├── generate_rain_video.py       # Legacy video generator
└── create_rain_video.py         # Legacy main script
```

## Contributing

Contributions welcome! Areas for improvement:

- Additional audio processing features (reverb, EQ)
- More video animation styles
- Performance optimizations
- Additional output formats
- Better asset management tools

## License

This project is open source. Feel free to use, modify, and distribute.

## Changelog

### Version 2.0 (Current)
- Complete audio engine rewrite with professional quality
- Asset-based generation with real recordings
- LUFS normalization and soft limiting
- Seamless crossfading and overlap-add
- Memory-efficient chunk-based rendering
- Improved procedural fallback with pink noise
- New CLI with extensive options
- Audio analysis tools

### Version 1.0 (Legacy)
- Basic procedural audio generation
- Simple video creation
- Web UI with intensity editor

## Acknowledgments

Inspired by popular rain sound channels on YouTube that help millions of people sleep better every night.

## References

Similar content for inspiration:
- https://www.youtube.com/watch?v=mPZkdNFkNps
- https://www.youtube.com/watch?v=IyYAGmnd2UI
- https://www.youtube.com/watch?v=-2Niq12ywZg
- https://www.youtube.com/watch?v=8plwv25NYRo
