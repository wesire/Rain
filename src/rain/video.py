#!/usr/bin/env python3
"""
Video generation utilities for rain videos.

Provides two modes:
1. Video loop mode: Loop an existing background video
2. Procedural mode: Generate rain animation using OpenCV
"""

import numpy as np
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from tqdm import tqdm


def check_opencv() -> bool:
    """Check if OpenCV is available."""
    try:
        import cv2
        return True
    except ImportError:
        return False


def create_looped_video(background_video: Path, duration_seconds: float,
                        output_path: Path, resolution: Tuple[int, int] = (1920, 1080),
                        fps: int = 30) -> None:
    """
    Loop a background MP4 to target duration (drops its audio).
    
    Uses ffmpeg with -stream_loop to repeat the video.
    
    Args:
        background_video: Path to input video file
        duration_seconds: Target duration in seconds
        output_path: Output video file path
        resolution: Target resolution (width, height)
        fps: Target frame rate
    """
    background_video = Path(background_video)
    output_path = Path(output_path)
    
    if not background_video.exists():
        raise FileNotFoundError(f"Background video not found: {background_video}")
    
    print(f"Creating looped video from {background_video}...")
    
    # Build ffmpeg command
    cmd = [
        'ffmpeg', '-y',
        '-stream_loop', '-1',  # Loop indefinitely
        '-i', str(background_video),
        '-t', str(duration_seconds),  # Duration
        '-vf', f'scale={resolution[0]}:{resolution[1]}',  # Scale to resolution
        '-r', str(fps),  # Frame rate
        '-an',  # No audio
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        str(output_path)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Video loop created: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating video loop: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise


def create_procedural_rain_video(duration_seconds: float, output_path: Path,
                                  resolution: Tuple[int, int] = (1920, 1080),
                                  fps: int = 30, chunk_seconds: float = 60.0,
                                  seed: Optional[int] = None) -> None:
    """
    Generate rain animation using OpenCV.
    
    Creates:
    - Dark gradient background (night sky colors)
    - Drifting streak particles (raindrops)
    - Renders in chunks to manage memory
    
    Uses cv2.VideoWriter to stream frames directly to file.
    
    Args:
        duration_seconds: Duration in seconds
        output_path: Output video file path
        resolution: Video resolution (width, height)
        fps: Frames per second
        chunk_seconds: Render chunks of this duration
        seed: Random seed for reproducibility
    """
    if not check_opencv():
        raise ImportError(
            "OpenCV not available. Install with: pip install opencv-python"
        )
    
    import cv2
    
    output_path = Path(output_path)
    width, height = resolution
    total_frames = int(duration_seconds * fps)
    
    print(f"Generating procedural rain video ({duration_seconds}s, {fps} fps)...")
    
    # Set random seed
    if seed is not None:
        np.random.seed(seed)
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    if not out.isOpened():
        raise RuntimeError(f"Failed to open video writer for {output_path}")
    
    # Initialize raindrop particles
    num_drops = 300
    raindrops = _init_raindrops(num_drops, width, height)
    
    # Create background
    background = _create_night_background(width, height)
    
    # Render frames
    for frame_num in tqdm(range(total_frames), desc="Rendering video"):
        # Create frame
        frame = background.copy()
        
        # Update and draw raindrops
        _update_raindrops(raindrops, width, height)
        _draw_raindrops(frame, raindrops)
        
        # Write frame
        out.write(frame)
    
    out.release()
    print(f"Video generated: {output_path}")


def _create_night_background(width: int, height: int) -> np.ndarray:
    """
    Create a dark gradient background suitable for sleep videos.
    
    Args:
        width: Image width
        height: Image height
        
    Returns:
        BGR image array (height, width, 3)
    """
    # Create vertical gradient from dark blue-gray to darker
    background = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Dark blue-gray tones
    top_color = np.array([40, 35, 30], dtype=np.uint8)  # BGR
    bottom_color = np.array([20, 18, 15], dtype=np.uint8)  # BGR
    
    for y in range(height):
        alpha = y / height
        color = (1 - alpha) * top_color + alpha * bottom_color
        background[y, :] = color.astype(np.uint8)
    
    return background


def _init_raindrops(num_drops: int, width: int, height: int) -> np.ndarray:
    """
    Initialize raindrop particles.
    
    Returns array with columns: [x, y, speed, length, opacity]
    
    Args:
        num_drops: Number of raindrops
        width: Frame width
        height: Frame height
        
    Returns:
        Array of raindrop properties (num_drops, 5)
    """
    raindrops = np.zeros((num_drops, 5), dtype=np.float32)
    
    # Random x positions
    raindrops[:, 0] = np.random.uniform(0, width, num_drops)
    
    # Random y positions
    raindrops[:, 1] = np.random.uniform(-height, height, num_drops)
    
    # Random speeds (pixels per frame)
    raindrops[:, 2] = np.random.uniform(15, 30, num_drops)
    
    # Random lengths
    raindrops[:, 3] = np.random.uniform(20, 50, num_drops)
    
    # Random opacity
    raindrops[:, 4] = np.random.uniform(0.3, 0.8, num_drops)
    
    return raindrops


def _update_raindrops(raindrops: np.ndarray, width: int, height: int) -> None:
    """
    Update raindrop positions.
    
    Args:
        raindrops: Raindrop array (num_drops, 5) - modified in place
        width: Frame width
        height: Frame height
    """
    # Move drops down
    raindrops[:, 1] += raindrops[:, 2]
    
    # Slight horizontal drift
    raindrops[:, 0] += np.random.uniform(-0.5, 0.5, len(raindrops))
    
    # Reset drops that went off screen
    off_screen = raindrops[:, 1] > height
    raindrops[off_screen, 1] = np.random.uniform(-50, 0, np.sum(off_screen))
    raindrops[off_screen, 0] = np.random.uniform(0, width, np.sum(off_screen))


def _draw_raindrops(frame: np.ndarray, raindrops: np.ndarray) -> None:
    """
    Draw raindrops on frame.
    
    Args:
        frame: BGR image array (height, width, 3) - modified in place
        raindrops: Raindrop array (num_drops, 5)
    """
    import cv2
    
    for drop in raindrops:
        x, y, speed, length, opacity = drop
        
        # Calculate end point
        x1, y1 = int(x), int(y)
        x2, y2 = int(x), int(y + length)
        
        # Skip if completely off screen
        if y1 < 0 or y1 >= frame.shape[0]:
            continue
        if x1 < 0 or x1 >= frame.shape[1]:
            continue
        
        # Draw line (light blue-white)
        color = (255, 255, 255)  # White
        alpha = int(opacity * 255)
        
        # Blend line onto frame
        try:
            cv2.line(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)
        except:
            pass  # Skip if coordinates are invalid


def convert_to_h264(input_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Convert video to H.264 codec for better compatibility.
    
    Args:
        input_path: Input video file
        output_path: Output video file (default: input_h264.mp4)
        
    Returns:
        Path to output file
    """
    input_path = Path(input_path)
    
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_h264.mp4"
    else:
        output_path = Path(output_path)
    
    print(f"Converting to H.264: {input_path} -> {output_path}")
    
    cmd = [
        'ffmpeg', '-y',
        '-i', str(input_path),
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-an',  # No audio
        str(output_path)
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Conversion complete: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"Error converting video: {e}")
        raise
