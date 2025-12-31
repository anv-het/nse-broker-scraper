import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_URL = "https://enit.nseindia.com"
OUTPUT_DIR = "html_pages"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# SESSION & HEADERS (IMPORTANT FOR NSE)
# --------------------------------------------------
session = requests.Session()

headers = {
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

# 🔥 VERY IMPORTANT — warm up NSE session
session.get("https://www.nseindia.com", headers=headers, timeout=(10, 40))

# --------------------------------------------------
# STEP 1: MAIN BROKER PAGE
# --------------------------------------------------
main_url = (
    "https://enit.nseindia.com/MemDirWeb/"
    "brokerDetailPage_Beta"
    "?memID=397&h_MemType=members&memName=ANGEL%20ONE%20LIMITED"
)

main_resp = session.get(main_url, headers=headers, timeout=15)
main_resp.raise_for_status()

main_html_path = os.path.join(OUTPUT_DIR, "01_main_page.html")
with open(main_html_path, "w", encoding="utf-8") as f:
    f.write(main_resp.text)

print("Saved:", main_html_path)

# --------------------------------------------------
# STEP 2: EXTRACT DATA FROM MAIN PAGE
# --------------------------------------------------
soup = BeautifulSoup(main_resp.text, "html.parser")

# memberCode (used by all next pages)
member_code = soup.find(id="memberCodeTdId").get_text(strip=True)

# memID (hidden input or fallback)
mem_id_input = soup.find("input", {"name": "memID"})
mem_id = mem_id_input["value"] if mem_id_input else "397"

# memberName (hidden input or fallback)
mem_name_input = soup.find("input", {"name": "memName"})
member_name = mem_name_input["value"] if mem_name_input else "ANGEL ONE LIMITED"

encoded_member_name = quote(member_name)

print("Extracted values:")
print("memID:", mem_id)
print("memberName:", member_name)
print("memberCode:", member_code)

# --------------------------------------------------
# STEP 3: AUTH & OFFICE DETAIL PAGES (JS PATTERN)
# --------------------------------------------------
auth_details_url = (
    f"{BASE_URL}/MemDirWeb/brokerAuthPersonDtls"
    f"?memID={mem_id}"
    f"&memberName={encoded_member_name}"
    f"&memberCode={member_code}"
)

office_details_url = (
    f"{BASE_URL}/MemDirWeb/brokerOfficeDtls"
    f"?memID={mem_id}"
    f"&memberName={encoded_member_name}"
    f"&memberCode={member_code}"
)

# --------------------------------------------------
# STEP 4: FETCH & SAVE AUTH / OFFICE PAGES
# --------------------------------------------------
auth_details_resp = session.get(auth_details_url, headers=headers, timeout=15)
office_details_resp = session.get(office_details_url, headers=headers, timeout=15)

auth_details_path = os.path.join(OUTPUT_DIR, "02_auth_details.html")
office_details_path = os.path.join(OUTPUT_DIR, "03_office_details.html")

with open(auth_details_path, "w", encoding="utf-8") as f:
    f.write(auth_details_resp.text)

with open(office_details_path, "w", encoding="utf-8") as f:
    f.write(office_details_resp.text)

print("Saved:", auth_details_path)
print("Saved:", office_details_path)

# --------------------------------------------------
# STEP 5: FINAL SEARCH URLS (DATA PAGES)
# --------------------------------------------------
auth_search_url = (
    f"{BASE_URL}/MemDirWeb/searchAuthPerson"
    f"?step=searchAuthPersonList"
    f"&memId={mem_id}"
    f"&memberName={encoded_member_name}"
    f"&memberCode={member_code}"
)

office_search_url = (
    f"{BASE_URL}/MemDirWeb/searchDealingOffice"
    f"?step=searchDealingOfficeList"
    f"&memId={mem_id}"
    f"&memberName={encoded_member_name}"    
    f"&memberCode={member_code}"
)

# --------------------------------------------------
# STEP 6: FETCH & SAVE FINAL SEARCH PAGES
# --------------------------------------------------
auth_search_resp = session.get(auth_search_url, headers=headers, timeout=15)
office_search_resp = session.get(office_search_url, headers=headers, timeout=15)

auth_search_path = os.path.join(OUTPUT_DIR, "04_auth_search.html")
office_search_path = os.path.join(OUTPUT_DIR, "05_office_search.html")

with open(auth_search_path, "w", encoding="utf-8") as f:
    f.write(auth_search_resp.text)

with open(office_search_path, "w", encoding="utf-8") as f:
    f.write(office_search_resp.text)

print("Saved:", auth_search_path)
print("Saved:", office_search_path)

print("\n✅ DONE: All pages fetched & saved successfully")
