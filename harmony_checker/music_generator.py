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
            if root.tag != 'score-partwise':
                return False
                
            # Check for required elements
            if root.find('.//part-list') is None or root.find('.//part') is None:
                return False
                
            # Parse with music21 to validate musical content
            try:
                music21.converter.parseData(content)
                return True
            except Exception as e:
                logger.error(f"Music21 validation failed: {str(e)}")
                return False
                
        except ET.ParseError:
            return False
        except Exception as e:
            logger.error(f"MusicXML validation error: {str(e)}")
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
                timeout=30
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
                
            system_prompt = '''You are a music composer that creates valid MusicXML content. Follow these rules:
1. Always start with the XML declaration and DOCTYPE
2. Use the following template structure:
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">
<score-partwise version="4.0">
    <part-list>
        <score-part id="P1">
            <part-name>Music</part-name>
        </score-part>
    </part-list>
    <part id="P1">
        <!-- Your measures here -->
    </part>
</score-partwise>'''
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate a {style} piece in valid MusicXML format: {prompt}"}
            ]
            
            try:
                response = self._make_api_call(messages, temperature=0.7)
                music_data = response.choices[0].message.content
                
                # Validate MusicXML with detailed error messages
                if not self.validate_musicxml(music_data):
                    error_msg = "Generated content is not in valid MusicXML format. "
                    if not music_data.strip().startswith('<?xml'):
                        error_msg += "Missing XML declaration."
                    elif "score-partwise" not in music_data:
                        error_msg += "Missing score-partwise element."
                    elif "part-list" not in music_data:
                        error_msg += "Missing part-list element."
                    return {
                        "success": False,
                        "error": error_msg,
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
