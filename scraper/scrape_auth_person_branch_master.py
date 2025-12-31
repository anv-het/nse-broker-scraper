"""
NSE Broker Auth Person & Branch Data Scraper - Dynamic Master Version
======================================================================
A comprehensive, dynamic scraper for NSE broker authorized person and dealing office data.
Scrapes auth person and branch details for all brokers with proper error handling, 
logging, and configurable output formats.

Features:
- Dynamic broker loading from MongoDB
- Configurable output switches (JSON, CSV, TXT, HTML, MongoDB)
- Smart skip logic (don't re-scrape existing data)
- Comprehensive logging with progress tracking
- Retry mechanism for failed requests
- Random delays to avoid rate limiting
- Proper error handling and recovery
- Statistics tracking and reporting
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
from urllib.parse import quote

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================================
# CONFIGURATION SECTION - MODIFY THESE SETTINGS
# ============================================================================

# --- Output Format Switches (True = Save, False = Skip) ---
SAVE_JSON = True      # Save structured JSON data
SAVE_CSV = False      # Save tabular CSV data
SAVE_TXT = False      # Save human-readable text report
SAVE_HTML = False     # Save raw HTML source
SAVE_MONGODB = True   # Upload to MongoDB database

# --- MongoDB Configuration ---
MONGO_URI = "mongodb://sa:963852@192.168.102.120:27017/"
MONGO_DB_NAME = "WEB_SCRAPING"
MONGO_MEMBER_LIST_COLLECTION = "Broker_member_list"
MONGO_DEALING_OFFICE_COLLECTION = "Broker_list_search_dealing_office"
MONGO_AUTH_PERSON_COLLECTION = "Broker_member_Auth_Person"

# --- File Paths ---
DATA_DIR = "auth_person_branch_data"  # Directory to save scraped data
LOGS_DIR = "logs"                     # Directory to save log files

# --- Scraping Range --- 
START_INDEX = 1       # Start from this broker number (sr_no)
END_INDEX = 1377        # End at this broker number (change to scrape all)

# --- Request Settings ---
MAX_RETRIES = 5        # Maximum retry attempts for failed requests
REQUEST_TIMEOUT = 60   # Request timeout in seconds
MIN_DELAY = 2          # Minimum delay between requests (seconds)
MAX_DELAY = 5          # Maximum delay between requests (seconds)

# --- Long Break Configuration (Anti-Rate-Limit) ---
BREAK_AFTER_COUNT = 50   # Take a long break after this many successful scrapes
MIN_BREAK_MINUTES = 2      # Minimum break duration in minutes
MAX_BREAK_MINUTES = 5      # Maximum break duration in minutes

# --- Skip Logic ---
SKIP_EXISTING = False   # Skip brokers that are already scraped

# --- NSE Configuration ---
BASE_URL = "https://enit.nseindia.com"
NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://www.nseindia.com/"
}

# ============================================================================
# END OF CONFIGURATION - DO NOT MODIFY BELOW THIS LINE
# ============================================================================


class NSEAuthPersonBranchScraper:
    """Main scraper class for NSE broker auth person and branch data."""
    
    def __init__(self):
        """Initialize the scraper with configuration."""
        self.mongo_collections = {}
        self.start_time = datetime.now()
        self.stats = {
            "total_processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "total_retries": 0,
            "breaks_taken": 0,
            "total_break_time": 0,
            "auth_person_scraped": 0,
            "dealing_office_scraped": 0,
            "auth_person_failed": 0,
            "dealing_office_failed": 0
        }
        self.consecutive_success = 0
        
        # Ensure directories exist
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Connect to MongoDB
        self._connect_mongodb()
        
        # Setup request session
        self.session = requests.Session()
        self._init_session()
    
    def _setup_logging(self):
        """Configure logging system."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(LOGS_DIR, f"auth_person_branch_scraping_{timestamp}.log")
        
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
        logging.info("NSE AUTH PERSON & BRANCH SCRAPER - DYNAMIC MASTER VERSION")
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
            self.mongo_collections = {
                'member_list': db[MONGO_MEMBER_LIST_COLLECTION],
                'dealing_office': db[MONGO_DEALING_OFFICE_COLLECTION],
                'auth_person': db[MONGO_AUTH_PERSON_COLLECTION]
            }
            logging.info(f"✓ Connected to MongoDB: {MONGO_DB_NAME}")
        except Exception as e:
            logging.error(f"✗ Failed to connect to MongoDB: {e}")
            raise Exception("MongoDB connection required for this scraper")
    
    def _init_session(self):
        """Initialize request session with NSE."""
        try:
            self.session.get("https://www.nseindia.com", headers=NSE_HEADERS, timeout=(10, 40))
            logging.info("✓ Initialized NSE session")
        except Exception as e:
            logging.warning(f"⚠ Session initialization warning: {e}")
    
    @staticmethod
    def sanitize_filename(name):
        """Remove illegal characters from filenames."""
        return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).strip()
    
    def download_page(self, url, description="page"):
        """
        Download HTML content from URL with retry logic.
        
        Args:
            url (str): URL to download
            description (str): Description for logging
            
        Returns:
            tuple: (html_content, retry_count) or (None, retry_count) if failed
        """
        retries = 0
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url, 
                    headers=NSE_HEADERS, 
                    verify=False, 
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                return response.text, retries
                
            except requests.exceptions.Timeout:
                retries += 1
                logging.warning(f"    Attempt {attempt+1}/{MAX_RETRIES}: Timeout for {description}")
                time.sleep(random.uniform(2, 4))
                
            except requests.exceptions.RequestException as e:
                retries += 1
                logging.warning(f"    Attempt {attempt+1}/{MAX_RETRIES}: {str(e)[:100]} for {description}")
                time.sleep(random.uniform(2, 4))
        
        logging.error(f"    Failed to download {description} after {MAX_RETRIES} attempts")
        return None, retries
    
    def parse_table(self, html_text, table_id="resultTable"):
        """Parse HTML table to extract data rows."""
        try:
            soup = BeautifulSoup(html_text, "html.parser")
            table = soup.find("table", {"id": table_id})
            
            if not table:
                logging.warning(f"    No table found with id '{table_id}'")
                return []
            
            rows = table.find_all("tr")[1:]  # skip header
            
            data = []
            for row in rows:
                cols = [td.get_text(strip=True) for td in row.find_all("td")]
                if cols and len(cols) > 1:  # Ensure we have meaningful data
                    data.append(cols)
            
            return data
            
        except Exception as e:
            logging.error(f"    Error parsing table: {e}")
            return []
    
    def parse_auth_person_data(self, html_content):
        """Parse authorized person data from HTML."""
        try:
            auth_rows = self.parse_table(html_content)
            auth_data = []
            
            for row in auth_rows:
                if len(row) >= 16:  # Ensure we have all required columns
                    auth_data.append({
                        "sr_no": row[0] if len(row) > 0 else "",
                        "authorised_person_name": row[1] if len(row) > 1 else "",
                        "authorized_person_trade_name": row[2] if len(row) > 2 else "",
                        "registration_no": row[3] if len(row) > 3 else "",
                        "registration_date": row[4] if len(row) > 4 else "",
                        "number_of_terminals": row[5] if len(row) > 5 else "",
                        "type_of_entity": row[6] if len(row) > 6 else "",
                        "ap_contact_person_name": row[7] if len(row) > 7 else "",
                        "ap_email_id": row[8] if len(row) > 8 else "",
                        "contact_no": row[9] if len(row) > 9 else "",
                        "traded_segments": row[10] if len(row) > 10 else "",
                        "status": row[11] if len(row) > 11 else "",
                        "address": row[12] if len(row) > 12 else "",
                        "city": row[13] if len(row) > 13 else "",
                        "state": row[14] if len(row) > 14 else "",
                        "pincode": row[15] if len(row) > 15 else ""
                    })
            
            return auth_data
            
        except Exception as e:
            logging.error(f"    Error parsing auth person data: {e}")
            return []
    
    def parse_dealing_office_data(self, html_content):
        """Parse dealing office data from HTML."""
        try:
            office_rows = self.parse_table(html_content)
            office_data = []
            
            for row in office_rows:
                if len(row) >= 7:  # Ensure we have all required columns
                    office_data.append({
                        "sr_no": row[0] if len(row) > 0 else "",
                        "office_type": row[1] if len(row) > 1 else "",
                        "contact_person_name": row[2] if len(row) > 2 else "",
                        "address": row[3] if len(row) > 3 else "",
                        "city": row[4] if len(row) > 4 else "",
                        "state": row[5] if len(row) > 5 else "",
                        "pincode": row[6] if len(row) > 6 else ""
                    })
            
            return office_data
            
        except Exception as e:
            logging.error(f"    Error parsing dealing office data: {e}")
            return []
    
    def save_html(self, html_content, target_dir, filename):
        """Save HTML content to file."""
        if not SAVE_HTML:
            return
        
        try:
            html_path = os.path.join(target_dir, f"{filename}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logging.info(f"      ✓ Saved HTML: {filename}.html")
        except Exception as e:
            logging.error(f"      ✗ Failed to save HTML: {e}")
    
    def save_json(self, data, target_dir, filename):
        """Save data as JSON file."""
        if not SAVE_JSON:
            return
        
        try:
            json_path = os.path.join(target_dir, f"{filename}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logging.info(f"      ✓ Saved JSON: {filename}.json")
        except Exception as e:
            logging.error(f"      ✗ Failed to save JSON: {e}")
    
    def save_csv(self, data, target_dir, filename):
        """Save data as CSV file."""
        if not SAVE_CSV:
            return
        
        try:
            csv_path = os.path.join(target_dir, f"{filename}.csv")
            
            if data and len(data) > 0:
                # Write CSV with headers
                with open(csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                    
                logging.info(f"      ✓ Saved CSV: {filename}.csv")
            else:
                logging.warning(f"      ⚠ No data to save for CSV: {filename}.csv")
                
        except Exception as e:
            logging.error(f"      ✗ Failed to save CSV: {e}")
    
    def save_txt(self, data, target_dir, filename, title):
        """Save data as formatted text file."""
        if not SAVE_TXT:
            return
        
        try:
            txt_path = os.path.join(target_dir, f"{filename}.txt")
            
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"{title}\n")
                f.write("=" * len(title) + "\n\n")
                
                if data and len(data) > 0:
                    for i, item in enumerate(data, 1):
                        f.write(f"{i}. ")
                        for key, value in item.items():
                            f.write(f"{key}: {value}, ")
                        f.write("\n\n")
                else:
                    f.write("No data found.\n")
            
            logging.info(f"      ✓ Saved TXT: {filename}.txt")
        except Exception as e:
            logging.error(f"      ✗ Failed to save TXT: {e}")
    
    def save_to_mongodb(self, data_type, broker_data, scraped_data):
        """Save data to MongoDB collections."""
        if not SAVE_MONGODB:
            return
        
        try:
            mem_id = str(broker_data.get('internal_id', ''))
            member_code = str(broker_data.get('member_code', ''))
            member_name = broker_data.get('member_name', '')
            sr_no = broker_data.get('sr_no', '')
            
            if data_type == "auth_person":
                document = {
                    "broker_name": member_name,
                    "mem_id": mem_id,
                    "member_code": member_code,
                    "sr_no": sr_no,
                    "authorized_persons": scraped_data,
                    "scraped_at": datetime.now().isoformat(),
                    "scraper_version": "auth_person_branch_master_v1.0"
                }
                
                filter_query = {"mem_id": mem_id, "member_code": member_code}
                self.mongo_collections['auth_person'].replace_one(
                    filter_query, document, upsert=True
                )
                logging.info(f"      ✓ Saved Auth Person data to MongoDB")
                
            elif data_type == "dealing_office":
                document = {
                    "broker_name": member_name,
                    "mem_id": mem_id,
                    "member_code": member_code,
                    "sr_no": sr_no,
                    "offices": scraped_data,
                    "scraped_at": datetime.now().isoformat(),
                    "scraper_version": "auth_person_branch_master_v1.0"
                }
                
                filter_query = {"mem_id": mem_id, "member_code": member_code}
                self.mongo_collections['dealing_office'].replace_one(
                    filter_query, document, upsert=True
                )
                logging.info(f"      ✓ Saved Dealing Office data to MongoDB")
                
        except Exception as e:
            logging.error(f"      ✗ Failed to save {data_type} to MongoDB: {e}")
    
    def scrape_broker_auth_branch_data(self, broker_data):
        """
        Scrape auth person and dealing office data for a single broker.
        
        Args:
            broker_data (dict): Broker information from MongoDB
            
        Returns:
            dict: Status with success/failure details
        """
        sr_no = broker_data.get("sr_no")
        member_name = broker_data.get("member_name")
        member_code = broker_data.get("member_code")
        internal_id = broker_data.get("internal_id")
        
        # Validate required data
        if not all([member_name, member_code, internal_id]):
            logging.warning(f"    ⚠ Missing required data - SKIPPING")
            return {"status": "FAILED", "reason": "missing_data"}
        
        # Create folder structure
        folder_name_raw = f"{member_name}_{sr_no}_{member_code}"
        folder_name = self.sanitize_filename(folder_name_raw)
        target_dir = os.path.join(DATA_DIR, folder_name)
        os.makedirs(target_dir, exist_ok=True)
        
        # Check if already scraped (skip logic)
        if SKIP_EXISTING and SAVE_JSON:
            auth_json = os.path.join(target_dir, "auth_person.json")
            office_json = os.path.join(target_dir, "dealing_office.json")
            if os.path.exists(auth_json) and os.path.exists(office_json):
                logging.info(f"    ⊘ Already scraped - SKIPPING")
                return {"status": "SKIPPED", "reason": "already_exists"}
        
        # Encode member name for URLs
        encoded_member_name = quote(member_name)
        
        # Generate URLs
        auth_search_url = f"{BASE_URL}/MemDirWeb/searchAuthPerson?step=searchAuthPersonList&memId={internal_id}&memberName={encoded_member_name}&memberCode={member_code}"
        office_search_url = f"{BASE_URL}/MemDirWeb/searchDealingOffice?step=searchDealingOfficeList&memId={internal_id}&memberName={encoded_member_name}&memberCode={member_code}"
        
        results = {
            "auth_person": {"success": False, "data": [], "retries": 0},
            "dealing_office": {"success": False, "data": [], "retries": 0}
        }
        
        # Scrape Auth Person Data
        logging.info(f"    → Downloading Auth Person data...")
        auth_html, auth_retries = self.download_page(auth_search_url, "Auth Person page")
        results["auth_person"]["retries"] = auth_retries
        
        if auth_html:
            # Save HTML
            self.save_html(auth_html, target_dir, "auth_person_raw")
            
            # Parse data
            auth_data = self.parse_auth_person_data(auth_html)
            results["auth_person"]["data"] = auth_data
            results["auth_person"]["success"] = True
            
            # Save in various formats
            logging.info(f"    → Saving Auth Person data ({len(auth_data)} records)...")
            self.save_json(auth_data, target_dir, "auth_person")
            self.save_csv(auth_data, target_dir, "auth_person")
            self.save_txt(auth_data, target_dir, "auth_person", f"Authorized Persons - {member_name}")
            self.save_to_mongodb("auth_person", broker_data, auth_data)
            
            self.stats["auth_person_scraped"] += 1
        else:
            self.stats["auth_person_failed"] += 1
        
        # Scrape Dealing Office Data
        logging.info(f"    → Downloading Dealing Office data...")
        office_html, office_retries = self.download_page(office_search_url, "Dealing Office page")
        results["dealing_office"]["retries"] = office_retries
        
        if office_html:
            # Save HTML
            self.save_html(office_html, target_dir, "dealing_office_raw")
            
            # Parse data
            office_data = self.parse_dealing_office_data(office_html)
            results["dealing_office"]["data"] = office_data
            results["dealing_office"]["success"] = True
            
            # Save in various formats
            logging.info(f"    → Saving Dealing Office data ({len(office_data)} records)...")
            self.save_json(office_data, target_dir, "dealing_office")
            self.save_csv(office_data, target_dir, "dealing_office")
            self.save_txt(office_data, target_dir, "dealing_office", f"Dealing Offices - {member_name}")
            self.save_to_mongodb("dealing_office", broker_data, office_data)
            
            self.stats["dealing_office_scraped"] += 1
        else:
            self.stats["dealing_office_failed"] += 1
        
        # Update overall retry count
        self.stats["total_retries"] += auth_retries + office_retries
        
        # Determine overall status
        if results["auth_person"]["success"] and results["dealing_office"]["success"]:
            return {"status": "SUCCESS", "auth_records": len(auth_data), "office_records": len(office_data)}
        elif results["auth_person"]["success"] or results["dealing_office"]["success"]:
            return {"status": "PARTIAL", "results": results}
        else:
            return {"status": "FAILED", "reason": "both_failed"}
    
    def load_brokers_from_db(self):
        """Load broker list from MongoDB."""
        try:
            # Query brokers within the range
            brokers = list(self.mongo_collections['member_list'].find({
                "sr_no": {"$gte": START_INDEX, "$lte": END_INDEX}
            }).sort("sr_no", 1))
            
            logging.info(f"✓ Loaded {len(brokers)} brokers from MongoDB")
            return brokers
            
        except Exception as e:
            logging.error(f"✗ Failed to load brokers from MongoDB: {e}")
            return []
    
    def print_configuration(self):
        """Print current configuration."""
        logging.info("CONFIGURATION:")
        logging.info("-" * 80)
        logging.info(f"  Broker Range: {START_INDEX} to {END_INDEX}")
        logging.info(f"  Skip Existing: {SKIP_EXISTING}")
        logging.info("")
        logging.info("  Output Formats:")
        logging.info(f"    HTML     : {'✓ Enabled' if SAVE_HTML else '✗ Disabled'}")
        logging.info(f"    JSON     : {'✓ Enabled' if SAVE_JSON else '✗ Disabled'}")
        logging.info(f"    CSV      : {'✓ Enabled' if SAVE_CSV else '✗ Disabled'}")
        logging.info(f"    TXT      : {'✓ Enabled' if SAVE_TXT else '✗ Disabled'}")
        logging.info(f"    MongoDB  : {'✓ Enabled' if SAVE_MONGODB else '✗ Disabled'}")
        logging.info("")
        logging.info("  MongoDB Collections:")
        logging.info(f"    Source     : {MONGO_MEMBER_LIST_COLLECTION}")
        logging.info(f"    Auth Person: {MONGO_AUTH_PERSON_COLLECTION}")
        logging.info(f"    Dealing Off: {MONGO_DEALING_OFFICE_COLLECTION}")
        logging.info("")
        logging.info("  Request Settings:")
        logging.info(f"    Delay: {MIN_DELAY}-{MAX_DELAY} seconds")
        logging.info(f"    Max Retries: {MAX_RETRIES}")
        logging.info(f"    Timeout: {REQUEST_TIMEOUT}s")
        logging.info("")
        logging.info("  Break Settings:")
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
        
        # Calculate total time
        total_elapsed = datetime.now() - self.start_time
        total_time_str = self._format_time(total_elapsed.total_seconds())
        
        # Calculate scrap time (total time minus break time)
        scrap_time_seconds = total_elapsed.total_seconds() - (self.stats['total_break_time'] * 60)
        scrap_time_str = self._format_time(scrap_time_seconds)
        
        logging.info("")
        logging.info("=" * 80)
        logging.info("AUTH PERSON & BRANCH SCRAPING SUMMARY")
        logging.info("=" * 80)
        logging.info(f"Total Processed:      {self.stats['total_processed']}")
        logging.info(f"✓ Successful:         {self.stats['success']}")
        logging.info(f"✗ Failed:             {self.stats['failed']}")  
        logging.info(f"⊘ Skipped:            {self.stats['skipped']}")
        logging.info(f"Success Rate:         {success_rate:.2f}%")
        logging.info("")
        logging.info("Detailed Statistics:")
        logging.info(f"  Auth Person Scraped:    {self.stats['auth_person_scraped']}")
        logging.info(f"  Auth Person Failed:     {self.stats['auth_person_failed']}")
        logging.info(f"  Dealing Office Scraped: {self.stats['dealing_office_scraped']}")
        logging.info(f"  Dealing Office Failed:  {self.stats['dealing_office_failed']}")
        logging.info(f"  Total Retry Attempts:   {self.stats['total_retries']}")
        logging.info("")
        logging.info(f"Total Time:           {total_time_str}")
        logging.info(f"Active Scrap Time:    {scrap_time_str}")
        logging.info(f"Long Breaks Taken:    {self.stats['breaks_taken']}")
        logging.info(f"Total Break Time:     {self.stats['total_break_time']:.1f} minutes")
        logging.info("=" * 80)
        logging.info(f"Log file: {self.log_file}")
        logging.info("=" * 80)
    
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
    
    def take_long_break(self):
        """Take a long break to avoid rate limiting."""
        break_minutes = random.uniform(MIN_BREAK_MINUTES, MAX_BREAK_MINUTES)
        break_seconds = break_minutes * 60
        
        self.stats['breaks_taken'] += 1
        self.stats['total_break_time'] += break_minutes
        
        resume_time = datetime.now() + timedelta(minutes=int(break_minutes) + 1)
        
        logging.info("")
        logging.info("=" * 80)
        logging.info("⏸  TAKING LONG BREAK (Anti-Rate-Limit)")
        logging.info("=" * 80)
        logging.info(f"  Scraped {self.consecutive_success} brokers successfully")
        logging.info(f"  Break Duration: {break_minutes:.1f} minutes")
        logging.info(f"  Resume Time: ~{resume_time.strftime('%I:%M %p')}")
        logging.info("  💤 Sleeping...")
        logging.info("=" * 80)
        logging.info("")
        
        try:
            time.sleep(break_seconds)
        except KeyboardInterrupt:
            logging.info("  ⚠ Break interrupted by user. Resuming...")
        
        logging.info("  ✓ Break completed! Resuming scraping...")
        self.consecutive_success = 0
    
    def run(self):
        """Main scraping workflow."""
        # Print configuration
        self.print_configuration()
        
        # Load brokers
        brokers = self.load_brokers_from_db()
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
            result = self.scrape_broker_auth_branch_data(broker)
            
            if result["status"] == "SUCCESS":
                self.stats["success"] += 1
                self.consecutive_success += 1
                logging.info(f"  ✓ SUCCESS - Auth: {result.get('auth_records', 0)}, Office: {result.get('office_records', 0)} records")
                
                # Check if we need to take a long break
                if self.consecutive_success >= BREAK_AFTER_COUNT and i < total_brokers:
                    self.take_long_break()
                else:
                    delay = random.uniform(MIN_DELAY, MAX_DELAY)
                    logging.info(f"    Waiting {delay:.2f}s...")
                    time.sleep(delay)
                
            elif result["status"] == "PARTIAL":
                self.stats["success"] += 1  # Count as success since we got some data
                logging.warning(f"  ⚠ PARTIAL SUCCESS - Some data retrieved")
                
            elif result["status"] == "FAILED":
                self.stats["failed"] += 1
                logging.error(f"  ✗ FAILED - {result.get('reason', 'unknown error')}")
                
            elif result["status"] == "SKIPPED":
                self.stats["skipped"] += 1
            
            logging.info("")
        
        # Print summary
        self.print_summary()


def main():
    """Entry point for the scraper."""
    try:
        scraper = NSEAuthPersonBranchScraper()
        scraper.run()
        
    except KeyboardInterrupt:
        logging.info("\n\n⚠ Scraping interrupted by user (Ctrl+C)")
        
    except Exception as e:
        logging.error(f"\n\n✗ Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
