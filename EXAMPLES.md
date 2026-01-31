# Examples and Use Cases

This document provides practical examples for different use cases of the Rain Sound Video Generator.

## Quick Examples

### 1. Test the Setup
```bash
# Create a 1-minute test video to verify everything works
python create_rain_video.py --test

# Result: test_rain.mp4 (1 minute, ~30MB)
```

### 2. Standard YouTube Video
```bash
# Create a standard 12-hour video for overnight sleep
python create_rain_video.py

# Result: rain_sleep_video.mp4 (12 hours, ~3-5GB)
# Upload time: 30-60 minutes (depending on internet speed)
```

### 3. Study Session Video
```bash
# Create a 2-hour video for study sessions
python create_rain_video.py --duration 2 --intensity light --output study_rain.mp4

# Result: study_rain.mp4 (2 hours, ~600MB)
# Perfect for: Studying, reading, working
```

### 4. Power Nap Video
```bash
# Create a 20-minute video for power naps (0.33 hours)
python create_rain_video.py --duration 0.33 --intensity medium --output nap_rain.mp4

# Result: nap_rain.mp4 (20 minutes, ~100MB)
# Perfect for: Quick naps, meditation
```

### 5. Heavy Rain for Noise Masking
```bash
# Create an 8-hour heavy rain video for blocking loud noises
python create_rain_video.py --duration 8 --intensity heavy --output heavy_rain.mp4

# Result: heavy_rain.mp4 (8 hours, ~2.5GB)
# Perfect for: Noisy environments, tinnitus relief
```

## Batch Creation Examples

### Create a Full Channel Library
```bash
# Use the batch script to create multiple variations
./create_multiple_videos.sh  # Linux/Mac
# or
create_multiple_videos.bat   # Windows

# Creates:
# - test_rain.mp4 (1 minute)
# - light_rain_8hr.mp4 (8 hours, light)
# - medium_rain_10hr.mp4 (10 hours, medium)
# - heavy_rain_12hr.mp4 (12 hours, heavy)
```

### Custom Batch Creation
```bash
# Create your own custom set
for duration in 6 8 10 12; do
  for intensity in light medium heavy; do
    python create_rain_video.py \
      --duration $duration \
      --intensity $intensity \
      --output "rain_${intensity}_${duration}hr.mp4"
  done
done

# Creates 12 videos: 4 durations × 3 intensities
```

## Component Examples

### Audio Only Generation

Generate just the audio for use in other projects:

```bash
# Generate 1 hour of medium rain audio
python generate_rain_audio.py --duration 3600 --intensity medium --output 1hr_rain.wav

# Generate 30 minutes of light rain
python generate_rain_audio.py --duration 1800 --intensity light --output 30min_light.wav

# Generate 2 hours of heavy rain at higher quality
python generate_rain_audio.py --duration 7200 --intensity heavy --sample-rate 48000 --output 2hr_heavy_hq.wav
```

### Video Background Only

Generate just the visual background:

```bash
# Create a static background image
python generate_rain_video.py --style static --output-dir backgrounds

# Create animated frames (first 100 frames)
python generate_rain_video.py --style animated --intensity heavy --output-dir rain_frames
```

### Combine Pre-generated Audio and Video

Use FFmpeg directly to combine existing audio and video:

```bash
# Create background
python -c "from generate_rain_video import create_static_background; create_static_background(1920, 1080, 'night').save('bg.png')"

# Generate audio
python generate_rain_audio.py --duration 43200 --output rain.wav

# Combine with FFmpeg
ffmpeg -loop 1 -i bg.png -i rain.wav \
  -c:v libx264 -tune stillimage \
  -c:a aac -b:a 192k \
  -pix_fmt yuv420p \
  -shortest final_video.mp4
```

## Use Case Scenarios

### Scenario 1: New YouTube Channel

**Goal**: Launch a rain sounds channel with initial content

**Steps**:
1. Create test video to verify quality
2. Generate 3 core videos (light, medium, heavy rain)
3. Upload with optimized metadata
4. Monitor analytics and adjust

**Commands**:
```bash
# Day 1: Test and first video
python create_rain_video.py --test
python create_rain_video.py --duration 10 --intensity medium

# Day 2-4: Complete library
./create_multiple_videos.sh

# Week 2: Add variations
python create_rain_video.py --duration 6 --intensity light --output morning_rain.mp4
python create_rain_video.py --duration 8 --intensity heavy --output night_rain.mp4
```

### Scenario 2: Content Creator Needing Background Audio

**Goal**: Create rain sounds for use in other videos

**Steps**:
1. Generate various lengths and intensities
2. Use as background audio in vlogs, meditation videos, etc.

**Commands**:
```bash
# Short clips for intros/outros
python generate_rain_audio.py --duration 30 --intensity light --output intro_rain.wav

# Medium clips for b-roll
python generate_rain_audio.py --duration 300 --intensity medium --output broll_rain.wav

# Long ambient tracks
python generate_rain_audio.py --duration 1800 --intensity medium --output ambient_rain.wav
```

### Scenario 3: App Developer Needing Sound Effects

**Goal**: Generate rain sounds for a meditation or sleep app

**Steps**:
1. Create various lengths and formats
2. Convert to different formats (MP3, OGG) if needed
3. Loop shorter clips for app use

**Commands**:
```bash
# Generate base sounds
python generate_rain_audio.py --duration 60 --intensity light --output app_light.wav
python generate_rain_audio.py --duration 60 --intensity heavy --output app_heavy.wav

# Convert to MP3 (requires FFmpeg)
ffmpeg -i app_light.wav -b:a 192k app_light.mp3
ffmpeg -i app_heavy.wav -b:a 192k app_heavy.mp3
```

### Scenario 4: Personal Use - Better Sleep

**Goal**: Create custom rain sounds for personal sleep routine

**Steps**:
1. Test different intensities to find preference
2. Create overnight video matching sleep schedule
3. Play on phone/tablet while sleeping

**Commands**:
```bash
# Try different intensities (1 minute each)
python create_rain_video.py --test  # Creates medium intensity
python generate_rain_audio.py --duration 60 --intensity light --output test_light.wav
python generate_rain_audio.py --duration 60 --intensity heavy --output test_heavy.wav

# Create full video for your preferred intensity
python create_rain_video.py --duration 9 --intensity light --output my_sleep_rain.mp4
```

## Performance Tips

### For Faster Processing

1. **Reduce duration for testing**:
   ```bash
   python create_rain_video.py --duration 0.5 --output quick_test.mp4
   ```

2. **Use static video (not animated)**:
   ```bash
   python create_rain_video.py --style static  # Default, most efficient
   ```

3. **Lower FPS for static videos**:
   ```bash
   python create_rain_video.py --fps 1  # Minimal for static background
   ```

4. **Generate audio separately** (can be done overnight):
   ```bash
   # Generate audio first (long process)
   python generate_rain_audio.py --duration 43200 --output rain.wav
   
   # Then quickly combine with video later
   python create_rain_video.py --use-existing-audio rain.wav
   ```

### For Better Quality

1. **Higher sample rate**:
   ```bash
   python generate_rain_audio.py --duration 3600 --sample-rate 48000 --output hq_rain.wav
   ```

2. **Higher video bitrate** (edit in create_rain_video.py):
   - Change `bitrate='2000k'` to `bitrate='5000k'`

3. **Longer, more varied generation**:
   - Increase duration to create unique content throughout

## Troubleshooting Examples

### Problem: Out of Memory

**Solution**: Generate in chunks
```bash
# Instead of 12 hours at once, generate 3x 4-hour segments
python generate_rain_audio.py --duration 14400 --output rain_part1.wav
python generate_rain_audio.py --duration 14400 --output rain_part2.wav
python generate_rain_audio.py --duration 14400 --output rain_part3.wav

# Combine with FFmpeg
ffmpeg -i "concat:rain_part1.wav|rain_part2.wav|rain_part3.wav" -c copy rain_12hr.wav
```

### Problem: Processing Too Slow

**Solution**: Use simpler generation
```bash
# Reduce drops per second by editing generate_rain_audio.py
# Or use pre-generated audio and just create video
```

### Problem: File Too Large

**Solution**: Reduce bitrate
```bash
# Edit create_rain_video.py and change:
# bitrate='2000k' → bitrate='1000k'
# Or compress after generation:
ffmpeg -i rain_sleep_video.mp4 -b:v 1000k -b:a 128k compressed_rain.mp4
```

## Advanced Customization Examples

### Custom Background Colors

Edit `generate_rain_video.py`:
```python
# Change background_color in create_static_background()
# Example: Darker night
background_color = (10, 15, 20)  # Very dark blue

# Example: Warmer tone
background_color = (25, 20, 15)  # Warm dark
```

### Custom Rain Characteristics

Edit `generate_rain_audio.py`:
```python
# For more intense rain, increase drops_per_second
drops_per_second = np.random.uniform(100, 200)  # Heavy

# For lighter, more sparse rain
drops_per_second = np.random.uniform(5, 15)  # Very light

# For more variety in drop sounds
drop_types = ['light'] * 2 + ['medium'] * 5 + ['heavy'] * 3
```

## YouTube Upload Examples

### Optimal Upload Settings
```
Resolution: 1920x1080 (1080p)
Frame Rate: 30fps (or 1fps for static)
Bitrate: 2000-5000 kbps
Audio: AAC, 192 kbps
Format: MP4 (H.264)
```

### Upload Schedule Strategy
```
Week 1: 
  - Monday: 12hr Heavy Rain
  - Thursday: 10hr Medium Rain
  
Week 2:
  - Monday: 8hr Light Rain
  - Thursday: 6hr Study Rain
  
Continue alternating...
```

### Title Testing
Test different titles with same video:
```
Test A: "Rain Sounds for Sleeping - 12 Hours"
Test B: "12 Hour Rain Sounds - Black Screen Sleep"
Test C: "Heavy Rain Sounds - 12 Hours for Deep Sleep"

Monitor which gets better click-through rate
```

---

For more examples and ideas, see the main README.md and QUICKSTART.md files.
