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
            
            # Method 1: Try using graph.plot
            try:
                plot = graph.plot.PlotScore(self.score)
                plot.run()
                plot.figure.savefig(filepath)
                return os.path.join('visualizations', filename)
            except Exception as e1:
                logger.debug(f"PlotScore failed: {e1}")
                
            # Method 2: Try basic notation plot
            try:
                plot = graph.plot.ScoreHorizontalBar(self.score)
                plot.run()
                plot.figure.savefig(filepath)
                return os.path.join('visualizations', filename)
            except Exception as e2:
                logger.debug(f"ScoreHorizontalBar failed: {e2}")
                
            # Method 3: Try piano roll visualization
            try:
                plot = graph.plot.HorizontalBarPitchSpaceOffset(self.score)
                plot.run()
                plot.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                return os.path.join('visualizations', filename)
            except Exception as e3:
                logger.debug(f"HorizontalBarPitchSpaceOffset failed: {e3}")
                
            return None
            
        except Exception as e:
            logger.error(f"All visualization methods failed: {str(e)}")
            return None

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

    def check_voice_leading(self):
        """Checks voice leading rules"""
        if not self.score:
            return
            
        try:
            parts = self.score.parts
            for part_idx, part in enumerate(parts):
                notes = part.flatten().notes
                for i in range(len(notes) - 1):
                    try:
                        # Handle both Note and Chord objects
                        current_pitch = notes[i].pitch if hasattr(notes[i], 'pitch') else notes[i].root()
                        next_pitch = notes[i+1].pitch if hasattr(notes[i+1], 'pitch') else notes[i+1].root()
                        
                        # Check for large leaps
                        interval_obj = interval.Interval(noteStart=note.Note(current_pitch), 
                                                      noteEnd=note.Note(next_pitch))
                        interval_size = abs(interval_obj.semitones)
                        
                        if interval_size > 12:  # Larger than an octave
                            self.errors.append({
                                'type': 'Large Leap',
                                'measure': notes[i].measureNumber,
                                'description': f'Large melodic leap of {interval_size} semitones in voice {part_idx + 1}'
                            })
                            
                        # Check for voice crossing with next lower voice
                        if part_idx < len(parts) - 1:
                            lower_voice = parts[part_idx + 1].flatten().notes
                            if i < len(lower_voice):
                                lower_pitch = lower_voice[i].pitch if hasattr(lower_voice[i], 'pitch') else lower_voice[i].root()
                                if current_pitch < lower_pitch:
                                    self.errors.append({
                                        'type': 'Voice Crossing',
                                        'measure': notes[i].measureNumber,
                                        'description': f'Voice {part_idx + 1} crosses below voice {part_idx + 2}'
                                    })
                                    
                    except Exception as e:
                        logger.warning(f"Error checking voice leading at position {i}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error in voice leading check: {str(e)}", exc_info=True)

    # [Rest of the class implementation remains the same...]
    def check_parallel_fifths(self):
        """Checks for parallel fifths between voices"""
        if not self.score:
            return
            
        try:
            parts = self.score.parts
            if len(parts) < 2:  # Need at least 2 voices to check parallels
                return
                
            for part1_idx in range(len(parts) - 1):
                for part2_idx in range(part1_idx + 1, len(parts)):
                    notes1 = parts[part1_idx].flatten().notes
                    notes2 = parts[part2_idx].flatten().notes
                    
                    for i in range(len(notes1) - 1):
                        try:
                            curr_interval = interval.Interval(noteStart=notes1[i], noteEnd=notes2[i])
                            next_interval = interval.Interval(noteStart=notes1[i + 1], noteEnd=notes2[i + 1])
                            
                            if curr_interval.simpleName == 'P5' and next_interval.simpleName == 'P5':
                                self.errors.append({
                                    'type': 'Parallel Fifths',
                                    'measure': notes1[i].measureNumber,
                                    'description': f'Parallel fifth movement detected between voices {part1_idx + 1} and {part2_idx + 1}'
                                })
                        except Exception as e:
                            logger.warning(f"Error checking interval at position {i}: {str(e)}")
                            continue
                    
        except Exception as e:
            logger.error(f"Error in parallel fifths check: {str(e)}", exc_info=True)

    def check_parallel_octaves(self):
        """Checks for parallel octaves between voices"""
        if not self.score:
            return
            
        try:
            parts = self.score.parts
            if len(parts) < 2:
                return
                
            for part1_idx in range(len(parts) - 1):
                for part2_idx in range(part1_idx + 1, len(parts)):
                    notes1 = parts[part1_idx].flatten().notes
                    notes2 = parts[part2_idx].flatten().notes
                    
                    for i in range(len(notes1) - 1):
                        try:
                            curr_interval = interval.Interval(noteStart=notes1[i], noteEnd=notes2[i])
                            next_interval = interval.Interval(noteStart=notes1[i + 1], noteEnd=notes2[i + 1])
                            
                            if curr_interval.simpleName == 'P8' and next_interval.simpleName == 'P8':
                                self.errors.append({
                                    'type': 'Parallel Octaves',
                                    'measure': notes1[i].measureNumber,
                                    'description': f'Parallel octave movement detected between voices {part1_idx + 1} and {part2_idx + 1}'
                                })
                        except Exception as e:
                            logger.warning(f"Error checking interval at position {i}: {str(e)}")
                            continue
                    
        except Exception as e:
            logger.error(f"Error in parallel octaves check: {str(e)}", exc_info=True)

    def check_chord_progressions(self):
        """Analyzes chord progressions"""
        if not self.score:
            return
            
        try:
            chordified = self.score.chordify()
            prev_chord = None
            
            for chord in chordified.recurse().getElementsByClass('Chord'):
                if prev_chord:
                    try:
                        # Check for V-IV progression (considered weak in traditional harmony)
                        if (prev_chord.root().name == 'G' and chord.root().name == 'F'):
                            self.errors.append({
                                'type': 'Weak Progression',
                                'measure': chord.measureNumber,
                                'description': 'V-IV progression detected (usually considered weak)'
                            })
                    except Exception as e:
                        logger.warning(f"Error analyzing chord progression: {str(e)}")
                prev_chord = chord
                
        except Exception as e:
            logger.error(f"Error in chord progression check: {str(e)}", exc_info=True)

    def check_cadences(self):
        """Verifies proper cadences"""
        if not self.score:
            return
            
        try:
            chordified = self.score.chordify()
            chords = list(chordified.recurse().getElementsByClass('Chord'))
            
            if len(chords) >= 2:
                final_chords = chords[-2:]
                try:
                    # Check for authentic cadence (V-I)
                    if not (final_chords[0].root().name == 'G' and final_chords[1].root().name == 'C'):
                        self.errors.append({
                            'type': 'Invalid Cadence',
                            'measure': final_chords[1].measureNumber,
                            'description': 'Phrase does not end with proper authentic cadence (V-I)'
                        })
                except Exception as e:
                    logger.warning(f"Error analyzing cadence: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in cadence check: {str(e)}", exc_info=True)

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
                'Parallel Fifths': 'Use contrary or oblique motion between voices',
                'Parallel Octaves': 'Use contrary or oblique motion between voices',
                'Large Leap': 'Consider stepwise motion or smaller intervals',
                'Voice Crossing': 'Keep voices within their designated ranges',
                'Weak Progression': 'Consider using stronger chord progressions like V-I',
                'Invalid Cadence': 'End the phrase with an authentic cadence (V-I)'
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
