import os
import sys
import logging
from app import create_app, check_port_available, configure_music21

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist with proper permissions"""
    directories = [
        'tmp',
        os.path.join('static', 'visualizations'),
        os.path.join('tmp', 'score_renders')
    ]
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            os.chmod(directory, 0o755)
            logger.info(f"Created directory: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {str(e)}")
            raise

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port"""
    try:
        # Always try port 5000 first for consistency
        if check_port_available(5000):
            return 5000
            
        # If port 5000 is not available, try others
        for port in range(start_port + 1, start_port + max_attempts):
            if check_port_available(port):
                return port
                
        raise RuntimeError(f"No available ports found between {start_port} and {start_port + max_attempts - 1}")
    except Exception as e:
        logger.error(f"Error finding available port: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Ensure directories exist first
        ensure_directories()
        
        # Configure music21 environment
        logger.info("Configuring music21 environment...")
        if not configure_music21():
            logger.warning("Music21 environment not fully configured - visualization features may be limited")
        
        # Find an available port
        port = find_available_port()
        logger.info(f"Found available port: {port}")
        
        # Create and configure Flask app
        logger.info("Creating Flask application...")
        app = create_app()
        
        # Run the Flask app
        logger.info(f"Starting Flask application on port {port}...")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            use_reloader=False  # Disable reloader to maintain port consistency
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        sys.exit(1)
