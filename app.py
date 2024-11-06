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

def cleanup_visualizations():
    """Cleanup visualization files from previous analyses"""
    vis_dir = os.path.join('static', 'visualizations')
    try:
        for file in os.listdir(vis_dir):
            file_path = os.path.join(vis_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        logger.debug("Successfully cleaned up visualization files")
    except Exception as e:
        logger.error(f"Error cleaning visualizations: {str(e)}")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        logger.debug("Processing file upload request")
        
        # Cleanup previous visualizations at the start
        cleanup_visualizations()
        
        # Check if multiple files were uploaded
        files = request.files.getlist('file')
        if not files or all(file.filename == '' for file in files):
            logger.warning("No files selected")
            flash('Please select at least one file to upload.', 'danger')
            return redirect(request.url)

        analysis_results = []
        current_analyzers = []

        for file in files:
            if not allowed_file(file.filename):
                logger.warning(f"Invalid file type: {file.filename}")
                flash(f'Invalid file type for {file.filename}. Skipping.', 'warning')
                continue

            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logger.debug(f"Saving uploaded file to {filepath}")
                file.save(filepath)

                # Validate MusicXML structure
                if not is_valid_musicxml(filepath):
                    os.remove(filepath)
                    flash(f'File {filename} appears to be invalid or corrupted. Skipping.', 'warning')
                    continue

                logger.debug(f"Analyzing {filename}")
                analyzer = HarmonyAnalyzer()

                try:
                    analyzer.load_score(filepath)
                except Exception as e:
                    os.remove(filepath)
                    flash(f'Error loading score {filename}: {str(e)}', 'warning')
                    continue

                try:
                    file_results = analyzer.analyze()
                    analysis_results.append({
                        'filename': filename,
                        'results': file_results,
                        'report': analyzer.generate_report(),
                        'visualization_path': analyzer.visualization_path
                    })
                    current_analyzers.append(analyzer)
                except Exception as e:
                    flash(f'Error analyzing {filename}: {str(e)}', 'warning')

                # Clean up the uploaded file
                os.remove(filepath)

            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}", exc_info=True)
                flash(f'Error processing {file.filename}. Skipping.', 'warning')
                continue

        if not analysis_results:
            flash('No valid files were processed successfully.', 'danger')
            return redirect(request.url)

        # Store analyzers in global variable for PDF generation
        global current_analyzer
        current_analyzer = current_analyzers[0] if current_analyzers else None

        logger.debug("Rendering results template")
        return render_template('results.html',
                            batch_results=analysis_results,
                            has_errors=any(result['results'] for result in analysis_results))

    return render_template('index.html')

@app.route('/download_pdf')
def download_pdf():
    logger.debug("Processing PDF download request")
    try:
        global current_analyzer
        if not current_analyzer:
            logger.error("No analyzer available for PDF generation")
            flash('No analysis results available. Please analyze a score first.', 'danger')
            return redirect(url_for('index'))

        logger.debug("Generating PDF report")
        pdf_content = current_analyzer.generate_pdf_report()

        # Cleanup visualizations after PDF generation
        cleanup_visualizations()

        logger.debug("Sending PDF file")
        return send_file(
            io.BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='harmony_analysis_report.pdf'
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        # Cleanup visualizations in case of error
        cleanup_visualizations()
        flash('Error generating PDF report. Please try analyzing the score again.', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
