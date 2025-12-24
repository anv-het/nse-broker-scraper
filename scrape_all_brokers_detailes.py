import requests
import os
import urllib3
from bs4 import BeautifulSoup, Comment
import json
import csv
import time
import random
import logging
from pymongo import MongoClient
import sys
from datetime import datetime
import re

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
MONGO_URI = "mongodb://sa:963852@192.168.102.120:27017/"
MONGO_DB_NAME = "WEB_SCRAPING"
MONGO_COLLECTION_NAME = "Broker_list_details"

INPUT_CSV = "nse_members.csv"
DATA_DIR = "data"
LOGS_DIR = "logs"

START_INDEX = 1340
END_INDEX = 1341

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
    text = text.replace('\xa0', ' ')
    return " ".join(text.split()).strip()

def get_cell_data(tr):
    """Extract key-value pair from a table row."""
    if not tr or tr.name != "tr":
        return None, None
    
    # Standard case: two direct children
    cells = tr.find_all(["th", "td"], recursive=False)
    if len(cells) >= 2:
        return clean_text(cells[0].get_text()), clean_text(cells[1].get_text())
    
    # Malformed case: td nested inside th
    if len(cells) == 1:
        th = cells[0]
        td = th.find("td")
        if td:
            # Key is text before td
            key = ""
            for c in th.contents:
                if c == td: break
                if isinstance(c, Comment): continue
                if isinstance(c, str): key += c
                elif hasattr(c, 'get_text'):
                    key += c.get_text()
            return clean_text(key), clean_text(td.get_text())
        return clean_text(th.get_text()), ""
    
    return None, None

def get_months_years():
    """Generate last 6 months in Mon_YYYY format."""
    today = datetime.now()
    arr = []
    for i in range(1, 7):
        month = today.month - i - 1  # 0-indexed for calculation
        year = today.year
        if month < 0:
            month += 12
            year -= 1
        month_name = datetime(year, month + 1, 1).strftime('%b')
        arr.append(f"{month_name}_{year}")
    return arr

def get_financial_years():
    """Generate last 3 financial years."""
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    if current_month < 4:
        current_year -= 1
    
    years = []
    for i in range(1, 4):
        start_year = current_year - i
        end_year = start_year + 1
        years.append(f"{start_year}_{end_year}")
    return years

def get_reporting_periods():
    """Generate reporting periods for 6-monthly data."""
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    arr = []
    if current_month >= 4 and current_month < 10:
        arr.append(f"MAR {current_year}")
        arr.append(f"SEP {current_year - 1}")
        arr.append(f"MAR {current_year - 1}")
        arr.append(f"SEP {current_year - 2}")
        arr.append(f"MAR {current_year - 2}")
        arr.append(f"SEP {current_year - 3}")
    else:
        arr.append(f"SEP {current_year}")
        arr.append(f"MAR {current_year}")
        arr.append(f"SEP {current_year - 1}")
        arr.append(f"MAR {current_year - 1}")
        arr.append(f"SEP {current_year - 2}")
        arr.append(f"MAR {current_year - 2}")
    return arr

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
        # Heuristic: if mostly th, assume header
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

def parse_key_value_table(table):
    """Parses a table that is essentially a list of Key-Value pairs (Header-Value)."""
    data = {}
    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all(["th", "td"])
        if len(cells) >= 2:
            key = clean_text(cells[0].get_text())
            val = clean_text(cells[1].get_text())
            if key and val:
                data[key] = val
    return data

def scrape_broker(broker_data, mongo_collection):
    sr_no = broker_data.get("sr_no")
    member_name = broker_data.get("member_name")
    member_code = broker_data.get("member_code")
    details_url = broker_data.get("details_url")

    if not details_url:
        logging.warning(f"Skipping {member_name} (Sr: {sr_no}): No details URL.")
        return "FAILED", 0

    # Construct Folder Name
    folder_name_raw = f"{member_name}_{sr_no}_{member_code}"
    folder_name = sanitize_filename(folder_name_raw)
    target_dir = os.path.join(DATA_DIR, folder_name)
    
    # Check if already exists (SKIP LOGIC DISABLED FOR RE-SCRAPING ARHAM)
    # if os.path.exists(target_dir):
    #     logging.info(f"Skipping {member_name} (Sr: {sr_no}): Already scraped.")
    #     return "SKIPPED", 0
    
    os.makedirs(target_dir, exist_ok=True)
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

    # 1. Inputs
    inputs = soup.find_all("input")
    for inp in inputs:
        name = inp.get("name") or inp.get("id")
        val = inp.get("value")
        if name and val and val.strip():
            full_data[f"Input_{name}"] = clean_text(val)

    # 2. Top Basic Details Table
    # Look for table containing "Member Name"
    tables = soup.find_all("table")
    for table in tables:
        if "Member Name" in table.get_text() and "SEBI Registration no" in table.get_text():
            # This is likely the basic details table
            basic_details = parse_key_value_table(table)
            full_data["Basic_Details"] = basic_details
            break

    # 3. Key Management / Compliance Table
    # Look for table containing "COMPLIANCE OFFICER DETAILS" or "MANAGING DIRECTOR"
    for table in tables:
        text = table.get_text()
        if "COMPLIANCE OFFICER DETAILS" in text or "MANAGING DIRECTOR" in text:
            # This table is a bit mixed (headers in rows), so parse as key-value
            kmp_details = parse_key_value_table(table)
            full_data["Key_Management_Personnel"] = kmp_details
            # Don't break, there might be multiple such tables or one big one

    # 4. Accordions
    accordions = soup.find_all("div", class_="accordion-item")
    for acc in accordions:
        header = acc.find("div", class_="accordion-header")
        content = acc.find("div", class_="accordion-content")
        if header and content:
            header_text = clean_text(header.get_text())
            key = f"Section_{header_text}"
            acc_data = parse_accordion_content(content)
            full_data[key] = acc_data

    # 5. Dropdowns
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

    mongo_collection = get_mongo_collection()
    if mongo_collection is None:
        logging.warning("Proceeding without MongoDB connection.")

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
            delay = random.uniform(1, 5)
            logging.info(f"Waiting for {delay:.2f} seconds...")
            time.sleep(delay)
        elif status == "FAILED":
            stats["failed"] += 1
        elif status == "SKIPPED":
            stats["skipped"] += 1

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
