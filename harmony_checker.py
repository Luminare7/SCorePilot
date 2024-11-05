from music21 import *
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import logging
import os
import uuid
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot

logger = logging.getLogger(__name__)

class HarmonyAnalyzer:
    def __init__(self):
        self.score = None
        self.errors = []
        self.visualization_path = None
        
    def load_score(self, musicxml_path):
        """Loads a score from MusicXML file"""
        try:
            self.score = converter.parse(musicxml_path)
            logger.debug(f"Successfully loaded score from {musicxml_path}")
            # Generate visualization after loading
            self.visualization_path = self.generate_visualization()
        except Exception as e:
            logger.error(f"Error loading score: {str(e)}", exc_info=True)
            raise Exception(f"Failed to load score: {str(e)}")
            
    def generate_visualization(self):
        try:
            if not self.score:
                return None
                
            vis_dir = os.path.join('static', 'visualizations')
            os.makedirs(vis_dir, exist_ok=True)
            
            filename = f"score_{uuid.uuid4()}.png"
            filepath = os.path.join(vis_dir, filename)
            
            # Try direct stream visualization
            try:
                # Create a stream with just the notes/chords
                reduced_score = self.score.measures(0, None).stripTies()
                reduced_score.write('musicxml.png', fp=filepath)
                return os.path.join('visualizations', filename)
            except Exception as e1:
                logger.debug(f"Direct visualization failed: {e1}")
                
                # Try alternative visualization using piano roll
                try:
                    plot = graph.plot.Piano(reduced_score, doneAction=None)
                    plot.run()
                    plot.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                    return os.path.join('visualizations', filename)
                except Exception as e2:
                    logger.debug(f"Piano roll visualization failed: {e2}")
                    return None
                    
        except Exception as e:
            logger.error(f"All visualization methods failed: {str(e)}")
            return None

    def check_parallel_fifths(self):
        """Checks for parallel fifths between voices"""
        if not self.score:
            return
            
        try:
            parts = self.score.parts
            for i in range(len(parts) - 1):
                for j in range(i + 1, len(parts)):
                    prev_interval = None
                    for n1, n2 in zip(parts[i].flatten().notesAndRests, 
                                    parts[j].flatten().notesAndRests):
                        if isinstance(n1, note.Note) and isinstance(n2, note.Note):
                            curr_interval = interval.Interval(noteStart=n1, noteEnd=n2)
                            if prev_interval and prev_interval.simpleName == 'P5' and curr_interval.simpleName == 'P5':
                                self.errors.append({
                                    'type': 'Parallel Fifth',
                                    'measure': n1.measureNumber,
                                    'description': f'Parallel fifth found between parts {i+1} and {j+1}'
                                })
                            prev_interval = curr_interval
        except Exception as e:
            logger.error(f"Error checking parallel fifths: {str(e)}")
            raise Exception(f"Failed to check parallel fifths: {str(e)}")

    def check_parallel_octaves(self):
        """Checks for parallel octaves between voices"""
        if not self.score:
            return
            
        try:
            parts = self.score.parts
            for i in range(len(parts) - 1):
                for j in range(i + 1, len(parts)):
                    prev_interval = None
                    for n1, n2 in zip(parts[i].flatten().notesAndRests, 
                                    parts[j].flatten().notesAndRests):
                        if isinstance(n1, note.Note) and isinstance(n2, note.Note):
                            curr_interval = interval.Interval(noteStart=n1, noteEnd=n2)
                            if prev_interval and prev_interval.simpleName == 'P8' and curr_interval.simpleName == 'P8':
                                self.errors.append({
                                    'type': 'Parallel Octave',
                                    'measure': n1.measureNumber,
                                    'description': f'Parallel octave found between parts {i+1} and {j+1}'
                                })
                            prev_interval = curr_interval
        except Exception as e:
            logger.error(f"Error checking parallel octaves: {str(e)}")
            raise Exception(f"Failed to check parallel octaves: {str(e)}")

    def check_voice_leading(self):
        """Checks voice leading rules"""
        if not self.score:
            return
            
        try:
            parts = self.score.parts
            for i, part in enumerate(parts):
                notes = list(part.flatten().notesAndRests)
                for j in range(len(notes) - 1):
                    if isinstance(notes[j], note.Note) and isinstance(notes[j+1], note.Note):
                        # Check for large leaps
                        curr_interval = interval.Interval(noteStart=notes[j], noteEnd=notes[j+1])
                        if abs(curr_interval.semitones) > 9:  # Larger than major 6th
                            self.errors.append({
                                'type': 'Voice Leading',
                                'measure': notes[j].measureNumber,
                                'description': f'Large leap ({abs(curr_interval.semitones)} semitones) in part {i+1}'
                            })
                        
                        # Check for voice crossing
                        if i < len(parts) - 1:
                            lower_part_notes = list(parts[i+1].flatten().notesAndRests)
                            if j < len(lower_part_notes) and isinstance(lower_part_notes[j], note.Note):
                                if notes[j].pitch.ps < lower_part_notes[j].pitch.ps:
                                    self.errors.append({
                                        'type': 'Voice Leading',
                                        'measure': notes[j].measureNumber,
                                        'description': f'Voice crossing detected between parts {i+1} and {i+2}'
                                    })
        except Exception as e:
            logger.error(f"Error checking voice leading: {str(e)}")
            raise Exception(f"Failed to check voice leading: {str(e)}")

    def check_chord_progressions(self):
        """Analyzes chord progressions for common practice period rules"""
        if not self.score:
            return
            
        try:
            chords = self.score.chordify()
            prev_chord = None
            
            for chord in chords.recurse().getElementsByClass('Chord'):
                if prev_chord:
                    # Check for direct fifth/octave motion
                    if len(chord.pitches) >= 2 and len(prev_chord.pitches) >= 2:
                        if chord.root().name == prev_chord.root().name:
                            continue
                            
                        # Check for weak root progression
                        curr_root = chord.root()
                        prev_root = prev_chord.root()
                        interval_between_roots = interval.Interval(noteStart=prev_root, noteEnd=curr_root)
                        
                        if interval_between_roots.directedSimpleName in ['P4', '-P5']:
                            self.errors.append({
                                'type': 'Chord Progression',
                                'measure': chord.measureNumber,
                                'description': 'Weak root progression (descending fifth)'
                            })
                
                prev_chord = chord
                
        except Exception as e:
            logger.error(f"Error checking chord progressions: {str(e)}")
            raise Exception(f"Failed to check chord progressions: {str(e)}")

    def check_cadences(self):
        """Verifies proper cadential formulas"""
        if not self.score:
            return
            
        try:
            chords = self.score.chordify()
            chord_list = list(chords.recurse().getElementsByClass('Chord'))
            
            if len(chord_list) >= 2:
                final_chords = chord_list[-2:]
                
                # Check for authentic cadence (V-I)
                if len(final_chords) == 2:
                    penultimate = final_chords[0]
                    final = final_chords[1]
                    
                    if penultimate.quality == 'major' and final.quality == 'major':
                        interval_between = interval.Interval(
                            noteStart=penultimate.root(),
                            noteEnd=final.root()
                        )
                        
                        if interval_between.directedSimpleName != 'P4':  # Not a V-I progression
                            self.errors.append({
                                'type': 'Cadence',
                                'measure': final.measureNumber,
                                'description': 'Final cadence is not an authentic cadence (V-I)'
                            })
                            
        except Exception as e:
            logger.error(f"Error checking cadences: {str(e)}")
            raise Exception(f"Failed to check cadences: {str(e)}")

    def analyze(self):
        """Performs complete analysis of the score"""
        try:
            self.errors = []  # Reset errors before new analysis
            self.check_parallel_fifths()
            self.check_parallel_octaves()
            self.check_voice_leading()
            self.check_chord_progressions()
            self.check_cadences()
            return self.errors
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            raise Exception(f"Analysis failed: {str(e)}")

    def generate_report(self):
        """Generates detailed analysis report"""
        return {
            'total_errors': len(self.errors),
            'errors_by_type': self._categorize_errors(),
            'corrections': self._suggest_corrections(),
            'statistics': {
                'measures_analyzed': len(self.score.measures(0, None)) if self.score else 0,
                'common_problems': self._identify_common_problems()
            }
        }

    def _categorize_errors(self):
        """Helper method to categorize errors by type"""
        categories = {}
        for error in self.errors:
            if error['type'] not in categories:
                categories[error['type']] = 0
            categories[error['type']] += 1
        return categories

    def _suggest_corrections(self):
        """Generates correction suggestions for each error"""
        corrections = []
        for error in self.errors:
            suggestion = {
                'Parallel Fifth': 'Use contrary or oblique motion between voices',
                'Parallel Octave': 'Use contrary or oblique motion between voices',
                'Voice Leading': 'Consider stepwise motion or smaller intervals',
                'Chord Progression': 'Consider using stronger root progressions',
                'Cadence': 'End the phrase with a proper authentic cadence (V-I)'
            }.get(error['type'], 'Review and revise this section')
            
            corrections.append({
                'error': error,
                'suggestion': suggestion
            })
        return corrections

    def _identify_common_problems(self):
        """Identifies frequently occurring issues"""
        categories = self._categorize_errors()
        return [error_type for error_type, count in categories.items() if count > 1]

    def generate_pdf_report(self):
        """Generates a PDF report of the analysis"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            story.append(Paragraph("Harmony Analysis Report", title_style))
            story.append(Spacer(1, 12))

            story.append(Paragraph(f"Total Errors Found: {len(self.errors)}", styles['Heading2']))
            story.append(Spacer(1, 12))

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
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate PDF report: {str(e)}")
