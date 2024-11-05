from music21 import environment
import os
import logging
import matplotlib
matplotlib.use('Agg')  # Set the backend before any other matplotlib imports
import subprocess

logger = logging.getLogger(__name__)

def check_musescore_installation():
    """Check if MuseScore is properly installed and accessible"""
    try:
        result = subprocess.run(['which', 'mscore'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        
        result = subprocess.run(['which', 'musescore'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
            
        return None
    except Exception as e:
        logger.error(f"Error checking MuseScore installation: {str(e)}")
        return None

def configure_music21():
    """Configure music21 environment with proper paths for score visualization"""
    try:
        # Get music21 environment
        env = environment.Environment()
        
        # Check MuseScore installation
        musescore_path = check_musescore_installation()
        if not musescore_path:
            logger.warning("MuseScore not found in PATH")
            
            # Search in Nix store as fallback
            try:
                result = subprocess.run(['find', '/nix/store', '-name', 'mscore', '-type', 'f'], 
                                     capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    musescore_path = result.stdout.splitlines()[0]
                    logger.info(f"Found MuseScore in Nix store: {musescore_path}")
            except Exception as e:
                logger.error(f"Error searching Nix store: {str(e)}")
        
        if musescore_path:
            # Configure music21 environment
            env['musicxmlPath'] = musescore_path
            env['musescoreDirectPNGPath'] = musescore_path
            env.write()
            logger.info(f"Configured music21 with MuseScore path: {musescore_path}")
            
            # Set up matplotlib
            matplotlib.rcParams.update({
                'backend': 'Agg',
                'figure.max_open_warning': 50,
                'figure.dpi': 300,
                'savefig.dpi': 300
            })
            
            # Create necessary directories with proper permissions
            for directory in ['tmp', os.path.join('static', 'visualizations')]:
                os.makedirs(directory, exist_ok=True)
                os.chmod(directory, 0o755)
                logger.info(f"Created directory: {directory}")
            
            return True
            
        logger.warning("MuseScore not found in any standard locations")
        return False
        
    except Exception as e:
        logger.error(f"Error configuring music21: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    if configure_music21():
        print("Successfully configured music21 environment")
    else:
        print("Failed to configure music21 environment")
