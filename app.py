# app.py
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, session, jsonify
from werkzeug.utils import secure_filename
from harmony_checker import HarmonyAnalyzer, HarmonyError
from harmony_checker.report_generator import ReportGenerator
from harmony_checker.music_generator import MusicGenerator
from harmony_checker.midi_handler import MIDIHandler
from typing import Dict, Optional, Tuple, List
import os
import logging
import io
import xml.etree.ElementTree as ET
import magic
import matplotlib
matplotlib.use('Agg')  # Set backend before importing pyplot

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
ALLOWED_EXTENSIONS = {'musicxml', 'xml', 'mid', 'midi'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
ALLOWED_MIME_TYPES = {
    'application/xml',
    'text/xml',
    'application/musicxml',
    'application/x-musicxml',
    'audio/midi',
    'audio/x-midi'
}

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

# Initialize MusicGenerator
music_generator = MusicGenerator()

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

@app.route('/cleanup')
def cleanup():
    """Endpoint for cleaning up visualization files"""
    cleanup_visualizations()
    return '', 204

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_type_and_size(file) -> Tuple[bool, str]:
    """Validate file type and size"""
    try:
        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > MAX_FILE_SIZE:
            return False, f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024:.1f}MB"
        
        # Read the first chunk for MIME type detection
        chunk = file.read(2048)
        file.seek(0)
        
        mime = magic.from_buffer(chunk, mime=True)
        if mime not in ALLOWED_MIME_TYPES:
            return False, f"Invalid file type. Detected MIME type: {mime}"
            
        return True, ""
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        return False, "File validation failed"

def validate_musicxml_structure(file_path: str) -> Tuple[bool, str]:
    """Validate MusicXML file structure"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Check for required root elements
        if not any(tag in root.tag for tag in ['score-partwise', 'score-timewise']):
            return False, "Invalid MusicXML: Missing required root element"
            
        # Check for basic required elements
        required_elements = ['part-list', 'part']
        missing_elements = [elem for elem in required_elements if root.find(f".//{elem}") is None]
        
        if missing_elements:
            return False, f"Invalid MusicXML: Missing required elements: {', '.join(missing_elements)}"
            
        return True, ""
    except ET.ParseError as e:
        logger.error(f"MusicXML parsing error: {str(e)}")
        return False, f"XML parsing error: {str(e)}"
    except Exception as e:
        logger.error(f"MusicXML validation error: {str(e)}")
        return False, "Invalid or corrupted MusicXML file"

def analyze_file(file, filename: str) -> Optional[Dict]:
    """Analyze a single file and return results"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # Validate file type and size
        is_valid, error_message = validate_file_type_and_size(file)
        if not is_valid:
            raise ValueError(error_message)
            
        file.save(filepath)
        
        # Handle MIDI files
        if filename.lower().endswith(('.mid', '.midi')):
            midi_handler = MIDIHandler()
            success, musicxml_path, message = midi_handler.midi_to_musicxml(filepath)
            
            if not success:
                raise ValueError(f"MIDI conversion failed: {message}")
                
            # Create piano roll visualization
            piano_roll_path = os.path.join('static', 'visualizations', f'piano_roll_{os.path.splitext(filename)[0]}.png')
            success, message = midi_handler.create_piano_roll(filepath, piano_roll_path)
            
            if not success:
                logger.warning(f"Piano roll creation failed: {message}")
            
            # Get MIDI information
            midi_info = midi_handler.get_midi_info(filepath)
            
            # Update filepath to use converted MusicXML
            filepath = musicxml_path
        
        # Validate MusicXML structure
        is_valid, error_message = validate_musicxml_structure(filepath)
        if not is_valid:
            raise ValueError(error_message)
            
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
                'total_voices': len(analyzer.score.parts) if analyzer.score else 0,
                'midi_info': midi_info if 'midi_info' in locals() else None
            }
        }

        session['last_analysis'] = {
            'errors': error_dicts,
            'statistics': report['statistics']
        }

        result = {
            'filename': filename,
            'results': error_dicts,
            'report': report,
            'visualization_path': analyzer.visualization_path,
            'piano_roll_path': f'visualizations/piano_roll_{os.path.splitext(filename)[0]}.png' if 'piano_roll_path' in locals() else None
        }

        return result
    finally:
        # Clean up the uploaded file
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                logger.error(f"Failed to remove file {filepath}: {str(e)}")

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
            flash(f'Invalid file type for {file.filename}. Only MusicXML and MIDI files are allowed.', 'warning')
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
            flash(f'An unexpected error occurred while processing {file.filename}.', 'danger')

    if not analysis_results:
        flash('No valid files were processed successfully. Please check the file requirements and try again.', 'danger')
        return redirect(request.url)

    return render_template(
        'results.html',
        batch_results=analysis_results,
        has_errors=any(result['results'] for result in analysis_results)
    )

@app.route('/generate-music', methods=['POST'])
def generate_music():
    """Generate music using AI"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        style = data.get('style')
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
            
        result = music_generator.generate_music(prompt, style)
        
        if not result['success']:
            return jsonify({'error': result['error']}), 500
            
        # Store the generated music in the session
        session['generated_music'] = result['music_data']
        
        return jsonify({
            'success': True,
            'message': 'Music generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Music generation failed: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to generate music'}), 500

@app.route('/download-generated-music')
def download_generated_music():
    """Download the generated music file"""
    try:
        music_data = session.get('generated_music')
        if not music_data:
            flash('No generated music available. Please generate music first.', 'danger')
            return redirect(url_for('index'))
            
        return send_file(
            io.BytesIO(music_data.encode()),
            mimetype='audio/midi',
            as_attachment=True,
            download_name='generated_music.mid'
        )
        
    except Exception as e:
        logger.error(f"Music download failed: {str(e)}", exc_info=True)
        flash('Error downloading generated music.', 'danger')
        return redirect(url_for('index'))

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
