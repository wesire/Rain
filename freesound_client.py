#!/usr/bin/env python3
"""
Freesound.org API client for searching and downloading audio samples.
API Documentation: https://freesound.org/docs/api/
"""

import requests
import json
from pathlib import Path
from typing import List, Dict, Optional
import config

class FreesoundClient:
    """Client for interacting with Freesound.org API."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Freesound client.
        
        Args:
            api_key: Freesound API key. If None, uses config.FREESOUND_API_KEY
        """
        self.api_key = api_key or config.FREESOUND_API_KEY
        self.base_url = config.FREESOUND_API_BASE_URL
        
        if not self.api_key:
            raise ValueError("Freesound API key is required. Set FREESOUND_API_KEY environment variable.")
    
    def search(self, query: str, filter_params: Optional[Dict] = None, page: int = 1, 
               page_size: int = None) -> Dict:
        """
        Search for sounds on Freesound.
        
        Args:
            query: Search query (e.g., "rain on window", "thunder")
            filter_params: Optional filters (duration, license, etc.)
            page: Page number for pagination
            page_size: Number of results per page
            
        Returns:
            Dictionary with search results including:
            - count: Total number of results
            - results: List of sound objects
            - next/previous: Pagination URLs
        """
        if page_size is None:
            page_size = config.DEFAULT_SEARCH_PAGE_SIZE
            
        url = f"{self.base_url}/search/text/"
        
        params = {
            'query': query,
            'token': self.api_key,
            'page': page,
            'page_size': page_size,
            'fields': 'id,name,duration,previews,download,license,avg_rating,num_ratings,tags,description'
        }
        
        # Add filters if provided
        if filter_params:
            if 'min_duration' in filter_params or 'max_duration' in filter_params:
                duration_filter = []
                if 'min_duration' in filter_params:
                    duration_filter.append(f"duration:[{filter_params['min_duration']} TO *]")
                if 'max_duration' in filter_params:
                    duration_filter.append(f"duration:[* TO {filter_params['max_duration']}]")
                params['filter'] = ' '.join(duration_filter)
            
            if 'license' in filter_params:
                params['filter'] = params.get('filter', '') + f" license:{filter_params['license']}"
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'count': 0,
                'results': []
            }
    
    def get_sound_info(self, sound_id: int) -> Dict:
        """
        Get detailed information about a specific sound.
        
        Args:
            sound_id: Freesound sound ID
            
        Returns:
            Dictionary with sound details
        """
        url = f"{self.base_url}/sounds/{sound_id}/"
        params = {'token': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    def download_sound(self, sound_id: int, output_path: Path, use_preview: bool = False) -> bool:
        """
        Download a sound file from Freesound.
        
        Args:
            sound_id: Freesound sound ID
            output_path: Path where to save the file
            use_preview: If True, download preview MP3 instead of original file
            
        Returns:
            True if download successful, False otherwise
        """
        # Get sound info to get download URL
        sound_info = self.get_sound_info(sound_id)
        
        if 'error' in sound_info:
            print(f"Error getting sound info: {sound_info['error']}")
            return False
        
        try:
            if use_preview:
                # Use high-quality preview
                download_url = sound_info['previews']['preview-hq-mp3']
            else:
                # Use original file (requires OAuth2 authentication in real implementation)
                # For now, we'll use the high-quality preview
                download_url = sound_info['previews']['preview-hq-mp3']
            
            # Download the file
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()
            
            # Save to file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except (requests.exceptions.RequestException, KeyError) as e:
            print(f"Error downloading sound: {e}")
            return False
    
    def get_preview_url(self, sound_id: int, quality: str = 'hq-mp3') -> Optional[str]:
        """
        Get preview URL for a sound.
        
        Args:
            sound_id: Freesound sound ID
            quality: Preview quality ('hq-mp3', 'lq-mp3', 'hq-ogg', 'lq-ogg')
            
        Returns:
            Preview URL or None if error
        """
        sound_info = self.get_sound_info(sound_id)
        
        if 'error' in sound_info:
            return None
        
        try:
            preview_key = f'preview-{quality}'
            return sound_info['previews'].get(preview_key)
        except KeyError:
            return None
    
    def categorize_sound(self, sound_info: Dict) -> str:
        """
        Suggest a category for a sound based on its duration and characteristics.
        
        Args:
            sound_info: Sound information dictionary
            
        Returns:
            Suggested category: 'bed', 'texture', 'detail', or 'environmental'
        """
        duration = sound_info.get('duration', 0)
        name = sound_info.get('name', '').lower()
        tags = [tag.lower() for tag in sound_info.get('tags', [])]
        
        # Check for environmental keywords
        environmental_keywords = ['thunder', 'wind', 'storm', 'lightning']
        if any(keyword in name or keyword in tags for keyword in environmental_keywords):
            return 'environmental'
        
        # Categorize by duration
        if duration >= config.MIN_BED_DURATION:
            return 'bed'
        elif duration >= config.MIN_TEXTURE_DURATION:
            return 'texture'
        elif duration >= config.MIN_DETAIL_DURATION:
            return 'detail'
        else:
            return 'detail'  # Default to detail for very short sounds

def test_client():
    """Test the Freesound client."""
    try:
        client = FreesoundClient()
        print("Testing Freesound API client...")
        
        # Test search
        results = client.search("rain", page_size=5)
        if 'error' in results:
            print(f"Error: {results['error']}")
        else:
            print(f"Found {results['count']} sounds")
            for sound in results['results'][:3]:
                print(f"  - {sound['name']} ({sound['duration']:.1f}s)")
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    test_client()
