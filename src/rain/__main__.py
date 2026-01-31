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
@click.option('--lufs', type=float, default=-14.0,
              help='Target loudness in LUFS (default: -14.0)')
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
    """Generate sleep-grade rain video or audio."""
    
    # Import here to avoid slow startup
    from .audio_engine import AudioAssetLoader, RainAudioEngine
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
    click.echo("\n=== Step 1: Generating Audio ===")
    
    # Load audio assets
    loader = AudioAssetLoader(assets_path, target_sr=sample_rate)
    loader.load_all()
    
    # Report what was loaded
    click.echo(f"Loaded {len(loader.bed_samples)} bed samples")
    click.echo(f"Loaded {len(loader.detail_samples)} detail samples")
    click.echo(f"Loaded {len(loader.thunder_samples)} thunder samples")
    
    # Create audio engine
    include_thunder = not no_thunder
    engine = RainAudioEngine(
        loader=loader,
        chunk_seconds=20.0,
        overlap_seconds=3.0,
        include_thunder=include_thunder,
        seed=seed
    )
    
    # Generate raw audio to temp file
    with tempfile.NamedTemporaryFile(suffix='_raw.wav', delete=False) as tmp:
        raw_audio_path = Path(tmp.name)
    
    try:
        engine.generate_to_file(raw_audio_path, duration_seconds)
        
        # Step 2: Process audio (loudness, limiting, fades, filters)
        click.echo("\n=== Step 2: Processing Audio ===")
        
        if audio_only:
            # Process directly to output
            process_audio_file(
                raw_audio_path,
                out_path,
                target_lufs=lufs,
                apply_limiting=True,
                fade_in_sec=3.0,
                fade_out_sec=5.0,
                hpf_freq=25.0,
                lpf_freq=15000.0
            )
            click.echo(f"\n✓ Audio saved to: {out_path}")
            
        else:
            # Process to temp file for video muxing
            with tempfile.NamedTemporaryFile(suffix='_processed.wav', delete=False) as tmp:
                processed_audio_path = Path(tmp.name)
            
            try:
                process_audio_file(
                    raw_audio_path,
                    processed_audio_path,
                    target_lufs=lufs,
                    apply_limiting=True,
                    fade_in_sec=3.0,
                    fade_out_sec=5.0,
                    hpf_freq=25.0,
                    lpf_freq=15000.0
                )
                
                # Step 3: Generate video
                click.echo("\n=== Step 3: Generating Video ===")
                
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
                    
                    # Step 4: Mux audio and video
                    click.echo("\n=== Step 4: Combining Audio and Video ===")
                    mux_audio_video_simple(silent_video_path, processed_audio_path, out_path)
                    
                    click.echo(f"\n✓ Video saved to: {out_path}")
                    
                finally:
                    # Clean up silent video
                    if silent_video_path.exists():
                        silent_video_path.unlink()
                
            finally:
                # Clean up processed audio
                if processed_audio_path.exists():
                    processed_audio_path.unlink()
    
    finally:
        # Clean up raw audio
        if raw_audio_path.exists():
            raw_audio_path.unlink()
    
    click.echo("\n✓ Generation complete!")


@cli.command()
def version():
    """Show version information."""
    from . import __version__
    click.echo(f"Rain Audio/Video Generator v{__version__}")


if __name__ == '__main__':
    cli()
