#!/usr/bin/env python3
"""
Generate video visuals for rain videos.
Creates animated rain or static calming imagery for sleep videos.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import argparse
from tqdm import tqdm
import os


def create_raindrop_frame(width, height, num_drops, background_color=(20, 25, 35)):
    """
    Create a single frame with animated raindrops.
    
    Args:
        width: Frame width in pixels
        height: Frame height in pixels
        num_drops: Number of raindrops to render
        background_color: RGB tuple for background
    
    Returns:
        PIL Image object
    """
    # Create dark background
    img = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Draw raindrops
    for _ in range(num_drops):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        length = np.random.randint(10, 30)
        thickness = np.random.randint(1, 3)
        opacity = np.random.randint(100, 200)
        
        # Draw raindrop as a line
        draw.line(
            [(x, y), (x + thickness, y + length)],
            fill=(180, 200, 220, opacity),
            width=thickness
        )
    
    # Apply slight blur for softer appearance
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    return img


def create_static_background(width, height, style='night'):
    """
    Create a static calming background image.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        style: Background style ('night', 'window', 'gradient')
    
    Returns:
        PIL Image object
    """
    if style == 'night':
        # Dark nighttime gradient
        img = Image.new('RGB', (width, height))
        pixels = img.load()
        
        for y in range(height):
            # Gradient from dark blue to darker
            r = int(15 + (10 * (height - y) / height))
            g = int(20 + (15 * (height - y) / height))
            b = int(35 + (25 * (height - y) / height))
            
            for x in range(width):
                pixels[x, y] = (r, g, b)
        
        # Add some subtle noise for texture
        noise_array = np.array(img)
        noise = np.random.randint(-5, 5, noise_array.shape, dtype=np.int16)
        noise_array = np.clip(noise_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(noise_array)
        
    elif style == 'window':
        # Window pane with rain view
        img = Image.new('RGB', (width, height), (25, 30, 40))
        draw = ImageDraw.Draw(img)
        
        # Draw window frame
        frame_width = width // 20
        draw.rectangle(
            [(width//2 - 2, 0), (width//2 + 2, height)],
            fill=(40, 40, 40)
        )
        draw.rectangle(
            [(0, height//2 - 2), (width, height//2 + 2)],
            fill=(40, 40, 40)
        )
        
    else:  # gradient
        # Smooth dark gradient
        img = Image.new('RGB', (width, height))
        pixels = img.load()
        
        for y in range(height):
            intensity = int(20 + (20 * y / height))
            for x in range(width):
                pixels[x, y] = (intensity - 5, intensity, intensity + 5)
    
    return img


def generate_rain_video_frames(output_dir, duration_seconds, fps=30, width=1920, height=1080,
                               style='animated', intensity='medium'):
    """
    Generate frames for rain video.
    
    Args:
        output_dir: Directory to save frames
        duration_seconds: Video duration in seconds
        fps: Frames per second
        width: Frame width in pixels
        height: Frame height in pixels
        style: Video style ('animated', 'static')
        intensity: Rain intensity for animated style
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    total_frames = duration_seconds * fps
    print(f"Generating {total_frames} frames ({duration_seconds}s @ {fps}fps)...")
    
    # Create base background
    background = create_static_background(width, height, 'night')
    
    if style == 'static':
        # Save single frame for static video
        print("Creating static background...")
        background.save(os.path.join(output_dir, 'frame_0000.png'))
        print(f"Saved static frame to {output_dir}")
        
    else:  # animated
        # Determine drop range based on intensity
        if intensity == 'light':
            drop_range = (30, 60)
        elif intensity == 'heavy':
            drop_range = (150, 250)
        else:  # medium
            drop_range = (80, 120)
        
        print(f"Generating animated frames with {drop_range[0]}-{drop_range[1]} drops per frame...")
        
        # Generate frames (limited to 100 for efficiency - can be looped in video creation)
        # For 12-hour videos, generating all frames would require ~1.3 million frames
        # Instead, we generate a smaller set that can be repeated or used as a pattern
        num_frames_to_generate = min(total_frames, 100)
        
        for frame_num in tqdm(range(num_frames_to_generate), desc="Generating frames"):
            # Vary number of drops per frame for natural animation
            drops_per_frame = np.random.randint(drop_range[0], drop_range[1])
            
            # Create frame with raindrops
            frame = background.copy()
            rain_layer = create_raindrop_frame(width, height, drops_per_frame, (0, 0, 0))
            
            # Composite rain over background
            frame = Image.blend(frame, rain_layer, 0.3)
            
            # Save frame
            frame_path = os.path.join(output_dir, f'frame_{frame_num:04d}.png')
            frame.save(frame_path)
        
        print(f"Generated {num_frames_to_generate} frames saved to {output_dir}")
        if num_frames_to_generate < total_frames:
            print(f"Note: Generated {num_frames_to_generate} frames for efficiency.")
            print("For static-style videos, use --style static instead.")
            print("These frames can be looped or repeated in video creation.")


def main():
    parser = argparse.ArgumentParser(description='Generate video frames for rain videos')
    parser.add_argument('--duration', type=int, default=60,
                        help='Duration in seconds (default: 60)')
    parser.add_argument('--fps', type=int, default=30,
                        help='Frames per second (default: 30)')
    parser.add_argument('--output-dir', type=str, default='frames',
                        help='Output directory for frames (default: frames)')
    parser.add_argument('--width', type=int, default=1920,
                        help='Frame width in pixels (default: 1920)')
    parser.add_argument('--height', type=int, default=1080,
                        help='Frame height in pixels (default: 1080)')
    parser.add_argument('--style', choices=['animated', 'static'], default='static',
                        help='Video style (default: static)')
    parser.add_argument('--intensity', choices=['light', 'medium', 'heavy'], default='medium',
                        help='Rain intensity for animated style (default: medium)')
    
    args = parser.parse_args()
    
    generate_rain_video_frames(
        output_dir=args.output_dir,
        duration_seconds=args.duration,
        fps=args.fps,
        width=args.width,
        height=args.height,
        style=args.style,
        intensity=args.intensity
    )


if __name__ == '__main__':
    main()
