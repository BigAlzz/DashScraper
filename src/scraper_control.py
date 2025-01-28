import os
import sys
import signal
import psutil
import logging
from pathlib import Path
from subprocess import Popen
from typing import Optional
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_control.log'),
        logging.StreamHandler()
    ]
)

class ScraperControl:
    def __init__(self):
        self.pid_file = Path('scraper.pid')
        self.script_path = Path('src/scrape_dashboard.py')

    def get_pid(self) -> Optional[int]:
        """Get the PID of the running scraper if it exists."""
        if not self.pid_file.exists():
            return None
            
        try:
            pid = int(self.pid_file.read_text().strip())
            # Check if process is actually running
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                if 'python' in process.name().lower():
                    return pid
            # Clean up stale PID file
            self.pid_file.unlink()
        except (ValueError, psutil.NoSuchProcess):
            if self.pid_file.exists():
                self.pid_file.unlink()
        return None

    def start(self):
        """Start the scraper if it's not already running."""
        if self.get_pid():
            logging.info("Scraper is already running")
            return

        try:
            # Start the scraper script
            process = Popen([sys.executable, str(self.script_path)],
                          stdout=open('scraper_output.log', 'a'),
                          stderr=open('scraper_error.log', 'a'))
            
            # Save PID
            self.pid_file.write_text(str(process.pid))
            logging.info(f"Started scraper (PID: {process.pid})")
            
        except Exception as e:
            logging.error(f"Failed to start scraper: {str(e)}")

    def stop(self):
        """Stop the running scraper if it exists."""
        pid = self.get_pid()
        if not pid:
            logging.info("No running scraper found")
            return

        try:
            # Send SIGTERM signal to the process group
            os.kill(pid, signal.SIGTERM)
            logging.info(f"Stopped scraper (PID: {pid})")
            
            # Clean up PID file
            if self.pid_file.exists():
                self.pid_file.unlink()
                
        except ProcessLookupError:
            logging.error(f"Process {pid} not found")
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception as e:
            logging.error(f"Error stopping scraper: {str(e)}")

    def status(self):
        """Check the status of the scraper."""
        pid = self.get_pid()
        if not pid:
            logging.info("Scraper is not running")
            return False

        try:
            process = psutil.Process(pid)
            runtime = datetime.datetime.now() - datetime.datetime.fromtimestamp(process.create_time())
            memory = process.memory_info().rss / 1024 / 1024  # Convert to MB
            
            logging.info(f"Scraper is running:")
            logging.info(f"  PID: {pid}")
            logging.info(f"  Runtime: {runtime}")
            logging.info(f"  Memory usage: {memory:.1f} MB")
            return True
            
        except psutil.NoSuchProcess:
            logging.error(f"Process {pid} not found")
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ['start', 'stop', 'status']:
        print("Usage: python scraper_control.py [start|stop|status]")
        sys.exit(1)

    control = ScraperControl()
    command = sys.argv[1]

    if command == 'start':
        control.start()
    elif command == 'stop':
        control.stop()
    elif command == 'status':
        control.status()

if __name__ == '__main__':
    main() 