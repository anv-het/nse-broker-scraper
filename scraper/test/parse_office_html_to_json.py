import json
from bs4 import BeautifulSoup
from pathlib import Path

# ---------------------------------------
# FILE PATHS
# ---------------------------------------
INPUT_HTML = Path("html_pages/05_office_search.html")
OUTPUT_JSON = Path("html_pages/office_details.json")

# ---------------------------------------
# LOAD HTML FILE
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
    header_text = th.get_text(strip=True).lower().replace(" ", "_")
    headers.append(header_text)

# ---------------------------------------
# EXTRACT DATA ROWS
# ---------------------------------------
rows_data = []

for tr in table.find_all("tr")[1:]:  # skip header row
    tds = tr.find_all("td")
    if not tds:
        continue

    row = {}
    for idx, td in enumerate(tds):
        key = headers[idx] if idx < len(headers) else f"column_{idx}"
        value = " ".join(td.get_text(" ", strip=True).split())
        row[key] = value

    rows_data.append(row)

# ---------------------------------------
# SAVE TO JSON
# ---------------------------------------
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(rows_data, f, indent=2, ensure_ascii=False)

print(f"✅ Parsed {len(rows_data)} records")
print(f"📄 Saved JSON → {OUTPUT_JSON}")
