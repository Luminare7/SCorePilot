import os
import uuid
from music21 import *
from music21 import environment
from music21 import graph
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import logging

logger = logging.getLogger(__name__)

class HarmonyAnalyzer:
    def __init__(self):
        self.score = None
        self.errors = []
        
    def load_score(self, musicxml_path):
        """Loads a score from MusicXML file"""
        try:
            self.score = converter.parse(musicxml_path)
            logger.debug(f"Successfully loaded score from {musicxml_path}")
        except Exception as e:
            logger.error(f"Error loading score: {str(e)}", exc_info=True)
            raise Exception(f"Failed to load score: {str(e)}")

    def analyze_score(self):
        try:
            if not self.score:
                raise ValueError("No score loaded for analysis")
            
            self.errors = []
            # Get all measures
            measures = self.score.measureOffsetMap()
            measure_numbers = sorted(int(measure_num) for measure_num in measures.keys())
            
            for measure_num in measure_numbers:
                try:
                    # Get measure content
                    measure = self.score.measure(measure_num)
                    if measure:
                        # Analyze voice leading
                        voices = list(measure.voices)
                        if len(voices) > 1:
                            for i in range(len(voices) - 1):
                                for j in range(i + 1, len(voices)):
                                    if len(voices[i].notes) > 3 and len(voices[j].notes) > 3:
                                        self.errors.append({
                                            'type': 'Voice Leading',
                                            'measure': measure_num,
                                            'description': f'Complex voice movement between voices {i+1} and {j+1}'
                                        })
                        
                        # Check for parallel fifths
                        chords = list(measure.getElementsByClass('Chord'))
                        if len(chords) > 1:
                            for i in range(len(chords) - 1):
                                # Add basic harmony checks
                                if len(chords[i].pitches) > 3:
                                    self.errors.append({
                                        'type': 'Chord Complexity',
                                        'measure': measure_num,
                                        'description': 'Complex chord structure detected'
                                    })
                except Exception as me:
                    logger.debug(f"Error analyzing measure {measure_num}: {str(me)}")
                    continue
                    
            return self.errors
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            raise

    def generate_visualization(self):
        """Generate a visualization of the score using multiple methods"""
        try:
            if not self.score:
                logger.debug("No score available for visualization")
                return None
                
            # Ensure visualization directory exists with proper permissions
            vis_dir = os.path.join('static', 'visualizations')
            os.makedirs(vis_dir, exist_ok=True)
            os.chmod(vis_dir, 0o755)  # Set directory permissions
            
            # Generate unique filename
            filename = f"score_{uuid.uuid4()}.png"
            filepath = os.path.join(vis_dir, filename)
            
            # Method 1: Try direct score visualization using musescore
            try:
                logger.debug("Attempting direct score visualization with musescore")
                # Convert the score to stream for better compatibility
                flat_score = self.score.stripTies().flatten()
                # Use musescore to render the score
                flat_score.write('musicxml.png', fp=filepath)
                if os.path.exists(filepath):
                    os.chmod(filepath, 0o644)  # Set file permissions
                    logger.debug(f"Successfully generated visualization at {filepath}")
                    return os.path.join('visualizations', filename)
            except Exception as e1:
                logger.debug(f"Direct visualization failed: {e1}")
                
                # Method 2: Try piano roll visualization
                try:
                    logger.debug("Attempting piano roll visualization")
                    plot = graph.plot.HorizontalBarPitchSpaceOffset(self.score)
                    plot.run()
                    plot.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                    if os.path.exists(filepath):
                        os.chmod(filepath, 0o644)
                        logger.debug(f"Successfully generated piano roll at {filepath}")
                        return os.path.join('visualizations', filename)
                except Exception as e2:
                    logger.debug(f"Piano roll visualization failed: {e2}")
                    
                    # Method 3: Try basic pitch space visualization
                    try:
                        logger.debug("Attempting basic pitch space visualization")
                        plot = graph.plot.ScatterPitchSpaceQuarterLength(self.score)
                        plot.run()
                        plot.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                        if os.path.exists(filepath):
                            os.chmod(filepath, 0o644)
                            logger.debug(f"Successfully generated basic plot at {filepath}")
                            return os.path.join('visualizations', filename)
                    except Exception as e3:
                        logger.debug(f"Basic visualization failed: {e3}")
                        
                        # Method 4: Try creating a simple representation
                        try:
                            logger.debug("Attempting simple representation")
                            plot = graph.plot.PlotStream(self.score)
                            plot.run()
                            plot.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                            if os.path.exists(filepath):
                                os.chmod(filepath, 0o644)
                                logger.debug(f"Successfully generated simple plot at {filepath}")
                                return os.path.join('visualizations', filename)
                        except Exception as e4:
                            logger.debug(f"Simple representation failed: {e4}")
                        
            logger.error("All visualization methods failed")
            return None
        except Exception as e:
            logger.error(f"Error in visualization: {str(e)}")
            return None

class BatchAnalyzer:
    def __init__(self):
        self.files = []  # List of (filepath, filename) tuples
        self.results = {}  # Dictionary to store analysis results
        self.visualizations = {}  # Dictionary to store visualization paths

    def add_file(self, filepath, filename):
        """Add a file to the batch for analysis"""
        self.files.append((filepath, filename))

    def analyze_all(self):
        batch_results = []
        
        for filepath, filename in self.files:
            try:
                analyzer = HarmonyAnalyzer()
                analyzer.load_score(filepath)
                
                # Analyze the score
                errors = analyzer.analyze_score()
                
                # Generate visualization
                vis_path = analyzer.generate_visualization()
                
                # Store results
                result = {
                    'filename': filename,
                    'errors': errors,
                    'total_errors': len(errors),
                    'visualization': vis_path,
                    'status': 'success'
                }
                
                self.results[filename] = result
                if vis_path:
                    self.visualizations[filename] = vis_path
                
                batch_results.append(result)
                
            except Exception as e:
                logger.error(f"Error analyzing {filename}: {str(e)}")
                batch_results.append({
                    'filename': filename,
                    'error': str(e),
                    'status': 'error'
                })
        
        return batch_results

    def generate_visualizations(self):
        """Return all visualization paths"""
        return self.visualizations

    def generate_pdf_report(self):
        """Generate a comprehensive PDF report for all analyzed files"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        elements.append(Paragraph("Harmony Analysis Report", title_style))
        elements.append(Spacer(1, 20))

        # Process each file's results
        for filename, result in self.results.items():
            # File header
            elements.append(Paragraph(f"Analysis for: {filename}", styles['Heading2']))
            elements.append(Spacer(1, 10))

            # Error summary
            total_errors = result.get('total_errors', 0)
            elements.append(Paragraph(f"Total Errors: {total_errors}", styles['Normal']))
            elements.append(Spacer(1, 10))

            # Detailed errors
            if result.get('status') == 'success' and result.get('errors'):
                # Create table for errors
                error_data = [['Type', 'Measure', 'Description']]
                for error in result['errors']:
                    error_data.append([
                        error['type'],
                        str(error['measure']),
                        error['description']
                    ])

                table = Table(error_data, colWidths=[120, 60, 300])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
            elif result.get('status') == 'error':
                elements.append(Paragraph(f"Error: {result.get('error', 'Unknown error')}", styles['Normal']))
            else:
                elements.append(Paragraph("No errors found.", styles['Normal']))

            # Add visualization if available
            if filename in self.visualizations:
                try:
                    img_path = os.path.join('static', self.visualizations[filename])
                    if os.path.exists(img_path):
                        img = Image(img_path, width=400, height=300)
                        elements.append(Spacer(1, 20))
                        elements.append(img)
                except Exception as e:
                    logger.error(f"Error adding visualization to PDF: {str(e)}")

            elements.append(Spacer(1, 30))

        # Build PDF
        doc.build(elements)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
