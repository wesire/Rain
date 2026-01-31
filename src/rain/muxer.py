#!/usr/bin/env python3
"""
FFmpeg wrapper for muxing audio and video.

Provides utilities for combining silent video with audio tracks and checking
FFmpeg availability.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional


def check_ffmpeg() -> bool:
    """
    Check if ffmpeg is available.
    
    Returns:
        True if ffmpeg is in PATH, False otherwise
    """
    return shutil.which('ffmpeg') is not None


def get_ffmpeg_help_message() -> str:
    """
    Get helpful error message if ffmpeg is not available.
    
    Returns:
        Installation instructions for ffmpeg
    """
    return """
FFmpeg is required but not found in your system PATH.

Installation instructions:

Windows:
  1. Download from https://ffmpeg.org/download.html
  2. Extract the archive
  3. Add the bin folder to your system PATH

macOS:
  brew install ffmpeg

Linux (Ubuntu/Debian):
  sudo apt-get update
  sudo apt-get install ffmpeg

Linux (Fedora):
  sudo dnf install ffmpeg

After installation, restart your terminal and try again.
"""


def mux_audio_video(video_path: Path, audio_path: Path, output_path: Path,
                    video_codec: str = 'copy',
                    audio_codec: str = 'aac',
                    audio_bitrate: str = '192k',
                    video_bitrate: Optional[str] = None) -> None:
    """
    Combine silent video + audio into final MP4 using ffmpeg.
    
    Command structure:
    ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac -b:a 192k \
           -map 0:v:0 -map 1:a:0 -shortest output.mp4
    
    Args:
        video_path: Input video file path
        audio_path: Input audio file path
        output_path: Output video file path
        video_codec: Video codec (default: 'copy' to avoid re-encoding)
        audio_codec: Audio codec (default: 'aac')
        audio_bitrate: Audio bitrate (default: '192k')
        video_bitrate: Video bitrate (optional, only used if re-encoding video)
        
    Raises:
        FileNotFoundError: If ffmpeg is not available
        RuntimeError: If muxing fails
    """
    if not check_ffmpeg():
        raise FileNotFoundError(get_ffmpeg_help_message())
    
    video_path = Path(video_path)
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    print(f"Muxing video and audio...")
    print(f"  Video: {video_path}")
    print(f"  Audio: {audio_path}")
    print(f"  Output: {output_path}")
    
    # Build ffmpeg command
    cmd = [
        'ffmpeg', '-y',  # Overwrite output
        '-i', str(video_path),
        '-i', str(audio_path),
        '-c:v', video_codec,
        '-c:a', audio_codec,
        '-b:a', audio_bitrate,
        '-map', '0:v:0',  # Map video from first input
        '-map', '1:a:0',  # Map audio from second input
        '-shortest',      # End when shortest stream ends
    ]
    
    # Add video bitrate if specified and re-encoding
    if video_bitrate and video_codec != 'copy':
        cmd.extend(['-b:v', video_bitrate])
    
    # Add output path
    cmd.append(str(output_path))
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Muxing complete: {output_path}")
        
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg muxing failed:\n{e.stderr}"
        print(error_msg)
        raise RuntimeError(error_msg)


def mux_audio_video_simple(video_path: Path, audio_path: Path, 
                           output_path: Path) -> None:
    """
    Simple muxing with default settings.
    
    Convenience wrapper around mux_audio_video with sensible defaults.
    
    Args:
        video_path: Input video file
        audio_path: Input audio file
        output_path: Output video file
    """
    mux_audio_video(
        video_path=video_path,
        audio_path=audio_path,
        output_path=output_path,
        video_codec='copy',
        audio_codec='aac',
        audio_bitrate='192k'
    )


def get_video_duration(video_path: Path) -> float:
    """
    Get duration of a video file in seconds using ffprobe.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Duration in seconds
        
    Raises:
        FileNotFoundError: If ffprobe is not available
        RuntimeError: If getting duration fails
    """
    if not shutil.which('ffprobe'):
        raise FileNotFoundError("ffprobe not found (comes with ffmpeg)")
    
    video_path = Path(video_path)
    
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(video_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        duration = float(result.stdout.strip())
        return duration
        
    except (subprocess.CalledProcessError, ValueError) as e:
        raise RuntimeError(f"Failed to get video duration: {e}")


def get_audio_duration(audio_path: Path) -> float:
    """
    Get duration of an audio file in seconds using soundfile.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds
    """
    import soundfile as sf
    
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    info = sf.info(audio_path)
    return info.duration
