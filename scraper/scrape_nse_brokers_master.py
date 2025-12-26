"""
NSE Broker Data Scraper - Master Version
===========================================
A comprehensive, all-in-one scraper with configurable output formats.
Scrapes NSE broker details one by one with proper error handling, 
logging, and skip logic.

Features:
- Configurable output switches (JSON, CSV, TXT, HTML, MongoDB)
- Smart skip logic (don't re-scrape existing data)
- Comprehensive logging with progress tracking
- Retry mechanism for failed requests
- Random delays to avoid rate limiting
- Proper error handling and recovery
"""

import requests
import os
import urllib3
from bs4 import BeautifulSoup
import json
import csv
import time
import random
import logging
from pymongo import MongoClient
import sys
from datetime import datetime, timedelta

# Import the refined parser
from parse_broker_refined import parse_broker_details, format_data_as_text, format_data_as_csv

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================================
# CONFIGURATION SECTION - MODIFY THESE SETTINGS
# ============================================================================

# --- Output Format Switches (True = Save, False = Skip) ---
SAVE_JSON = True      # Save structured JSON data
SAVE_CSV = False       # Save tabular CSV data
SAVE_TXT = False       # Save human-readable text report
SAVE_HTML = False      # Save raw HTML source
SAVE_MONGODB = True   # Upload to MongoDB database

# --- MongoDB Configuration ---
MONGO_URI = "mongodb://sa:963852@192.168.102.120:27017/"
MONGO_DB_NAME = "WEB_SCRAPING"
MONGO_COLLECTION_NAME = "Broker_list_details"
MONGO_MEMBER_LIST_COLLECTION = "Broker_member_list"

# --- File Paths ---
INPUT_CSV = "nse_members.csv"      # Input CSV with broker list
DATA_DIR = "data"                  # Directory to save scraped data
LOGS_DIR = "logs"                  # Directory to save log files

# --- Scraping Range --- TOTAL : 1377
START_INDEX = 1       # Start from this broker number
END_INDEX =  1377      # End at this broker number (change to scrape all)

# --- Request Settings ---
MAX_RETRIES = 5        # Maximum retry attempts for failed requests
REQUEST_TIMEOUT = 60   # Request timeout in seconds
MIN_DELAY = 2          # Minimum delay between requests (seconds)
MAX_DELAY = 5          # Maximum delay between requests (seconds)

# --- Long Break Configuration (Anti-Rate-Limit) ---
BREAK_AFTER_COUNT = 100    # Take a long break after this many successful scrapes
MIN_BREAK_MINUTES = 1     # Minimum break duration in minutes
MAX_BREAK_MINUTES = 10     # Maximum break duration in minutes

# --- Skip Logic ---
SKIP_EXISTING = True   # Skip brokers that are already scraped
# If True, checks for JSON file existence before scraping
# If False, re-scrapes and overwrites existing data

# --- Data Source ---
LOAD_FROM_DB = True   # Load broker list from MongoDB instead of CSV

# ============================================================================
# END OF CONFIGURATION - DO NOT MODIFY BELOW THIS LINE
# ============================================================================


class NSEBrokerScraper:
    """Main scraper class for NSE broker data."""
    
    def __init__(self):
        """Initialize the scraper with configuration."""
        self.mongo_collection = None
        self.start_time = datetime.now()  # Track start time
        self.stats = {
            "total_processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "total_retries": 0,
            "breaks_taken": 0,
            "total_break_time": 0  # in minutes
        }
        self.consecutive_success = 0  # Track consecutive successful scrapes
        
        # Ensure directories exist
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Connect to MongoDB if enabled for saving or loading
        if SAVE_MONGODB or LOAD_FROM_DB:
            self._connect_mongodb()
    
    def _setup_logging(self):
        """Configure logging system."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(LOGS_DIR, f"scraping_master_log_{timestamp}.txt")
        
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        
        # Add console output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
        
        self.log_file = log_file
        logging.info("=" * 80)
        logging.info("NSE BROKER SCRAPER - MASTER VERSION")
        logging.info("=" * 80)
        logging.info(f"Log file: {log_file}")
        logging.info("")
        
    def _connect_mongodb(self):
        """Connect to MongoDB database."""
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            client.server_info()
            
            db = client[MONGO_DB_NAME]
            self.mongo_collection = db[MONGO_COLLECTION_NAME]
            self.member_list_collection = db[MONGO_MEMBER_LIST_COLLECTION]
            logging.info(f"✓ Connected to MongoDB: {MONGO_DB_NAME}.{MONGO_COLLECTION_NAME}")
        except Exception as e:
            logging.error(f"✗ Failed to connect to MongoDB: {e}")
            logging.warning("  Continuing without MongoDB connection.")
            self.mongo_collection = None
            self.member_list_collection = None
    
    @staticmethod
    def sanitize_filename(name):
        """Remove illegal characters from filenames."""
        return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).strip()
    
    def download_page(self, url, member_name):
        """
        Download HTML content from URL with retry logic.
        
        Args:
            url (str): URL to download
            member_name (str): Broker name for logging
            
        Returns:
            tuple: (html_content, retry_count) or (None, retry_count) if failed
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        retries = 0
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    verify=False, 
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                return response.text, retries
                
            except requests.exceptions.Timeout:
                retries += 1
                logging.warning(f"  Attempt {attempt+1}/{MAX_RETRIES}: Timeout")
                time.sleep(random.uniform(2, 4))
                
            except requests.exceptions.RequestException as e:
                retries += 1
                logging.warning(f"  Attempt {attempt+1}/{MAX_RETRIES}: {str(e)[:100]}")
                time.sleep(random.uniform(2, 4))
        
        logging.error(f"  Failed to download after {MAX_RETRIES} attempts")
        return None, retries
    
    def save_html(self, html_content, target_dir, base_filename):
        """Save HTML content to file."""
        if not SAVE_HTML:
            return
        
        try:
            html_path = os.path.join(target_dir, f"{base_filename}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logging.info("  ✓ Saved HTML")
        except Exception as e:
            logging.error(f"  ✗ Failed to save HTML: {e}")
    
    def save_json(self, data, target_dir, base_filename):
        """Save data as JSON file."""
        if not SAVE_JSON:
            return
        
        try:
            json_path = os.path.join(target_dir, f"{base_filename}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info("  ✓ Saved JSON")
        except Exception as e:
            logging.error(f"  ✗ Failed to save JSON: {e}")
    
    def save_txt(self, data, target_dir, base_filename, member_name):
        """Save data as formatted text file."""
        if not SAVE_TXT:
            return
        
        try:
            txt_path = os.path.join(target_dir, f"{base_filename}.txt")
            txt_content = format_data_as_text(data, member_name)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(txt_content)
            logging.info("  ✓ Saved TXT")
        except Exception as e:
            logging.error(f"  ✗ Failed to save TXT: {e}")
    
    def save_csv(self, data, target_dir, base_filename):
        """Save data as CSV file."""
        if not SAVE_CSV:
            return
        
        try:
            csv_path = os.path.join(target_dir, f"{base_filename}.csv")
            csv_rows = format_data_as_csv(data)
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(csv_rows)
            logging.info("  ✓ Saved CSV")
        except Exception as e:
            logging.error(f"  ✗ Failed to save CSV: {e}")
    
    def save_mongodb(self, data, member_code, sr_no, member_name):
        """Upload data to MongoDB."""
        if not SAVE_MONGODB or self.mongo_collection is None:
            return
        
        try:
            filter_query = {
                "_metadata.member_code": member_code,
                "_metadata.sr_no": sr_no
            }
            self.mongo_collection.replace_one(filter_query, data, upsert=True)
            logging.info("  ✓ Saved to MongoDB")
        except Exception as e:
            logging.error(f"  ✗ Failed to save to MongoDB: {e}")
    
    def scrape_broker(self, broker_data):
        """
        Scrape a single broker's details page.
        
        Args:
            broker_data (dict): Broker information from CSV
            
        Returns:
            str: Status - 'SUCCESS', 'FAILED', or 'SKIPPED'
        """
        sr_no = broker_data.get("sr_no")
        member_name = broker_data.get("member_name")
        member_code = broker_data.get("member_code")
        details_url = broker_data.get("details_url")
        
        # Validate URL
        if not details_url:
            logging.warning(f"  ⚠ No URL found - SKIPPING")
            return "FAILED"
        
        # Create folder structure
        folder_name_raw = f"{member_name}_{sr_no}_{member_code}"
        folder_name = self.sanitize_filename(folder_name_raw)
        target_dir = os.path.join(DATA_DIR, folder_name)
        os.makedirs(target_dir, exist_ok=True)
        base_filename = folder_name
        
        # Check if already scraped (skip logic)
        if SKIP_EXISTING and SAVE_JSON:
            json_file = os.path.join(target_dir, f"{base_filename}.json")
            if os.path.exists(json_file):
                logging.info(f"  ⊘ Already scraped - SKIPPING")
                return "SKIPPED"
        
        # Step 1: Download HTML
        logging.info(f"  → Downloading from: {details_url[:80]}...")
        html_content, retries = self.download_page(details_url, member_name)
        self.stats["total_retries"] += retries
        
        if html_content is None:
            return "FAILED"
        
        # Step 2: Save HTML (if enabled)
        self.save_html(html_content, target_dir, base_filename)
        
        # Step 3: Parse HTML
        logging.info(f"  → Parsing data...")
        try:
            parsed_data = parse_broker_details(html_content)
            
            # Add metadata
            parsed_data["_metadata"] = {
                "sr_no": sr_no,
                "member_name": member_name,
                "member_code": member_code,
                "details_url": details_url,
                "scraped_at": datetime.now().isoformat(),
                "scraper_version": "3.0_master",
                "output_formats": {
                    "json": SAVE_JSON,
                    "csv": SAVE_CSV,
                    "txt": SAVE_TXT,
                    "html": SAVE_HTML,
                    "mongodb": SAVE_MONGODB
                }
            }
            
        except Exception as e:
            logging.error(f"  ✗ Parsing failed: {e}")
            return "FAILED"
        
        # Step 4: Save all enabled formats
        logging.info(f"  → Saving data...")
        self.save_json(parsed_data, target_dir, base_filename)
        self.save_txt(parsed_data, target_dir, base_filename, member_name)
        self.save_csv(parsed_data, target_dir, base_filename)
        self.save_mongodb(parsed_data, member_code, sr_no, member_name)
        
        return "SUCCESS"
    
    def load_brokers(self):
        """Load broker list from CSV file or MongoDB."""
        if LOAD_FROM_DB:
            # Load from MongoDB
            if not self.member_list_collection:
                logging.error("MongoDB not connected, cannot load broker list from DB")
                return []
            
            try:
                # Query brokers within the range
                brokers = list(self.member_list_collection.find({
                    "sr_no": {"$gte": START_INDEX, "$lte": END_INDEX}
                }).sort("sr_no", 1))  # Sort by sr_no ascending
                
                logging.info(f"✓ Loaded {len(brokers)} brokers from MongoDB")
                return brokers
            except Exception as e:
                logging.error(f"✗ Failed to load brokers from MongoDB: {e}")
                return []
        else:
            # Load from CSV file
            if not os.path.exists(INPUT_CSV):
                logging.error(f"Input CSV not found: {INPUT_CSV}")
                return []
            
            brokers = []
            with open(INPUT_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        sr = int(row.get("sr_no", 0))
                        if START_INDEX <= sr <= END_INDEX:
                            brokers.append(row)
                    except ValueError:
                        continue
            
            logging.info(f"✓ Loaded {len(brokers)} brokers from CSV")
            return brokers
    
    def print_configuration(self):
        """Print current configuration."""
        logging.info("CONFIGURATION:")
        logging.info("-" * 80)
        logging.info(f"  Broker Range: {START_INDEX} to {END_INDEX}")
        logging.info(f"  Skip Existing: {SKIP_EXISTING}")
        logging.info(f"  Load from DB: {LOAD_FROM_DB}")
        logging.info("")
        logging.info("  Output Formats:")
        logging.info(f"    HTML     : {'✓ Enabled' if SAVE_HTML else '✗ Disabled'}")
        logging.info(f"    JSON     : {'✓ Enabled' if SAVE_JSON else '✗ Disabled'}")
        logging.info(f"    CSV      : {'✓ Enabled' if SAVE_CSV else '✗ Disabled'}")
        logging.info(f"    TXT      : {'✓ Enabled' if SAVE_TXT else '✗ Disabled'}")
        logging.info(f"    MongoDB  : {'✓ Enabled' if SAVE_MONGODB else '✗ Disabled'}")
        logging.info("")
        logging.info("  Request Settings:")
        logging.info(f"    Short Delay: {MIN_DELAY}-{MAX_DELAY} seconds")
        logging.info(f"    Max Retries: {MAX_RETRIES}")
        logging.info(f"    Timeout: {REQUEST_TIMEOUT}s")
        logging.info("")
        logging.info("  Long Break Settings:")
        logging.info(f"    Break After: Every {BREAK_AFTER_COUNT} successful scrapes")
        logging.info(f"    Break Duration: {MIN_BREAK_MINUTES}-{MAX_BREAK_MINUTES} minutes")
        logging.info("")
        logging.info(f"  Data Directory: {DATA_DIR}")
        logging.info(f"  Logs Directory: {LOGS_DIR}")
        logging.info("=" * 80)
        logging.info("")
    
    def print_summary(self):
        """Print scraping summary statistics."""
        total_attempted = self.stats["total_processed"] - self.stats["skipped"]
        success_rate = (
            (self.stats["success"] / total_attempted * 100) 
            if total_attempted > 0 else 0
        )
        
        # Calculate total time from start to finish
        total_elapsed = datetime.now() - self.start_time
        total_time_str = self._format_time(total_elapsed.total_seconds())
        
        # Calculate scrap time (total time minus break time)
        scrap_time_seconds = total_elapsed.total_seconds() - (self.stats['total_break_time'] * 60)
        scrap_time_str = self._format_time(scrap_time_seconds)
        
        logging.info("")
        logging.info("=" * 80)
        logging.info("SCRAPING SUMMARY")
        logging.info("=" * 80)
        logging.info(f"Total Processed:      {self.stats['total_processed']}")
        logging.info(f"✓ Successful:         {self.stats['success']}")
        logging.info(f"✗ Failed:             {self.stats['failed']}")  
        logging.info(f"⊘ Skipped:            {self.stats['skipped']}")
        logging.info(f"Total Retry Attempts: {self.stats['total_retries']}")
        logging.info(f"Success Rate:         {success_rate:.2f}%")
        logging.info("")
        logging.info(f"Total Time (Start to End): {total_time_str}")
        logging.info(f"Active Scrap Time:     {scrap_time_str}")
        logging.info(f"Long Breaks Taken:    {self.stats['breaks_taken']}")
        logging.info(f"Total Break Time:     {self.stats['total_break_time']:.1f} minutes")
        logging.info("=" * 80)
        logging.info(f"Log file: {self.log_file}")
        logging.info("=" * 80)
    
    def get_progress_stats(self, current_index, total_brokers):
        """Calculate and return progress statistics."""
        elapsed_time = datetime.now() - self.start_time
        elapsed_seconds = elapsed_time.total_seconds()
        
        # Calculate rates
        total_attempted = self.stats["total_processed"] - self.stats["skipped"]
        if total_attempted > 0:
            avg_time_per_broker = elapsed_seconds / total_attempted
            remaining_brokers = total_brokers - current_index
            estimated_remaining_seconds = remaining_brokers * avg_time_per_broker
            expected_completion = datetime.now() + timedelta(seconds=estimated_remaining_seconds)
        else:
            avg_time_per_broker = 0
            remaining_brokers = total_brokers - current_index
            estimated_remaining_seconds = 0
            expected_completion = datetime.now()
        
        # Format time displays
        elapsed_str = self._format_time(elapsed_seconds)
        remaining_str = self._format_time(estimated_remaining_seconds)
        completion_str = expected_completion.strftime("%I:%M %p %d-%b-%Y")
        
        return {
            "elapsed_time": elapsed_str,
            "remaining_time": remaining_str,
            "expected_completion": completion_str,
            "remaining_brokers": remaining_brokers,
            "avg_time_per_broker": avg_time_per_broker
        }
    
    def _format_time(self, seconds):
        """Format seconds into human readable time string."""
        if seconds < 60:
            return f"{seconds:.0f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
    
    def print_progress_update(self, current_index, total_brokers):
        """Print detailed progress update."""
        if current_index % 10 == 0 or current_index == total_brokers:  # Update every 10 brokers or at end
            stats = self.get_progress_stats(current_index, total_brokers)
            
            logging.info("")
            logging.info("=" * 80)
            logging.info("📊 PROGRESS UPDATE")
            logging.info("=" * 80)
            logging.info(f"Current Progress:     {current_index}/{total_brokers} brokers")
            logging.info(f"Total Scrap Time:     {stats['elapsed_time']}")
            logging.info(f"Expected Time Left:   {stats['remaining_time']}")
            logging.info(f"Expected Finish At:   {stats['expected_completion']}")
            logging.info(f"Remaining Brokers:    {stats['remaining_brokers']}")
            logging.info("")
            logging.info(f"Success Rate:         {(self.stats['success'] / max(1, self.stats['total_processed'] - self.stats['skipped']) * 100):.1f}%")
            logging.info(f"Avg Time/Broker:      {stats['avg_time_per_broker']:.1f} seconds")
            logging.info("=" * 80)
            logging.info("")
    
    def print_compact_progress(self, current_index, total_brokers):
        """Print compact progress line after each broker."""
        stats = self.get_progress_stats(current_index, total_brokers)
        progress_percentage = (current_index / total_brokers * 100)
        
        logging.info(f"📊 PROGRESS: [{current_index}/{total_brokers}] | Time: {stats['elapsed_time']} | Left: {stats['remaining_time']} | ETA: {stats['expected_completion']} | Remaining: {stats['remaining_brokers']} | Progress: {progress_percentage:.1f}%")
    
    def take_long_break(self):
        """Take a long break to avoid rate limiting."""
        # Calculate random break duration
        break_minutes = random.uniform(MIN_BREAK_MINUTES, MAX_BREAK_MINUTES)
        break_seconds = break_minutes * 60
        
        # Update statistics
        self.stats['breaks_taken'] += 1
        self.stats['total_break_time'] += break_minutes
        
        # Calculate resume time
        resume_time = datetime.now()
        resume_time = resume_time.replace(second=0, microsecond=0)
        from datetime import timedelta
        resume_time = resume_time + timedelta(minutes=int(break_minutes) + 1)
        
        logging.info("")
        logging.info("=" * 80)
        logging.info("⏸  TAKING LONG BREAK (Anti-Rate-Limit)")
        logging.info("=" * 80)
        logging.info(f"  Scraped {self.consecutive_success} brokers successfully")
        logging.info(f"  Break Duration: {break_minutes:.1f} minutes ({break_minutes*60:.0f} seconds)")
        logging.info(f"  Current Time: {datetime.now().strftime('%I:%M %p')}")
        logging.info(f"  Resume Time: ~{resume_time.strftime('%I:%M %p')}")
        logging.info(f"  Progress: {self.stats['success']}/{self.stats['total_processed']} completed")
        logging.info("-" * 80)
        logging.info("  💤 Sleeping... You can safely stop with Ctrl+C and resume later")
        logging.info("=" * 80)
        logging.info("")
        
        # Sleep in smaller intervals to allow for interruption
        sleep_interval = 30  # Check every 30 seconds
        total_slept = 0
        
        try:
            while total_slept < break_seconds:
                remaining = break_seconds - total_slept
                if remaining < sleep_interval:
                    time.sleep(remaining)
                    total_slept += remaining
                else:
                    time.sleep(sleep_interval)
                    total_slept += sleep_interval
                    
                    # Show progress every 5 minutes
                    if int(total_slept) % 300 == 0:
                        elapsed_min = total_slept / 60
                        remaining_min = (break_seconds - total_slept) / 60
                        logging.info(f"  ⏳ Break progress: {elapsed_min:.0f}m elapsed, {remaining_min:.0f}m remaining...")
        
        except KeyboardInterrupt:
            logging.info("")
            logging.info("  ⚠ Break interrupted by user. Resuming scraping...")
            logging.info("")
            return
        
        logging.info("")
        logging.info("  ✓ Break completed! Resuming scraping...")
        logging.info("")
        
        # Reset consecutive counter
        self.consecutive_success = 0
    
    def run(self):
        """Main scraping workflow."""
        # Print configuration
        self.print_configuration()
        
        # Load brokers
        brokers = self.load_brokers()
        total_brokers = len(brokers)
        
        if total_brokers == 0:
            logging.error("No brokers found in the specified range!")
            return
        
        logging.info(f"Found {total_brokers} brokers to process")
        logging.info("=" * 80)
        logging.info("")
        
        # Process each broker
        for i, broker in enumerate(brokers, 1):
            member_name = broker.get("member_name", "Unknown")
            sr_no = broker.get("sr_no", "?")
            
            logging.info(f"[{i}/{total_brokers}] {member_name} (Sr: {sr_no})")
            
            self.stats["total_processed"] += 1
            status = self.scrape_broker(broker)
            
            if status == "SUCCESS":
                self.stats["success"] += 1
                self.consecutive_success += 1
                
                # Check if we need to take a long break
                if self.consecutive_success >= BREAK_AFTER_COUNT and i < total_brokers:
                    self.take_long_break()
                else:
                    # Regular short delay
                    delay = random.uniform(MIN_DELAY, MAX_DELAY)
                    logging.info(f"  ✓ SUCCESS - Waiting {delay:.2f}s...")
                    time.sleep(delay)
                
            elif status == "FAILED":
                self.stats["failed"] += 1
                logging.error(f"  ✗ FAILED")
                
            elif status == "SKIPPED":
                self.stats["skipped"] += 1
            
            # Print compact progress after each broker
            self.print_compact_progress(i, total_brokers)
            
            # Print detailed progress update every 10 brokers or at end
            self.print_progress_update(i, total_brokers)
            
            logging.info("")
        
        # Print summary
        self.print_summary()


def main():
    """Entry point for the scraper."""
    try:
        scraper = NSEBrokerScraper()
        scraper.run()
        
    except KeyboardInterrupt:
        logging.info("\n\n⚠ Scraping interrupted by user (Ctrl+C)")
        
    except Exception as e:
        logging.error(f"\n\n✗ Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
