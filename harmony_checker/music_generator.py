import os
import music21
import tempfile
import xml.etree.ElementTree as ET
from openai import OpenAI
import httpx
from typing import Dict, Optional
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)

class MusicGenerator:
    def __init__(self):
        self.client = OpenAI()
        self._cache = {}  # Simple memory cache
        
    def validate_musicxml(self, content: str) -> bool:
        """Validate if content is valid MusicXML"""
        try:
            if not content.strip().startswith('<?xml'):
                return False
            root = ET.fromstring(content)
            return root.tag == 'score-partwise'
        except ET.ParseError:
            return False

    def convert_to_midi(self, musicxml_content: str) -> bytes:
        """Convert MusicXML content to MIDI format"""
        try:
            # Convert MusicXML string to music21 stream
            stream = music21.converter.parse(musicxml_content)
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
                # Write MIDI file
                stream.write('midi', tmp.name)
                # Read the MIDI data
                with open(tmp.name, 'rb') as f:
                    midi_data = f.read()
                # Clean up
                os.unlink(tmp.name)
            return midi_data
        except Exception as e:
            logger.error(f"MIDI conversion failed: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=10, max=60),
        reraise=True
    )
    def _make_api_call(self, messages, temperature):
        try:
            return self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=2000,
                presence_penalty=0.6,
                frequency_penalty=0.6,
                timeout=30  # Add timeout
            )
        except Exception as e:
            if isinstance(e, httpx.TimeoutException):
                raise ValueError("Request timed out. Please try again.")
            elif isinstance(e, httpx.NetworkError):
                raise ValueError("Network error occurred. Please check your connection.")
            raise

    def generate_music(self, prompt: str, style: Optional[str] = None) -> Dict:
        try:
            cache_key = f"{prompt}_{style}"
            if cache_key in self._cache:
                return self._cache[cache_key]
                
            messages = [
                {
                    "role": "system",
                    "content": '''You are a music composer that creates valid MusicXML content. Always respond with complete, valid MusicXML structure including:
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="4.0">
    <!-- Your music content here -->
</score-partwise>'''
                },
                {
                    "role": "user", 
                    "content": f"Generate a {style} piece in valid MusicXML format: {prompt}"
                }
            ]
            
            try:
                response = self._make_api_call(messages, temperature=0.7)
                music_data = response.choices[0].message.content
                
                # Validate MusicXML
                if not self.validate_musicxml(music_data):
                    return {
                        "success": False,
                        "error": "Generated content is not in valid MusicXML format",
                        "error_type": "invalid_format"
                    }
                
                # Convert to MIDI
                try:
                    midi_data = self.convert_to_midi(music_data)
                except Exception as e:
                    logger.error(f"MIDI conversion failed: {str(e)}")
                    return {
                        "success": False,
                        "error": "Failed to convert music to MIDI format",
                        "error_type": "conversion_error"
                    }
                
                result = {
                    "success": True,
                    "music_data": midi_data,
                    "format": "midi"
                }
                
                self._cache[cache_key] = result
                return result
                
            except Exception as api_error:
                error_message = str(api_error).lower()
                if "quota" in error_message or "rate" in error_message:
                    return {
                        "success": False,
                        "error": "API rate limit exceeded. Please try again in a few moments.",
                        "error_type": "rate_limit"
                    }
                elif "network" in error_message:
                    return {
                        "success": False,
                        "error": "Network error occurred. Please check your connection and try again.",
                        "error_type": "network_error"
                    }
                elif "timeout" in error_message:
                    return {
                        "success": False,
                        "error": "Request timed out. Please try again.",
                        "error_type": "timeout"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API error: {str(api_error)}",
                        "error_type": "api_error"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error"
            }
