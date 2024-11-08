import os
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
            # Prepare the complete prompt with style if provided
            complete_prompt = f"Generate a {style} piece of music: {prompt}" if style else prompt
            
            # Make API call to generate music using the latest API
            response = self.client.completions.create(
                model="gpt-4",  # Using GPT-4 for music generation
                prompt=complete_prompt,
                max_tokens=1024,
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Convert the response to MIDI-compatible format
            # Note: This is a simplified version, in practice you'd need to convert
            # the text response to actual MIDI data
            music_data = response.choices[0].text
            
            return {
                "success": True,
                "music_data": music_data,
                "format": "midi"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
