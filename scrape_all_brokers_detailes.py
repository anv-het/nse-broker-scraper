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
from datetime import datetime

START_INDEX = 1
END_INDEX = 100

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
MONGO_URI = "mongodb://sa:963852@192.168.102.120:27017/"
MONGO_DB_NAME = "WEB_SCRAPING"
MONGO_COLLECTION_NAME = "Broker_list_details"

INPUT_CSV = "nse_members.csv"
DATA_DIR = "data"
LOGS_DIR = "logs"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Logging Setup
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = os.path.join(LOGS_DIR, f"scraping_log_{timestamp}.txt")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger().addHandler(console_handler)

def get_mongo_collection():
    try:
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        return collection
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        return None

def clean_text(text):
    if not text:
        return ""
    return " ".join(text.split())

def sanitize_filename(name):
    """Removes illegal characters from filenames."""
    return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_', '-')).strip()

def parse_table(table):
    """Parses a generic HTML table into a list of dictionaries."""
    rows = table.find_all("tr")
    data = []
    headers = []
    
    thead = table.find("thead")
    if thead:
        header_cells = thead.find_all(["th", "td"])
        headers = [clean_text(cell.get_text()) for cell in header_cells]
    
    if not headers and rows:
        first_row_cells = rows[0].find_all(["th", "td"])
        if any(cell.name == "th" for cell in first_row_cells):
             headers = [clean_text(cell.get_text()) for cell in first_row_cells]
             rows = rows[1:]

    for row in rows:
        cells = row.find_all(["td", "th"])
        row_data = {}
        values = [clean_text(cell.get_text()) for cell in cells]
        
        if not any(values):
            continue

        if headers:
            for i, header in enumerate(headers):
                if i < len(values):
                    row_data[header] = values[i]
                else:
                    row_data[header] = ""
            if len(values) > len(headers):
                for i in range(len(headers), len(values)):
                    row_data[f"Column_{i+1}"] = values[i]
        else:
            for i, val in enumerate(values):
                row_data[f"Column_{i+1}"] = val
        
        if row_data:
            data.append(row_data)
    return data

def parse_accordion_content(content_div):
    tables = content_div.find_all("table")
    if tables:
        all_table_data = []
        for table in tables:
            t_data = parse_table(table)
            if t_data:
                all_table_data.extend(t_data)
        return all_table_data
    return clean_text(content_div.get_text())

def scrape_broker(broker_data, mongo_collection):
    sr_no = broker_data.get("sr_no")
    member_name = broker_data.get("member_name")
    member_code = broker_data.get("member_code")
    details_url = broker_data.get("details_url")

    if not details_url:
        logging.warning(f"Skipping {member_name} (Sr: {sr_no}): No details URL.")
        return "FAILED", 0

    # Construct Folder Name: member_name + sr_no + member_code
    folder_name_raw = f"{member_name}_{sr_no}_{member_code}"
    folder_name = sanitize_filename(folder_name_raw)
    
    # Target Directory inside DATA_DIR
    target_dir = os.path.join(DATA_DIR, folder_name)
    
    # Check if already exists
    if os.path.exists(target_dir):
        logging.info(f"Skipping {member_name} (Sr: {sr_no}): Already scraped (Folder exists).")
        return "SKIPPED", 0
    
    # Create Directory
    os.makedirs(target_dir, exist_ok=True)
    
    # Base Filename for files inside
    base_filename = folder_name 

    logging.info(f"Scraping {member_name} (Sr: {sr_no})...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    html_content = ""
    max_retries = 5
    success = False
    retries = 0

    for attempt in range(max_retries):
        try:
            response = requests.get(details_url, headers=headers, verify=False, timeout=60)
            response.raise_for_status()
            html_content = response.text
            success = True
            break
        except Exception as e:
            retries += 1
            logging.warning(f"Attempt {attempt+1}/{max_retries} failed for {member_name}: {e}")
            time.sleep(random.uniform(2, 5)) 

    if not success:
        logging.error(f"Failed to scrape {member_name} after {max_retries} attempts.")
        # Clean up empty directory if failed?
        # os.rmdir(target_dir) 
        return "FAILED", retries

    # Save HTML
    html_path = os.path.join(target_dir, f"{base_filename}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Parse Data
    soup = BeautifulSoup(html_content, "html.parser")
    full_data = {
        "meta_sr_no": sr_no,
        "meta_member_name": member_name,
        "meta_member_code": member_code,
        "meta_url": details_url
    }

    # Inputs
    inputs = soup.find_all("input")
    for inp in inputs:
        name = inp.get("name") or inp.get("id")
        val = inp.get("value")
        if name and val and val.strip():
            full_data[f"Input_{name}"] = clean_text(val)

    # Accordions
    accordions = soup.find_all("div", class_="accordion-item")
    for acc in accordions:
        header = acc.find("div", class_="accordion-header")
        content = acc.find("div", class_="accordion-content")
        if header and content:
            header_text = clean_text(header.get_text())
            key = f"Section_{header_text}"
            acc_data = parse_accordion_content(content)
            full_data[key] = acc_data

    # Dropdowns
    selects = soup.find_all("select")
    dropdown_data = {}
    for sel in selects:
        sel_id = sel.get("id") or "unknown_select"
        options = [opt.get("value") for opt in sel.find_all("option")]
        dropdown_data[sel_id] = options
    full_data["Dropdown_Options"] = dropdown_data

    # Save JSON
    json_path = os.path.join(target_dir, f"{base_filename}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4)

    # Save TXT
    txt_path = os.path.join(target_dir, f"{base_filename}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"BROKER DETAILS REPORT: {member_name}\n")
        f.write("====================================\n\n")
        for key, value in full_data.items():
            f.write(f"--- {key} ---\n")
            if isinstance(value, list):
                for item in value:
                    f.write(f"{item}\n")
            elif isinstance(value, dict):
                for k, v in value.items():
                    f.write(f"  {k}: {v}\n")
            else:
                f.write(f"{value}\n")
            f.write("\n")

    # Save CSV
    csv_path = os.path.join(target_dir, f"{base_filename}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Section/Key", "Sub-Key/Index", "Value"])
        for key, value in full_data.items():
            if isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        for k, v in item.items():
                            writer.writerow([key, f"Item_{i+1}_{k}", v])
                    else:
                        writer.writerow([key, f"Item_{i+1}", item])
            elif isinstance(value, dict):
                for k, v in value.items():
                    writer.writerow([key, k, v])
            else:
                writer.writerow([key, "", value])

    # Save to MongoDB
    if mongo_collection is not None:
        try:
            filter_query = {"meta_member_code": member_code, "meta_sr_no": sr_no}
            mongo_collection.replace_one(filter_query, full_data, upsert=True)
            logging.info(f"Saved to MongoDB: {member_name}")
        except Exception as e:
            logging.error(f"Failed to save to MongoDB for {member_name}: {e}")

    return "SUCCESS", retries

def main():
    # --- Configuration for Run ---
    # -----------------------------

    logging.info(f"Starting scraping process. Range: {START_INDEX} to {END_INDEX}")
    logging.info(f"Data Directory: {DATA_DIR}")
    logging.info(f"Logs Directory: {LOGS_DIR}")

    mongo_collection = get_mongo_collection()
    if mongo_collection is None:
        logging.warning("Proceeding without MongoDB connection.")

    # Read CSV
    brokers_to_scrape = []
    if not os.path.exists(INPUT_CSV):
        logging.error(f"Input CSV {INPUT_CSV} not found.")
        return

    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                sr = int(row.get("sr_no", 0))
                if START_INDEX <= sr <= END_INDEX:
                    brokers_to_scrape.append(row)
            except ValueError:
                continue
    
    logging.info(f"Found {len(brokers_to_scrape)} brokers in range.")

    stats = {
        "total_processed": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "total_retries": 0
    }

    for broker in brokers_to_scrape:
        stats["total_processed"] += 1
        status, retries = scrape_broker(broker, mongo_collection)
        stats["total_retries"] += retries
        
        if status == "SUCCESS":
            stats["success"] += 1
            # Random Delay only if actually scraped
            delay = random.uniform(1, 12)
            logging.info(f"Waiting for {delay:.2f} seconds...")
            time.sleep(delay)
        elif status == "FAILED":
            stats["failed"] += 1
        elif status == "SKIPPED":
            stats["skipped"] += 1
            # No delay for skipped items

    logging.info("="*30)
    logging.info("SCRAPING SUMMARY")
    logging.info("="*30)
    logging.info(f"Total Processed: {stats['total_processed']}")
    logging.info(f"Success: {stats['success']}")
    logging.info(f"Failed: {stats['failed']}")
    logging.info(f"Skipped (Already Exists): {stats['skipped']}")
    logging.info(f"Total Retry Attempts: {stats['total_retries']}")
    logging.info("="*30)
    logging.info("Scraping process completed.")

if __name__ == "__main__":
    main()
