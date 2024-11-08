import os
import music21
from openai import OpenAI
from typing import Dict, Optional

class MusicGenerator:
    def __init__(self):
        self.client = OpenAI()
        
    def generate_music(self, prompt: str, style: Optional[str] = None) -> Dict:
        """
        Generate music using OpenAI's API based on the given prompt and style
        """
        try:
            complete_prompt = f"Generate a {style} piece of music: {prompt}" if style else prompt
            
            # Use the chat completion API instead of completions
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use GPT-3.5-turbo instead of GPT-4
                messages=[
                    {"role": "system", "content": "You are a music composer assistant that creates MusicXML format compositions. Provide the output in valid MusicXML format only."},
                    {"role": "user", "content": complete_prompt}
                ],
                temperature=0.7
            )
            
            # Extract the generated music content
            music_data = response.choices[0].message.content
            
            # Basic validation of MusicXML format
            if not (music_data.startswith('<?xml') or music_data.startswith('<score-partwise>')):
                raise ValueError("Generated content is not in valid MusicXML format")
            
            return {
                "success": True,
                "music_data": music_data,
                "format": "musicxml"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
