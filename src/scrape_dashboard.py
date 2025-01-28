import os
import time
from datetime import datetime
import schedule
import pandas as pd
from pathlib import Path
from typing import Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)

class DashboardScraper:
    def __init__(self):
        self.url = os.getenv('DASHBOARD_URL')
        self.username = os.getenv('DASHBOARD_USERNAME')
        self.password = os.getenv('DASHBOARD_PASSWORD')
        
        if not all([self.url, self.username, self.password]):
            raise ValueError("Missing required environment variables")
        
        # Define selectors
        self.selectors = {
            'login': {
                'username': 'input[name="Username"]',
                'password': 'input[name="Password"]',
                'submit': 'button[type="submit"]'
            },
            'dashboard': {
                'in_progress': '#divInProgressCounter .counter-value',
                'awaiting_verification': '#divAwaitingVerificationCounter .counter-value',
                'incomplete': '#divIncompleteCounter .counter-value',
                'complete': '#divCompleteCounter .counter-value',
                'not_recommended': '#divNotRecommendedCounter .counter-value',
                'recommended': '#divRecommendedCounter .counter-value',
                'approved': '#divApprovedCounter .counter-value',
                'declined': '#divDeclinedCounter .counter-value',
                'suspended': '#divSuspendedCounter .counter-value',
                'sent_back': '#divSentBackCounter .counter-value',
                'reserved': '#divReservedCounter .counter-value',
                'reinstatement_request': '#divReinstatementRequestCounter .counter-value',
                'reinstatement_approved': '#divReinstatementApprovedCounter .counter-value',
                'reinstatement_declined': '#divReinstatementDeclinedCounter .counter-value'
            }
        }
    
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    def login(self, driver):
        try:
            driver.get(self.url)
            
            # Wait for login form
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['login']['username']))
            )
            
            # Enter credentials
            username_field.send_keys(self.username)
            driver.find_element(By.CSS_SELECTOR, self.selectors['login']['password']).send_keys(self.password)
            driver.find_element(By.CSS_SELECTOR, self.selectors['login']['submit']).click()
            
            # Wait for dashboard to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.selectors['dashboard']['in_progress']))
            )
            
            logging.info("Successfully logged in")
            return True
            
        except TimeoutException:
            logging.error("Login failed - timeout waiting for elements")
            return False
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            return False
    
    def extract_statistics(self, driver) -> Dict[str, int]:
        stats = {}
        
        try:
            # Extract all counter values
            for stat_name, selector in self.selectors['dashboard'].items():
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    value = int(element.text.strip().replace(',', ''))
                    stats[stat_name] = value
                except (TimeoutException, ValueError) as e:
                    logging.warning(f"Failed to extract {stat_name}: {str(e)}")
                    stats[stat_name] = 0
            
            logging.info("Successfully extracted statistics")
            return stats
            
        except Exception as e:
            logging.error(f"Error extracting statistics: {str(e)}")
            return {}
    
    def save_statistics(self, stats: Dict[str, int]):
        try:
            # Create data directory if it doesn't exist
            Path('data').mkdir(exist_ok=True)
            
            # Prepare the data
            stats['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Load existing data or create new DataFrame
            csv_path = 'data/statistics.csv'
            if Path(csv_path).exists():
                df = pd.read_csv(csv_path)
                df = pd.concat([df, pd.DataFrame([stats])], ignore_index=True)
            else:
                df = pd.DataFrame([stats])
            
            # Save to CSV
            df.to_csv(csv_path, index=False)
            logging.info("Successfully saved statistics")
            
        except Exception as e:
            logging.error(f"Error saving statistics: {str(e)}")
    
    def scrape(self):
        driver = None
        try:
            driver = self.setup_driver()
            
            if self.login(driver):
                stats = self.extract_statistics(driver)
                if stats:
                    self.save_statistics(stats)
                    
        except Exception as e:
            logging.error(f"Scraping failed: {str(e)}")
        finally:
            if driver:
                driver.quit()

def scrape_task():
    try:
        scraper = DashboardScraper()
        scraper.scrape()
    except Exception as e:
        logging.error(f"Task failed: {str(e)}")

if __name__ == "__main__":
    # Create logs directory
    Path('logs').mkdir(exist_ok=True)
    
    # Schedule the task
    schedule_time = os.getenv('SCHEDULE_TIME', '09:00')
    schedule.every().day.at(schedule_time).do(scrape_task)
    
    # Run once immediately
    scrape_task()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60) 