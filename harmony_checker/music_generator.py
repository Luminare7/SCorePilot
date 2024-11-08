import os
import music21
from openai import OpenAI
from typing import Dict, Optional
import time
from tenacity import retry, stop_after_attempt, wait_exponential

class MusicGenerator:
    def __init__(self):
        self.client = OpenAI()
        self._cache = {}  # Simple memory cache
        
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _make_api_call(self, messages, temperature):
        return self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=temperature
        )
    
    def generate_music(self, prompt: str, style: Optional[str] = None) -> Dict:
        """
        Generate music using OpenAI's API based on the given prompt and style
        """
        try:
            # Check cache first
            cache_key = f"{prompt}_{style}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            complete_prompt = f"Generate a {style} piece of music: {prompt}" if style else prompt
            
            messages = [
                {"role": "system", "content": "You are a music composer assistant that creates MusicXML format compositions. Provide the output in valid MusicXML format only."},
                {"role": "user", "content": complete_prompt}
            ]
            
            try:
                response = self._make_api_call(messages, temperature=0.7)
                music_data = response.choices[0].message.content
                
                if not (music_data.startswith('<?xml') or music_data.startswith('<score-partwise>')):
                    raise ValueError("Generated content is not in valid MusicXML format")
                
                result = {
                    "success": True,
                    "music_data": music_data,
                    "format": "musicxml"
                }
                
                # Cache successful result
                self._cache[cache_key] = result
                return result
                
            except Exception as api_error:
                if "quota" in str(api_error).lower():
                    return {
                        "success": False,
                        "error": "API rate limit exceeded. Please try again later.",
                        "error_type": "rate_limit"
                    }
                raise
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
