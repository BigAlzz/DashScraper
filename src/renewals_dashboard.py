# Copy the entire content of dashboard_gui.py but make these changes:
# 1. Change port to 8051
# 2. Change title to "GCRA Student Renewals Dashboard"
# 3. Use 'data/statistics_renewals.csv' for data storage
# 4. Use 'reports/renewals_' prefix for PDF reports
# 5. Add a check for "Renewals" text in the OCR output

import dash
from dash import html, dcc, Input, Output, State
from flask import send_from_directory, send_file
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path
import base64
import pytesseract
from PIL import Image
import io
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server

# Ensure data and reports directories exist
base_dir = Path(os.getcwd())
Path('data').mkdir(exist_ok=True)
reports_dir = base_dir / 'reports'
reports_dir.mkdir(exist_ok=True)

# Add static file serving route
@server.route('/download/<path:filename>')
def download_file(filename):
    """Serve files from reports directory."""
    try:
        file_path = reports_dir / filename
        print(f"Attempting to serve file: {file_path}")
        if file_path.exists():
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        print(f"File not found: {file_path}")
        return f"File not found: {filename}", 404
    except Exception as e:
        print(f"Error serving file: {e}")
        return f"Error: {str(e)}", 404

# ... [Keep all the helper functions from dashboard_gui.py] ...

def process_image(contents):
    """Extract text from image and parse statistics."""
    try:
        # Decode the image
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        image = Image.open(io.BytesIO(decoded))
        
        # Extract text using OCR
        text = pytesseract.image_to_string(image, config='--psm 11')
        print("OCR Output:", text)
        
        # Check if this is a renewals dashboard
        if 'Renewals' not in text:
            return None, "This appears to be an Applications dashboard. Please use the Applications dashboard for this screenshot."
        
        # Split text into lines and clean them
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        print("Lines:", lines)
        
        # Create a mapping of labels to their values
        values = {}
        numbers = []
        labels = []
        
        # First, collect all numbers and labels separately
        for line in lines:
            if line.replace(',', '').isdigit():
                numbers.append(int(line.replace(',', '')))
            elif not any(c.isdigit() for c in line) and line not in ['v', 'Ea', 'Renewals']:
                labels.append(line)
        
        print("Numbers found:", numbers)
        print("Labels found:", labels)
        
        # Match numbers to labels based on their order in the dashboard
        if len(numbers) >= 9:  # We expect at least 9 numbers
            stats = {
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'in_progress': numbers[0],
                'awaiting_verification': numbers[1],
                'incomplete': numbers[2],
                'complete': numbers[3],
                'awaiting_recommendation': numbers[4],
                'recommended': numbers[5],
                'awaiting_approval': numbers[6],
                'approved': numbers[7],
                'declined': numbers[8],
                'reserved': numbers[9] if len(numbers) > 9 else 0
            }
            
            print("Final stats:", stats)
            
            # Save to CSV
            save_statistics(stats)
            return stats, None
        else:
            print("Not enough numbers found in the screenshot")
            return None, "Could not extract all required numbers from the screenshot"
            
    except Exception as e:
        print("Error:", str(e))
        return None, str(e)

def save_statistics(stats):
    """Save statistics to CSV file."""
    try:
        # Ensure stats has a timestamp
        if 'date' not in stats:
            stats['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        df = pd.DataFrame([stats])
        csv_path = 'data/statistics_renewals.csv'  # Changed to renewals-specific file
        
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        df.to_csv(csv_path, index=False)
        print(f"Saved renewals statistics with timestamp: {stats['date']}")
    except Exception as e:
        print(f"Error saving statistics: {e}")

def generate_pdf_report(stats, prev_stats):
    """Generate a detailed PDF report."""
    try:
        # Create timestamp for unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"renewals_report_{timestamp}.pdf"  # Changed prefix
        pdf_path = reports_dir / pdf_filename
        print(f"Generating PDF at: {pdf_path}")
        
        # ... [Rest of the PDF generation code remains the same] ...
        
        return pdf_filename
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise

# Define the layout with initial values
app.layout = html.Div([
    html.H1("GCRA Student Renewals Dashboard", style={'textAlign': 'center', 'marginBottom': '30px'}),
    
    # Back to Landing Page Link
    html.Div([
        html.A(
            "← Back to Management System",
            href="http://127.0.0.1:8049/",
            style={
                'color': '#004b98',
                'textDecoration': 'none',
                'marginBottom': '20px',
                'display': 'inline-block'
            }
        )
    ], style={'marginBottom': '20px'}),
    
    # Dashboard description
    html.Div([
        html.P([
            "This dashboard is specifically for tracking ", 
            html.B("renewal applications"), 
            " from existing GCRA bursary students. For new applications, please use the New Applications Dashboard."
        ], style={
            'backgroundColor': '#e8f4f8',
            'padding': '15px',
            'borderRadius': '5px',
            'marginBottom': '30px'
        })
    ]),
    
    # ... [Rest of the layout remains the same] ...
    
], style={'padding': '20px', 'fontFamily': 'Arial'})

# ... [Keep all the callbacks from dashboard_gui.py] ...

if __name__ == '__main__':
    import webbrowser
    
    def open_browser():
        webbrowser.open('http://127.0.0.1:8051/')
    
    Timer(1.5, open_browser).start()
    
    app.run_server(debug=True, port=8051) 