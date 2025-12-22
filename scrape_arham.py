import requests
import os
import urllib3
from bs4 import BeautifulSoup
import json
import csv

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_text(text):
    if not text:
        return ""
    return " ".join(text.split())

def parse_table(table):
    """Parses a generic HTML table into a list of dictionaries."""
    rows = table.find_all("tr")
    data = []
    headers = []
    
    # Try to find headers
    thead = table.find("thead")
    if thead:
        header_cells = thead.find_all(["th", "td"])
        headers = [clean_text(cell.get_text()) for cell in header_cells]
    
    # If no thead, look for first row with th
    if not headers and rows:
        first_row_cells = rows[0].find_all(["th", "td"])
        if any(cell.name == "th" for cell in first_row_cells):
             headers = [clean_text(cell.get_text()) for cell in first_row_cells]
             rows = rows[1:] # Skip header row

    # Process rows
    for row in rows:
        cells = row.find_all(["td", "th"])
        
        row_data = {}
        values = [clean_text(cell.get_text()) for cell in cells]
        
        if not any(values): # Skip empty rows
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

def fetch_and_process_arham():
    url = "https://enit.nseindia.com/MemDirWeb/brokerDetailPage_Beta?memID=2549&h_MemType=members&memName=ARHAM%20SHARE%20PRIVATE%20LIMITED"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    print(f"Fetching URL: {url}")
    try:
        response = requests.get(url, headers=headers, verify=False, timeout=60)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Extract Member Code to use as filename
    member_code = "Unknown_Member"
    
    # Try finding the input field for member code
    # <input type="hidden" name="brokerLocatorBean.member_code" value="90456">
    # Or sometimes it's visible text
    
    member_code_input = soup.find("input", {"name": "brokerLocatorBean.member_code"})
    if member_code_input and member_code_input.get("value"):
        member_code = clean_text(member_code_input.get("value"))
    else:
        # Fallback: Try to find "Member Code" in the table
        # We can look for a cell with "Member Code" and get the next cell
        pass

    print(f"Identified Member Code: {member_code}")
    
    # Base filename
    base_filename = member_code
    
    # Save HTML
    html_file = f"{base_filename}.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Saved HTML to {html_file}")

    # 2. Parse Full Details
    full_data = {}
    
    # Inputs
    inputs = soup.find_all("input")
    for inp in inputs:
        name = inp.get("name") or inp.get("id")
        val = inp.get("value")
        if name and val and val.strip():
            full_data[f"Input_{name}"] = clean_text(val)

    # Accordions
    accordions = soup.find_all("div", class_="accordion-item")
    for idx, acc in enumerate(accordions):
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

    # 3. Save JSON
    json_file = f"{base_filename}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4)
    print(f"Saved JSON to {json_file}")

    # 4. Save TXT
    txt_file = f"{base_filename}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(f"BROKER DETAILS REPORT: {member_code}\n")
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
    print(f"Saved TXT to {txt_file}")

    # 5. Save CSV
    csv_file = f"{base_filename}.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
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
    print(f"Saved CSV to {csv_file}")

if __name__ == "__main__":
    fetch_and_process_arham()
