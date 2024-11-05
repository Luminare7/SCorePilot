from music21 import *
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import logging

logger = logging.getLogger(__name__)

class HarmonyAnalyzer:
    def __init__(self):
        self.score = None
        self.errors = []
        
    def load_score(self, musicxml_path):
        """Loads a score from MusicXML file"""
        try:
            self.score = converter.parse(musicxml_path)
            logger.debug(f"Successfully loaded score from {musicxml_path}")
        except Exception as e:
            logger.error(f"Error loading score: {str(e)}", exc_info=True)
            raise Exception(f"Failed to load score: {str(e)}")
        
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
        
    def get_pitch_from_element(self, element):
        """Helper method to get pitch from either Note or Chord"""
        try:
            if isinstance(element, note.Note):
                return element.pitch
            elif isinstance(element, chord.Chord):
                return element.root()  # Use root note for chords
            return None
        except Exception as e:
            logger.error(f"Error getting pitch: {str(e)}", exc_info=True)
            return None

    def check_parallel_fifths(self):
        """Checks for parallel fifths"""
        if not self.score:
            return
            
        try:
            parts = self.score.parts
            if len(parts) < 2:  # Need at least 2 voices to check parallels
                return
                
            # Use flatten() instead of flat
            notes1 = parts[0].flatten().notes
            notes2 = parts[1].flatten().notes
            
            for i in range(len(notes1) - 1):
                try:
                    # Get current and next notes/chords for both voices
                    curr_elem1 = notes1[i]
                    next_elem1 = notes1[i + 1]
                    curr_elem2 = notes2[i]
                    next_elem2 = notes2[i + 1]
                    
                    # Get pitches for both current and next elements
                    curr_pitch1 = self.get_pitch_from_element(curr_elem1)
                    next_pitch1 = self.get_pitch_from_element(next_elem1)
                    curr_pitch2 = self.get_pitch_from_element(curr_elem2)
                    next_pitch2 = self.get_pitch_from_element(next_elem2)
                    
                    if all([curr_pitch1, next_pitch1, curr_pitch2, next_pitch2]):
                        # Calculate intervals using pitches
                        curr_interval = interval.Interval(curr_pitch1, curr_pitch2)
                        next_interval = interval.Interval(next_pitch1, next_pitch2)
                        
                        if curr_interval.name == 'P5' and next_interval.name == 'P5':
                            self.errors.append({
                                'type': 'Parallel Fifths',
                                'measure': curr_elem1.measureNumber,
                                'description': 'Parallel fifth movement detected between voices'
                            })
                except Exception as e:
                    logger.warning(f"Error checking interval at position {i}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in parallel fifths check: {str(e)}", exc_info=True)
            raise Exception(f"Failed to check parallel fifths: {str(e)}")
    
    def check_parallel_octaves(self):
        """Checks for parallel octaves"""
        if not self.score:
            return
            
        try:
            parts = self.score.parts
            if len(parts) < 2:
                return
                
            notes1 = parts[0].flatten().notes
            notes2 = parts[1].flatten().notes
            
            for i in range(len(notes1) - 1):
                try:
                    curr_pitch1 = self.get_pitch_from_element(notes1[i])
                    next_pitch1 = self.get_pitch_from_element(notes1[i + 1])
                    curr_pitch2 = self.get_pitch_from_element(notes2[i])
                    next_pitch2 = self.get_pitch_from_element(notes2[i + 1])
                    
                    if all([curr_pitch1, next_pitch1, curr_pitch2, next_pitch2]):
                        curr_interval = interval.Interval(curr_pitch1, curr_pitch2)
                        next_interval = interval.Interval(next_pitch1, next_pitch2)
                        
                        if curr_interval.name == 'P8' and next_interval.name == 'P8':
                            self.errors.append({
                                'type': 'Parallel Octaves',
                                'measure': notes1[i].measureNumber,
                                'description': 'Parallel octave movement detected between voices'
                            })
                except Exception as e:
                    logger.warning(f"Error checking octave at position {i}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in parallel octaves check: {str(e)}", exc_info=True)
            raise Exception(f"Failed to check parallel octaves: {str(e)}")
    
    def check_voice_leading(self):
        """Checks voice leading rules"""
        if not self.score:
            return
            
        try:
            parts = self.score.parts
            for part in parts:
                notes = part.flatten().notes
                for i in range(len(notes) - 1):
                    try:
                        curr_pitch = self.get_pitch_from_element(notes[i])
                        next_pitch = self.get_pitch_from_element(notes[i + 1])
                        
                        if curr_pitch and next_pitch:
                            interval_size = abs(interval.Interval(curr_pitch, next_pitch).semitones)
                            
                            if interval_size > 12:  # Larger than an octave
                                self.errors.append({
                                    'type': 'Large Leap',
                                    'measure': notes[i].measureNumber,
                                    'description': f'Large melodic leap of {interval_size} semitones'
                                })
                    except Exception as e:
                        logger.warning(f"Error checking voice leading at position {i}: {str(e)}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error in voice leading check: {str(e)}", exc_info=True)
            raise Exception(f"Failed to check voice leading: {str(e)}")

    def check_chord_progressions(self):
        """Analyzes chord progressions"""
        if not self.score:
            return
            
        try:
            logger.debug("Starting chord progression analysis")
            
            # First try to get chords directly
            chords = self.score.flatten().getElementsByClass('Chord')
            logger.debug(f"Found {len(chords)} direct chords")
            
            # If no chords found, try to create them from the piano part
            if not chords:
                logger.debug("No direct chords found, attempting to chordify score")
                chords = self.score.chordify().flatten().getElementsByClass('Chord')
                logger.debug(f"Found {len(chords)} chords after chordifying")
            
            prev_chord = None
            for chord in chords:
                if prev_chord:
                    if self._is_dominant(prev_chord) and self._is_subdominant(chord):
                        self.errors.append({
                            'type': 'Weak Progression',
                            'measure': chord.measureNumber,
                            'description': 'V-IV progression detected'
                        })
                        logger.debug(f"Detected weak progression in measure {chord.measureNumber}")
                prev_chord = chord
                    
        except Exception as e:
            logger.error(f"Error in chord progression check: {str(e)}", exc_info=True)
            raise Exception(f"Failed to check chord progressions: {str(e)}")

    def check_cadences(self):
        """Verifies proper cadences"""
        if not self.score:
            return
            
        try:
            # First try to get chords directly
            chords = self.score.flatten().getElementsByClass('Chord')
            
            # If no chords found, try to create them from the piano part
            if not chords:
                chords = self.score.chordify().flatten().getElementsByClass('Chord')
            
            # Get the last two chords
            final_chords = list(chords)[-2:]
            
            if len(final_chords) >= 2:
                penultimate = final_chords[0]
                final = final_chords[1]
                
                if not self._is_valid_cadence(penultimate, final):
                    self.errors.append({
                        'type': 'Invalid Cadence',
                        'measure': final.measureNumber,
                        'description': 'Phrase does not end with proper cadence'
                    })
                    
        except Exception as e:
            logger.error(f"Error in cadence check: {str(e)}", exc_info=True)
            raise Exception(f"Failed to check cadences: {str(e)}")

    def _is_dominant(self, chord_elem):
        """Helper to check if chord is dominant"""
        try:
            root = chord_elem.root()
            if root and root.name == 'G':  # Assuming C major for simplicity
                return True
            return False
        except Exception:
            return False
    
    def _is_subdominant(self, chord_elem):
        """Helper to check if chord is subdominant"""
        try:
            root = chord_elem.root()
            if root and root.name == 'F':  # Assuming C major for simplicity
                return True
            return False
        except Exception:
            return False
    
    def _is_valid_cadence(self, penultimate, final):
        """Helper to check if cadence is valid"""
        try:
            return self._is_dominant(penultimate) and final.root().name == 'C'
        except Exception:
            return False

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
            
        try:
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
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate report: {str(e)}")

    def generate_pdf_report(self):
        """Generates a PDF report of the analysis"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate PDF report: {str(e)}")
