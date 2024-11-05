import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from score_visualizer import ScoreVisualizer
from harmony_checker import HarmonyAnalyzer
from music21 import environment, converter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Ensure required directories exist
os.makedirs(os.path.join('static', 'visualizations'), exist_ok=True)
os.makedirs(os.path.join('static', 'temp'), exist_ok=True)

# Set proper permissions
try:
    os.chmod(os.path.join('static', 'visualizations'), 0o755)
    os.chmod(os.path.join('static', 'temp'), 0o755)
except Exception as e:
    logger.warning(f"Could not set directory permissions: {str(e)}")

# Initialize ScoreVisualizer
visualizer = None
try:
    visualizer = ScoreVisualizer()
    logger.info("Score visualizer initialized successfully")
except Exception as e:
    logger.error(f"Error initializing score visualizer: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not visualizer:
            flash('Score visualization system is not properly initialized. Please try again later.', 'error')
            return redirect(request.url)

        try:
            if 'file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(request.url)

            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)

            # Save uploaded file to temporary location
            temp_dir = os.path.join('static', 'temp')
            temp_path = os.path.join(temp_dir, file.filename)
            file.save(temp_path)

            try:
                # Create analyzer and process file
                analyzer = HarmonyAnalyzer()
                analyzer.load_score(temp_path)

                # Generate visualization
                visualization_path = visualizer.generate_visualization(analyzer.score)
                if not visualization_path:
                    logger.warning("Failed to generate score visualization")
                    flash('Score visualization could not be generated. Showing analysis results without visual representation.', 'warning')
                else:
                    logger.info(f"Successfully generated visualization: {visualization_path}")

                # Analyze score
                results = analyzer.analyze()
                report = analyzer.generate_report()

                return render_template('results.html',
                                    results=results,
                                    report=report,
                                    visualization_path=visualization_path)
            finally:
                # Cleanup temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            logger.error(f"Error processing upload: {str(e)}", exc_info=True)
            flash('Error processing file. Please try again.', 'error')
            return redirect(request.url)

    return render_template('index.html')

@app.route('/download_pdf')
def download_pdf():
    flash('PDF download feature coming soon', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
