# Rain Sound Video Generator 🌧️

Generate high-quality, 12-hour rain sound videos perfect for YouTube channels focused on sleep, relaxation, and study content.

## Overview

This project provides a complete solution for creating professional rain sound videos similar to popular sleep/relaxation content on YouTube. The generated videos feature:

- **Realistic rain audio**: Procedurally generated rain sounds with customizable intensity
- **Calming visuals**: Dark, soothing backgrounds perfect for sleep videos
- **Long duration**: Generate videos up to 12 hours or more
- **YouTube-ready**: Optimized output format for direct upload

## Features

- 🎵 **Procedural Rain Audio Generation**: Creates realistic rain sounds by layering thousands of individual raindrop sounds
- 🎨 **Customizable Visuals**: Static backgrounds or animated rain effects
- ⚙️ **Flexible Parameters**: Control intensity, duration, and style
- 🚀 **Easy to Use**: Web UI or command-line interface
- 📦 **Standalone**: No external audio samples needed
- 🌊 **Dynamic Intensity**: Interactive timeline editor to vary rain intensity throughout the video
- 🎛️ **Beautiful Web UI**: Modern, intuitive interface for creating videos with variable intensity

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

### Option 1: Web UI (Recommended)

The easiest way to create rain videos with dynamic intensity variations:

```bash
python web_ui.py
```

Then open your browser to **http://localhost:5000**

**Features:**
- 🎨 Beautiful, modern interface
- 📊 Interactive timeline editor to control rain intensity over time
- 🎛️ Real-time visual preview of intensity curve
- 🎯 Drag-and-drop control points
- ⚡ Preset patterns (Light Rain, Storm)
- 🔄 Live generation progress tracking

See [WEB_UI_README.md](WEB_UI_README.md) for detailed UI documentation.

### Option 2: Command Line

For quick command-line generation with fixed intensity:

### 1. Create a Test Video (1 minute)

Test the setup with a quick 1-minute video:

```bash
python create_rain_video.py --test
```

This will create `test_rain.mp4` - a 1-minute sample to verify everything works.

### 2. Create a Full 12-Hour Video

Generate a complete 12-hour rain video:

```bash
python create_rain_video.py
```

This creates `rain_sleep_video.mp4` - a 12-hour video ready for YouTube upload.

**Note:** Generating a 12-hour video takes significant time and disk space:
- Processing time: 1-3 hours (depending on your system)
- File size: ~2-5 GB
- RAM usage: ~2-4 GB

## Usage

### Main Script: create_rain_video.py

```bash
python create_rain_video.py [OPTIONS]
```

**Options:**

- `--duration HOURS`: Video duration in hours (default: 12)
- `--intensity {light,medium,heavy}`: Rain sound intensity (default: medium)
- `--style {static,animated}`: Video style (default: static)
- `--output FILE`: Output video filename (default: rain_sleep_video.mp4)
- `--fps FPS`: Frames per second (default: 1 for static videos)
- `--test`: Create a 1-minute test video

**Examples:**

```bash
# Create a 1-hour video with light rain
python create_rain_video.py --duration 1 --intensity light

# Create a 6-hour video with heavy rain
python create_rain_video.py --duration 6 --intensity heavy

# Create a custom video
python create_rain_video.py --duration 8 --intensity medium --output my_rain.mp4
```

### Individual Components

#### Generate Audio Only

```bash
python generate_rain_audio.py --duration 3600 --intensity medium --output rain.wav
```

#### Generate Video Frames Only

```bash
python generate_rain_video.py --duration 60 --style static --output-dir frames
```

## How It Works

### Audio Generation

The audio generator creates realistic rain sounds using procedural synthesis:

1. **Raindrop Synthesis**: Each raindrop is generated using filtered white noise with an exponential decay envelope
2. **Layering**: Thousands of individual drops are layered at random intervals
3. **Intensity Control**: Drop frequency, size, and amplitude vary based on intensity setting
4. **Ambient Background**: Subtle continuous noise adds depth and realism

### Video Generation

The video generator creates calming visuals:

1. **Background Creation**: Generates dark, gradient backgrounds suitable for sleep content
2. **Static Mode**: Single image repeated throughout (efficient for long videos)
3. **Animated Mode**: Frame-by-frame raindrop animation (for shorter, more dynamic content)

### Combining Audio and Video

The main script combines both:

1. Generates the audio track
2. Creates the visual background
3. Uses MoviePy and FFmpeg to encode the final MP4 file
4. Optimizes for YouTube upload (H.264 video, AAC audio)

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

### Audio Specifications

- **Format**: WAV (uncompressed) → AAC (in final video)
- **Sample Rate**: 44,100 Hz
- **Bit Depth**: 16-bit
- **Channels**: Mono (stereo coming soon)

### Video Specifications

- **Resolution**: 1920x1080 (1080p)
- **Codec**: H.264 (x264)
- **Frame Rate**: 1-30 fps (1 fps for static content)
- **Bitrate**: 2000 kbps (adjustable)

### File Sizes (Approximate)

| Duration | Audio (WAV) | Video (MP4) |
|----------|-------------|-------------|
| 1 hour   | ~300 MB     | ~900 MB     |
| 6 hours  | ~1.8 GB     | ~5.3 GB     |
| 12 hours | ~3.6 GB     | ~10.5 GB    |

## Customization

### Modify Rain Intensity

Edit `generate_rain_audio.py` to adjust:
- `drops_per_second`: Number of raindrops
- Drop type distribution (light/medium/heavy ratio)
- Frequency ranges for different drop types

### Change Visual Style

Edit `generate_rain_video.py` to customize:
- Background colors and gradients
- Rain animation patterns
- Video resolution

### Alternative: Use FFmpeg Directly

If you prefer to use FFmpeg directly:

```bash
# Generate audio first
python generate_rain_audio.py --duration 43200 --output rain.wav

# Generate background
python -c "from generate_rain_video import create_static_background; create_static_background(1920, 1080, 'night').save('bg.png')"

# Combine with FFmpeg
ffmpeg -loop 1 -i bg.png -i rain.wav -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest rain_video.mp4
```

## Troubleshooting

### "MoviePy failed" or encoding errors

Install/update FFmpeg:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

### Memory errors with long videos

For very long videos (12+ hours), consider:
- Increasing system swap space
- Generating audio and video separately
- Using FFmpeg directly instead of MoviePy

### Audio quality issues

Adjust parameters in `generate_rain_audio.py`:
- Increase `sample_rate` to 48000 Hz
- Adjust `drops_per_second` for intensity
- Modify filter frequencies

## Contributing

Contributions welcome! Feel free to:
- Add new rain patterns (thunderstorms, drizzle, etc.)
- Improve audio quality
- Add new visual styles
- Optimize performance

## License

This project is open source. Feel free to use, modify, and distribute.

## Acknowledgments

Inspired by popular rain sound channels on YouTube that help millions of people sleep better every night.

## References

Similar content for inspiration:
- https://www.youtube.com/watch?v=mPZkdNFkNps
- https://www.youtube.com/watch?v=IyYAGmnd2UI
- https://www.youtube.com/watch?v=-2Niq12ywZg
- https://www.youtube.com/watch?v=8plwv25NYRo
