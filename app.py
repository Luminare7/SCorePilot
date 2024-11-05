import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, Response
from werkzeug.utils import secure_filename
from harmony_checker import HarmonyAnalyzer
import io
import xml.etree.ElementTree as ET
from configure_music21 import configure_music21
import socket

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'harmony_checker_secret_key')

    # Configure upload settings
    UPLOAD_FOLDER = 'tmp'
    ALLOWED_EXTENSIONS = {'musicxml', 'xml'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

    # Ensure required directories exist with proper permissions
    for directory in [UPLOAD_FOLDER, os.path.join('static', 'visualizations')]:
        try:
            os.makedirs(directory, exist_ok=True)
            os.chmod(directory, 0o755)
            logger.info(f"Created directory: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {str(e)}")
            raise

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

    # Initialize the global analyzer
    current_analyzer = None

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def is_valid_musicxml(file_path):
        """Validate if the file is a well-formed MusicXML file"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # More specific validation for MusicXML structure
            if 'score-partwise' in root.tag or 'score-timewise' in root.tag:
                # Check for required elements
                if root.find('.//part-list') is not None and root.find('.//part') is not None:
                    return True
                else:
                    logger.warning("MusicXML file missing required elements (part-list or part)")
                    return False
            logger.warning("Not a valid MusicXML file (missing score-partwise/timewise)")
            return False
        except ET.ParseError as e:
            logger.error(f"XML Parse error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error validating MusicXML: {str(e)}")
            return False

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('Please select a file to upload.', 'danger')
                return redirect(request.url)
                
            file = request.files['file']
            if file.filename == '':
                flash('No file selected.', 'danger')
                return redirect(request.url)

            if not allowed_file(file.filename):
                flash('Invalid file type. Please upload a MusicXML file (.musicxml or .xml).', 'danger')
                return redirect(request.url)

            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save file and validate
                file.save(filepath)
                os.chmod(filepath, 0o644)  # Ensure file is readable
                logger.info(f"File saved: {filepath}")

                if not is_valid_musicxml(filepath):
                    os.remove(filepath)
                    flash("Invalid or corrupted MusicXML file. Please ensure it contains proper score data.", "danger")
                    return redirect(request.url)

                # Process the file
                nonlocal current_analyzer
                try:
                    current_analyzer = HarmonyAnalyzer()
                    current_analyzer.load_score(filepath)
                    errors = current_analyzer.analyze_score()
                    visualization_path = current_analyzer.generate_visualization()

                    if not visualization_path:
                        logger.warning("Failed to generate score visualization")
                        flash("Score analysis completed, but visualization could not be generated.", "warning")
                    
                    return render_template('results.html',
                                        results=errors,
                                        visualization_path=visualization_path,
                                        report={
                                            'total_errors': len(errors),
                                            'statistics': {
                                                'measures_analyzed': len(errors),
                                                'common_problems': [error['type'] for error in errors[:3]] if errors else []
                                            }
                                        })

                except Exception as e:
                    logger.error(f"Error analyzing score: {str(e)}", exc_info=True)
                    flash(f"Error analyzing score: {str(e)}", 'danger')
                    return redirect(request.url)

                finally:
                    # Clean up uploaded file
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        logger.debug(f"Cleaned up uploaded file: {filepath}")

            except Exception as e:
                logger.error(f"Error processing file: {str(e)}", exc_info=True)
                flash(f"Error processing file: {str(e)}", 'danger')
                return redirect(request.url)
                
        return render_template('index.html')

    @app.route('/download_pdf')
    def download_pdf():
        try:
            nonlocal current_analyzer
            if not current_analyzer:
                flash('No analysis results available. Please analyze a score first.', 'danger')
                return redirect(url_for('index'))
                
            pdf_content = current_analyzer.generate_pdf_report()
            
            return send_file(
                io.BytesIO(pdf_content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name='harmony_analysis_report.pdf'
            )
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
            flash('Error generating PDF report. Please try analyzing the score again.', 'danger')
            return redirect(url_for('index'))

    return app

def check_port_available(port):
    """Check if the port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
        sock.close()
        return True
    except:
        return False

if __name__ == '__main__':
    # Configure music21 environment
    if not configure_music21():
        logger.warning("Music21 environment not fully configured - visualization features may be limited")
    
    # Check if port is available
    if not check_port_available(5000):
        logger.error("Port 5000 is already in use")
        raise RuntimeError("Port 5000 is already in use")
        
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
