import io
from typing import Dict, List
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from .utils import categorize_errors_by_severity, identify_common_problems

logger = logging.getLogger(__name__)

class ReportGenerator:
    @staticmethod
    def generate_pdf_report(errors: List[Dict], statistics: Dict) -> bytes:
        """Generates a PDF report of the analysis"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            story.append(Paragraph("Harmony Analysis Report", title_style))
            story.append(Spacer(1, 12))

            # Basic Information
            story.append(Paragraph(f"Key: {statistics['key']}", styles['Heading2']))
            story.append(Paragraph(f"Total Measures: {statistics['measures_analyzed']}", styles['Normal']))
            story.append(Paragraph(f"Number of Voices: {statistics['total_voices']}", styles['Normal']))
            story.append(Spacer(1, 12))

            # Error Summary by Severity
            error_categories = categorize_errors_by_severity(errors)
            story.append(Paragraph("Error Summary by Severity:", styles['Heading2']))
            story.append(Spacer(1, 6))

            severity_data = [
                ['Severity', 'Count'],
                ['High', str(error_categories['high'])],
                ['Medium', str(error_categories['medium'])],
                ['Low', str(error_categories['low'])]
            ]

            severity_table = Table(severity_data, colWidths=[200, 100])
            severity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(severity_table)
            story.append(Spacer(1, 12))

            # Detailed Errors
            if errors:
                story.append(Paragraph("Detailed Analysis of Errors:", styles['Heading2']))
                story.append(Spacer(1, 12))

                for error in sorted(errors, key=lambda x: (x['measure'], x['severity'])):
                    error_text = f"""
                    <para>
                    <b>Error Type:</b> {error['type']}<br/>
                    <b>Measure:</b> {error['measure']}<br/>
                    <b>Severity:</b> {error['severity']}<br/>
                    <b>Description:</b> {error['description']}
                    </para>
                    """
                    story.append(Paragraph(error_text, styles['Normal']))
                    story.append(Spacer(1, 12))

            # Common Problems Section
            common_problems = identify_common_problems(errors)
            if common_problems:
                story.append(Spacer(1, 20))
                story.append(Paragraph("Most Common Issues:", styles['Heading2']))
                story.append(Spacer(1, 12))

                for problem in common_problems:
                    story.append(Paragraph(f"• {problem}", styles['Normal']))

            # Build PDF
            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            return pdf_content

        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate PDF report: {str(e)}")

    @staticmethod
    def generate_text_report(errors: List[Dict], statistics: Dict) -> str:
        """Generates a text report of the analysis"""
        try:
            text_report = [
                "Harmony Analysis Report",
                "=====================",
                f"Key: {statistics['key']}",
                f"Total Measures: {statistics['measures_analyzed']}",
                f"Total Errors: {len(errors)}",
                "\nErrors by Severity:",
                "-------------------"
            ]

            error_categories = categorize_errors_by_severity(errors)
            for severity, count in error_categories.items():
                text_report.append(f"{severity.capitalize()}: {count}")

            text_report.extend([
                "\nDetailed Errors:",
                "----------------"
            ])

            for error in errors:
                text_report.extend([
                    f"\nType: {error['type']}",
                    f"Measure: {error['measure']}",
                    f"Severity: {error['severity']}",
                    f"Description: {error['description']}"
                ])

            return "\n".join(text_report)

        except Exception as e:
            logger.error(f"Error generating text report: {str(e)}")
            raise Exception(f"Failed to generate text report: {str(e)}")