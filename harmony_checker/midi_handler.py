import music21
import pretty_midi
import os
from typing import Optional, Tuple
import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

logger = logging.getLogger(__name__)

class MIDIHandler:
    @staticmethod
    def midi_to_musicxml(midi_file: str) -> Tuple[bool, Optional[str], str]:
        try:
            # Parse MIDI file directly with music21
            score = music21.converter.parse(midi_file)
            
            # Create output paths
            base_name = os.path.splitext(os.path.basename(midi_file))[0]
            xml_path = os.path.join('static', 'visualizations', f"{base_name}.musicxml")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(xml_path), exist_ok=True)
            
            # Clean up the score
            score.makeNotation()
            
            # Add missing elements if needed
            for part in score.parts:
                if not part.recurse().getElementsByClass('Clef'):
                    part.insert(0, music21.clef.TrebleClef())
                if not part.recurse().getElementsByClass('TimeSignature'):
                    part.insert(0, music21.meter.TimeSignature('4/4'))
                if not part.recurse().getElementsByClass('KeySignature'):
                    part.insert(0, music21.key.Key('C'))
            
            # Write MusicXML
            score.write('musicxml', fp=xml_path)
            
            # Create visualization using music21's built-in plotter
            try:
                for part in score.parts:
                    part.plot('pianoroll',
                             title=f'Piano Score - {base_name}',
                             saved=True,
                             filepath=os.path.join('static', 'visualizations', f"{base_name}_score.png"))
                    break
            except Exception as e:
                logger.warning(f"Score visualization failed: {str(e)}")
            
            return True, xml_path, "Successfully converted MIDI to MusicXML"
        except Exception as e:
            logger.error(f"Error converting MIDI to MusicXML: {str(e)}")
            return False, None, f"Failed to convert MIDI: {str(e)}"

    @staticmethod
    def create_piano_roll(midi_file: str, output_path: str) -> Tuple[bool, str]:
        """Create enhanced piano roll visualization from MIDI file"""
        try:
            midi_data = pretty_midi.PrettyMIDI(midi_file)
            
            # Get piano roll with higher resolution
            fs = 100  # Higher sampling frequency
            piano_roll = midi_data.get_piano_roll(fs=fs)
            
            # Create custom colormap for better visibility
            colors = [(0.95, 0.95, 0.95), (0.2, 0.4, 0.8), (0.1, 0.2, 0.5)]  # Light blue to dark blue
            cmap = LinearSegmentedColormap.from_list('custom_blues', colors)
            
            # Create figure with larger size and higher DPI
            plt.figure(figsize=(15, 10), dpi=300)
            
            # Plot piano roll with enhanced visualization
            plt.imshow(piano_roll, aspect='auto', origin='lower', 
                      cmap=cmap, interpolation='nearest')
            
            # Add colorbar with proper label
            cbar = plt.colorbar(label='Velocity')
            cbar.ax.tick_params(labelsize=10)
            
            # Customize axis labels and ticks
            plt.ylabel('MIDI Note Number')
            plt.xlabel('Time (seconds)')
            
            # Add grid for better readability
            plt.grid(True, alpha=0.3, linestyle='--')
            
            # Calculate time axis ticks
            total_time = midi_data.get_end_time()
            x_ticks = np.linspace(0, piano_roll.shape[1], num=10)
            x_labels = [f"{(t/fs):.1f}" for t in x_ticks]
            plt.xticks(x_ticks, x_labels)
            
            # Add note number labels
            y_ticks = np.arange(0, 128, 12)
            y_labels = [pretty_midi.note_number_to_name(n) for n in y_ticks]
            plt.yticks(y_ticks, y_labels)
            
            # Add title
            plt.title("Piano Roll Visualization")
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout()
            
            # Save figure with high quality
            plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            return True, "Successfully created piano roll visualization"
        except Exception as e:
            logger.error(f"Error creating piano roll: {str(e)}")
            return False, f"Failed to create piano roll: {str(e)}"

    @staticmethod
    def get_midi_info(midi_file: str) -> dict:
        """Get detailed information about MIDI file"""
        try:
            midi_data = pretty_midi.PrettyMIDI(midi_file)
            
            # Get instrument names
            instrument_names = []
            for instrument in midi_data.instruments:
                if not instrument.is_drum:
                    program = instrument.program
                    instrument_name = pretty_midi.program_to_instrument_name(program)
                    instrument_names.append(instrument_name)
            
            return {
                'length': round(midi_data.get_end_time(), 2),
                'tempo': 120.0,  # Default tempo
                'time_signature': f"{midi_data.time_signature_changes[0].numerator}/{midi_data.time_signature_changes[0].denominator}" if midi_data.time_signature_changes else "4/4",
                'key_signature': midi_data.key_signature_changes[0].key_number if midi_data.key_signature_changes else 0,
                'instrument_names': instrument_names,
                'total_notes': sum(len(i.notes) for i in midi_data.instruments)
            }
        except Exception as e:
            logger.error(f"Error getting MIDI info: {str(e)}")
            return {}
