import os
import uuid
import logging
from music21 import *
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend before importing pyplot
import matplotlib.pyplot as plt
from music21 import environment, graph, converter, interval
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

class HarmonyAnalyzer:
    def __init__(self):
        self.score = None
        self.errors = []
        self._setup_visualization_environment()
        
    def _setup_visualization_environment(self):
        """Setup visualization environment and verify dependencies"""
        try:
            # Configure matplotlib with optimal settings for music visualization
            matplotlib.use('Agg')
            matplotlib.rcParams.update({
                'figure.max_open_warning': 50,
                'figure.dpi': 300,
                'savefig.dpi': 300,
                'figure.figsize': (12, 6),
                'figure.autolayout': True,
                'agg.path.chunksize': 20000
            })
            
            # Ensure visualization directories exist with proper permissions
            dirs_to_create = [
                os.path.join('static', 'visualizations'),
                os.path.join('tmp', 'score_renders'),
                'tmp'
            ]
            
            for directory in dirs_to_create:
                os.makedirs(directory, exist_ok=True)
                os.chmod(directory, 0o755)
                logger.info(f"Ensured directory exists with proper permissions: {directory}")
            
            # Verify and configure music21 environment
            env = environment.Environment()
            musescore_path = self._find_musescore()
            if musescore_path:
                env['musicxmlPath'] = musescore_path
                env['musescoreDirectPNGPath'] = musescore_path
                env.write()
                logger.info(f"MuseScore path configured: {musescore_path}")
            else:
                logger.warning("MuseScore path not configured - will use alternative visualization methods")
            
        except Exception as e:
            logger.error(f"Error setting up visualization environment: {str(e)}")
            raise

    def _find_musescore(self):
        """Find MuseScore executable in the system"""
        try:
            # Check common paths first
            common_names = ['mscore', 'musescore']
            for name in common_names:
                result = subprocess.run(['which', name], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()

            # Search in Nix store as fallback
            result = subprocess.run(
                ['find', '/nix/store', '-name', 'mscore', '-type', 'f'],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.splitlines()[0]

            return None
        except Exception as e:
            logger.error(f"Error finding MuseScore: {str(e)}")
            return None

    def load_score(self, musicxml_path):
        """Loads a score from MusicXML file"""
        try:
            self.score = converter.parse(musicxml_path)
            logger.info(f"Successfully loaded score from {musicxml_path}")
        except Exception as e:
            logger.error(f"Error loading score: {str(e)}", exc_info=True)
            raise Exception(f"Failed to load score: {str(e)}")

    def analyze_score(self):
        """Analyzes the loaded score for harmony errors"""
        try:
            if not self.score:
                raise ValueError("No score loaded for analysis")
            
            self.errors = []
            measures = self.score.measureOffsetMap()
            measure_numbers = sorted(int(measure_num) for measure_num in measures.keys())
            
            for measure_num in measure_numbers:
                try:
                    measure = self.score.measure(measure_num)
                    if not measure:
                        continue

                    self._analyze_voice_leading(measure, measure_num)
                    self._analyze_harmony(measure, measure_num)
                        
                except Exception as me:
                    logger.warning(f"Error analyzing measure {measure_num}: {str(me)}")
                    continue
                    
            return self.errors
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            raise

    def generate_visualization(self):
        """Generate a visualization of the score using multiple methods with fallbacks"""
        if not self.score:
            logger.warning("No score available for visualization")
            return None
            
        # Generate unique filename
        filename = f"score_{uuid.uuid4()}.png"
        filepath = os.path.join('static', 'visualizations', filename)
        
        visualization_methods = [
            ('piano_roll', self._try_piano_roll_visualization),
            ('pitch_space', self._try_pitch_space_visualization),
            ('direct', self._try_direct_visualization),
            ('simple', self._try_simple_visualization)
        ]
        
        successful_method = None
        for method_name, method in visualization_methods:
            try:
                logger.info(f"Attempting {method_name} visualization...")
                if method(filepath):
                    logger.info(f"Successfully generated {method_name} visualization")
                    successful_method = method_name
                    break
            except Exception as e:
                logger.error(f"{method_name} visualization failed: {str(e)}")
                continue
        
        if successful_method:
            logger.info(f"Final visualization generated using {successful_method} method")
            relative_path = os.path.join('visualizations', filename)
            if os.path.exists(filepath):
                os.chmod(filepath, 0o644)
                return relative_path
        
        logger.error("All visualization methods failed")
        return None

    def _try_piano_roll_visualization(self, filepath):
        """Generate enhanced piano roll visualization"""
        try:
            plt.figure(figsize=(12, 8))
            plt.clf()  # Clear any existing plots
            
            # Extract note events
            notes = []
            for n in self.score.flatten().notesAndRests:
                if n.isNote:
                    notes.append((n.offset, n.duration.quarterLength, n.pitch.midi))
                elif n.isChord:
                    for pitch in n.pitches:
                        notes.append((n.offset, n.duration.quarterLength, pitch.midi))
            
            if not notes:
                return False
                
            # Create piano roll
            for start, duration, pitch in notes:
                plt.hlines(pitch, start, start + duration, color='blue', alpha=0.5, linewidth=5)
                
            plt.title("Piano Roll Visualization", pad=20)
            plt.ylabel("MIDI Pitch")
            plt.xlabel("Time (Quarter Notes)")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save with high quality
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white', format='png')
            plt.close()
            
            return os.path.exists(filepath)
            
        except Exception as e:
            logger.error(f"Piano roll visualization failed: {str(e)}")
            plt.close()
            return False

    def _try_direct_visualization(self, filepath):
        """Attempt direct score visualization using MuseScore"""
        try:
            # Create a temporary MusicXML file
            with tempfile.NamedTemporaryFile(suffix='.musicxml', delete=False) as tmp:
                temp_xml = tmp.name
                
            # Save the score as MusicXML
            self.score.write('musicxml', temp_xml)
            
            # Try using MuseScore directly
            musescore_path = self._find_musescore()
            if musescore_path:
                try:
                    subprocess.run(
                        [musescore_path, '-T', '0', '-o', filepath, temp_xml],
                        check=True, capture_output=True, timeout=30
                    )
                    if os.path.exists(filepath):
                        os.chmod(filepath, 0o644)
                        os.unlink(temp_xml)
                        return True
                except Exception as e:
                    logger.warning(f"MuseScore direct conversion failed: {str(e)}")
            
            # Fallback to music21's built-in converter
            self.score.write('musicxml.png', fp=filepath)
            if os.path.exists(filepath):
                os.chmod(filepath, 0o644)
                os.unlink(temp_xml)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Direct visualization failed: {str(e)}")
            return False

    def _try_pitch_space_visualization(self, filepath):
        """Generate enhanced pitch space visualization"""
        try:
            plt.figure(figsize=(12, 8))
            plt.clf()  # Clear any existing plots
            
            # Create pitch space plot
            plot = graph.plot.ScatterPitchSpaceQuarterLength(self.score)
            plot.run()
            
            plt.title("Pitch Space Visualization", pad=20)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save with high quality
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white', format='png')
            plt.close()
            
            return os.path.exists(filepath)
            
        except Exception as e:
            logger.error(f"Pitch space visualization failed: {str(e)}")
            plt.close()
            return False

    def _try_simple_visualization(self, filepath):
        """Generate simplified score visualization as last resort"""
        try:
            plt.figure(figsize=(12, 8))
            plt.clf()  # Clear any existing plots
            
            # Create a simple representation
            notes = self.score.flatten().notesAndRests
            pitches = []
            times = []
            
            for n in notes:
                if n.isNote:
                    pitches.append(n.pitch.midi)
                    times.append(n.offset)
                elif n.isChord:
                    for p in n.pitches:
                        pitches.append(p.midi)
                        times.append(n.offset)
            
            if not pitches:
                return False
                
            plt.scatter(times, pitches, alpha=0.6, c='blue')
            plt.title("Simple Score Overview", pad=20)
            plt.ylabel("MIDI Pitch")
            plt.xlabel("Time (Quarter Notes)")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save with high quality
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white', format='png')
            plt.close()
            
            return os.path.exists(filepath)
            
        except Exception as e:
            logger.error(f"Simple visualization failed: {str(e)}")
            plt.close()
            return False

    def _analyze_voice_leading(self, measure, measure_num):
        """Analyze voice leading in the measure"""
        try:
            # Get all chords in the measure
            chords = measure.recurse().getElementsByClass('Chord')
            if len(chords) < 2:
                return  # Need at least 2 chords for voice leading analysis

            for i in range(len(chords) - 1):
                chord1, chord2 = chords[i], chords[i + 1]
                
                # Check for parallel fifths/octaves
                intervals1 = [interval.Interval(n1, n2) for n1, n2 in zip(chord1.notes, chord2.notes)]
                for int1, int2 in zip(intervals1[:-1], intervals1[1:]):
                    if int1.simpleName == int2.simpleName and int1.name in ['P5', 'P8']:
                        self.errors.append({
                            'type': 'Parallel Motion',
                            'measure': measure_num,
                            'description': f'Parallel {int1.niceName} found between voices'
                        })

                # Check for voice crossing
                for v1_idx, v2_idx in [(i, j) for i in range(len(chord1.notes)) for j in range(i+1, len(chord1.notes))]:
                    if chord1.notes[v1_idx].pitch > chord1.notes[v2_idx].pitch and \
                       chord2.notes[v1_idx].pitch < chord2.notes[v2_idx].pitch:
                        self.errors.append({
                            'type': 'Voice Crossing',
                            'measure': measure_num,
                            'description': 'Voice crossing detected between parts'
                        })

        except Exception as e:
            logger.warning(f"Voice leading analysis error in measure {measure_num}: {str(e)}")

    def _analyze_harmony(self, measure, measure_num):
        """Analyze harmony in the measure"""
        try:
            # Analyze chords in the measure
            chords = measure.recurse().getElementsByClass('Chord')
            
            for chord in chords:
                # Check for dissonant intervals
                intervals = [interval.Interval(n1, n2) 
                           for i, n1 in enumerate(chord.notes) 
                           for n2 in chord.notes[i+1:]]
                
                dissonant_intervals = [i for i in intervals 
                                     if i.simpleName in ['A4', 'd5', 'M7', 'm7', 'M2', 'm2']]
                
                if dissonant_intervals:
                    self.errors.append({
                        'type': 'Dissonant Harmony',
                        'measure': measure_num,
                        'description': f'Dissonant intervals found: {[i.niceName for i in dissonant_intervals]}'
                    })
                
                # Check for incomplete triads
                if len(chord.pitches) >= 3:
                    chord_type = chord.commonName
                    if 'incomplete' in chord_type.lower():
                        self.errors.append({
                            'type': 'Incomplete Chord',
                            'measure': measure_num,
                            'description': f'Incomplete chord found: {chord_type}'
                        })

        except Exception as e:
            logger.warning(f"Harmony analysis error in measure {measure_num}: {str(e)}")

    def generate_pdf_report(self):
        """Generate PDF report of analysis results"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            story.append(Paragraph("Harmony Analysis Report", styles['Title']))
            story.append(Spacer(1, 12))
            
            # Summary
            if self.errors:
                story.append(Paragraph(f"Total Errors Found: {len(self.errors)}", styles['Heading2']))
            else:
                story.append(Paragraph("No errors found in the analysis.", styles['Heading2']))
            
            story.append(Spacer(1, 12))
            
            # Detailed Errors
            if self.errors:
                story.append(Paragraph("Detailed Analysis", styles['Heading2']))
                for error in self.errors:
                    error_text = f"Measure {error['measure']}: {error['type']}\n{error['description']}"
                    story.append(Paragraph(error_text, styles['Normal']))
                    story.append(Spacer(1, 6))
            
            # Build PDF
            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise