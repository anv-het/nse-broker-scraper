import os
from bs4 import BeautifulSoup
import json
import csv

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
        # Heuristic: if mostly th, assume header
        if any(cell.name == "th" for cell in first_row_cells):
             headers = [clean_text(cell.get_text()) for cell in first_row_cells]
             rows = rows[1:] # Skip header row

    # Process rows
    for row in rows:
        cells = row.find_all(["td", "th"])
        
        # Handle colspan/rowspan? For now, simple extraction.
        # If headers exist, try to map.
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
            # Capture extra cells if any
            if len(values) > len(headers):
                for i in range(len(headers), len(values)):
                    row_data[f"Column_{i+1}"] = values[i]
        else:
            # No headers, just use indices
            for i, val in enumerate(values):
                row_data[f"Column_{i+1}"] = val
        
        if row_data:
            data.append(row_data)
            
    return data

def parse_accordion_content(content_div):
    """Parses content inside an accordion, looking for tables or key-value pairs."""
    # Check for tables
    tables = content_div.find_all("table")
    if tables:
        # If multiple tables, parse all. 
        # Often there's a layout table and a data table.
        # We'll try to extract the most "data-like" table.
        all_table_data = []
        for table in tables:
            t_data = parse_table(table)
            if t_data:
                all_table_data.extend(t_data)
        return all_table_data
    
    # If no tables, just get text
    return clean_text(content_div.get_text())

def parse_full_broker_details():
    input_file = "broker_details_3323.html"
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Reading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    full_data = {}

    # 1. Basic Details (Top of the page, usually in a form or main div)
    # We'll look for input fields with values or specific labels
    # Based on previous script, we can look for key-value pairs in the main tables
    
    # Extract inputs (hidden or text)
    inputs = soup.find_all("input")
    for inp in inputs:
        name = inp.get("name") or inp.get("id")
        val = inp.get("value")
        if name and val and val.strip():
            full_data[f"Input_{name}"] = clean_text(val)

    # 2. Accordions
    accordions = soup.find_all("div", class_="accordion-item")
    print(f"Found {len(accordions)} accordion items.")
    
    for idx, acc in enumerate(accordions):
        header = acc.find("div", class_="accordion-header")
        content = acc.find("div", class_="accordion-content")
        
        if header and content:
            header_text = clean_text(header.get_text())
            print(f"Processing Accordion: {header_text}")
            
            # Parse content
            acc_data = parse_accordion_content(content)
            
            # Store in full_data
            # Use a safe key
            key = f"Section_{header_text}"
            full_data[key] = acc_data

    # 3. Dropdowns (Selects)
    selects = soup.find_all("select")
    print(f"Found {len(selects)} dropdowns.")
    
    dropdown_data = {}
    for sel in selects:
        sel_id = sel.get("id") or "unknown_select"
        options = [opt.get("value") for opt in sel.find_all("option")]
        dropdown_data[sel_id] = options
        
    full_data["Dropdown_Options"] = dropdown_data

    # 4. Save to JSON
    json_file = "broker_full_details.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(full_data, f, indent=4)
    print(f"Saved JSON to {json_file}")

    # 5. Save to TXT (Readable Report)
    txt_file = "broker_full_details.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("BROKER FULL DETAILS REPORT\n")
        f.write("==========================\n\n")
        
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

    # 6. Save to CSV (Key-Value Pair format for flexibility)
    csv_file = "broker_full_details_kv.csv"
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
    parse_full_broker_details()
