#!/usr/bin/env python3
"""
Main script to create a complete rain video for YouTube.
Combines generated audio and video into a single MP4 file.
"""

import os
import sys
import argparse
import subprocess
from generate_rain_audio import generate_rain_audio
from generate_rain_video import generate_rain_video_frames, create_static_background
from PIL import Image
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from tqdm import tqdm


def create_rain_video(duration_hours=12, intensity='medium', style='static', 
                     output_file='rain_sleep_video.mp4', fps=30):
    """
    Create a complete rain video for YouTube with audio and visuals.
    
    Args:
        duration_hours: Video duration in hours
        intensity: Rain sound intensity ('light', 'medium', 'heavy')
        style: Video style ('static', 'animated')
        output_file: Output video file path
        fps: Frames per second for video
    """
    duration_seconds = int(duration_hours * 3600)
    
    print("=" * 60)
    print(f"Creating {duration_hours}-hour rain video for YouTube")
    print(f"Intensity: {intensity}, Style: {style}")
    print("=" * 60)
    
    # Step 1: Generate audio
    print("\n[1/3] Generating rain audio...")
    audio_file = 'rain_audio.wav'
    
    try:
        generate_rain_audio(
            duration_seconds=duration_seconds,
            intensity=intensity,
            output_file=audio_file
        )
    except Exception as e:
        print(f"Error generating audio: {e}")
        sys.exit(1)
    
    # Step 2: Create video background
    print("\n[2/3] Creating video background...")
    
    if style == 'static':
        # Create a single static background image
        background_file = 'background.png'
        print("Creating static background image...")
        background = create_static_background(1920, 1080, 'night')
        background.save(background_file)
        print(f"Background saved to {background_file}")
    else:
        # For animated, we'd need frames (computationally expensive for 12 hours)
        print("Note: Animated style for 12 hours requires significant processing.")
        print("Falling back to static background for efficiency.")
        background_file = 'background.png'
        background = create_static_background(1920, 1080, 'night')
        background.save(background_file)
    
    # Step 3: Combine audio and video using moviepy
    print("\n[3/3] Combining audio and video...")
    
    try:
        print("Loading audio file...")
        audio = AudioFileClip(audio_file)
        
        print("Creating video clip from background...")
        # Create video clip from static image
        video = ImageClip(background_file, duration=duration_seconds)
        
        print("Setting audio track...")
        video = video.set_audio(audio)
        video = video.set_fps(fps)
        
        print(f"Writing final video to {output_file}...")
        print("This may take a while for a 12-hour video...")
        
        # Write video file with good compression for YouTube
        video.write_videofile(
            output_file,
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            bitrate='2000k',
            preset='medium',
            threads=4
        )
        
        # Clean up
        audio.close()
        video.close()
        
        print("\n" + "=" * 60)
        print(f"SUCCESS! Video created: {output_file}")
        print(f"Duration: {duration_hours} hours")
        print(f"File size: {os.path.getsize(output_file) / (1024**3):.2f} GB")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error creating video: {e}")
        print("\nAlternative: Use FFmpeg directly")
        print(f"ffmpeg -loop 1 -i {background_file} -i {audio_file} -c:v libx264 "
              f"-tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p "
              f"-shortest {output_file}")
        sys.exit(1)


def create_quick_test_video(duration_seconds=60, output_file='test_rain.mp4'):
    """
    Create a quick test video to validate the setup.
    
    Args:
        duration_seconds: Test video duration in seconds
        output_file: Output file path
    """
    print("Creating quick test video...")
    
    # Generate test audio
    audio_file = 'test_audio.wav'
    generate_rain_audio(
        duration_seconds=duration_seconds,
        intensity='medium',
        output_file=audio_file
    )
    
    # Create test background
    background_file = 'test_background.png'
    background = create_static_background(1920, 1080, 'night')
    background.save(background_file)
    
    # Combine with moviepy
    audio = AudioFileClip(audio_file)
    video = ImageClip(background_file, duration=duration_seconds)
    video = video.set_audio(audio)
    video = video.set_fps(30)
    
    video.write_videofile(
        output_file,
        fps=30,
        codec='libx264',
        audio_codec='aac',
        bitrate='2000k'
    )
    
    audio.close()
    video.close()
    
    print(f"\nTest video created: {output_file}")
    print(f"Duration: {duration_seconds} seconds")


def main():
    parser = argparse.ArgumentParser(
        description='Create rain sound videos for YouTube',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a quick 1-minute test video
  python create_rain_video.py --test
  
  # Create a 12-hour video (default)
  python create_rain_video.py
  
  # Create a 1-hour video with heavy rain
  python create_rain_video.py --duration 1 --intensity heavy
  
  # Create a video with custom output name
  python create_rain_video.py --output my_rain_video.mp4
        """
    )
    
    parser.add_argument('--duration', type=float, default=12.0,
                        help='Video duration in hours (default: 12)')
    parser.add_argument('--intensity', choices=['light', 'medium', 'heavy'], default='medium',
                        help='Rain sound intensity (default: medium)')
    parser.add_argument('--style', choices=['static', 'animated'], default='static',
                        help='Video style (default: static)')
    parser.add_argument('--output', type=str, default='rain_sleep_video.mp4',
                        help='Output video file (default: rain_sleep_video.mp4)')
    parser.add_argument('--fps', type=int, default=1,
                        help='Frames per second (default: 1 for static videos)')
    parser.add_argument('--test', action='store_true',
                        help='Create a quick 1-minute test video')
    
    args = parser.parse_args()
    
    if args.test:
        create_quick_test_video(duration_seconds=60, output_file='test_rain.mp4')
    else:
        create_rain_video(
            duration_hours=args.duration,
            intensity=args.intensity,
            style=args.style,
            output_file=args.output,
            fps=args.fps
        )


if __name__ == '__main__':
    main()
