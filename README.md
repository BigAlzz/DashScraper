# DashScraper
Dashboard Scraper for quick reporting to the boss off the dashboard. with watsap friendly, Historical data and a pdf report. Saves hours on long projects where you have to report and do a quick analysis

# Dashboard Scraper

A Python-based web application for processing and analyzing GCRA bursary application and renewal statistics. The application provides automated dashboard data extraction, statistical analysis, and PDF report generation.

## Features

### 1. Dashboard Data Processing
- Automated OCR-based data extraction from dashboard screenshots
- Support for both New Applications and Student Renewals dashboards
- Real-time data validation and error handling

### 2. Statistical Analysis
- Comprehensive statistical tracking for:
  - Processing Status (In Progress, Awaiting Verification, Incomplete, Complete)
  - Review Status (Awaiting Recommendation, Recommended, Awaiting Approval)
  - Approval Status (Approved, Declined, Reserved)
- Historical data tracking and trend analysis
- Automated change detection and percentage calculations

### 3. Reporting Features
- Automated PDF report generation
- WhatsApp-formatted summary generation
- Historical data visualization with trend graphs
- Separate tracking for Applications and Renewals
- Portrait/Landscape hybrid layout for optimal data presentation

### 4. User Interface
- Modern, intuitive web interface
- Drag-and-drop file upload
- Previous reports access through dropdown menu
- Real-time statistics display
- Interactive trend graphs

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd DashboardScraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Install Tesseract OCR:
- Windows: Download and install from [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt-get install tesseract-ocr`
- Mac: `brew install tesseract`

## Configuration

1. Ensure Tesseract is properly installed and accessible in your system PATH
2. Create necessary directories:
   - `data/` - For storing CSV statistics
   - `reports/` - For storing generated PDF reports

## Usage

1. Start the application:
```bash
python app.py
```

2. Access the web interface at `http://localhost:8050`

3. Using the Dashboard:
   - Navigate to either Applications or Renewals dashboard
   - Upload dashboard screenshots using the upload section
   - View real-time statistics and trend analysis
   - Generate PDF reports as needed
   - Access previous reports through the dropdown menu

## Report Generation

Reports can be generated during two time windows:
- Morning: 7:00-9:00
- Afternoon: 16:00-18:00

Reports include:
- Current statistics with change indicators
- Historical trend analysis
- Percentage changes
- WhatsApp-formatted summaries

## Data Storage

- Applications data: `data/statistics.csv`
- Renewals data: `data/statistics_renewals.csv`
- PDF Reports: `reports/` directory

## Dependencies

- Python 3.8+
- Dash
- Plotly
- Pandas
- ReportLab
- Tesseract OCR
- Pillow (PIL)
- PyTesseract

## Error Handling

The application includes comprehensive error handling for:
- Invalid file uploads
- OCR processing errors
- Data validation
- Report generation issues
- File system operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here]

## Support

For support and bug reports, please create an issue in the repository. 
