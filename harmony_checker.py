import os
import uuid
from music21 import *
from music21 import environment
from music21 import graph
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

    def generate_visualization(self):
        """Generate a visualization of the score using multiple methods"""
        try:
            if not self.score:
                logger.debug("No score available for visualization")
                return None
                
            # Ensure visualization directory exists with proper permissions
            vis_dir = os.path.join('static', 'visualizations')
            os.makedirs(vis_dir, exist_ok=True)
            os.chmod(vis_dir, 0o755)  # Set directory permissions
            
            # Generate unique filename
            filename = f"score_{uuid.uuid4()}.png"
            filepath = os.path.join(vis_dir, filename)
            
            # Method 1: Try direct score visualization using musescore
            try:
                logger.debug("Attempting direct score visualization with musescore")
                # Convert the score to stream for better compatibility
                flat_score = self.score.stripTies().flatten()
                # Use musescore to render the score
                flat_score.write('musicxml.png', fp=filepath)
                if os.path.exists(filepath):
                    os.chmod(filepath, 0o644)  # Set file permissions
                    logger.debug(f"Successfully generated visualization at {filepath}")
                    return os.path.join('visualizations', filename)
            except Exception as e1:
                logger.debug(f"Direct visualization failed: {e1}")
                
                # Method 2: Try piano roll visualization
                try:
                    logger.debug("Attempting piano roll visualization")
                    # Create a piano roll plot
                    plot = graph.plot.HorizontalBarPitchSpaceOffset(self.score)
                    plot.run()
                    plot.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                    if os.path.exists(filepath):
                        os.chmod(filepath, 0o644)
                        logger.debug(f"Successfully generated piano roll at {filepath}")
                        return os.path.join('visualizations', filename)
                except Exception as e2:
                    logger.debug(f"Piano roll visualization failed: {e2}")
                    
                    # Method 3: Try basic pitch space visualization
                    try:
                        logger.debug("Attempting basic pitch space visualization")
                        plot = graph.plot.ScatterPitchSpaceQuarterLength(self.score)
                        plot.run()
                        plot.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                        if os.path.exists(filepath):
                            os.chmod(filepath, 0o644)
                            logger.debug(f"Successfully generated basic plot at {filepath}")
                            return os.path.join('visualizations', filename)
                    except Exception as e3:
                        logger.debug(f"Basic visualization failed: {e3}")
                        
                        # Method 4: Try creating a simple representation
                        try:
                            logger.debug("Attempting simple representation")
                            plot = graph.plot.PlotStream(self.score)
                            plot.run()
                            plot.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                            if os.path.exists(filepath):
                                os.chmod(filepath, 0o644)
                                logger.debug(f"Successfully generated simple plot at {filepath}")
                                return os.path.join('visualizations', filename)
                        except Exception as e4:
                            logger.debug(f"Simple representation failed: {e4}")
                        
            logger.error("All visualization methods failed")
            return None
        except Exception as e:
            logger.error(f"Error in visualization: {str(e)}")
            return None

    # ... [rest of the class implementation remains the same]
