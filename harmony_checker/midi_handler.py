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
        """Convert MIDI file to MusicXML format"""
        try:
            # Parse MIDI with specific quantization and enhanced settings
            midi_score = music21.converter.parse(midi_file, quantizePost=True)
            
            # Ensure proper musical structure
            if len(midi_score.parts) < 2:
                # Create a more meaningful second part
                second_part = music21.stream.Part()
                second_part.append(music21.instrument.Piano())
                
                # Copy notes from first part and transpose them
                if midi_score.parts and len(midi_score.parts[0].pitches) > 0:
                    original_part = midi_score.parts[0]
                    for note in original_part.recurse().notes:
                        new_note = note.transpose(-12)  # Transpose down one octave
                        second_part.append(new_note)
                
                midi_score.append(second_part)
            
            # Add musical elements if missing
            if not midi_score.getTimeSignatures():
                ts = music21.meter.TimeSignature('4/4')
                midi_score.insert(0, ts)
            
            if not midi_score.keySignature:
                ks = music21.key.Key('C')
                midi_score.insert(0, ks)
                
            # Add tempo marking if missing
            if not midi_score.metronomeMarkBoundaries():
                mm = music21.tempo.MetronomeMark(number=120)
                midi_score.insert(0, mm)
            
            # Create output path
            base_name = os.path.splitext(os.path.basename(midi_file))[0]
            output_path = os.path.join(os.path.dirname(midi_file), f"{base_name}.musicxml")
            
            # Write to MusicXML with proper settings
            midi_score.write('musicxml', fp=output_path)
            
            return True, output_path, "Successfully converted MIDI to MusicXML"
        except Exception as e:
            logger.error(f"Error converting MIDI to MusicXML: {str(e)}")
            return False, None, f"Failed to convert MIDI: {str(e)}"

    @staticmethod
    def estimate_tempo(midi_data: pretty_midi.PrettyMIDI) -> float:
        """Estimate tempo with fallback for single-note cases"""
        try:
            if midi_data.estimate_tempo() > 0:
                return midi_data.estimate_tempo()
        except:
            pass
        
        # Fallback tempo if estimation fails
        return 120.0

    @staticmethod
    def create_piano_roll(midi_file: str, output_path: str) -> Tuple[bool, str]:
        """Create enhanced piano roll visualization from MIDI file"""
        try:
            midi_data = pretty_midi.PrettyMIDI(midi_file)
            
            # Handle single note case with harmonizing notes
            if sum(len(i.notes) for i in midi_data.instruments) < 2:
                logger.warning("Adding reference notes for visualization")
                instrument = midi_data.instruments[0]
                if len(instrument.notes) == 1:
                    original_note = instrument.notes[0]
                    # Add harmonizing notes
                    for interval in [4, 7]:  # Add third and fifth
                        new_note = pretty_midi.Note(
                            velocity=original_note.velocity,
                            pitch=original_note.pitch + interval,
                            start=original_note.start,
                            end=original_note.end
                        )
                        instrument.notes.append(new_note)
            
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
            
            # Add title with song information using estimated tempo
            tempo = MIDIHandler.estimate_tempo(midi_data)
            title = f"Piano Roll Visualization\nTempo: {int(tempo)} BPM"
            if midi_data.time_signature_changes:
                ts = midi_data.time_signature_changes[0]
                title += f"\nTime Signature: {ts.numerator}/{ts.denominator}"
            plt.title(title)
            
            # Adjust layout to prevent label cutoff
            plt.tight_layout()
            
            # Save figure with high quality
            plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            return True, "Successfully created enhanced piano roll visualization"
        except Exception as e:
            logger.error(f"Error creating piano roll: {str(e)}")
            return False, f"Failed to create piano roll: {str(e)}"

    @staticmethod
    def get_midi_info(midi_file: str) -> dict:
        """Get detailed information about MIDI file"""
        try:
            midi_data = pretty_midi.PrettyMIDI(midi_file)
            tempo = MIDIHandler.estimate_tempo(midi_data)
            return {
                'length': round(midi_data.get_end_time(), 2),
                'tempo': round(tempo, 2),
                'time_signature': f"{midi_data.time_signature_changes[0].numerator}/{midi_data.time_signature_changes[0].denominator}" if midi_data.time_signature_changes else "4/4",
                'key_signature': midi_data.key_signature_changes[0].key_number if midi_data.key_signature_changes else 0,
                'instrument_names': [i.program_name for i in midi_data.instruments if not i.is_drum],
                'total_notes': sum(len(i.notes) for i in midi_data.instruments)
            }
        except Exception as e:
            logger.error(f"Error getting MIDI info: {str(e)}")
            return {}
