import os
import uuid
import logging
from music21 import *
import matplotlib.pyplot as plt
from PIL import Image
import io
import glob

logger = logging.getLogger(__name__)

class ScoreVisualizer:
    def __init__(self, output_dir='static/visualizations'):
        self.output_dir = output_dir
        
        # Ensure directory exists with proper permissions
        try:
            os.makedirs(output_dir, exist_ok=True)
            os.chmod(output_dir, 0o755)  # rwxr-xr-x permissions
            logger.info(f"Visualization directory {output_dir} created with proper permissions")
        except Exception as e:
            logger.error(f"Failed to setup visualization directory: {str(e)}")
            raise
        
        # Configure music21 environment
        try:
            # Find musescore and lilypond in Nix store
            musescore_paths = glob.glob('/nix/store/*/bin/mscore') + glob.glob('/nix/store/*/bin/musescore')
            lilypond_paths = glob.glob('/nix/store/*/bin/lilypond')
            
            if musescore_paths:
                logger.info(f"Found MuseScore at: {musescore_paths[0]}")
                environment.set('musicxmlPath', musescore_paths[0])
            else:
                logger.warning("MuseScore not found in expected locations")
            
            if lilypond_paths:
                logger.info(f"Found LilyPond at: {lilypond_paths[0]}")
                environment.set('lilypondPath', lilypond_paths[0])
            else:
                logger.warning("LilyPond not found in expected locations")
                
            logger.info("Music21 environment paths configured successfully")
        except Exception as e:
            logger.warning(f"Could not set music21 environment paths: {str(e)}")

    def generate_visualization(self, score):
        """Generate multiple visualization attempts and return the best one"""
        if not score:
            logger.error("No score provided for visualization")
            return None

        methods = [
            self._direct_score_show,      # Try direct score.show() first
            self._create_score_plot,      # Traditional score visualization
            self._create_piano_roll,      # Piano roll visualization
            self._create_pitch_space_plot, # Pitch space visualization
            self._create_basic_representation  # Basic fallback
        ]

        for method in methods:
            try:
                logger.info(f"Attempting visualization using {method.__name__}")
                path = method(score)
                if path:
                    logger.info(f"Successfully generated visualization using {method.__name__}")
                    return path
            except Exception as e:
                logger.error(f"Visualization method {method.__name__} failed: {str(e)}", exc_info=True)
                continue

        logger.error("All visualization methods failed")
        return None

    def _direct_score_show(self, score):
        """Attempt direct score visualization using music21's show() method"""
        filename = f"score_direct_{uuid.uuid4()}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            logger.info("Attempting direct score visualization")
            score.show('musicxml.png', fp=filepath)
            
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                self._optimize_image(filepath)
                return os.path.join('visualizations', filename)
            else:
                logger.warning("Direct score visualization produced no output")
                return None
                
        except Exception as e:
            logger.error(f"Direct score visualization failed: {str(e)}", exc_info=True)
            return None

    def _create_score_plot(self, score):
        """Create traditional score visualization using music21's plotting"""
        filename = f"score_{uuid.uuid4()}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Try lilypond visualization
            logger.info("Attempting LilyPond visualization")
            score.write('lily.png', fp=filepath)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                self._optimize_image(filepath)
                return os.path.join('visualizations', filename)
        except Exception as e:
            logger.error(f"Traditional score rendering failed: {str(e)}", exc_info=True)
            return None

    def _create_piano_roll(self, score):
        """Create piano roll visualization"""
        filename = f"piano_roll_{uuid.uuid4()}.png"
        filepath = os.path.join(self.output_dir, filename)

        try:
            plt.figure(figsize=(15, 10))
            plot = graph.plot.HorizontalBarPitchSpaceOffset(score)
            plot.run()
            plot.figure.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            self._optimize_image(filepath)
            return os.path.join('visualizations', filename)
        except Exception as e:
            plt.close()
            logger.error(f"Piano roll visualization failed: {str(e)}", exc_info=True)
            return None

    def _create_pitch_space_plot(self, score):
        """Create pitch space visualization"""
        filename = f"pitch_space_{uuid.uuid4()}.png"
        filepath = os.path.join(self.output_dir, filename)

        try:
            plt.figure(figsize=(15, 10))
            plot = graph.plot.ScatterPitchSpaceQuarterLength(score)
            plot.run()
            plot.figure.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            self._optimize_image(filepath)
            return os.path.join('visualizations', filename)
        except Exception as e:
            plt.close()
            logger.error(f"Pitch space visualization failed: {str(e)}", exc_info=True)
            return None

    def _create_basic_representation(self, score):
        """Create basic visual representation as final fallback"""
        filename = f"basic_{uuid.uuid4()}.png"
        filepath = os.path.join(self.output_dir, filename)

        try:
            plt.figure(figsize=(15, 10))
            for i, part in enumerate(score.parts):
                pitches = []
                for n in part.flat.notes:
                    if hasattr(n, 'pitch'):
                        pitches.append(n.pitch.midi)
                    elif hasattr(n, 'pitches') and len(n.pitches) > 0:
                        pitches.append(n.pitches[0].midi)
                
                if pitches:
                    times = range(len(pitches))
                    plt.plot(times, pitches, 'o-', label=f'Part {i+1}')

            plt.grid(True)
            plt.legend()
            plt.ylabel('MIDI Pitch')
            plt.xlabel('Note Index')
            plt.title('Basic Score Representation')
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            self._optimize_image(filepath)
            return os.path.join('visualizations', filename)
        except Exception as e:
            plt.close()
            logger.error(f"Basic representation failed: {str(e)}", exc_info=True)
            return None

    def _optimize_image(self, filepath):
        """Optimize the image file size while maintaining quality"""
        try:
            with Image.open(filepath) as img:
                img.save(filepath, optimize=True, quality=85)
        except Exception as e:
            logger.error(f"Failed to optimize image {filepath}: {str(e)}")
