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
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    def _make_api_call(self, messages, temperature):
        try:
            return self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=2000,  # Add token limit
                presence_penalty=0.6,  # Add presence penalty
                frequency_penalty=0.6  # Add frequency penalty
            )
        except Exception as e:
            if "rate limits exceeded" in str(e).lower():
                time.sleep(20)  # Add delay before retry
                raise
            elif "network" in str(e).lower():
                time.sleep(5)  # Add shorter delay for network issues
                raise
            else:
                raise

    def generate_music(self, prompt: str, style: Optional[str] = None) -> Dict:
        try:
            cache_key = f"{prompt}_{style}"
            if cache_key in self._cache:
                return self._cache[cache_key]
                
            complete_prompt = f"Generate a {style} piece of music: {prompt}" if style else prompt
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a music composer assistant. Create a MusicXML score with these rules:\n1. Use only basic notations\n2. Keep the length reasonable\n3. Focus on melody and harmony\n4. Include proper time and key signatures"
                },
                {"role": "user", "content": complete_prompt}
            ]
            
            try:
                response = self._make_api_call(messages, temperature=0.7)
                music_data = response.choices[0].message.content
                
                # Validate MusicXML
                if not (music_data.startswith('<?xml') or music_data.startswith('<score-partwise>')):
                    return {
                        "success": False,
                        "error": "Generated content is not in valid MusicXML format",
                        "error_type": "invalid_format"
                    }
                
                result = {
                    "success": True,
                    "music_data": music_data,
                    "format": "musicxml"
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
