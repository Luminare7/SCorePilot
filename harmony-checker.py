from music21 import *
import numpy as np

class HarmonyAnalyzer:
    def __init__(self):
        self.score = None
        self.errors = []
        
    def load_score(self, musicxml_path):
        """Carica uno spartito da file MusicXML (esportato da Sibelius)"""
        self.score = converter.parse(musicxml_path)
        
    def analyze(self):
        """Esegue l'analisi completa dello spartito"""
        self.check_parallel_fifths()
        self.check_parallel_octaves()
        self.check_voice_leading()
        self.check_chord_progressions()
        self.check_cadences()
        return self.errors
        
    def check_parallel_fifths(self):
        """Controlla la presenza di quinte parallele"""
        for measure in self.score.measureRange:
            voices = self.extract_voices(measure)
            for i in range(len(voices[0]) - 1):
                # Calcola gli intervalli tra voci consecutive
                interval1 = interval.Interval(voices[0][i], voices[1][i])
                interval2 = interval.Interval(voices[0][i+1], voices[1][i+1])
                
                if (interval1.name == 'P5' and interval2.name == 'P5'):
                    self.errors.append({
                        'type': 'Quinte parallele',
                        'measure': measure.number,
                        'beat': i + 1,
                        'description': 'Movimento parallelo di quinte tra le voci'
                    })
    
    def check_voice_leading(self):
        """Controlla le regole della condotta delle parti"""
        for measure in self.score.measureRange:
            voices = self.extract_voices(measure)
            
            # Controlla incroci di voci
            for i in range(len(voices[0])):
                if voices[0][i].pitch.midi < voices[1][i].pitch.midi:
                    self.errors.append({
                        'type': 'Incrocio di voci',
                        'measure': measure.number,
                        'beat': i + 1,
                        'description': 'Le voci si incrociano'
                    })
            
            # Controlla salti melodici eccessivi
            for voice in voices:
                for i in range(len(voice) - 1):
                    interval_size = abs(voice[i].pitch.midi - voice[i+1].pitch.midi)
                    if interval_size > 12:  # Maggiore di un'ottava
                        self.errors.append({
                            'type': 'Salto melodico eccessivo',
                            'measure': measure.number,
                            'beat': i + 1,
                            'description': f'Salto melodico di {interval_size} semitoni'
                        })

    def check_chord_progressions(self):
        """Analizza le progressioni armoniche"""
        chords = self.score.chordify()
        
        for i, chord in enumerate(chords.recurse().getElementsByClass('Chord')):
            if i > 0:
                prev_chord = chords[i-1]
                
                # Controlla movimento V-IV (movimento retrogrado da evitare)
                if self.is_dominant(prev_chord) and self.is_subdominant(chord):
                    self.errors.append({
                        'type': 'Progressione debole',
                        'measure': chord.measureNumber,
                        'description': 'Movimento dal V al IV grado'
                    })

    def check_cadences(self):
        """Verifica la correttezza delle cadenze"""
        phrases = self.identify_phrases()
        
        for phrase in phrases:
            last_chords = phrase[-2:]  # Ultimi due accordi della frase
            
            if not self.is_valid_cadence(last_chords):
                self.errors.append({
                    'type': 'Cadenza irregolare',
                    'measure': last_chords[-1].measureNumber,
                    'description': 'La frase non termina con una cadenza regolare'
                })

    def suggest_corrections(self):
        """Suggerisce correzioni per gli errori trovati"""
        corrections = []
        
        for error in self.errors:
            if error['type'] == 'Quinte parallele':
                corrections.append({
                    'error': error,
                    'suggestion': 'Muovere una delle voci per moto contrario o obliquo'
                })
            elif error['type'] == 'Salto melodico eccessivo':
                corrections.append({
                    'error': error,
                    'suggestion': 'Considerare note di passaggio o suddividere il salto'
                })
            # ... altri tipi di correzioni ...
        
        return corrections

    def generate_report(self):
        """Genera un report dettagliato dell'analisi"""
        return {
            'total_errors': len(self.errors),
            'errors_by_type': self.categorize_errors(),
            'corrections': self.suggest_corrections(),
            'statistics': {
                'measures_analyzed': len(self.score.measures),
                'common_problems': self.identify_common_problems()
            }
        }

    def extract_voices(self, measure):
        """Estrae le voci separate da una misura"""
        voices = []
        for part in measure.parts:
            voices.append(part.flat.notes)
        return voices
