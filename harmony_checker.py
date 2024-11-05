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

    # [Rest of the class implementation remains the same...]
