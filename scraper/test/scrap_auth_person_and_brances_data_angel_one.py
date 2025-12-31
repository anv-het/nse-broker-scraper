import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
from pymongo import MongoClient
import os
import json

# -------------------------------
# CONFIG
# -------------------------------
BASE_URL = "https://enit.nseindia.com"
HEADERS = {
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

MEM_ID = 397
MEM_NAME = "ANGEL ONE LIMITED"
ENCODED_MEM_NAME = quote(MEM_NAME)

# -------------------------------
# DATA DIRECTORY
# -------------------------------
DATA_DIR = "data"
BROKER_DIR = os.path.join(DATA_DIR, MEM_NAME)
os.makedirs(BROKER_DIR, exist_ok=True)

# -------------------------------
# MONGO CONFIG
# -------------------------------
MONGO_URI = "mongodb://sa:963852@192.168.102.120:27017/"
MONGO_DB_NAME = "WEB_SCRAPING"
MONGO_DEALING_OFFICE_COLLECTION = "Broker_list_search_dealing_office"
MONGO_AUTH_PERSON_COLLECTION = "Broker_member_Auth_Person"

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
dealing_office_collection = db[MONGO_DEALING_OFFICE_COLLECTION]
auth_person_collection = db[MONGO_AUTH_PERSON_COLLECTION]

# -------------------------------
# REQUEST SESSION
# -------------------------------
session = requests.Session()
session.get("https://www.nseindia.com", headers=HEADERS, timeout=(10, 40))

# -------------------------------
# STEP 1: FETCH MAIN PAGE
# -------------------------------
main_url = f"{BASE_URL}/MemDirWeb/brokerDetailPage_Beta?memID={MEM_ID}&h_MemType=members&memName={ENCODED_MEM_NAME}"
main_resp = session.get(main_url, headers=HEADERS, timeout=15)
main_resp.raise_for_status()

soup = BeautifulSoup(main_resp.text, "html.parser")
member_code = soup.find(id="memberCodeTdId").get_text(strip=True)

# -------------------------------
# STEP 2: FETCH AUTH / OFFICE SEARCH PAGES
# -------------------------------
auth_search_url = f"{BASE_URL}/MemDirWeb/searchAuthPerson?step=searchAuthPersonList&memId={MEM_ID}&memberName={ENCODED_MEM_NAME}&memberCode={member_code}"
office_search_url = f"{BASE_URL}/MemDirWeb/searchDealingOffice?step=searchDealingOfficeList&memId={MEM_ID}&memberName={ENCODED_MEM_NAME}&memberCode={member_code}"

auth_resp = session.get(auth_search_url, headers=HEADERS, timeout=15)
office_resp = session.get(office_search_url, headers=HEADERS, timeout=15)

# -------------------------------
# STEP 3: PARSE HTML TO LIST OF DICTS
# -------------------------------
def parse_table(html_text, table_id="resultTable"):
    soup = BeautifulSoup(html_text, "html.parser")
    table = soup.find("table", {"id": table_id})
    rows = table.find_all("tr")[1:]  # skip header

    data = []
    for row in rows:
        cols = [td.get_text(strip=True) for td in row.find_all("td")]
        if not cols or len(cols) < 1:
            continue
        data.append(cols)
    return data

# Parse AUTH page (for authorized persons)
auth_rows = parse_table(auth_resp.text)
auth_data = []
for row in auth_rows:
    auth_data.append({
        "sr.no": row[0],
        "authorised_person_name": row[1],
        "authorized_person_trade_name": row[2],
        "registration_no.": row[3],
        "registration_date": row[4],
        "number_of_terminals": row[5],
        "type_of_entity": row[6],
        "ap_contact_person_name": row[7],
        "ap_email_id": row[8],
        "contact_no": row[9],
        "traded_segments": row[10],
        "status": row[11],
        "address": row[12],
        "city": row[13],
        "state": row[14],
        "pincode": row[15]
    })

# Parse OFFICE page (for dealing offices)
office_rows = parse_table(office_resp.text)
office_data = []
for row in office_rows:
    office_data.append({
        "sr.no": row[0],
        "office_type": row[1],
        "contact_person_name": row[2],
        "address": row[3],
        "city": row[4],
        "state": row[5],
        "pincode": row[6]
    })

# -------------------------------
# STEP 4: SAVE TO MONGO COLLECTIONS
# -------------------------------
# Save Dealing Office Data
dealing_office_document = {
    "broker_name": MEM_NAME,
    "mem_id": str(MEM_ID),
    "member_code": member_code,
    "offices": office_data
}

dealing_office_collection.update_one(
    {"mem_id": str(MEM_ID), "member_code": member_code},
    {"$set": dealing_office_document},
    upsert=True
)

# Save Authorized Person Data
auth_person_document = {
    "broker_name": MEM_NAME,
    "mem_id": str(MEM_ID),
    "member_code": member_code,
    "authorized_persons": auth_data
}

auth_person_collection.update_one(
    {"mem_id": str(MEM_ID), "member_code": member_code},
    {"$set": auth_person_document},
    upsert=True
)

# -------------------------------
# STEP 5: SAVE JSON FILES LOCALLY
# -------------------------------
with open(os.path.join(BROKER_DIR, "dealing_office.json"), "w", encoding="utf-8") as f:
    json.dump(dealing_office_document, f, ensure_ascii=False, indent=2)

with open(os.path.join(BROKER_DIR, "authorized_persons.json"), "w", encoding="utf-8") as f:
    json.dump(auth_person_document, f, ensure_ascii=False, indent=2)

print(f"✅ DONE: Broker '{MEM_NAME}' data saved in MongoDB and local folder '{BROKER_DIR}'")
