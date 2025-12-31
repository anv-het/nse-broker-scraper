import json
from bs4 import BeautifulSoup
from pathlib import Path
import re

# ---------------------------------------
# FILE PATHS
# ---------------------------------------
INPUT_HTML = Path("html_pages/04_auth_search.html")
OUTPUT_JSON = Path("html_pages/auth_person_details.json")

# ---------------------------------------
# LOAD HTML
# ---------------------------------------
with open(INPUT_HTML, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# ---------------------------------------
# FIND RESULT TABLE
# ---------------------------------------
table = soup.find("table", id="resultTable")
if not table:
    raise Exception("❌ resultTable not found in HTML")

# ---------------------------------------
# EXTRACT HEADERS
# ---------------------------------------
headers = []
header_row = table.find("tr")

for th in header_row.find_all("th"):
    header = th.get_text(" ", strip=True)
    header = re.sub(r"\s+", " ", header)        # normalize spaces
    header = header.lower().replace(" ", "_")   # json-friendly keys
    headers.append(header)

# ---------------------------------------
# EXTRACT ROW DATA
# ---------------------------------------
records = []

for tr in table.find_all("tr")[1:]:  # skip header
    tds = tr.find_all("td")
    if not tds:
        continue

    row = {}
    for idx, td in enumerate(tds):
        key = headers[idx] if idx < len(headers) else f"column_{idx}"
        value = " ".join(td.get_text(" ", strip=True).split())
        row[key] = value

    records.append(row)

# ---------------------------------------
# SAVE JSON
# ---------------------------------------
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"✅ Parsed {len(records)} authorized persons")
print(f"📄 Saved JSON → {OUTPUT_JSON}")
