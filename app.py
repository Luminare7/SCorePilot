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

# Initialize the global analyzer list
current_analyzers = []

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
        
        # Check if any file was uploaded
        if 'file' not in request.files:
            logger.warning("No file part in request")
            flash('Please select at least one file to upload.', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('file')
        
        # Check if any files were selected
        if not files or files[0].filename == '':
            logger.warning("No selected files")
            flash('No files selected. Please choose MusicXML files to analyze.', 'danger')
            return redirect(request.url)

        # Process each file
        global current_analyzers
        current_analyzers = []
        analysis_results = []
        
        for file in files:
            if not allowed_file(file.filename):
                logger.warning(f"Invalid file type: {file.filename}")
                flash(f'Invalid file type for {file.filename}. Please upload only MusicXML files (.musicxml or .xml).', 'danger')
                continue

            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logger.debug(f"Saving uploaded file to {filepath}")
                file.save(filepath)

                # Validate MusicXML structure
                if not is_valid_musicxml(filepath):
                    os.remove(filepath)
                    flash(f'The file {filename} appears to be invalid or corrupted. Please ensure it is a valid MusicXML file.', 'danger')
                    continue

                logger.debug(f"Initializing HarmonyAnalyzer for {filename}")
                analyzer = HarmonyAnalyzer()

                logger.debug("Loading score file")
                try:
                    analyzer.load_score(filepath)
                except Exception as e:
                    os.remove(filepath)
                    flash(f'Error loading score {filename}: {str(e)}. Please ensure the file contains valid musical notation.', 'danger')
                    continue

                logger.debug("Analyzing score")
                try:
                    file_results = analyzer.analyze()
                    logger.debug(f"Analysis complete. Found {len(file_results)} issues")
                except Exception as e:
                    os.remove(filepath)
                    flash(f'Error analyzing score {filename}: {str(e)}. Please check if the score contains valid musical content.', 'danger')
                    continue

                logger.debug("Generating report")
                report = analyzer.generate_report()
                
                # Add filename and results to the analysis results
                analysis_results.append({
                    'filename': filename,
                    'results': file_results,
                    'report': report,
                    'visualization_path': analyzer.visualization_path
                })
                
                current_analyzers.append(analyzer)

                # Clean up the uploaded file
                logger.debug("Cleaning up uploaded file")
                os.remove(filepath)

            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
                flash(f'An unexpected error occurred while processing {file.filename}. Please try again or contact support if the problem persists.', 'danger')
                continue

        if not analysis_results:
            flash('No files were successfully analyzed. Please check the file format and try again.', 'danger')
            return redirect(request.url)

        logger.debug("Rendering results template")
        return render_template('results.html', 
                            analysis_results=analysis_results,
                            has_errors=any(bool(result['results']) for result in analysis_results))

    return render_template('index.html')

@app.route('/download_pdf')
def download_pdf():
    logger.debug("Processing PDF download request")
    try:
        global current_analyzers
        if not current_analyzers:
            logger.error("No analyzers available for PDF generation")
            flash('No analysis results available. Please analyze scores first.', 'danger')
            return redirect(url_for('index'))

        # Combine all PDF reports
        all_pdfs = []
        for analyzer in current_analyzers:
            pdf_content = analyzer.generate_pdf_report()
            all_pdfs.append(pdf_content)

        # Combine PDFs using PyPDF2 (assuming the generate_pdf_report returns bytes)
        from PyPDF2 import PdfMerger
        merger = PdfMerger()
        
        for pdf in all_pdfs:
            merger.append(io.BytesIO(pdf))
        
        output = io.BytesIO()
        merger.write(output)
        output.seek(0)
        
        logger.debug("Sending combined PDF file")
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='harmony_analysis_report.pdf'
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        flash('Error generating PDF report. Please try analyzing the scores again.', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
