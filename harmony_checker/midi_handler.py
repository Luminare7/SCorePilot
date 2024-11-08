import music21
import pretty_midi
import os
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MIDIHandler:
    @staticmethod
    def midi_to_musicxml(midi_file: str) -> Tuple[bool, Optional[str], str]:
        """Convert MIDI file to MusicXML format"""
        try:
            # Load MIDI file using music21
            midi_score = music21.converter.parse(midi_file)
            
            # Create output filename
            base_name = os.path.splitext(os.path.basename(midi_file))[0]
            output_path = os.path.join(os.path.dirname(midi_file), f"{base_name}.musicxml")
            
            # Convert to MusicXML
            midi_score.write('musicxml', fp=output_path)
            
            return True, output_path, "Successfully converted MIDI to MusicXML"
        except Exception as e:
            logger.error(f"Error converting MIDI to MusicXML: {str(e)}")
            return False, None, f"Failed to convert MIDI: {str(e)}"

    @staticmethod
    def create_piano_roll(midi_file: str, output_path: str) -> Tuple[bool, str]:
        """Create piano roll visualization from MIDI file"""
        try:
            # Load MIDI file
            midi_data = pretty_midi.PrettyMIDI(midi_file)
            
            # Get piano roll
            piano_roll = midi_data.get_piano_roll()
            
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Create figure
            plt.figure(figsize=(12, 8))
            plt.imshow(piano_roll, aspect='auto', origin='lower', cmap='Blues')
            plt.colorbar(label='Velocity')
            plt.ylabel('Pitch')
            plt.xlabel('Time (frames)')
            plt.title('Piano Roll Visualization')
            
            # Save figure
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            return True, "Successfully created piano roll visualization"
        except Exception as e:
            logger.error(f"Error creating piano roll: {str(e)}")
            return False, f"Failed to create piano roll: {str(e)}"

    @staticmethod
    def get_midi_info(midi_file: str) -> dict:
        """Get basic information about MIDI file"""
        try:
            midi_data = pretty_midi.PrettyMIDI(midi_file)
            return {
                'length': round(midi_data.get_end_time(), 2),
                'tempo': round(midi_data.estimate_tempo(), 2),
                'time_signature': midi_data.time_signature_changes[0] if midi_data.time_signature_changes else None,
                'key_signature': midi_data.key_signature_changes[0] if midi_data.key_signature_changes else None,
                'instrument_names': [i.program_name for i in midi_data.instruments if not i.is_drum]
            }
        except Exception as e:
            logger.error(f"Error getting MIDI info: {str(e)}")
            return {}
