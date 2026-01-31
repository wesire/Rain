# Quick Start Guide

This guide will help you create your first rain sound video in minutes.

## Step 1: Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Make sure FFmpeg is installed:
```bash
# Test FFmpeg installation
ffmpeg -version
```

If FFmpeg is not installed, install it:
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Step 2: Create a Test Video

Create a 1-minute test video to verify everything works:

```bash
python create_rain_video.py --test
```

This will create `test_rain.mp4`. Play it to verify the audio and video work correctly.

## Step 3: Create Your First Full Video

### Option A: Use the Simple Command

For a standard 12-hour video:
```bash
python create_rain_video.py
```

This creates `rain_sleep_video.mp4` - a 12-hour video ready for YouTube.

### Option B: Customize Your Video

Create different variations:

**Light Rain (8 hours):**
```bash
python create_rain_video.py --duration 8 --intensity light --output light_rain_8hr.mp4
```

**Heavy Rain (10 hours):**
```bash
python create_rain_video.py --duration 10 --intensity heavy --output heavy_rain_10hr.mp4
```

**Medium Rain (6 hours):**
```bash
python create_rain_video.py --duration 6 --intensity medium --output medium_rain_6hr.mp4
```

## Step 4: Upload to YouTube

1. Log in to YouTube Studio
2. Click "Create" → "Upload videos"
3. Select your generated MP4 file
4. Add title, description, and thumbnail
5. Set to "Public" and publish

### Recommended Video Settings:

**Title Ideas:**
- "Rain Sounds for Sleeping - 12 Hours Black Screen"
- "Heavy Rain & Thunder - 10 Hours Sleep Music"
- "Gentle Rain Sounds - 8 Hours Relaxation"

**Tags:**
```
rain sounds, sleep sounds, rain for sleeping, white noise, rain sounds for sleeping, 
sleep music, relaxing rain, thunder sounds, storm sounds, nature sounds, 
ambient sounds, study music, meditation music, insomnia relief
```

## Tips for Success

### Audio Quality
- Use headphones to test the audio quality
- Ensure consistent volume throughout
- Light rain: Gentle, soothing for deep sleep
- Heavy rain: More intense, great for noise masking

### Video Duration
- 8-12 hours is ideal for overnight use
- Shorter videos (1-3 hours) work for naps or study sessions

### File Size Management
- 12-hour video ≈ 3-5 GB (reasonable for upload)
- Use `--fps 1` for static videos to reduce file size
- YouTube will re-encode your video anyway

### Processing Time
- 1-minute test: ~30 seconds
- 1-hour video: ~5-10 minutes
- 12-hour video: ~1-3 hours (depending on your computer)

## Advanced Usage

### Generate Only Audio
```bash
python generate_rain_audio.py --duration 43200 --intensity medium --output rain_12hr.wav
```

### Generate Only Video Background
```bash
python generate_rain_video.py --style static --output-dir frames
```

### Use FFmpeg Directly
```bash
# After generating audio and background separately:
ffmpeg -loop 1 -i background.png -i rain_audio.wav \
  -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
  -pix_fmt yuv420p -shortest output.mp4
```

## Troubleshooting

**"MoviePy error"**: Install FFmpeg
**"Memory error"**: Try a shorter duration first
**"Module not found"**: Run `pip install -r requirements.txt`

## Next Steps

1. Create multiple versions (light, medium, heavy)
2. Experiment with different durations
3. Monitor YouTube analytics to see what viewers prefer
4. Consider adding variations like thunder or wind

Happy creating! 🌧️
