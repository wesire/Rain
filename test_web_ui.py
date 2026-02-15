#!/usr/bin/env python3
"""
Quick test script to validate the web UI functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from web_ui import generate_rain_audio_variable
import numpy as np

def test_variable_intensity_audio():
    """Test that variable intensity audio generation works."""
    print("Testing variable intensity audio generation...")
    
    # Create a simple timeline with 2 points
    timeline = [
        {'time': 0, 'intensity': 0.3, 'drop_density': 0.5},
        {'time': 5, 'intensity': 0.7, 'drop_density': 0.8}
    ]
    
    # Generate 5 seconds of audio
    output_file = '/tmp/test_rain.wav'
    try:
        generate_rain_audio_variable(
            duration_seconds=5,
            intensity_timeline=timeline,
            output_file=output_file
        )
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✓ Audio generated successfully: {file_size} bytes")
            os.remove(output_file)
            return True
        else:
            print("✗ Audio file not created")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Rain Video Creator - Web UI Tests")
    print("=" * 60)
    
    # Note: We need to reset the global state for testing
    import web_ui
    web_ui.generation_status = {
        'in_progress': False,
        'progress': 0,
        'message': '',
        'output_file': None,
        'error': None
    }
    
    success = test_variable_intensity_audio()
    
    print("=" * 60)
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)
