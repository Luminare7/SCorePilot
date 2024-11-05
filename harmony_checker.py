from music21 import *
import numpy as np

class HarmonyAnalyzer:
    def __init__(self):
        self.score = None
        self.errors = []
        
    def load_score(self, musicxml_path):
        """Loads a score from MusicXML file (exported from Sibelius)"""
        self.score = converter.parse(musicxml_path)
        
    def analyze(self):
        """Performs complete analysis of the score"""
        self.errors = []  # Reset errors before new analysis
        self.check_parallel_fifths()
        self.check_parallel_octaves()
        self.check_voice_leading()
        self.check_chord_progressions()
        self.check_cadences()
        return self.errors
        
    def check_parallel_fifths(self):
        """Checks for parallel fifths"""
        if not self.score:
            return
            
        parts = self.score.parts
        if len(parts) < 2:  # Need at least 2 voices to check parallels
            return
            
        for i in range(len(parts[0].flat.notes) - 1):
            # Get current and next notes for both voices
            curr_note1 = parts[0].flat.notes[i]
            next_note1 = parts[0].flat.notes[i + 1]
            curr_note2 = parts[1].flat.notes[i]
            next_note2 = parts[1].flat.notes[i + 1]
            
            # Calculate intervals
            curr_interval = interval.Interval(noteStart=curr_note1, noteEnd=curr_note2)
            next_interval = interval.Interval(noteStart=next_note1, noteEnd=next_note2)
            
            if curr_interval.name == 'P5' and next_interval.name == 'P5':
                self.errors.append({
                    'type': 'Parallel Fifths',
                    'measure': curr_note1.measureNumber,
                    'description': 'Parallel fifth movement detected between voices'
                })
    
    def check_parallel_octaves(self):
        """Checks for parallel octaves"""
        if not self.score:
            return
            
        parts = self.score.parts
        if len(parts) < 2:
            return
            
        for i in range(len(parts[0].flat.notes) - 1):
            curr_note1 = parts[0].flat.notes[i]
            next_note1 = parts[0].flat.notes[i + 1]
            curr_note2 = parts[1].flat.notes[i]
            next_note2 = parts[1].flat.notes[i + 1]
            
            curr_interval = interval.Interval(noteStart=curr_note1, noteEnd=curr_note2)
            next_interval = interval.Interval(noteStart=next_note1, noteEnd=next_note2)
            
            if curr_interval.name == 'P8' and next_interval.name == 'P8':
                self.errors.append({
                    'type': 'Parallel Octaves',
                    'measure': curr_note1.measureNumber,
                    'description': 'Parallel octave movement detected between voices'
                })
    
    def check_voice_leading(self):
        """Checks voice leading rules"""
        if not self.score:
            return
            
        parts = self.score.parts
        for part in parts:
            notes = part.flat.notes
            for i in range(len(notes) - 1):
                # Check for large leaps
                interval_size = abs(interval.Interval(
                    noteStart=notes[i],
                    noteEnd=notes[i + 1]
                ).semitones)
                
                if interval_size > 12:  # Larger than an octave
                    self.errors.append({
                        'type': 'Large Leap',
                        'measure': notes[i].measureNumber,
                        'description': f'Large melodic leap of {interval_size} semitones'
                    })

    def check_chord_progressions(self):
        """Analyzes chord progressions"""
        if not self.score:
            return
            
        chords = self.score.chordify()
        measures = chords.measures(0, None)
        
        prev_chord = None
        for measure in measures:
            for chord in measure.getElementsByClass('Chord'):
                if prev_chord:
                    # Simple check for V-IV progression (usually avoided)
                    if self._is_dominant(prev_chord) and self._is_subdominant(chord):
                        self.errors.append({
                            'type': 'Weak Progression',
                            'measure': chord.measureNumber,
                            'description': 'V-IV progression detected'
                        })
                prev_chord = chord
    
    def check_cadences(self):
        """Verifies proper cadences"""
        if not self.score:
            return
            
        chords = self.score.chordify()
        measures = chords.measures(0, None)
        
        # Get last two chords
        final_chords = []
        for m in measures[-2:]:
            for chord in m.getElementsByClass('Chord'):
                final_chords.append(chord)
        
        if len(final_chords) >= 2:
            penultimate = final_chords[-2]
            final = final_chords[-1]
            
            if not self._is_valid_cadence(penultimate, final):
                self.errors.append({
                    'type': 'Invalid Cadence',
                    'measure': final.measureNumber,
                    'description': 'Phrase does not end with proper cadence'
                })
    
    def _is_dominant(self, chord):
        """Helper to check if chord is dominant"""
        # Simplified check - looks for V chord characteristics
        root = chord.root()
        if root and root.pitch.name == 'G':  # Assuming C major for simplicity
            return True
        return False
    
    def _is_subdominant(self, chord):
        """Helper to check if chord is subdominant"""
        # Simplified check - looks for IV chord characteristics
        root = chord.root()
        if root and root.pitch.name == 'F':  # Assuming C major for simplicity
            return True
        return False
    
    def _is_valid_cadence(self, penultimate, final):
        """Helper to check if cadence is valid"""
        # Simplified check for authentic cadence
        return self._is_dominant(penultimate) and final.root().name == 'C'
    
    def generate_report(self):
        """Generates detailed analysis report"""
        if not self.errors:
            return {
                'total_errors': 0,
                'errors_by_type': {},
                'corrections': [],
                'statistics': {
                    'measures_analyzed': len(self.score.measures(0, None)) if self.score else 0,
                    'common_problems': []
                }
            }
            
        # Count errors by type
        error_types = {}
        for error in self.errors:
            if error['type'] not in error_types:
                error_types[error['type']] = 0
            error_types[error['type']] += 1
        
        # Generate corrections
        corrections = []
        for error in self.errors:
            suggestion = {
                'Parallel Fifths': 'Use contrary or oblique motion between voices',
                'Parallel Octaves': 'Use contrary or oblique motion between voices',
                'Large Leap': 'Consider using stepwise motion or smaller intervals',
                'Weak Progression': 'Consider using stronger chord progressions like V-I',
                'Invalid Cadence': 'End the phrase with an authentic cadence (V-I)'
            }.get(error['type'], 'Review and revise this section')
            
            corrections.append({
                'error': error,
                'suggestion': suggestion
            })
        
        return {
            'total_errors': len(self.errors),
            'errors_by_type': error_types,
            'corrections': corrections,
            'statistics': {
                'measures_analyzed': len(self.score.measures(0, None)) if self.score else 0,
                'common_problems': [k for k, v in error_types.items() if v > 1]
            }
        }
