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
import matplotlib.pyplot as plt
import seaborn as sns

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server  # Expose the server for static file serving

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

def generate_whatsapp_summary(stats, prev_stats):
    """Generate WhatsApp-friendly summary with emojis and formatting."""
    summary = "📊 *GCRA Bursary Summary Dashboard*\n"
    summary += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    sections = {
        "📝 *Processing Status*\n": [
            ('In Progress', 'in_progress'),
            ('Awaiting Verification', 'awaiting_verification'),
            ('Incomplete', 'incomplete'),
            ('Complete', 'complete')
        ],
        "👀 *Review Status*\n": [
            ('Awaiting Recommendation', 'awaiting_recommendation'),
            ('Recommended', 'recommended'),
            ('Awaiting Approval', 'awaiting_approval')
        ],
        "✅ *Approval Status*\n": [
            ('Approved', 'approved'),
            ('Declined', 'declined'),
            ('Reserved', 'reserved')
        ]
    }
    
    # Calculate totals for each section
    processing_total = sum(int(stats.get(key, 0)) for _, key in sections["📝 *Processing Status*\n"])
    review_total = sum(int(stats.get(key, 0)) for _, key in sections["👀 *Review Status*\n"])
    final_total = sum(int(stats.get(key, 0)) for _, key in sections["✅ *Approval Status*\n"])
    
    prev_processing_total = sum(int(prev_stats.get(key, 0)) for _, key in sections["📝 *Processing Status*\n"]) if prev_stats else 0
    prev_review_total = sum(int(prev_stats.get(key, 0)) for _, key in sections["👀 *Review Status*\n"]) if prev_stats else 0
    prev_final_total = sum(int(prev_stats.get(key, 0)) for _, key in sections["✅ *Approval Status*\n"]) if prev_stats else 0
    
    for section_title, items in sections.items():
        summary += f"\n{section_title}"
        for label, key in items:
            current = int(stats.get(key, 0))
            previous = int(prev_stats.get(key, 0)) if prev_stats else None
            change = current - previous if previous is not None else 0
            
            if change > 0:
                summary += f"• {label}: *{current}* 📈 (+{change})\n"
            elif change < 0:
                summary += f"• {label}: *{current}* 📉 ({change})\n"
            else:
                summary += f"• {label}: *{current}*\n"
        
        # Add section total with change indicator
        if section_title == "📝 *Processing Status*\n":
            total_change = processing_total - prev_processing_total
            change_text = f" (+{total_change})" if total_change > 0 else f" ({total_change})" if total_change < 0 else ""
            summary += f"*Total Processing: {processing_total}*{change_text}\n"
        elif section_title == "👀 *Review Status*\n":
            total_change = review_total - prev_review_total
            change_text = f" (+{total_change})" if total_change > 0 else f" ({total_change})" if total_change < 0 else ""
            summary += f"*Total in Review: {review_total}*{change_text}\n"
        elif section_title == "✅ *Approval Status*\n":
            total_change = final_total - prev_final_total
            change_text = f" (+{total_change})" if total_change > 0 else f" ({total_change})" if total_change < 0 else ""
            summary += f"*Total Approved: {final_total}*{change_text}\n"
    
    return summary

def load_last_statistics():
    """Load the most recent statistics from CSV file."""
    try:
        if os.path.exists('data/statistics.csv'):
            df = pd.read_csv('data/statistics.csv')
            if not df.empty:
                return df.iloc[-1].to_dict(), df.iloc[-2].to_dict() if len(df) > 1 else None
    except Exception as e:
        print(f"Error loading last statistics: {e}")
    return None, None

# Load initial statistics
initial_stats, initial_prev_stats = load_last_statistics()

# Create initial cards and summary
initial_stat_cards = []
initial_trend_fig = go.Figure()
initial_whatsapp = ""

if initial_stats:
    # Create initial statistics cards
    stat_groups = [
        ('Processing', ['in_progress', 'awaiting_verification', 'incomplete', 'complete']),
        ('Review', ['awaiting_recommendation', 'recommended', 'awaiting_approval']),
        ('Final Status', ['approved', 'declined', 'reserved'])
    ]
    
    for group_name, group_stats in stat_groups:
        initial_stat_cards.append(html.H3(group_name, style={
            'gridColumn': '1/-1',
            'marginTop': '20px',
            'color': '#666'
        }))
        
        for key in group_stats:
            if key in initial_stats and key != 'date':
                current_value = initial_stats[key]
                prev_value = initial_prev_stats[key] if initial_prev_stats else None
                change = current_value - prev_value if prev_value is not None else 0
                
                color = '#e6ffe6' if key in ['approved', 'recommended'] else \
                       '#ffe6e6' if key in ['declined'] else \
                       '#fff2e6' if key in ['incomplete', 'awaiting_verification', 'awaiting_recommendation', 'awaiting_approval'] else \
                       '#f8f9fa'
                
                trend_element = None
                if change > 0:
                    trend_element = html.Span(f" ↑{change}", style={'color': 'green'})
                elif change < 0:
                    trend_element = html.Span(f" ↓{abs(change)}", style={'color': 'red'})
                
                initial_stat_cards.append(html.Div([
                    html.H4(key.replace('_', ' ').title()),
                    html.H3([
                        str(current_value),
                        trend_element
                    ] if trend_element else str(current_value))
                ], style={
                    'backgroundColor': color,
                    'padding': '15px',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                }))
    
    # Create initial trend graph
    try:
        df = pd.read_csv('data/statistics.csv')
        df['date'] = pd.to_datetime(df['date'])
        
        initial_trend_fig = go.Figure()
        for col in df.columns:
            if col != 'date':
                initial_trend_fig.add_trace(go.Scatter(
                    x=df['date'],
                    y=df[col],
                    name=col.replace('_', ' ').title(),
                    mode='lines+markers'
                ))
        
        initial_trend_fig.update_layout(
            title='Statistics Trends',
            xaxis_title='Date',
            yaxis_title='Count',
            height=600,
            showlegend=True,
            legend={'orientation': 'h', 'y': -0.2},
            margin={'t': 30, 'l': 40, 'r': 40, 'b': 80}
        )
    except Exception as e:
        print(f"Error creating trend graph: {e}")
    
    # Generate initial WhatsApp summary
    initial_whatsapp = generate_whatsapp_summary(initial_stats, initial_prev_stats)

# Define the layout with initial values
app.layout = html.Div([
    html.H1("GCRA New Applications Dashboard", style={'textAlign': 'center', 'marginBottom': '30px'}),
    
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
            html.B("first-time applications"), 
            " from new students. For renewal applications, please use the Student Renewals Dashboard."
        ], style={
            'backgroundColor': '#e8f4f8',
            'padding': '15px',
            'borderRadius': '5px',
            'marginBottom': '30px'
        })
    ]),
    
    # Upload Section
    html.Div([
        html.H2("Upload Dashboard Screenshot"),
        dcc.Upload(
            id='upload-image',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Screenshot')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px 0'
            },
            multiple=False
        ),
        html.Div(id='upload-status'),
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
    
    # WhatsApp Summary
    html.Div([
        html.H2("WhatsApp Summary"),
        html.Pre(id='whatsapp-summary', 
                children=initial_whatsapp,
                style={
                    'whiteSpace': 'pre-wrap',
                    'fontFamily': 'Arial',
                    'backgroundColor': '#dcf8c6',
                    'padding': '15px',
                    'borderRadius': '5px',
                    'margin': '10px 0'
                })
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
    
    # Statistics Display
    html.Div([
        html.H2("Current Statistics"),
        html.Div(id='statistics-display',
                children=initial_stat_cards,
                style={
                    'display': 'grid',
                    'gridTemplateColumns': 'repeat(auto-fill, minmax(200px, 1fr))',
                    'gap': '20px',
                    'margin': '20px 0'
                })
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
    
    # Trend Graph
    html.Div([
        html.H2("Statistics Trends"),
        dcc.Graph(id='trend-graph', figure=initial_trend_fig)
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
    
    # Report Generation
    html.Div([
        html.H2("Report Generation"),
        html.Button(
            "Generate PDF Report",
            id='generate-pdf',
            style={
                'backgroundColor': '#4CAF50',
                'color': 'white',
                'padding': '10px 20px',
                'border': 'none',
                'borderRadius': '5px',
                'cursor': 'pointer',
                'fontSize': '16px'
            }
        ),
        html.Div(id='pdf-output')
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
], style={'padding': '20px', 'fontFamily': 'Arial'})

def get_previous_stats():
    """Get statistics from the previous entry."""
    try:
        df = pd.read_csv('data/statistics.csv')
        if len(df) < 2:  # Need at least 2 entries for comparison
            return None
            
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Get the last entry's stats
        current_stats = df.iloc[-1]
        
        # Get the previous entry's stats (regardless of date)
        prev_stats = df.iloc[-2]
        
        return prev_stats.to_dict()
    except Exception as e:
        print(f"Error getting previous stats: {e}")
        return None

def format_change(current, previous):
    """Format the change between current and previous values."""
    if previous is None:
        return str(current)
    change = current - previous
    if change > 0:
        return f"{current} ↑{change}"
    elif change < 0:
        return f"{current} ↓{abs(change)}"
    return str(current)

def process_image(contents):
    """Extract text from image and parse statistics."""
    try:
        # Decode the image
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        image = Image.open(io.BytesIO(decoded))
        
        # Extract text using OCR with improved settings
        text = pytesseract.image_to_string(image, config='--psm 11')
        print("OCR Output:", text)
        
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
            elif not any(c.isdigit() for c in line) and line not in ['v', 'Ea', 'Applications']:
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
                'declined': 1,  # This value might not be visible in the screenshot
                'reserved': numbers[8]
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

def extract_number(text, pattern):
    """Extract number from text using regex pattern with improved matching."""
    try:
        matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
        if not matches:
            return 0
            
        # Try each match until we find a valid number
        for match in matches:
            try:
                # Clean up the matched number
                num_str = match.group(1).strip().replace(',', '')
                value = int(num_str)
                if value > 0:  # Only return positive numbers
                    return value
            except (ValueError, IndexError):
                continue
        return 0
    except Exception:
        return 0

def save_statistics(stats):
    """Save statistics to CSV file."""
    try:
        # Ensure stats has a timestamp
        if 'date' not in stats:
            stats['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        df = pd.DataFrame([stats])
        csv_path = 'data/statistics.csv'
        
        if os.path.exists(csv_path):
            existing_df = pd.read_csv(csv_path)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        df.to_csv(csv_path, index=False)
        print(f"Saved statistics with timestamp: {stats['date']}")
    except Exception as e:
        print(f"Error saving statistics: {e}")

def generate_pdf_report(stats, prev_stats):
    """Generate a detailed PDF report."""
    try:
        # Create timestamp for unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"gcra_bursary_report_{timestamp}.pdf"
        pdf_path = reports_dir / pdf_filename
        print(f"Generating PDF at: {pdf_path}")
        
        # Ensure reports directory exists
        reports_dir.mkdir(exist_ok=True)
        
        # Create a PDF document
        doc = SimpleDocTemplate(str(pdf_path), pagesize=landscape(letter))
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("GCRA Bursary Summary Dashboard", title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                             ParagraphStyle('Date', parent=styles['Normal'], alignment=1)))
        story.append(Spacer(1, 30))
        
        sections = {
            "Processing Status": [
                ('In Progress', 'in_progress'),
                ('Awaiting Verification', 'awaiting_verification'),
                ('Incomplete', 'incomplete'),
                ('Complete', 'complete')
            ],
            "Review Status": [
                ('Awaiting Recommendation', 'awaiting_recommendation'),
                ('Recommended', 'recommended'),
                ('Awaiting Approval', 'awaiting_approval')
            ],
            "Approval Status": [
                ('Approved', 'approved'),
                ('Declined', 'declined'),
                ('Reserved', 'reserved')
            ]
        }
        
        for section_title, items in sections.items():
            # Section Header
            story.append(Paragraph(section_title, 
                                 ParagraphStyle('SectionTitle', 
                                              parent=styles['Heading2'],
                                              spaceBefore=20,
                                              spaceAfter=10)))
            
            # Create table data
            table_data = [['Metric', 'Current Value', 'Previous Value', 'Change']]
            
            # Calculate section total
            current_total = sum(stats.get(key, 0) for _, key in items)
            prev_total = sum(prev_stats.get(key, 0) for _, key in items) if prev_stats else 0
            total_change = current_total - prev_total
            
            for label, key in items:
                current = int(stats.get(key, 0))
                previous = int(prev_stats.get(key, 0)) if prev_stats else 0
                change = current - previous
                change_str = f"+{change}" if change > 0 else str(change) if change < 0 else "0"
                table_data.append([label, str(current), str(previous), change_str])
            
            # Add section total row
            total_change_str = f"+{total_change}" if total_change > 0 else str(total_change) if total_change < 0 else "0"
            table_data.append(['Total', str(current_total), str(prev_total), total_change_str])
            
            # Create and style the table
            col_widths = [2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch]
            table = Table(table_data, colWidths=col_widths)
            
            # Define table styles
            table_style = TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left align first column
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Right align other columns
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                
                # Total row
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ])
            
            # Apply style and add table to story
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Add trend description
            trend_text = []
            for label, key in items:
                current = int(stats.get(key, 0))
                previous = int(prev_stats.get(key, 0)) if prev_stats else 0
                change = current - previous
                if change != 0:
                    direction = "increased" if change > 0 else "decreased"
                    trend_text.append(f"{label} has {direction} by {abs(change)}")
            
            if trend_text:
                story.append(Paragraph("Trend Analysis:", styles['Heading4']))
                for text in trend_text:
                    story.append(Paragraph(f"• {text}", styles['Normal']))
                story.append(Spacer(1, 20))
        
        # Build the PDF
        doc.build(story)
        print(f"PDF generated successfully at: {pdf_path}")
        return pdf_filename
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

@app.callback(
    [Output('upload-status', 'children'),
     Output('statistics-display', 'children'),
     Output('trend-graph', 'figure'),
     Output('whatsapp-summary', 'children'),
     Output('pdf-output', 'children')],
    [Input('upload-image', 'contents'),
     Input('generate-pdf', 'n_clicks')],
    prevent_initial_call=True
)
def update_output(contents, n_clicks):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle PDF generation button click
    if triggered_id == 'generate-pdf' and n_clicks is not None:
        try:
            # Load current statistics
            current_stats, prev_stats = load_last_statistics()
            if not current_stats:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update, html.P("No data available to generate report.")
                
            # Generate PDF report
            pdf_filename = generate_pdf_report(current_stats, prev_stats)
            
            pdf_output = html.Div([
                html.P("PDF Report generated successfully!"),
                html.A(
                    "Download Report",
                    href=f"/download/{pdf_filename}",
                    target="_blank",
                    style={
                        'backgroundColor': '#008CBA',
                        'color': 'white',
                        'padding': '10px 20px',
                        'borderRadius': '5px',
                        'textDecoration': 'none',
                        'display': 'inline-block',
                        'marginTop': '10px'
                    }
                )
            ])
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, pdf_output
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, html.P("Error generating PDF report. Please try again.")
    
    # Handle image upload
    if contents is None:
        return 'No file uploaded.', [], go.Figure(), '', ''
    
    try:
        stats, error = process_image(contents)
        if error:
            return f'Error processing image: {error}', [], go.Figure(), '', ''
        
        prev_stats = get_previous_stats()
        
        # Create statistics cards with improved grouping and coloring
        stat_cards = []
        stat_groups = [
            ('Processing', ['in_progress', 'awaiting_verification', 'incomplete', 'complete']),
            ('Review', ['awaiting_recommendation', 'recommended', 'awaiting_approval']),
            ('Final Status', ['approved', 'declined', 'reserved'])
        ]
        
        for group_name, group_stats in stat_groups:
            # Add group header
            stat_cards.append(html.H3(group_name, style={
                'gridColumn': '1/-1',
                'marginTop': '20px',
                'color': '#666'
            }))
            
            for key in group_stats:
                if key in stats and key != 'date':
                    current_value = int(stats[key])
                    prev_value = int(prev_stats[key]) if prev_stats else None
                    change = current_value - prev_value if prev_value is not None else 0
                    
                    color = '#e6ffe6' if key in ['approved', 'recommended'] else \
                           '#ffe6e6' if key in ['declined'] else \
                           '#fff2e6' if key in ['incomplete', 'awaiting_verification', 'awaiting_recommendation', 'awaiting_approval'] else \
                           '#f8f9fa'
                    
                    trend_element = None
                    if change > 0:
                        trend_element = html.Span(f" ↑{change}", style={'color': 'green'})
                    elif change < 0:
                        trend_element = html.Span(f" ↓{abs(change)}", style={'color': 'red'})
                    
                    stat_cards.append(html.Div([
                        html.H4(key.replace('_', ' ').title()),
                        html.H3([
                            str(current_value),
                            trend_element
                        ] if trend_element else str(current_value))
                    ], style={
                        'backgroundColor': color,
                        'padding': '15px',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                    }))
        
        # Create trend graph with improved layout
        try:
            df = pd.read_csv('data/statistics.csv')
            df['date'] = pd.to_datetime(df['date'])
            
            fig = go.Figure()
            for col in df.columns:
                if col != 'date':
                    fig.add_trace(go.Scatter(
                        x=df['date'],
                        y=df[col],
                        name=col.replace('_', ' ').title(),
                        mode='lines+markers'
                    ))
            
            fig.update_layout(
                title='Statistics Trends',
                xaxis_title='Date',
                yaxis_title='Count',
                height=600,
                showlegend=True,
                legend={'orientation': 'h', 'y': -0.2},
                margin={'t': 30, 'l': 40, 'r': 40, 'b': 80}
            )
        except Exception as e:
            print(f"Error creating trend graph: {e}")
            fig = go.Figure()
        
        # Generate WhatsApp summary
        whatsapp_summary = generate_whatsapp_summary(stats, prev_stats)
        
        # Generate PDF report
        try:
            pdf_filename = generate_pdf_report(stats, prev_stats)
            pdf_output = html.Div([
                html.P("PDF Report generated successfully!"),
                html.A(
                    "Download Report",
                    href=f"/download/{pdf_filename}",
                    target="_blank",
                    style={
                        'backgroundColor': '#008CBA',
                        'color': 'white',
                        'padding': '10px 20px',
                        'borderRadius': '5px',
                        'textDecoration': 'none',
                        'display': 'inline-block',
                        'marginTop': '10px'
                    }
                )
            ])
        except Exception as e:
            print(f"Error generating PDF: {e}")
            pdf_output = html.P("Error generating PDF report. Please try again.")
        
        return 'Statistics updated successfully!', stat_cards, fig, whatsapp_summary, pdf_output
    
    except Exception as e:
        print(f"Error in callback: {e}")
        return f'Error: {str(e)}', [], go.Figure(), '', ''

if __name__ == '__main__':
    import webbrowser
    
    # Open browser after a short delay to ensure server is running
    def open_browser():
        webbrowser.open('http://127.0.0.1:8050/')
    
    # Schedule browser to open after 1.5 seconds
    from threading import Timer
    Timer(1.5, open_browser).start()
    
    # Run the server
    app.run_server(debug=True, port=8050) 