import dash
from dash import html, dcc
from flask import send_file
from pathlib import Path
import os

# Create the Dash app
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    use_pages=True
)

# Ensure necessary directories exist
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

reports_dir = Path('reports')
reports_dir.mkdir(exist_ok=True)

# Add static file serving route
@app.server.route('/download/<path:filename>')
def download_file(filename):
    """Serve files from reports directory."""
    try:
        # Use absolute path for file serving
        file_path = Path.cwd() / 'reports' / filename
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

# Define the layout
app.layout = html.Div([
    # Title
    html.H1(
        "GCRA Bursary Management System",
        style={
            'textAlign': 'center',
            'color': '#004b98',
            'marginBottom': '40px',
            'marginTop': '20px'
        }
    ),
    
    # Navigation
    html.Div([
        dcc.Link(
            page['name'],
            href=page['path'],
            style={
                'backgroundColor': '#004b98',
                'color': 'white',
                'padding': '10px 20px',
                'margin': '10px',
                'borderRadius': '5px',
                'textDecoration': 'none',
                'display': 'inline-block'
            }
        ) for page in dash.page_registry.values()
    ], style={
        'textAlign': 'center',
        'marginBottom': '40px'
    }),
    
    # Page content
    dash.page_container
], style={
    'maxWidth': '1200px',
    'margin': '0 auto',
    'padding': '20px',
    'fontFamily': 'Arial'
})

if __name__ == '__main__':
    app.run_server(debug=True, threaded=True) 