#!/usr/bin/env python3
"""
CLI entry point for Rain audio/video generation system.

Usage:
    python -m rain generate [options]

Examples:
    # 8-hour video with looped background
    python -m rain generate --duration-hours 8 --out rain_8hr.mp4 \
        --mode video_loop --background-video bg.mp4
    
    # 10-minute preview with procedural visuals
    python -m rain generate --preview-minutes 10 --out preview.mp4 --mode procedural
    
    # Audio only
    python -m rain generate --duration-hours 1 --out rain.wav --audio-only
"""

import click
from pathlib import Path
import sys


@click.group()
def cli():
    """Rain audio and video generation system."""
    pass


@cli.command()
@click.option('--duration-hours', type=float, default=8.0,
              help='Duration in hours (default: 8.0)')
@click.option('--seed', type=int, default=None,
              help='Random seed for reproducibility')
@click.option('--out', type=click.Path(), required=True,
              help='Output file path (e.g., rain.mp4 or rain.wav)')
@click.option('--assets-dir', type=click.Path(exists=True), default='assets',
              help='Path to assets directory (default: assets)')
@click.option('--sample-rate', type=int, default=48000,
              help='Audio sample rate in Hz (default: 48000)')
@click.option('--lufs', type=float, default=-22.0,
              help='Target loudness in LUFS (default: -22.0 for sleep)')
@click.option('--mode', type=click.Choice(['video_loop', 'procedural']), default='procedural',
              help='Video generation mode (default: procedural)')
@click.option('--background-video', type=click.Path(exists=True), default=None,
              help='Background video file for video_loop mode')
@click.option('--no-thunder', is_flag=True, default=False,
              help='Disable thunder sounds')
@click.option('--preview-minutes', type=float, default=None,
              help='Quick preview duration in minutes (overrides duration-hours)')
@click.option('--audio-only', is_flag=True, default=False,
              help='Generate audio only (no video)')
@click.option('--video-fps', type=int, default=30,
              help='Video frame rate (default: 30)')
@click.option('--video-resolution', type=str, default='1920x1080',
              help='Video resolution (default: 1920x1080)')
def generate(duration_hours, seed, out, assets_dir, sample_rate, lufs,
             mode, background_video, no_thunder, preview_minutes, audio_only,
             video_fps, video_resolution):
    """Generate sleep-grade rain audio from REAL SAMPLES ONLY.
    
    Requires audio files in assets/audio/bed/ directory.
    """
    
    # Import here to avoid slow startup
    from .sample_audio_engine import SampleBasedAudioEngine
    from .loudness import process_audio_file
    from .video import create_looped_video, create_procedural_rain_video
    from .muxer import mux_audio_video_simple, check_ffmpeg
    import tempfile
    
    # Determine duration
    if preview_minutes is not None:
        duration_seconds = preview_minutes * 60
        print(f"Preview mode: {preview_minutes} minutes")
    else:
        duration_seconds = duration_hours * 3600
        print(f"Generating {duration_hours} hour(s) of rain")
    
    # Parse video resolution
    try:
        width, height = map(int, video_resolution.split('x'))
        resolution = (width, height)
    except:
        click.echo(f"Error: Invalid resolution format: {video_resolution}", err=True)
        click.echo("Use format like: 1920x1080", err=True)
        sys.exit(1)
    
    out_path = Path(out)
    assets_path = Path(assets_dir)
    
    # Check if ffmpeg is available for video modes
    if not audio_only:
        if not check_ffmpeg():
            click.echo("Error: FFmpeg is required for video generation", err=True)
            click.echo("", err=True)
            click.echo("Installation instructions:", err=True)
            click.echo("  Windows: Download from https://ffmpeg.org/download.html", err=True)
            click.echo("  macOS: brew install ffmpeg", err=True)
            click.echo("  Linux: sudo apt install ffmpeg", err=True)
            sys.exit(1)
    
    # Step 1: Generate audio
    click.echo("\n=== Step 1: Generating Audio (Sample-Based) ===")
    
    # Create sample-based audio engine
    try:
        include_thunder = not no_thunder
        engine = SampleBasedAudioEngine(
            assets_dir=assets_path,
            target_sr=sample_rate,
            seed=seed,
            chunk_seconds=120.0,
            crossfade_seconds=5.0,
            include_thunder=include_thunder
        )
        
        # Report what was found
        click.echo(f"Found {len(engine.bed_files)} bed recordings")
        click.echo(f"Found {len(engine.detail_files)} detail samples")
        click.echo(f"Found {len(engine.thunder_files)} thunder samples")
        
    except RuntimeError as e:
        click.echo(f"\nError: {e}", err=True)
        click.echo("\nPlease add at least one long rain recording to assets/audio/bed/", err=True)
        click.echo("Supported formats: .wav, .flac, .mp3", err=True)
        sys.exit(1)
    
    # Generate audio directly to output (or temp file for video)
    if audio_only:
        # Generate directly to output
        engine.generate_to_file(out_path, duration_seconds, target_lufs=lufs)
        click.echo(f"\n✓ Audio saved to: {out_path}")
        else:
        # Generate to temp file for video muxing
        with tempfile.NamedTemporaryFile(suffix='_audio.wav', delete=False) as tmp:
            audio_path = Path(tmp.name)
        
        try:
            engine.generate_to_file(audio_path, duration_seconds, target_lufs=lufs)
            
            # Step 2: Generate video
            click.echo("\n=== Step 2: Generating Video ===")
            
            with tempfile.NamedTemporaryFile(suffix='_silent.mp4', delete=False) as tmp:
                silent_video_path = Path(tmp.name)
            
            try:
                if mode == 'video_loop':
                    if background_video is None:
                        click.echo("Error: --background-video required for video_loop mode", err=True)
                        sys.exit(1)
                    create_looped_video(
                        Path(background_video),
                        duration_seconds,
                        silent_video_path,
                        resolution=resolution,
                        fps=video_fps
                    )
                else:  # procedural
                    create_procedural_rain_video(
                        duration_seconds,
                        silent_video_path,
                        resolution=resolution,
                        fps=video_fps,
                        chunk_seconds=60.0,
                        seed=seed
                    )
                
                # Step 3: Mux audio and video
                click.echo("\n=== Step 3: Combining Audio and Video ===")
                mux_audio_video_simple(silent_video_path, audio_path, out_path)
                
                click.echo(f"\n✓ Video saved to: {out_path}")
                
            finally:
                # Clean up silent video
                if silent_video_path.exists():
                    silent_video_path.unlink()
        
        finally:
            # Clean up audio
            if audio_path.exists():
                audio_path.unlink()
    
    click.echo("\n✓ Generation complete!")


@cli.command()
def version():
    """Show version information."""
    from . import __version__
    click.echo(f"Rain Audio/Video Generator v{__version__}")


if __name__ == '__main__':
    cli()
