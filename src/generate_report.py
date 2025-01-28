import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
import os
from typing import Dict, List, Tuple

class ReportGenerator:
    def __init__(self):
        self.data_path = Path('data/statistics.csv')
        self.reports_dir = Path('reports')
        self.reports_dir.mkdir(exist_ok=True)

    def load_data(self) -> pd.DataFrame:
        """Load statistics from CSV file."""
        if not self.data_path.exists():
            raise FileNotFoundError("No statistics data found")
        return pd.read_csv(self.data_path)

    def calculate_changes(self, df: pd.DataFrame) -> Dict[str, int]:
        """Calculate changes between last two days."""
        if len(df) < 2:
            return {col: 0 for col in df.columns if col != 'date'}
        
        last_two_days = df.tail(2)
        changes = {}
        for col in df.columns:
            if col != 'date':
                changes[col] = int(last_two_days.iloc[1][col]) - int(last_two_days.iloc[0][col])
        return changes

    def generate_trend_graph(self, df: pd.DataFrame, metric: str) -> go.Figure:
        """Generate a trend line graph for a specific metric."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df[metric],
            mode='lines+markers',
            name=metric.replace('_', ' ').title()
        ))
        
        fig.update_layout(
            title=f"{metric.replace('_', ' ').title()} Over Time",
            xaxis_title="Date",
            yaxis_title="Count",
            template="plotly_white"
        )
        return fig

    def generate_html_report(self, df: pd.DataFrame, changes: Dict[str, int]) -> str:
        """Generate HTML report with statistics and visualizations."""
        current_stats = df.iloc[-1].to_dict()
        date = datetime.now().strftime('%Y-%m-%d')
        
        # Generate trend graphs
        metrics = [col for col in df.columns if col != 'date']
        graphs = {metric: self.generate_trend_graph(df, metric) for metric in metrics}
        
        # Create HTML content
        html_content = f"""
        <html>
        <head>
            <title>Bursary Applications Report - {date}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .change-positive {{ color: green; }}
                .change-negative {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Bursary Applications Daily Report</h1>
            <p>Generated on: {date}</p>
            
            <div class="summary">
                <h2>Current Statistics</h2>
                <ul>
        """
        
        # Add current statistics and changes
        for metric in metrics:
            display_metric = metric.replace('_', ' ').title()
            change = changes.get(metric, 0)
            change_class = 'change-positive' if change > 0 else 'change-negative' if change < 0 else ''
            change_symbol = '+' if change > 0 else ''
            
            html_content += f"""
                <li>{display_metric}: {int(current_stats[metric])}
                    <span class="{change_class}">({change_symbol}{change} since yesterday)</span>
                </li>
            """
        
        html_content += """
                </ul>
            </div>
            
            <h2>Trends</h2>
        """
        
        # Add trend graphs
        for metric, fig in graphs.items():
            html_content += f"""
            <div id="{metric}_graph">
                {fig.to_html(full_html=False)}
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        return html_content

    def save_report(self, html_content: str) -> str:
        """Save the HTML report to file."""
        date = datetime.now().strftime('%Y-%m-%d')
        report_path = self.reports_dir / f'report_{date}.html'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return str(report_path)

def main():
    generator = ReportGenerator()
    
    # Load data
    df = generator.load_data()
    
    # Calculate changes
    changes = generator.calculate_changes(df)
    
    # Generate report
    html_content = generator.generate_html_report(df, changes)
    
    # Save report
    report_path = generator.save_report(html_content)
    print(f"Report generated: {report_path}")

if __name__ == '__main__':
    main() 