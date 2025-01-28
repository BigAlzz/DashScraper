import dash
from dash import html
import webbrowser
from threading import Timer

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("GCRA Bursary Management System", style={
        'textAlign': 'center',
        'marginBottom': '50px',
        'marginTop': '50px',
        'color': '#004b98'
    }),
    
    html.Div([
        # New Applications Dashboard Card
        html.Div([
            html.H2("New Applications Dashboard", style={'color': '#004b98'}),
            html.P([
                "Track and monitor ", html.B("first-time"), " bursary applications.",
                html.Br(),
                html.Small("Use this for processing new student applications.")
            ], style={'marginBottom': '20px'}),
            html.A(
                html.Button(
                    "Open New Applications Dashboard",
                    style={
                        'backgroundColor': '#004b98',
                        'color': 'white',
                        'padding': '15px 30px',
                        'border': 'none',
                        'borderRadius': '5px',
                        'cursor': 'pointer',
                        'fontSize': '16px',
                        'width': '100%'
                    }
                ),
                href="http://127.0.0.1:8050",
                style={'textDecoration': 'none'}
            )
        ], style={
            'padding': '30px',
            'backgroundColor': '#f8f9fa',
            'borderRadius': '10px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'margin': '20px',
            'flex': '1'
        }),
        
        # Student Renewals Dashboard Card
        html.Div([
            html.H2("Student Renewals Dashboard", style={'color': '#004b98'}),
            html.P([
                "Track and monitor ", html.B("renewal applications"), " from existing students.",
                html.Br(),
                html.Small("Use this for processing continuing student renewals.")
            ], style={'marginBottom': '20px'}),
            html.A(
                html.Button(
                    "Open Student Renewals Dashboard",
                    style={
                        'backgroundColor': '#004b98',
                        'color': 'white',
                        'padding': '15px 30px',
                        'border': 'none',
                        'borderRadius': '5px',
                        'cursor': 'pointer',
                        'fontSize': '16px',
                        'width': '100%'
                    }
                ),
                href="http://127.0.0.1:8051",
                style={'textDecoration': 'none'}
            )
        ], style={
            'padding': '30px',
            'backgroundColor': '#f8f9fa',
            'borderRadius': '10px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'margin': '20px',
            'flex': '1'
        })
    ], style={
        'display': 'flex',
        'justifyContent': 'center',
        'padding': '20px',
        'maxWidth': '1200px',
        'margin': '0 auto'
    }),
    
    # Footer with instructions
    html.Div([
        html.Hr(style={'margin': '40px 0 20px 0'}),
        html.P([
            html.B("How to use:"),
            html.Br(),
            "• Use New Applications Dashboard for first-time applicants",
            html.Br(),
            "• Use Student Renewals Dashboard for existing student renewals",
            html.Br(),
            "• Make sure to upload screenshots to the correct dashboard"
        ], style={
            'textAlign': 'center',
            'color': '#666',
            'fontSize': '14px'
        })
    ])
], style={
    'fontFamily': 'Arial',
    'padding': '20px'
})

if __name__ == '__main__':
    def open_browser():
        webbrowser.open('http://127.0.0.1:8049/')
    
    Timer(1.5, open_browser).start()
    app.run_server(debug=True, port=8049) 