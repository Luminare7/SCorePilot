import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from harmony_checker import HarmonyAnalyzer
import io
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "harmony_checker_secret_key"  # Required for flash messages

# Configure upload settings
UPLOAD_FOLDER = 'tmp'
ALLOWED_EXTENSIONS = {'musicxml', 'xml'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

# Ensure upload and visualization directories exist
for directory in [UPLOAD_FOLDER, os.path.join('static', 'visualizations')]:
    if not os.path.exists(directory):
        os.makedirs(directory)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE  # Flask will automatically reject larger files

# Initialize the global analyzer
current_analyzer = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_musicxml(file_path):
    """Validate if the file is a well-formed MusicXML file"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        # Check for basic MusicXML structure
        return 'score-partwise' in root.tag or 'score-timewise' in root.tag
    except ET.ParseError:
        return False
    except Exception as e:
        logger.error(f"Error validating MusicXML: {str(e)}")
        return False

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        logger.debug("Processing file upload request")
        
        # Check if the post request has the file part
        if 'file' not in request.files:
            logger.warning("No file part in request")
            flash('Please select a file to upload.', 'danger')
            return redirect(request.url), 400
            
        file = request.files['file']
        
        # Check if a file was selected
        if file.filename == '':
            logger.warning("No selected file")
            flash('No file selected. Please choose a MusicXML file to analyze.', 'danger')
            return redirect(request.url), 400
            
        # Check file extension
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            flash('Invalid file type. Please upload a MusicXML file (.musicxml or .xml).', 'danger')
            return redirect(request.url), 400
            
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logger.debug(f"Saving uploaded file to {filepath}")
            file.save(filepath)
            
            # Validate MusicXML structure
            if not is_valid_musicxml(filepath):
                os.remove(filepath)
                flash('The uploaded file appears to be invalid or corrupted. Please ensure it is a valid MusicXML file.', 'danger')
                return redirect(request.url), 422
            
            logger.debug("Initializing HarmonyAnalyzer")
            analyzer = HarmonyAnalyzer()
            
            logger.debug("Loading score file")
            try:
                analyzer.load_score(filepath)
            except Exception as e:
                os.remove(filepath)
                flash(f'Error loading score: {str(e)}. Please ensure the file contains valid musical notation.', 'danger')
                return redirect(request.url), 422
            
            logger.debug("Analyzing score")
            try:
                analysis_results = analyzer.analyze()
                logger.debug(f"Analysis complete. Found {len(analysis_results)} issues")
            except Exception as e:
                os.remove(filepath)
                flash(f'Error analyzing score: {str(e)}. Please check if the score contains valid musical content.', 'danger')
                return redirect(request.url), 500
            
            logger.debug("Generating report")
            report = analyzer.generate_report()
            
            # Store analyzer in global variable for PDF generation
            global current_analyzer
            current_analyzer = analyzer
            
            # Get visualization path
            visualization_path = analyzer.visualization_path
            
            # Clean up the uploaded file
            logger.debug("Cleaning up uploaded file")
            os.remove(filepath)
            
            logger.debug("Rendering results template")
            return render_template('results.html', 
                                results=analysis_results,
                                report=report,
                                has_errors=bool(analysis_results),
                                visualization_path=visualization_path), 200
                                
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}", exc_info=True)
            flash('An unexpected error occurred. Please try again or contact support if the problem persists.', 'danger')
            return redirect(request.url), 500
            
    return render_template('index.html')

@app.route('/download_pdf')
def download_pdf():
    logger.debug("Processing PDF download request")
    try:
        global current_analyzer
        if not current_analyzer:
            logger.error("No analyzer available for PDF generation")
            flash('No analysis results available. Please analyze a score first.', 'danger')
            return redirect(url_for('index')), 404
            
        logger.debug("Generating PDF report")
        pdf_content = current_analyzer.generate_pdf_report()
        
        logger.debug("Sending PDF file")
        return send_file(
            io.BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='harmony_analysis_report.pdf'
        ), 200
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        flash('Error generating PDF report. Please try analyzing the score again.', 'danger')
        return redirect(url_for('index')), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
