import os
from bs4 import BeautifulSoup
import json
import csv
import re
import urllib.parse

def parse_nse_members():
    input_file = "nse_members_data.html"
    json_output_file = "nse_members.json"
    csv_output_file = "nse_members.csv"

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Reading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    
    # The rows seem to have IDs starting with "displayStyleID"
    # Or we can look for the table with id "resultTable"
    table = soup.find("table", {"id": "resultTable"})
    
    if not table:
        print("Error: Could not find table with id 'resultTable'")
        return

    members_data = []
    
    # Find all rows that look like data rows
    # Based on the snippet, they have ids like displayStyleID1, displayStyleID2...
    rows = table.find_all("tr", id=lambda x: x and x.startswith("displayStyleID"))
    
    print(f"Found {len(rows)} member rows.")

    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 4:
            # Cell 0: Sr No
            sr_no = cells[0].get_text(strip=True).rstrip('.')
            
            # Cell 1: Member Name
            # The name is often inside an <a> tag or just text. 
            # The snippet shows <a ...>NAME<br/>...
            member_name_cell = cells[1]
            member_name = member_name_cell.get_text(strip=True)
            
            # Extract internal ID from href
            # href="javascript:actionToDetailPage(3323,'CENTRICITY SECURITIES PRIVATE LIMITED','TM');"
            internal_id = ""
            anchor = member_name_cell.find('a')
            if anchor and anchor.get('href'):
                href = anchor['href']
                match = re.search(r"actionToDetailPage\((\d+),", href)
                if match:
                    internal_id = match.group(1)

            # Cell 2: SEBI Registration No
            sebi_reg_no = cells[2].get_text(strip=True).replace('\u00a0', '').strip()
            
            # Cell 3: Member Code
            member_code = cells[3].get_text(strip=True)

            member_entry = {
                "sr_no": sr_no,
                "member_name": member_name,
                "sebi_reg_no": sebi_reg_no,
                "member_code": member_code,
                "internal_id": internal_id,
                "details_url": f"https://enit.nseindia.com/MemDirWeb/brokerDetailPage_Beta?memID={internal_id}&h_MemType=members&memName={urllib.parse.quote(member_name)}" if internal_id else ""
            }
            members_data.append(member_entry)

    # Save to JSON
    print(f"Saving {len(members_data)} records to {json_output_file}...")
    with open(json_output_file, "w", encoding="utf-8") as f:
        json.dump(members_data, f, indent=4)

    # Save to CSV
    print(f"Saving {len(members_data)} records to {csv_output_file}...")
    if members_data:
        keys = members_data[0].keys()
        with open(csv_output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(members_data)

    print("Done.")

if __name__ == "__main__":
    parse_nse_members()
