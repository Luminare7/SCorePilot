# visualization.py
import os
import uuid
import logging
from music21 import converter
from .utils import ensure_directory

logger = logging.getLogger(__name__)

def generate_visualization(score) -> str:
    """Generates visual representation of the score"""
    try:
        if not score:
            logger.warning("No score loaded for visualization")
            return None

        vis_dir = os.path.join('static', 'visualizations')
        ensure_directory(vis_dir)

        filename = f"score_{uuid.uuid4()}.png"
        filepath = os.path.join(vis_dir, filename)

        # Check if MuseScore is installed
        try:
            from music21.configure import Environment
            env = Environment()
            if env['musescoreDirectPNGPath'] is None:
                logger.warning("MuseScore not found - skipping visualization")
                return None
        except Exception as e:
            logger.warning(f"Could not check MuseScore installation: {e}")
            return None

        # Try different visualization methods
        try:
            logger.debug("Attempting score.show() method")
            score.show('musicxml.png', fp=filepath)
            logger.debug("score.show() method succeeded")
        except Exception as e1:
            logger.debug(f"show() method failed: {e1}")
            try:
                logger.debug("Attempting score.write() method")
                score.write('musicxml.png', fp=filepath)
                logger.debug("score.write() method succeeded")
            except Exception as e2:
                logger.debug(f"write() method failed: {e2}")
                try:
                    logger.debug("Attempting alternative visualization method")
                    if len(score.parts) > 0:
                        score.parts[0].write('musicxml.png', fp=filepath)
                    else:
                        score.measures(0, None).write('musicxml.png', fp=filepath)
                    logger.debug("Alternative visualization method succeeded")
                except Exception as e3:
                    logger.debug(f"All visualization methods failed: {e3}")
                    return None

        if os.path.exists(filepath):
            os.chmod(filepath, 0o644)  # Set file permissions
            logger.debug(f"Successfully generated visualization at {filepath}")
            return os.path.join('visualizations', filename)

        logger.warning("Visualization file was not created")
        return None

    except Exception as e:
        logger.error(f"Visualization generation failed: {str(e)}")
        return None