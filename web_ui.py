#!/usr/bin/env python3
"""
Web UI for creating rain videos with variable intensity over time.
Provides an interactive interface to adjust rain and audio parameters throughout the video.
"""

import os
import json
import threading
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from generate_rain_audio import generate_rain_audio
from generate_rain_video import create_static_background
from create_rain_video import create_rain_video
import numpy as np
from scipy.io import wavfile
from scipy import signal
from tqdm import tqdm
from PIL import Image
from moviepy.editor import ImageClip, AudioFileClip
from pathlib import Path
import config
from freesound_client import FreesoundClient
from audio_stitcher import MultiLayerMixer
import shutil
import librosa
import soundfile as sf

app = Flask(__name__)

# Global variable to track generation progress
generation_status = {
    'in_progress': False,
    'progress': 0,
    'message': '',
    'output_file': None,
    'error': None
}

# Thread cancellation event
cancel_event = threading.Event()

# Category mapping for frontend/backend compatibility
CATEGORY_MAP = {
    'bed': 'beds',
    'beds': 'beds',
    'texture': 'textures',
    'textures': 'textures',
    'detail': 'details',
    'details': 'details',
    'environmental': 'environmental'
}

def normalize_audio(audio_path, target_db=-3.0):
    """
    Normalize audio file to target dB level.
    
    Args:
        audio_path: Path to audio file
        target_db: Target peak level in dB (default: -3.0)
        
    Returns:
        Tuple of (original_peak_db, target_db) or None if error
    """
    try:
        # Load audio at native sample rate, mono
        y, sr = librosa.load(str(audio_path), sr=None, mono=True)
        
        # Calculate current peak
        peak = np.max(np.abs(y))
        current_db = 20 * np.log10(peak) if peak > 0 else -np.inf
        
        # Calculate gain needed
        target_linear = 10 ** (target_db / 20)
        gain = target_linear / peak if peak > 0 else 1.0
        
        # Apply gain
        y_normalized = y * gain
        
        # Save normalized audio back at original sample rate
        sf.write(str(audio_path), y_normalized, sr)
        
        return current_db, target_db
    except Exception as e:
        print(f"Error normalizing audio: {e}")
        return None

def generate_rain_audio_variable(duration_seconds, intensity_timeline, sample_rate=44100, output_file='rain.wav'):
    """
    Generate rain audio with variable intensity based on timeline.
    
    Args:
        duration_seconds: Total duration in seconds
        intensity_timeline: List of {time: seconds, intensity: 0.0-1.0, drop_density: 0.0-1.0}
        sample_rate: Audio sample rate
        output_file: Output WAV file path
    """
    global generation_status
    
    generation_status['message'] = 'Generating variable intensity rain audio...'
    generation_status['progress'] = 10
    
    # Initialize audio buffer
    total_samples = int(duration_seconds * sample_rate)
    audio = np.zeros(total_samples, dtype=np.float32)
    
    # Convert timeline to intensity function
    def get_intensity_at_time(t):
        """Get intensity value at time t by interpolating timeline"""
        if not intensity_timeline:
            return 0.5  # default medium intensity
        
        # Sort timeline by time, filtering out invalid entries
        sorted_timeline = sorted(
            [p for p in intensity_timeline if p.get('time') is not None and p.get('intensity') is not None],
            key=lambda x: x['time']
        )
        
        if not sorted_timeline:
            return 0.5  # default if no valid points
        
        # Find surrounding points
        if t <= sorted_timeline[0]['time']:
            return sorted_timeline[0]['intensity']
        if t >= sorted_timeline[-1]['time']:
            return sorted_timeline[-1]['intensity']
        
        # Linear interpolation between points
        for i in range(len(sorted_timeline) - 1):
            t1, i1 = sorted_timeline[i]['time'], sorted_timeline[i]['intensity']
            t2, i2 = sorted_timeline[i + 1]['time'], sorted_timeline[i + 1]['intensity']
            
            if t1 is None or t2 is None or i1 is None or i2 is None:
                continue  # Skip invalid points
                
            if t1 <= t <= t2:
                # Linear interpolation
                alpha = (t - t1) / (t2 - t1) if t2 != t1 else 0
                return i1 + alpha * (i2 - i1)
        
        return 0.5
    
    def get_drop_density_at_time(t):
        """Get drop density at time t by interpolating timeline"""
        if not intensity_timeline:
            return 0.5
        
        # Sort timeline by time, filtering out invalid entries
        sorted_timeline = sorted(
            [p for p in intensity_timeline if p.get('time') is not None],
            key=lambda x: x['time']
        )
        
        if not sorted_timeline:
            return 0.5  # default if no valid points
        
        if t <= sorted_timeline[0]['time']:
            return sorted_timeline[0].get('drop_density', 0.5)
        if t >= sorted_timeline[-1]['time']:
            return sorted_timeline[-1].get('drop_density', 0.5)
        
        for i in range(len(sorted_timeline) - 1):
            t1 = sorted_timeline[i]['time']
            t2 = sorted_timeline[i + 1]['time']
            
            if t1 is None or t2 is None:
                continue  # Skip invalid points
                
            if t1 <= t <= t2:
                d1 = sorted_timeline[i].get('drop_density', 0.5)
                d2 = sorted_timeline[i + 1].get('drop_density', 0.5)
                alpha = (t - t1) / (t2 - t1) if t2 != t1 else 0
                return d1 + alpha * (d2 - d1)
        
        return 0.5
    
    # Generate drops throughout the duration
    # Divide into 1-second segments for better control
    segment_duration = 1.0
    num_segments = int(duration_seconds / segment_duration)
    
    generation_status['progress'] = 20
    
    for seg_idx in range(num_segments):
        # Check for cancellation
        if cancel_event.is_set():
            generation_status['message'] = 'Generation cancelled by user'
            return
        
        if seg_idx % 10 == 0:
            progress = 20 + int((seg_idx / num_segments) * 60)
            generation_status['progress'] = progress
            generation_status['message'] = f'Generating audio segment {seg_idx}/{num_segments}...'
        
        seg_start_time = seg_idx * segment_duration
        seg_center_time = seg_start_time + segment_duration / 2
        
        # Get intensity values at segment center
        intensity = get_intensity_at_time(seg_center_time)
        drop_density = get_drop_density_at_time(seg_center_time)
        
        # Calculate drops per second based on intensity and density
        base_drops = 20 + intensity * 150  # 20-170 drops/sec based on intensity
        drops_this_segment = int(base_drops * segment_duration * drop_density)
        
        # Determine drop type distribution based on intensity
        if intensity < 0.3:  # Light
            drop_types = ['light'] * 8 + ['medium'] * 2
        elif intensity > 0.7:  # Heavy
            drop_types = ['light'] * 2 + ['medium'] * 5 + ['heavy'] * 3
        else:  # Medium
            drop_types = ['light'] * 5 + ['medium'] * 4 + ['heavy'] * 1
        
        # Generate drops for this segment
        for _ in range(drops_this_segment):
            drop_type = np.random.choice(drop_types)
            drop_time = seg_start_time + np.random.uniform(0, segment_duration)
            start_sample = int(drop_time * sample_rate)
            
            # Generate drop
            drop = generate_raindrop_sound(sample_rate, drop_type)
            end_sample = min(start_sample + len(drop), total_samples)
            
            # Add to audio buffer
            if start_sample < total_samples:
                audio[start_sample:end_sample] += drop[:end_sample - start_sample]
    
    generation_status['message'] = 'Adding ambient background...'
    generation_status['progress'] = 85
    
    # Add subtle background noise for continuous ambiance
    print("Adding ambient background...")
    BACKGROUND_NOISE_AMPLITUDE = 0.01
    background_noise = np.random.randn(total_samples) * BACKGROUND_NOISE_AMPLITUDE
    b, a = signal.butter(4, 500 / (sample_rate / 2), btype='low')
    background_noise = signal.filtfilt(b, a, background_noise)
    audio += background_noise
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.9
    
    # Convert to 16-bit PCM
    audio_int16 = (audio * 32767).astype(np.int16)
    
    generation_status['message'] = 'Saving audio file...'
    generation_status['progress'] = 95
    
    # Save to WAV file
    wavfile.write(output_file, sample_rate, audio_int16)

def generate_raindrop_sound(sample_rate=44100, drop_type='light'):
    """Generate a single raindrop sound."""
    if drop_type == 'light':
        duration = np.random.uniform(0.02, 0.05)
        freq_range = (2000, 8000)
        amplitude = np.random.uniform(0.1, 0.3)
    elif drop_type == 'medium':
        duration = np.random.uniform(0.05, 0.1)
        freq_range = (1000, 6000)
        amplitude = np.random.uniform(0.2, 0.5)
    else:  # heavy
        duration = np.random.uniform(0.1, 0.2)
        freq_range = (500, 4000)
        amplitude = np.random.uniform(0.4, 0.7)
    
    num_samples = int(duration * sample_rate)
    noise = np.random.randn(num_samples)
    
    # Apply bandpass filter
    nyquist = sample_rate / 2
    low = freq_range[0] / nyquist
    high = freq_range[1] / nyquist
    b, a = signal.butter(4, [low, high], btype='band')
    filtered = signal.filtfilt(b, a, noise)
    
    # Apply envelope
    envelope = np.exp(-np.linspace(0, 10, num_samples))
    drop_sound = filtered * envelope * amplitude
    
    return drop_sound

def generate_video_with_timeline(duration_hours, intensity_timeline, output_file='rain_video.mp4'):
    """
    Generate complete video with variable intensity timeline.
    """
    global generation_status, cancel_event
    
    try:
        # Reset cancellation event
        cancel_event.clear()
        
        generation_status['in_progress'] = True
        generation_status['progress'] = 0
        generation_status['message'] = 'Starting video generation...'
        generation_status['error'] = None
        
        duration_seconds = int(duration_hours * 3600)
        
        # Generate audio with variable intensity
        audio_file = 'rain_audio_variable.wav'
        generate_rain_audio_variable(duration_seconds, intensity_timeline, output_file=audio_file)
        
        # Check for cancellation after audio generation
        if cancel_event.is_set():
            generation_status['in_progress'] = False
            generation_status['message'] = 'Generation cancelled'
            return
        
        generation_status['message'] = 'Creating video background...'
        generation_status['progress'] = 96
        
        # Create static background
        background_file = 'background.png'
        background = create_static_background(1920, 1080, 'night')
        background.save(background_file)
        
        generation_status['message'] = 'Combining audio and video...'
        generation_status['progress'] = 97
        
        # Combine audio and video
        audio = AudioFileClip(audio_file)
        video = ImageClip(background_file, duration=duration_seconds)
        video = video.set_audio(audio)
        video = video.set_fps(1)
        
        generation_status['message'] = 'Encoding final video...'
        generation_status['progress'] = 98
        
        video.write_videofile(
            output_file,
            fps=1,
            codec='libx264',
            audio_codec='aac',
            bitrate='2000k',
            preset='medium',
            threads=4,
            logger=None  # Suppress moviepy output
        )
        
        audio.close()
        video.close()
        
        generation_status['in_progress'] = False
        generation_status['progress'] = 100
        generation_status['message'] = 'Video generation complete!'
        generation_status['output_file'] = output_file
        
    except Exception as e:
        generation_status['in_progress'] = False
        generation_status['error'] = str(e)
        generation_status['message'] = f'Error: {str(e)}'


@app.route('/')
def index():
    """Serve the main UI page."""
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """API endpoint to start video generation."""
    global generation_status
    
    if generation_status['in_progress']:
        return jsonify({'error': 'Generation already in progress'}), 400
    
    data = request.json
    duration_hours = data.get('duration', 0.1)  # Default 0.1 hours (6 minutes) for testing
    intensity_timeline = data.get('timeline', [])
    output_file = data.get('output', 'rain_video.mp4')
    
    # Start generation in background thread
    thread = threading.Thread(
        target=generate_video_with_timeline,
        args=(duration_hours, intensity_timeline, output_file)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/api/status', methods=['GET'])
def api_status():
    """API endpoint to get generation status."""
    return jsonify(generation_status)

@app.route('/api/cancel', methods=['POST'])
def api_cancel():
    """API endpoint to cancel generation."""
    global generation_status, cancel_event
    
    # Signal the thread to cancel
    cancel_event.set()
    
    generation_status['in_progress'] = False
    generation_status['message'] = 'Cancelling generation...'
    
    return jsonify({'status': 'cancelled'})

@app.route('/download/<filename>')
def download_file(filename):
    """Download generated video file."""
    # Security: Only allow downloading files from current directory
    # Prevent directory traversal attacks
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(os.getcwd(), safe_filename)
    
    # Only allow downloading .mp4 files
    if not safe_filename.endswith('.mp4'):
        return jsonify({'error': 'Invalid file type'}), 400
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

# ============= Sample Library Management API =============

@app.route('/api/samples/list', methods=['GET'])
def api_list_samples():
    """List all samples in the library organized by category."""
    config.ensure_sample_directories()
    
    samples = {
        'beds': [],
        'textures': [],
        'details': [],
        'environmental': []
    }
    
    for category in samples.keys():
        category_path = config.SAMPLES_DIR / category
        if category_path.exists():
            for file_path in category_path.glob('*'):
                if file_path.suffix.lower() in config.SUPPORTED_AUDIO_FORMATS:
                    samples[category].append({
                        'name': file_path.name,
                        'path': str(file_path.relative_to(config.BASE_DIR)),
                        'size': file_path.stat().st_size
                    })
    
    return jsonify(samples)

@app.route('/api/samples/upload', methods=['POST'])
def api_upload_sample():
    """Upload a custom sample file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    category = request.form.get('category', 'details')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Normalize category to plural form (except environmental)
    if category not in CATEGORY_MAP:
        return jsonify({'error': 'Invalid category'}), 400
    
    category = CATEGORY_MAP[category]
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in config.SUPPORTED_AUDIO_FORMATS:
        return jsonify({'error': 'Unsupported file format'}), 400
    
    # Save file
    config.ensure_sample_directories()
    category_path = config.SAMPLES_DIR / category
    file_path = category_path / file.filename
    
    try:
        file.save(str(file_path))
        return jsonify({
            'status': 'success',
            'filename': file.filename,
            'category': category
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/samples/delete', methods=['POST'])
def api_delete_sample():
    """Delete a sample file."""
    data = request.json
    category = data.get('category')
    filename = data.get('filename')
    
    if not category or not filename:
        return jsonify({'error': 'Missing category or filename'}), 400
    
    # Normalize category to plural form (except environmental)
    if category not in CATEGORY_MAP:
        return jsonify({'error': 'Invalid category'}), 400
    
    category = CATEGORY_MAP[category]
    
    file_path = config.SAMPLES_DIR / category / filename
    
    # Ensure file is within samples directory
    try:
        file_path = file_path.resolve()
        if not str(file_path).startswith(str(config.SAMPLES_DIR.resolve())):
            return jsonify({'error': 'Invalid file path'}), 400
    except Exception:
        return jsonify({'error': 'Invalid file path'}), 400
    
    if file_path.exists():
        try:
            file_path.unlink()
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/samples/preview/<category>/<filename>')
def api_preview_sample(category, filename):
    """Stream a sample file for preview."""
    # Normalize category to plural form (except environmental)
    if category not in CATEGORY_MAP:
        return jsonify({'error': 'Invalid category'}), 400
    
    category = CATEGORY_MAP[category]
    
    file_path = config.SAMPLES_DIR / category / filename
    
    # Security check
    try:
        file_path = file_path.resolve()
        if not str(file_path).startswith(str(config.SAMPLES_DIR.resolve())):
            return jsonify({'error': 'Invalid file path'}), 400
    except Exception:
        return jsonify({'error': 'Invalid file path'}), 400
    
    if file_path.exists():
        return send_file(file_path)
    
    return jsonify({'error': 'File not found'}), 404

# ============= Freesound API Integration =============

@app.route('/api/freesound/search', methods=['POST'])
def api_freesound_search():
    """Search Freesound for audio samples."""
    data = request.json
    query = data.get('query', '')
    page = data.get('page', 1)
    filters = data.get('filters', {})
    
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    # Check if API key is configured
    if not config.FREESOUND_API_KEY:
        return jsonify({
            'error': 'Freesound API key not configured. Please set FREESOUND_API_KEY environment variable.',
            'results': [],
            'count': 0
        }), 200
    
    try:
        client = FreesoundClient()
        results = client.search(query, filter_params=filters, page=page)
        return jsonify(results)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'results': [],
            'count': 0
        }), 200

@app.route('/api/freesound/download', methods=['POST'])
def api_freesound_download():
    """Download a sound from Freesound."""
    data = request.json
    sound_id = data.get('sound_id')
    category = data.get('category', 'details')
    
    if not sound_id:
        return jsonify({'error': 'No sound ID provided'}), 400
    
    # Normalize category to plural form (except environmental)
    if category not in CATEGORY_MAP:
        return jsonify({'error': 'Invalid category'}), 400
    
    category = CATEGORY_MAP[category]
    
    if not config.FREESOUND_API_KEY:
        return jsonify({'error': 'Freesound API key not configured'}), 400
    
    try:
        client = FreesoundClient()
        
        # Get sound info to get the name
        sound_info = client.get_sound_info(sound_id)
        if 'error' in sound_info:
            return jsonify({'error': sound_info['error']}), 500
        
        # Create filename from sound name
        filename = f"{sound_info['name']}_{sound_id}.mp3"
        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.')).rstrip()
        
        config.ensure_sample_directories()
        output_path = config.SAMPLES_DIR / category / filename
        
        # Download
        success = client.download_sound(sound_id, output_path, use_preview=True)
        
        if success:
            # Apply normalization using configured target level
            target_db = config.DEFAULT_DOWNLOAD_NORMALIZATION_DB
            normalize_result = normalize_audio(output_path, target_db=target_db)
            
            if normalize_result:
                original_db, target_db = normalize_result
                print(f"Normalized audio from {original_db:.2f}dB to {target_db:.2f}dB")
            else:
                print("Warning: Audio normalization failed, file saved without normalization")
            
            return jsonify({
                'status': 'success',
                'filename': filename,
                'category': category,
                'normalized': normalize_result is not None
            })
        else:
            return jsonify({'error': 'Download failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def api_get_config():
    """Get current configuration."""
    return jsonify(config.get_config())

@app.route('/api/config', methods=['POST'])
def api_update_config():
    """Update configuration (layer volumes, frequencies, etc.)."""
    data = request.json
    
    # This would update runtime configuration
    # For now, just return success
    return jsonify({'status': 'success'})

def main():
    """Run the web UI."""
    # Ensure sample directories exist
    config.ensure_sample_directories()
    
    print("=" * 60)
    print("Rain Video Creator - Web UI")
    print("=" * 60)
    print("\nStarting web server...")
    print("Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server.")
    print("\nNote: Server is only accessible from localhost for security.")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=5000, debug=False)


if __name__ == '__main__':
    main()