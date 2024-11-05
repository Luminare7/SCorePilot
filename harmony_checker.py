from music21 import *
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

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

    def generate_pdf_report(self):
        """Generates a PDF report of the analysis"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        story.append(Paragraph("Harmony Analysis Report", title_style))
        story.append(Spacer(1, 12))

        # Summary
        story.append(Paragraph(f"Total Errors Found: {len(self.errors)}", styles['Heading2']))
        story.append(Spacer(1, 12))

        # Errors by Type
        if self.errors:
            story.append(Paragraph("Detailed Errors:", styles['Heading2']))
            story.append(Spacer(1, 12))

            for error in self.errors:
                error_text = f"""
                <b>Type:</b> {error['type']}<br/>
                <b>Measure:</b> {error['measure']}<br/>
                <b>Description:</b> {error['description']}
                """
                story.append(Paragraph(error_text, styles['Normal']))
                story.append(Spacer(1, 12))

            # Statistics
            report = self.generate_report()
            stats_data = [
                ['Statistic', 'Value'],
                ['Total Measures Analyzed', str(report['statistics']['measures_analyzed'])],
                ['Total Errors', str(report['total_errors'])]
            ]
            
            for error_type, count in report['errors_by_type'].items():
                stats_data.append([f'{error_type} Errors', str(count)])

            table = Table(stats_data, colWidths=[300, 200])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)

            # Suggestions
            story.append(Spacer(1, 20))
            story.append(Paragraph("Suggested Corrections:", styles['Heading2']))
            story.append(Spacer(1, 12))

            for correction in report['corrections']:
                correction_text = f"""
                <b>Issue:</b> {correction['error']['type']}<br/>
                <b>Suggestion:</b> {correction['suggestion']}
                """
                story.append(Paragraph(correction_text, styles['Normal']))
                story.append(Spacer(1, 12))
        else:
            story.append(Paragraph("No errors found in the score!", styles['Heading2']))

        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content