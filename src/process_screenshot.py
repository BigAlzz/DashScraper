import os
import pytesseract
from PIL import Image
from datetime import datetime
from typing import Dict

class ScreenshotProcessor:
    def __init__(self):
        # Configure Tesseract path for Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def extract_text(self, image_path: str) -> str:
        """Extract text from the screenshot using OCR."""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")

    def parse_statistics(self, text: str) -> Dict[str, int]:
        """Parse the extracted text to get application statistics."""
        stats = {
            'in_progress': 0,
            'awaiting_verification': 0,
            'complete': 0,
            'recommended': 0,
            'approved': 0
        }
        
        # Add your parsing logic here based on the dashboard layout
        # This is a placeholder - you'll need to adjust based on your actual dashboard format
        lines = text.split('\n')
        for line in lines:
            if 'In Progress' in line:
                stats['in_progress'] = int(''.join(filter(str.isdigit, line)))
            elif 'Awaiting Verification' in line:
                stats['awaiting_verification'] = int(''.join(filter(str.isdigit, line)))
            elif 'Complete' in line:
                stats['complete'] = int(''.join(filter(str.isdigit, line)))
            elif 'Recommended' in line:
                stats['recommended'] = int(''.join(filter(str.isdigit, line)))
            elif 'Approved' in line:
                stats['approved'] = int(''.join(filter(str.isdigit, line)))

        return stats

    def save_statistics(self, stats: Dict[str, int]):
        """Save the statistics to a CSV file."""
        import pandas as pd
        from pathlib import Path

        date = datetime.now().strftime('%Y-%m-%d')
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)
        
        csv_path = data_dir / 'statistics.csv'
        
        # Create new DataFrame with current stats
        new_data = pd.DataFrame([{
            'date': date,
            **stats
        }])
        
        # Append to existing file or create new one
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df = pd.concat([df, new_data], ignore_index=True)
        else:
            df = new_data
            
        df.to_csv(csv_path, index=False)

def main(image_path: str):
    processor = ScreenshotProcessor()
    
    # Extract text from image
    text = processor.extract_text(image_path)
    
    # Parse statistics
    stats = processor.parse_statistics(text)
    
    # Save statistics
    processor.save_statistics(stats)
    
    return stats

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python process_screenshot.py <path_to_screenshot>")
        sys.exit(1)
        
    stats = main(sys.argv[1])
    print("Extracted statistics:", stats) 