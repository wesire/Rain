# Rain Video Creator - Web UI

Beautiful, interactive web interface for creating rain videos with dynamic intensity variations throughout the video duration.

## Features

- 🎨 **Beautiful Modern UI**: Gradient backgrounds, smooth animations, and intuitive controls
- 📊 **Interactive Timeline Editor**: Visual timeline to control rain intensity over time
- 🎛️ **Real-time Control**: Adjust rain intensity and drop density with interactive sliders
- 📈 **Visual Preview**: See your intensity curve in real-time on the canvas
- ⚡ **Preset Options**: Quick-start with "Light Rain" or "Storm" presets
- 🔄 **Live Progress**: Real-time generation progress with detailed status updates
- 🎯 **Drag & Drop**: Click to add control points, drag to adjust timing and intensity

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure FFmpeg is installed (required for video encoding):
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

## Running the Web UI

Start the web server:

```bash
python web_ui.py
```

Then open your browser to: **http://localhost:5000**

## How to Use

### 1. Set Video Duration
- Enter the desired video duration in hours (e.g., 0.1 for 6 minutes, 12 for 12 hours)
- For testing, start with 0.1 hours to generate quickly

### 2. Create Your Intensity Timeline
- **Click** on the timeline canvas to add control points
- **Drag** control points to adjust their timing and intensity
- **Double-click** a point to remove it
- Use the **sliders** to fine-tune the selected point's properties:
  - **Rain Intensity**: Overall loudness/strength of rain
  - **Drop Density**: Number of raindrops per second

### 3. Use Presets (Optional)
- **Light Rain**: Gentle, consistent rainfall
- **Storm**: Dynamic storm with building and fading intensity

### 4. Generate Video
- Click **"Generate Video"** to start creation
- Watch real-time progress in the progress bar
- Download your video when complete

## Timeline Features

### Control Points
- Each point represents intensity at a specific time
- The system interpolates between points for smooth transitions
- Minimum 2 points required (start and end)

### Visual Elements
- **Blue Gradient Curve**: Shows intensity over time
- **Red Circles**: Draggable control points
- **Grid Lines**: Time (horizontal) and intensity (vertical) markers
- **Time Labels**: Show duration in minutes:seconds
- **Intensity Labels**: Show percentage (0-100%)

## Advanced Features

### Variable Intensity Generation
The backend generates rain audio with:
- **Smooth interpolation** between control points
- **Dynamic drop density** based on timeline settings
- **Varied drop types** (light, medium, heavy) based on intensity
- **Procedural synthesis** for natural-sounding rain

### Technical Details
- Audio generated in 1-second segments for precise control
- Real-time progress updates during generation
- Background threading for non-blocking generation
- Automatic normalization to prevent audio clipping

## Tips for Best Results

1. **Start Small**: Test with 0.1 hours before generating long videos
2. **Smooth Transitions**: Add intermediate points for gradual intensity changes
3. **Dramatic Effects**: Create steep changes for storm effects
4. **Preview First**: Use short durations to preview your intensity pattern
5. **Save Settings**: The timeline data is sent to the server for generation

## Output Files

Generated files will be saved in the project directory:
- `rain_video.mp4`: Your final video (or custom name)
- `rain_audio_variable.wav`: Generated audio track
- `background.png`: Video background image

## Troubleshooting

### Browser Compatibility
- Works best in modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled
- HTML5 Canvas support required

### Generation Issues
- Ensure FFmpeg is installed and in PATH
- Check available disk space for large videos
- Long videos (12+ hours) may take 1-3 hours to generate

### Performance
- Generation runs in background thread
- Progress updates every second
- You can cancel generation at any time

## Architecture

- **Frontend**: Pure HTML5/CSS3/JavaScript (no frameworks)
- **Backend**: Flask Python web server
- **Audio Generation**: NumPy + SciPy procedural synthesis
- **Video Encoding**: MoviePy + FFmpeg

## Future Enhancements

Potential additions:
- Audio preview before full generation
- Multiple audio layer control (rain, thunder, wind)
- Visual effect timeline (animations, colors)
- Save/load timeline configurations
- Export timeline as JSON
- Batch generation with multiple timelines
