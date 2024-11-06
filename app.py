# app.py
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, session
from werkzeug.utils import secure_filename
from harmony_checker import HarmonyAnalyzer, HarmonyError
from harmony_checker.report_generator import ReportGenerator
import os
import logging
import io
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'harmony_checker_secret_key')

# Configure upload settings
UPLOAD_FOLDER = 'tmp'
ALLOWED_EXTENSIONS = {'musicxml', 'xml'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

# Initialize directories with proper error handling
required_dirs = [UPLOAD_FOLDER, os.path.join('static', 'visualizations')]
for directory in required_dirs:
    try:
        os.makedirs(directory, exist_ok=True)
        os.chmod(directory, 0o755)
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {str(e)}")
        raise

app.config.update(
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH=MAX_FILE_SIZE,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

@contextmanager
def safe_file_handler(filepath: str):
    """Context manager for safe file handling"""
    try:
        yield
    finally:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                logger.error(f"Failed to remove file {filepath}: {str(e)}")

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_musicxml(file_path: str) -> bool:
    """Validate MusicXML file structure"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        return any(tag in root.tag for tag in ['score-partwise', 'score-timewise'])
    except (ET.ParseError, Exception) as e:
        logger.error(f"MusicXML validation error for {file_path}: {str(e)}")
        return False

def cleanup_visualizations() -> None:
    """Clean up visualization files"""
    vis_dir = os.path.join('static', 'visualizations')
    try:
        for file in os.listdir(vis_dir):
            file_path = os.path.join(vis_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        logger.debug("Visualization cleanup completed")
    except Exception as e:
        logger.error(f"Visualization cleanup failed: {str(e)}")

def analyze_file(file, filename: str) -> Optional[Dict]:
    """Analyze a single file and return results"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    with safe_file_handler(filepath):
        file.save(filepath)

        if not is_valid_musicxml(filepath):
            raise ValueError("Invalid or corrupted MusicXML file")

        analyzer = HarmonyAnalyzer()
        analyzer.load_score(filepath)
        errors = analyzer.analyze()

        error_dicts = [{
            'type': error.type,
            'measure': error.measure,
            'description': error.description,
            'severity': error.severity,
            'voice1': error.voice1,
            'voice2': error.voice2
        } for error in errors]

        report = {
            'total_errors': len(errors),
            'errors_by_severity': {
                'high': sum(1 for e in errors if e.severity == 'high'),
                'medium': sum(1 for e in errors if e.severity == 'medium'),
                'low': sum(1 for e in errors if e.severity == 'low')
            },
            'statistics': {
                'measures_analyzed': len(analyzer.score.measures(0, None)) if analyzer.score else 0,
                'key': str(analyzer.key) if analyzer.key else 'Unknown',
                'total_voices': len(analyzer.score.parts) if analyzer.score else 0
            }
        }

        session['last_analysis'] = {
            'errors': error_dicts,
            'statistics': report['statistics']
        }

        return {
            'filename': filename,
            'results': error_dicts,
            'report': report,
            'visualization_path': analyzer.visualization_path
        }

@app.route('/cleanup')
def cleanup():
    """Endpoint for cleaning up visualization files"""
    cleanup_visualizations()
    return '', 204

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route for file upload and analysis"""
    if request.method == 'GET':
        cleanup_visualizations()
        return render_template('index.html')

    logger.debug("Processing file upload request")
    cleanup_visualizations()

    if 'file' not in request.files:
        flash('No file selected', 'danger')
        return redirect(request.url)

    files = request.files.getlist('file')
    if not files or all(file.filename == '' for file in files):
        flash('Please select at least one file to upload.', 'danger')
        return redirect(request.url)

    analysis_results = []

    for file in files:
        if not allowed_file(file.filename):
            flash(f'Invalid file type for {file.filename}. Skipping.', 'warning')
            continue

        try:
            filename = secure_filename(file.filename)
            result = analyze_file(file, filename)
            if result:
                analysis_results.append(result)
        except ValueError as e:
            flash(f'Error with {file.filename}: {str(e)}', 'warning')
        except Exception as e:
            logger.error(f"Error processing {file.filename}: {str(e)}", exc_info=True)
            flash(f'Error processing {file.filename}. Skipping.', 'warning')

    if not analysis_results:
        flash('No valid files were processed successfully.', 'danger')
        return redirect(request.url)

    return render_template(
        'results.html',
        batch_results=analysis_results,
        has_errors=any(result['results'] for result in analysis_results)
    )

@app.route('/download_pdf')
def download_pdf():
    """Generate and download PDF report"""
    try:
        analysis_data = session.get('last_analysis')
        if not analysis_data:
            flash('No analysis results available. Please analyze a score first.', 'danger')
            return redirect(url_for('index'))

        pdf_content = ReportGenerator.generate_pdf_report(
            analysis_data['errors'],
            analysis_data['statistics']
        )

        return send_file(
            io.BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='harmony_analysis_report.pdf'
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}", exc_info=True)
        flash('Error generating PDF report. Please try analyzing the score again.', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

# main.py
from app import app
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    app.run(host=host, port=port)