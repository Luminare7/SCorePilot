import os
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from harmony_checker import HarmonyAnalyzer
import io

app = Flask(__name__)
app.secret_key = "harmony_checker_secret_key"  # Required for flash messages

# Configure upload folder
UPLOAD_FOLDER = 'tmp'
ALLOWED_EXTENSIONS = {'musicxml', 'xml'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                analyzer = HarmonyAnalyzer()
                analyzer.load_score(filepath)
                analysis_results = analyzer.analyze()
                report = analyzer.generate_report()
                
                # Store analyzer in session for PDF generation
                global current_analyzer
                current_analyzer = analyzer
                
                # Clean up the uploaded file
                os.remove(filepath)
                
                return render_template('results.html', 
                                     results=analysis_results,
                                     report=report)
                                     
            except Exception as e:
                flash(f'Error analyzing file: {str(e)}', 'error')
                return redirect(request.url)
                
        else:
            flash('Invalid file type. Please upload a MusicXML file.', 'error')
            return redirect(request.url)
            
    return render_template('index.html')

@app.route('/download_pdf')
def download_pdf():
    try:
        if current_analyzer:
            pdf_content = current_analyzer.generate_pdf_report()
            return send_file(
                io.BytesIO(pdf_content),
                mimetype='application/pdf',
                as_attachment=True,
                download_name='harmony_analysis_report.pdf'
            )
    except Exception as e:
        flash('Error generating PDF report', 'error')
        return redirect(url_for('index'))
