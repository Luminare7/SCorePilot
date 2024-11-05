import os
import logging
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from harmony_checker import HarmonyAnalyzer
import io

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "harmony_checker_secret_key"  # Required for flash messages

# Configure upload folder
UPLOAD_FOLDER = 'tmp'
ALLOWED_EXTENSIONS = {'musicxml', 'xml'}

# Ensure upload and visualization directories exist
for directory in [UPLOAD_FOLDER, os.path.join('static', 'visualizations')]:
    if not os.path.exists(directory):
        os.makedirs(directory)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the global analyzer
current_analyzer = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        logger.debug("Processing file upload request")
        
        if 'file' not in request.files:
            logger.warning("No file part in request")
            flash('No file selected', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            logger.warning("No selected file")
            flash('No file selected', 'error')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                logger.debug(f"Saving uploaded file to {filepath}")
                file.save(filepath)
                
                logger.debug("Initializing HarmonyAnalyzer")
                analyzer = HarmonyAnalyzer()
                
                logger.debug("Loading score file")
                analyzer.load_score(filepath)
                
                logger.debug("Analyzing score")
                analysis_results = analyzer.analyze()
                logger.debug(f"Analysis complete. Found {len(analysis_results)} issues")
                
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
                                    visualization_path=visualization_path)
                                    
            except Exception as e:
                logger.error(f"Error during analysis: {str(e)}", exc_info=True)
                flash(f'Error analyzing file: {str(e)}', 'error')
                return redirect(request.url)
                
        else:
            logger.warning(f"Invalid file type: {file.filename}")
            flash('Invalid file type. Please upload a MusicXML file.', 'error')
            return redirect(request.url)
            
    return render_template('index.html')

@app.route('/download_pdf')
def download_pdf():
    logger.debug("Processing PDF download request")
    try:
        global current_analyzer
        if not current_analyzer:
            logger.error("No analyzer available for PDF generation")
            flash('No analysis results available. Please analyze a score first.', 'error')
            return redirect(url_for('index'))
            
        logger.debug("Generating PDF report")
        pdf_content = current_analyzer.generate_pdf_report()
        
        logger.debug("Sending PDF file")
        return send_file(
            io.BytesIO(pdf_content),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='harmony_analysis_report.pdf'
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        flash('Error generating PDF report', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
