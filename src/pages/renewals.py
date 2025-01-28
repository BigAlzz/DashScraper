import dash
from dash import html, dcc, callback, Input, Output, State, no_update
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import base64
from PIL import Image
import io
import pytesseract
from pathlib import Path
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Register this page
dash.register_page(
    __name__,
    path='/renewals',
    title='GCRA Student Renewals Dashboard',
    order=2
)

# Ensure data directories exist
Path('data').mkdir(exist_ok=True)

def is_valid_report_time():
    """Check if current time is valid for report generation."""
    current_time = datetime.now()
    current_hour = current_time.hour
    
    # Define morning window (7:00-9:00) and afternoon window (16:00-18:00)
    morning_window = (7, 9)
    afternoon_window = (16, 18)
    
    return morning_window[0] <= current_hour <= morning_window[1] or \
           afternoon_window[0] <= current_hour <= afternoon_window[1]

def should_generate_report():
    """Determine if a new report should be generated based on historical data."""
    try:
        csv_path = 'data/statistics_renewals.csv'
        if not os.path.exists(csv_path):
            return True
            
        df = pd.read_csv(csv_path)
        if df.empty:
            return True
            
        # Get the last entry's timestamp
        last_entry = pd.to_datetime(df['date'].iloc[-1])
        current_time = datetime.now()
        
        # Check if we're in the same time window as the last report
        time_diff = current_time - last_entry
        if time_diff.total_seconds() < 3600:  # Less than 1 hour between updates
            return False
            
        return True
        
    except Exception as e:
        print(f"Error checking report generation timing: {e}")
        return False

def process_image(contents):
    """Extract text from image and parse statistics."""
    try:
        # Check if we should generate a new report (prevent duplicate entries)
        if not should_generate_report():
            return None, "A report was already generated within the last hour. Please wait before uploading new data."
            
        # Decode the image
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        image = Image.open(io.BytesIO(decoded))
        
        # Extract text using OCR
        text = pytesseract.image_to_string(image, config='--psm 11')
        print("OCR Output:", text)
        
        # Check if this is a renewals dashboard
        if 'Renewals' not in text:
            return None, "This appears to be an Applications dashboard. Please use the New Applications Dashboard for this screenshot."
        
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

def get_previous_stats():
    """Get the previous statistics from the CSV file."""
    try:
        csv_path = 'data/statistics_renewals.csv'  # Use renewals-specific file
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if not df.empty:
                return df.iloc[-1].to_dict()
        return None
    except Exception as e:
        print(f"Error getting previous stats: {e}")
        return None

def load_last_statistics():
    """Load the last two sets of statistics for comparison."""
    try:
        csv_path = 'data/statistics_renewals.csv'
        if not os.path.exists(csv_path):
            return None, None
            
        df = pd.read_csv(csv_path)
        if df.empty:
            return None, None
            
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # For morning reports (7-9 AM), compare with the last report from previous day
        if 7 <= current_hour <= 9:
            # Get the last entry from today (if exists)
            today_mask = df['date'].dt.date == current_time.date()
            last_entry = df[today_mask].iloc[-1].to_dict() if any(today_mask) else None
            
            # Get the last entry from previous days
            prev_days_mask = df['date'].dt.date < current_time.date()
            prev_entry = df[prev_days_mask].iloc[-1].to_dict() if any(prev_days_mask) else None
            
            # If we have both entries, use them; otherwise fall back to last two entries
            if last_entry and prev_entry:
                return last_entry, prev_entry
        
        # For afternoon reports or if we couldn't find overnight entries
        if len(df) >= 2:
            return df.iloc[-1].to_dict(), df.iloc[-2].to_dict()
        elif len(df) == 1:
            return df.iloc[-1].to_dict(), None
            
        return None, None
        
    except Exception as e:
        print(f"Error loading statistics: {e}")
        return None, None

def create_whatsapp_preview(current_stats, prev_stats):
    """Create WhatsApp preview text."""
    try:
        # Calculate changes based on historical data
        changes = {}
        if prev_stats:
            for key in current_stats:
                if key != 'date':
                    current_val = float(current_stats[key]) if not pd.isna(current_stats[key]) else 0
                    prev_val = float(prev_stats[key]) if not pd.isna(prev_stats[key]) else 0
                    changes[key] = current_val - prev_val

        # Determine if it's a morning or afternoon report
        current_time = datetime.now()
        report_type = "Morning" if current_time.hour <= 11 else "Afternoon"

        # Helper function to format change indicators
        def format_change(value, change):
            if not prev_stats:
                return str(int(value) if value == int(value) else value)
            change_str = ""
            if change > 0:
                change_str = f" 📈 (+{int(change) if change == int(change) else change})"
            elif change < 0:
                change_str = f" 📉 ({int(change) if change == int(change) else change})"
            return f"{int(value) if value == int(value) else value}{change_str}"

        # Format the preview with proper change tracking
        preview = [
            "📊 GCRA Bursary Summary Dashboard",
            f"{report_type} Report - Renewals",
            f"📅 {current_stats['date']}",
            "",
            "📝 Processing Status",
            f"• In Progress: {format_change(current_stats['in_progress'], changes.get('in_progress', 0))}",
            f"• Awaiting Verification: {format_change(current_stats['awaiting_verification'], changes.get('awaiting_verification', 0))}",
            f"• Incomplete: {format_change(current_stats['incomplete'], changes.get('incomplete', 0))}",
            f"• Complete: {format_change(current_stats['complete'], changes.get('complete', 0))}",
        ]

        # Calculate processing total and change
        processing_total = sum([
            float(current_stats['in_progress']) if not pd.isna(current_stats['in_progress']) else 0,
            float(current_stats['awaiting_verification']) if not pd.isna(current_stats['awaiting_verification']) else 0,
            float(current_stats['incomplete']) if not pd.isna(current_stats['incomplete']) else 0,
            float(current_stats['complete']) if not pd.isna(current_stats['complete']) else 0
        ])
        if prev_stats:
            prev_processing_total = sum([
                float(prev_stats['in_progress']) if not pd.isna(prev_stats['in_progress']) else 0,
                float(prev_stats['awaiting_verification']) if not pd.isna(prev_stats['awaiting_verification']) else 0,
                float(prev_stats['incomplete']) if not pd.isna(prev_stats['incomplete']) else 0,
                float(prev_stats['complete']) if not pd.isna(prev_stats['complete']) else 0
            ])
            processing_change = processing_total - prev_processing_total
            preview.append(f"Total Processing: {format_change(processing_total, processing_change)}")
        else:
            preview.append(f"Total Processing: {int(processing_total) if processing_total == int(processing_total) else processing_total}")

        preview.extend([
            "",
            "👀 Review Status",
            f"• Awaiting Recommendation: {format_change(current_stats['awaiting_recommendation'], changes.get('awaiting_recommendation', 0))}",
            f"• Recommended: {format_change(current_stats['recommended'], changes.get('recommended', 0))}",
            f"• Awaiting Approval: {format_change(current_stats['awaiting_approval'], changes.get('awaiting_approval', 0))}",
        ])

        # Calculate review total and change
        review_total = sum([
            float(current_stats['awaiting_recommendation']) if not pd.isna(current_stats['awaiting_recommendation']) else 0,
            float(current_stats['recommended']) if not pd.isna(current_stats['recommended']) else 0,
            float(current_stats['awaiting_approval']) if not pd.isna(current_stats['awaiting_approval']) else 0
        ])
        if prev_stats:
            prev_review_total = sum([
                float(prev_stats['awaiting_recommendation']) if not pd.isna(prev_stats['awaiting_recommendation']) else 0,
                float(prev_stats['recommended']) if not pd.isna(prev_stats['recommended']) else 0,
                float(prev_stats['awaiting_approval']) if not pd.isna(prev_stats['awaiting_approval']) else 0
            ])
            review_change = review_total - prev_review_total
            preview.append(f"Total in Review: {format_change(review_total, review_change)}")
        else:
            preview.append(f"Total in Review: {int(review_total) if review_total == int(review_total) else review_total}")

        preview.extend([
            "",
            "✅ Approval Status",
            f"• Approved: {format_change(current_stats['approved'], changes.get('approved', 0))}",
            f"• Declined: {format_change(current_stats['declined'], changes.get('declined', 0))}",
            f"• Reserved: {format_change(current_stats['reserved'], changes.get('reserved', 0))}",
        ])

        # Calculate approval total and change
        approval_total = sum([
            float(current_stats['approved']) if not pd.isna(current_stats['approved']) else 0,
            float(current_stats['declined']) if not pd.isna(current_stats['declined']) else 0,
            float(current_stats['reserved']) if not pd.isna(current_stats['reserved']) else 0
        ])
        if prev_stats:
            prev_approval_total = sum([
                float(prev_stats['approved']) if not pd.isna(prev_stats['approved']) else 0,
                float(prev_stats['declined']) if not pd.isna(prev_stats['declined']) else 0,
                float(prev_stats['reserved']) if not pd.isna(prev_stats['reserved']) else 0
            ])
            approval_change = approval_total - prev_approval_total
            preview.append(f"Total Approved: {format_change(approval_total, approval_change)}")
        else:
            preview.append(f"Total Approved: {int(approval_total) if approval_total == int(approval_total) else approval_total}")

        return '\n'.join(preview)
    except Exception as e:
        print(f"Error creating WhatsApp preview: {e}")
        return "Error creating WhatsApp preview"

def generate_pdf_report(current_stats, prev_stats):
    """Generate a detailed PDF report with historical data and comparisons."""
    try:
        # Create timestamp for unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"renewals_report_{timestamp}.pdf"
        
        # Use path relative to project root
        reports_dir = Path.cwd() / 'reports'
        reports_dir.mkdir(exist_ok=True)
        pdf_path = reports_dir / pdf_filename
        
        # Create PDF document with adjusted margins
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,  # Start with portrait orientation
            leftMargin=30,
            rightMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Create custom styles
        styles = getSampleStyleSheet()
        
        # Custom title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#004b98'),  # GCRA Blue
            fontName='Helvetica-Bold'
        )
        
        # Custom subtitle style
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            alignment=1,
            textColor=colors.HexColor('#666666'),
            spaceBefore=10,
            spaceAfter=20,
            fontName='Helvetica'
        )
        
        # Custom section header style
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=25,
            spaceAfter=15,
            textColor=colors.HexColor('#004b98'),
            fontName='Helvetica-Bold'
        )
        
        story = []
        
        # Add logo placeholder (if needed)
        # story.append(Image('path_to_logo.png', width=1.5*inch, height=1.5*inch))
        
        # Title and date
        story.append(Paragraph("GCRA Bursary Renewals Dashboard", title_style))
        story.append(Paragraph(
            f"Report Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
            subtitle_style
        ))
        story.append(Spacer(1, 20))
        
        # Define sections and their metrics
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
        
        # Helper function to format numbers and changes
        def format_change(current, previous):
            if pd.isna(current): current = 0
            if pd.isna(previous): previous = 0
            current = float(current)
            previous = float(previous)
            change = current - previous
            
            # Calculate percentage change
            if previous > 0:
                pct_change = (change / previous) * 100
                if change > 0:
                    change_str = f"+{int(change)} (+{pct_change:.1f}%) ▲"
                elif change < 0:
                    change_str = f"{int(change)} ({pct_change:.1f}%) ▼"
                else:
                    change_str = "0 (0%) ●"
            else:
                # Handle case where previous value is 0
                if current > 0:
                    change_str = f"+{int(change)} (NEW) ▲"
                else:
                    change_str = "0 (0%) ●"
            
            return int(current), int(previous), change_str
        
        # Create tables for each section with portrait-optimized widths
        col_widths = [2.5*inch, 1.2*inch, 1.2*inch, 1.8*inch]  # Increased last column width for percentage
        
        # Create tables for each section
        for section_title, metrics in sections.items():
            # Section Header
            story.append(Paragraph(section_title, section_style))
            
            # Create table data
            table_data = [['Metric', 'Current Value', 'Previous Value', 'Change']]
            
            # Calculate section total
            section_total_current = 0
            section_total_prev = 0
            
            for label, key in metrics:
                current, previous, change = format_change(
                    current_stats.get(key, 0),
                    prev_stats.get(key, 0) if prev_stats else 0
                )
                table_data.append([label, str(current), str(previous), change])
                section_total_current += current
                section_total_prev += previous
            
            # Add section total
            total_change = f"+{section_total_current - section_total_prev}" if section_total_current > section_total_prev \
                          else str(section_total_current - section_total_prev)
            table_data.append(['Total', str(section_total_current), str(section_total_prev), total_change])
            
            # Create and style the table
            table = Table(table_data, colWidths=col_widths)
            
            # Define table styles
            table_style = TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004b98')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),  # Reduced from 12
                ('TOPPADDING', (0, 0), (-1, 0), 6),     # Reduced from 12
                
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left align first column
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center align other columns
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),  # Reduced from 10
                ('TOPPADDING', (0, 1), (-1, -1), 4),     # Reduced from 10
                
                # Total row
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f4f8')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#004b98')),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#004b98')),
            ])
            
            # Apply style and add table to story
            table.setStyle(table_style)
            story.append(table)
            story.append(Spacer(1, 6))  # Reduced from 10
            
            # Add trend analysis with improved styling
            trend_text = []
            for label, key in metrics:
                current, previous, change = format_change(
                    current_stats.get(key, 0),
                    prev_stats.get(key, 0) if prev_stats else 0
                )
                if current != previous:
                    direction = "increased" if current > previous else "decreased"
                    trend_text.append(f"{label} has {direction} by {abs(current - previous)}")
            
            if trend_text:
                story.append(Paragraph("Trend Analysis", 
                    ParagraphStyle('TrendTitle', 
                        parent=styles['Heading4'],
                        textColor=colors.HexColor('#004b98'),
                        fontSize=11,  # Reduced from 12
                        spaceBefore=6,  # Reduced from 10
                        spaceAfter=3   # Reduced from 5
                    )))
                for text in trend_text:
                    story.append(Paragraph(
                        f"• {text}",
                        ParagraphStyle('TrendText',
                            parent=styles['Normal'],
                            fontSize=9,  # Reduced from 10
                            leftIndent=20,
                            spaceBefore=1  # Reduced from 2
                        )
                    ))
                story.append(Spacer(1, 8))  # Reduced from 15
        
        # Force a page break before historical data
        story.append(PageBreak())
        
        # Switch to landscape for historical data
        doc.pagesize = landscape(letter)
        
        # Add historical data with improved styling
        try:
            df = pd.read_csv('data/statistics_renewals.csv')  # Note: Using renewals-specific file
            df['date'] = pd.to_datetime(df['date'])
            df = df.tail(10)  # Get last 10 entries
            
            story.append(Paragraph("Historical Data Analysis", section_style))
            story.append(Spacer(1, 10))
            
            # Filter out unwanted columns
            excluded_columns = ['sent_back', 'declined', 'not_recommended']
            included_columns = [col for col in df.columns if col != 'date' and col not in excluded_columns]
            
            # Create transposed historical data table
            # First row will be dates
            hist_data = [['Metric'] + [row['date'].strftime('%Y-%m-%d %H:%M') for _, row in df.iterrows()]]
            
            # Add data rows (one row per metric)
            for col in included_columns:
                metric_name = col.replace('_', ' ').title()
                row_data = [metric_name]
                row_data.extend([f"{int(val):,}" if not pd.isna(val) else '0' for val in df[col]])
                hist_data.append(row_data)
            
            # Calculate column widths - first column wider for metric names
            col_widths = [2.5*inch] + [(6.5*inch) / len(df)] * len(df)
            
            # Create and style the historical table
            hist_table = Table(hist_data, colWidths=col_widths, repeatRows=1)
            hist_table.setStyle(TableStyle([
                # Header row (dates)
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004b98')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                # First column (metric names)
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e8f4f8')),
                ('TEXTCOLOR', (0, 1), (0, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (0, -1), 9),
                
                # Data cells
                ('BACKGROUND', (1, 1), (-1, -1), colors.white),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (1, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#004b98')),
                
                # Zebra striping for data rows
                ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))
            
            story.append(hist_table)
            
        except Exception as e:
            print(f"Error adding historical data: {e}")
        
        # Build the PDF
        doc.build(story)
        print(f"PDF generated successfully at: {pdf_path}")
        return pdf_filename
        
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        raise

# Define the layout
layout = html.Div([
    html.H1("GCRA Student Renewals Dashboard", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Container for Previous Reports and Upload Section
    html.Div([
        # Upload Section (Left)
        html.Div([
            html.H2("Upload Dashboard Screenshot", style={'marginBottom': '10px', 'fontSize': '1.3em'}),
            html.Div([
                dcc.Upload(
                    id='upload-image-renewals',
                    children=html.Div([
                        html.Button('Choose File', style={
                            'backgroundColor': '#004b98',
                            'color': 'white',
                            'padding': '8px 16px',
                            'border': 'none',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'fontSize': '14px',
                            'marginRight': '10px'
                        }),
                        html.Span('or drag and drop here', style={
                            'color': '#666',
                            'fontSize': '13px'
                        })
                    ]),
                    style={
                        'width': '100%',
                        'height': '50px',
                        'lineHeight': '50px',
                        'borderWidth': '2px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '8px 0',
                        'backgroundColor': '#fafafa',
                        'borderColor': '#004b98'
                    },
                    multiple=False
                ),
                html.Div(id='upload-status-renewals'),
            ])
        ], style={
            'flex': '2',
            'marginRight': '20px',
            'padding': '15px',
            'backgroundColor': '#f8f9fa',
            'borderRadius': '5px'
        }),
        
        # Right Section Container (Previous Reports and Generate Report)
        html.Div([
            # Previous Reports
            html.Div([
                html.H2("Previous Reports", style={'marginBottom': '10px', 'fontSize': '1.3em'}),
                dcc.Dropdown(
                    id='previous-reports-renewals',
                    options=[],  # Will be populated by callback
                    placeholder="Select a previous report to view",
                    style={'width': '100%'}
                ),
            ], style={
                'marginBottom': '15px'
            }),
            
            # Report Generation
            html.Div([
                html.H2("Report Generation", style={'marginBottom': '10px', 'fontSize': '1.3em'}),
                html.Button(
                    "Generate PDF Report",
                    id='generate-pdf-renewals',
                    style={
                        'backgroundColor': '#4CAF50',
                        'color': 'white',
                        'padding': '8px 16px',
                        'border': 'none',
                        'borderRadius': '5px',
                        'cursor': 'pointer',
                        'fontSize': '14px',
                        'width': '100%'
                    }
                ),
                html.Div(id='pdf-output-renewals', style={'marginTop': '10px'})
            ])
        ], style={
            'flex': '1',
            'padding': '15px',
            'backgroundColor': '#e8f4f8',
            'borderRadius': '5px',
            'display': 'flex',
            'flexDirection': 'column'
        }),
    ], style={
        'display': 'flex',
        'marginBottom': '20px',
        'gap': '20px'
    }),
    
    # WhatsApp Summary Preview (Moved up)
    html.Div([
        html.H2("WhatsApp Summary Preview"),
        html.Pre(
            id='whatsapp-preview-renewals',
            style={
                'whiteSpace': 'pre-wrap',
                'fontFamily': 'monospace',
                'backgroundColor': '#DCF8C6',  # WhatsApp message green
                'padding': '15px',
                'borderRadius': '10px',
                'margin': '10px 0',
                'maxWidth': '600px',
                'margin': '0 auto'
            }
        )
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
    
    # Statistics Display
    html.Div(id='statistics-display-renewals', style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fill, minmax(200px, 1fr))',
        'gap': '20px',
        'margin': '20px 0'
    }),
    
    # Trend Graph
    html.Div([
        html.H2("Statistics Trends"),
        dcc.Graph(id='trend-graph-renewals')
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'}),
], style={'padding': '20px', 'fontFamily': 'Arial'})

# Add callbacks
@callback(
    [Output('upload-status-renewals', 'children'),
     Output('statistics-display-renewals', 'children'),
     Output('trend-graph-renewals', 'figure'),
     Output('pdf-output-renewals', 'children'),
     Output('whatsapp-preview-renewals', 'children')],
    [Input('upload-image-renewals', 'contents'),
     Input('generate-pdf-renewals', 'n_clicks')],
    prevent_initial_call=False
)
def update_output(contents, n_clicks):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Initial load - populate with existing data
    if not triggered_id:
        try:
            current_stats = get_previous_stats()
            if not current_stats:
                return '', [], go.Figure(), '', ''
                
            # Create statistics cards
            stat_cards = create_stat_cards(current_stats, None)
            
            # Create trend graph
            fig = create_trend_graph()
            
            # Create WhatsApp preview
            whatsapp_text = create_whatsapp_preview(current_stats, None)
            
            return '', stat_cards, fig, '', whatsapp_text
        except Exception as e:
            print(f"Error loading initial data: {e}")
            return '', [], go.Figure(), '', ''
    
    # Handle PDF generation button click
    if triggered_id == 'generate-pdf-renewals' and n_clicks is not None:
        try:
            current_stats, prev_stats = load_last_statistics()
            if not current_stats:
                return dash.no_update, dash.no_update, dash.no_update, html.P("No data available to generate report."), dash.no_update
                
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
            return dash.no_update, dash.no_update, dash.no_update, pdf_output, dash.no_update
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return dash.no_update, dash.no_update, dash.no_update, html.P("Error generating PDF report. Please try again."), dash.no_update
    
    # Handle image upload
    if contents is None:
        return 'No file uploaded.', [], go.Figure(), '', ''
    
    try:
        stats, error = process_image(contents)
        if error:
            return f'Error processing image: {error}', [], go.Figure(), '', ''
        
        prev_stats = get_previous_stats()
        
        # Create statistics cards
        stat_cards = create_stat_cards(stats, prev_stats)
        
        # Create trend graph
        fig = create_trend_graph()
        
        # Create WhatsApp preview
        whatsapp_text = create_whatsapp_preview(stats, prev_stats)
        
        return 'Statistics updated successfully!', stat_cards, fig, '', whatsapp_text
    
    except Exception as e:
        print(f"Error in callback: {e}")
        return f'Error: {str(e)}', [], go.Figure(), '', ''

def create_stat_cards(stats, prev_stats):
    """Helper function to create statistics cards."""
    stat_cards = []
    stat_groups = [
        ('Processing', ['in_progress', 'awaiting_verification', 'incomplete', 'complete']),
        ('Review', ['awaiting_recommendation', 'recommended', 'awaiting_approval']),
        ('Final Status', ['approved', 'declined', 'reserved'])
    ]
    
    for group_name, group_stats in stat_groups:
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
    
    return stat_cards

def create_trend_graph():
    """Helper function to create trend graph."""
    try:
        df = pd.read_csv('data/statistics_renewals.csv')  # Use renewals-specific file
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
        return fig
    except Exception as e:
        print(f"Error creating trend graph: {e}")
        return go.Figure() 