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
        """Generates visual representation of the score"""
        try:
            if not self.score:
                logger.warning("No score loaded for visualization")
                return None
                
            # Ensure directory exists with proper permissions
            vis_dir = os.path.join('static', 'visualizations')
            os.makedirs(vis_dir, exist_ok=True)
            os.chmod(vis_dir, 0o755)  # Set directory permissions
            
            # Generate unique filename
            filename = f"score_{uuid.uuid4()}.png"
            filepath = os.path.join(vis_dir, filename)
            
            # Try different visualization methods
            try:
                # Method 1: Direct PNG export
                logger.debug("Attempting direct PNG export")
                self.score.write('png', fp=filepath)
            except Exception as e1:
                logger.warning(f"Direct PNG export failed: {e1}")
                try:
                    # Method 2: Convert to stream first
                    logger.debug("Attempting stream-based PNG export")
                    flattened = self.score.flatten()
                    flattened.write('png', fp=filepath)
                except Exception as e2:
                    logger.warning(f"Stream PNG export failed: {e2}")
                    try:
                        # Method 3: Try specific part visualization
                        logger.debug("Attempting part-based visualization")
                        for part in self.score.parts:
                            part.write('png', fp=filepath)
                            if os.path.exists(filepath):
                                break
                    except Exception as e3:
                        logger.error(f"All visualization methods failed: {e3}")
                        return None
                
            # Verify file exists and is readable
            if os.path.exists(filepath):
                os.chmod(filepath, 0o644)  # Set file permissions
                logger.debug(f"Successfully generated visualization at {filepath}")
                return os.path.join('visualizations', filename)
                
            return None
        except Exception as e:
            logger.error(f"Visualization generation failed: {str(e)}")
            return None

    # ... [rest of the class implementation remains the same]
