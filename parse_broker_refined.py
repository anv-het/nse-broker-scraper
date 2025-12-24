"""
Refined Broker Details Parser
Parses NSE broker HTML pages into structured JSON format
"""
import os
import re
import json
from bs4 import BeautifulSoup, Comment
from datetime import datetime


def clean_text(text):
    """Clean and normalize text."""
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


def parse_accordion_table(content_div):
    """Parse table data from accordion content, handling nested table structures."""
    data = []
    table = content_div.find("table", class_="tabular_data")
    
    if table:
        # Check for nested table structure (common in NSE pages)
        # Pattern: outer table -> tbody -> tr -> td[colspan] -> inner table
        tbody_outer = table.find("tbody", recursive=False)
        if tbody_outer:
            first_row = tbody_outer.find("tr", recursive=False)
        else:
            first_row = table.find("tr", recursive=False)
            
        if first_row:
            nested_td = first_row.find("td", {"colspan": True})
            if nested_td:
                nested_table = nested_td.find("table", class_="tabular_data")
                if nested_table:
                    table = nested_table  # Use nested table instead
        
        headers = []
        
        # Look for header row (thead or first tr with th elements)
        thead = table.find("thead")
        if thead:
            header_cells = thead.find_all(["th", "td"], recursive=False)
            headers = [clean_text(cell.get_text()) for cell in header_cells]
        
        # Get data rows from tbody or directly from table
        # Some NSE tables have multiple tbody elements, each containing one row!
        # Some even have nested tbody: <tbody><tbody><tr>...
        tbody_elements = table.find_all("tbody", recursive=False)
        if tbody_elements:
            # Check if the first tbody has child tbody elements (nested tbody structure)
            if tbody_elements[0].find("tbody"):
                # Use child tbody elements instead
                tbody_elements = tbody_elements[0].find_all("tbody", recursive=False)
            
            rows = []
            for tbody in tbody_elements:
                rows.extend(tbody.find_all("tr", recursive=False))
        else:
            rows = table.find_all("tr", recursive=False)
            # If we found headers in thead, skip them
            if thead and rows:
                # Headers already extracted, use all rows
                pass
            elif rows:
                # Check if first row is header
                first_row_cells = rows[0].find_all(["th", "td"], recursive=False)
                if any(cell.name == "th" for cell in first_row_cells):
                    headers = [clean_text(cell.get_text()) for cell in first_row_cells]
                    rows = rows[1:]  # Skip header row
        
        # Parse data rows
        for row in rows:
            cells = row.find_all(["td", "th"], recursive=False)
            row_data = {}
            for i, cell in enumerate(cells):
                header = headers[i] if i < len(headers) else f"Column_{i+1}"
                row_data[header] = clean_text(cell.get_text())
            
            if any(row_data.values()):  # Only add if row has data
                data.append(row_data)
    
    return data


def parse_broker_details(html_content):
    """
    Parse broker HTML page into structured data.
    
    Args:
        html_content (str): HTML content of broker details page
        
    Returns:
        dict: Structured broker data
    """
    soup = BeautifulSoup(html_content, "html.parser")
    full_data = {}

    # --- 1. Basic Details ---
    basic_details = {}
    for tr in soup.find_all("tr"):
        key, val = get_cell_data(tr)
        if key:
            if key == "Member Name": basic_details["Member Name"] = val
            elif key == "Trade Name": basic_details["Trade Name"] = val
            elif key == "Member Code": basic_details["Member Code"] = val
            elif key == "SEBI Registration no": basic_details["SEBI Registration no"] = val
            elif key == "SEBI Registration Date": basic_details["SEBI Registration Date"] = val
            elif key == "Constitution": basic_details["Constitution"] = val
            elif key == "Year of Incorporation": basic_details["Year of Incorporation"] = val
            elif key == "Year of NSE Membership": basic_details["Year of NSE Membership"] = val
    
    # Save specific fields at the top level
    for top_key in ["Member Name", "Member Code", "SEBI Registration no"]:
        if top_key in basic_details:
            full_data[top_key] = basic_details[top_key]
            
    full_data["Basic_Details"] = basic_details

    # --- 2. Segment Status ---
    segment_status = {"LEGEND": "", "Table_Data": []}
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header:
            header_text = header.get_text()
            if "Segment" in header_text and "status" in header_text:
                content = acc.find("div", class_="accordion-content")
                if content:
                    # Legend cell may be th or td and often contains the word LEGEND
                    legend_cell = content.find(lambda t: t.name in ["th", "td"] and "LEGEND" in t.get_text())
                    if legend_cell:
                        segment_status["LEGEND"] = clean_text(legend_cell.get_text())
                    segment_status["Table_Data"] = parse_accordion_table(content)
                break
    full_data["Segment_Status"] = segment_status

    # --- 3. Outer Details ---
    outer_details = {}
    for tr in soup.find_all("tr"):
        key, val = get_cell_data(tr)
        if not key: continue
        
        if "List of APs registered" in key:
            td = tr.find("td") or (tr.find("th") and tr.find("th").find("td"))
            link = td.find("a") if td else None
            outer_details["List of APs registered"] = {"text": val, "link": link.get("href") if link else ""}
        elif "List of dealing offices" in key:
            td = tr.find("td") or (tr.find("th") and tr.find("th").find("td"))
            link = td.find("a") if td else None
            outer_details["List of dealing offices"] = {"text": val, "link": link.get("href") if link else ""}
        elif key == "Listed":
            outer_details["Listed"] = val
        elif "Investor Grievance Email ID" in key:
            outer_details["Investor Grievance Email ID"] = val
        elif "Types of Clients Served" in key:
            outer_details["Types of Clients Served"] = val
    full_data["Outer_Details"] = outer_details

    # --- 4. Office Details ---
    def parse_office(header_name):
        office_data = {}
        for acc in soup.find_all("div", class_="accordion-item"):
            header = acc.find("div", class_="accordion-header")
            if header and header_name in header.get_text():
                content = acc.find("div", class_="accordion-content")
                if content:
                    for tr in content.find_all("tr"):
                        key, val = get_cell_data(tr)
                        if key: office_data[key] = val
                break
        return office_data

    full_data["Registered_Office"] = parse_office("Registered Office")
    full_data["Correspondence_Office"] = parse_office("Correspondence Office")

    # --- 5. Website & App Details ---
    website_app = {"Website Address": "", "Apps": [], "Social Media Details": []}
    for tr in soup.find_all("tr"):
        key, val = get_cell_data(tr)
        if key == "Website Address":
            website_app["Website Address"] = val
            break

    def parse_acc_table(pattern):
        data = []
        for acc in soup.find_all("div", class_="accordion-item"):
            header = acc.find("div", class_="accordion-header")
            if header and re.search(pattern, header.get_text(), re.I):
                content = acc.find("div", class_="accordion-content")
                if content:
                    data = parse_accordion_table(content)
                break
        return data

    website_app["Apps"] = parse_acc_table("Mobile Applications")
    website_app["Social Media Details"] = parse_acc_table("Social Media Details")
    full_data["website_app"] = website_app

    # --- 6. SEBI Details ---
    sebi_details = {}
    for key in ["PMS SEBI Registration details", "Research Analysts details", "Investment Adviser details", "Merchant Banker"]:
        for tr in soup.find_all("tr"):
            k, val = get_cell_data(tr)
            if k and key in k:
                # Try to extract link
                td = tr.find("td") or (tr.find("th") and tr.find("th").find("td"))
                link = td.find("a") if td else None
                sebi_details[key] = {
                    "Website": link.get("href") if link else "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognised=yes",
                    "Path": val or "Home » Intermediaries / Market Infrastructure Institutions » Recognised Intermediaries"
                }
                break
    full_data["sebi_details"] = sebi_details

    # --- 7. Depository Participant Details ---
    # depository_participant_details = {"As_on_Date": "", "Depositories": []}
    # for acc in soup.find_all("div", class_="accordion-item"):
    #     header = acc.find("div", class_="accordion-header")
    #     if header and "Whether Depostitory Participant" in header.get_text():
    #         date_match = re.search(r"as on (\d{1,2}-\w{3}-\d{4})", header.get_text(), re.I)
    #         if date_match: depository_participant_details["As_on_Date"] = date_match.group(1)
    #         depository_participant_details["Depositories"] = parse_acc_table("Whether Depostitory Participant")
    #         break
    # full_data["depository_participant_details"] = depository_participant_details
    
    


    depository_participant_details = {
        "As_on_Date": "",
        "Depositories": []
    }

    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if not header:
            continue

        header_text = header.get_text(" ", strip=True)

        if "Whether Depostitory Participant" in header_text:
            # Extract date
            date_match = re.search(r"as on\s*(\d{1,2}-[A-Z]{3}-\d{4})", header_text, re.I)
            if date_match:
                depository_participant_details["As_on_Date"] = date_match.group(1)

            table = acc.find("table", class_="tabular_data")
            if not table:
                break

            for row in table.find_all("tr"):
                cols = row.find_all("td")
                if len(cols) < 4:
                    continue

                sr_no = cols[0].get_text(strip=True)

                # 🔥 Skip header / garbage rows
                if not sr_no.isdigit():
                    continue

                depository_participant_details["Depositories"].append({
                    "Sr_No": sr_no,
                    "Name_of_Depository": cols[1].get_text(strip=True),
                    "Registration_No": cols[2].get_text(strip=True),
                    "Link": cols[3].find("a")["href"] if cols[3].find("a") else ""
                })

            break

    full_data["depository_participant_details"] = depository_participant_details


    # --- 8. Stock Exchange Membership Details ---
    stock_exchange_membership_details = {"As_on_Date": "", "Membership_Details": []}
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header and "Details of Membership with other Stock Exchanges" in header.get_text():
            date_match = re.search(r"as on (\d{1,2}-\w{3}-\d{4})", header.get_text(), re.I)
            if date_match: stock_exchange_membership_details["As_on_Date"] = date_match.group(1)
            stock_exchange_membership_details["Membership_Details"] = parse_acc_table("Details of Membership with other Stock Exchanges")
            break
    full_data["stock_exchange_membership_details"] = stock_exchange_membership_details

    # --- 9. Key Management Details ---
    key_management_details = {
        "Managing_Director_CEO": {"Name": "", "Designation": ""}, 
        "Compliance_Officer": {"Name": "", "Email": "", "Contact_Number": ""}
    }
    
    # MD/CEO
    md_header = soup.find(lambda t: t.name in ["td", "th"] and "MANAGING DIRECTOR / CEO DETAILS" in t.get_text())
    if md_header:
        curr = md_header.find_parent("tr").find_next_sibling("tr")
        while curr:
            if "COMPLIANCE OFFICER DETAILS" in curr.get_text(): break
            key, val = get_cell_data(curr)
            if key:
                if key == "Name": key_management_details["Managing_Director_CEO"]["Name"] = val
                if key == "Designation": key_management_details["Managing_Director_CEO"]["Designation"] = val
            curr = curr.find_next_sibling("tr")

    # Compliance Officer
    co_header = soup.find(lambda t: t.name in ["td", "th"] and "COMPLIANCE OFFICER DETAILS" in t.get_text())
    if co_header:
        curr = co_header.find_parent("tr").find_next_sibling("tr")
        while curr:
            if curr.find("td", class_="header"): break
            key, val = get_cell_data(curr)
            if key:
                if key == "Name": key_management_details["Compliance_Officer"]["Name"] = val
                if key == "E-mail": key_management_details["Compliance_Officer"]["Email"] = val
                if key == "Contact Number": key_management_details["Compliance_Officer"]["Contact_Number"] = val
            curr = curr.find_next_sibling("tr")
    full_data["key_management_details"] = key_management_details

    # --- 10. Directors Details ---
    directors_details = {"As_on_Date": "", "Directors": []}
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header and "DETAILS OF DIRECTORS" in header.get_text():
            date_match = re.search(r"AS ON (\d{1,2}-\w{3}-\d{4})", header.get_text(), re.I)
            if date_match: directors_details["As_on_Date"] = date_match.group(1)
            directors_details["Directors"] = parse_acc_table("DETAILS OF DIRECTORS")
            # Fix keys for directors
            for d in directors_details["Directors"]:
                if "Designated Director (Y/N)" in d:
                    d["Designated_Director"] = d.pop("Designated Director (Y/N)")
            break
    full_data["directors_details"] = directors_details

    # --- 11. Complaints Details (SCORES 2.0, ODR, GRC) ---
    # --- SCORES 2.0 Complaints (Inline Parsing) ---
    months = get_months_years()
    scores_data = {}

    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if not header:
            continue

        if "Details of Complaints received in Scores 2.0" not in header.get_text():
            continue

        content = acc.find("div", class_="accordion-content")
        if not content:
            break

        # ✅ Pick the REAL inner table safely
        tables = content.find_all("table", class_="tabular_data")
        table = None
        for t in tables:
            if t.find("th") and "opening" in t.get_text(strip=True).lower():
                table = t
                break

        if not table:
            break

        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue

            label = clean_text(cells[0].get_text()).lower()

            if "opening" in label:
                key = "Opening_Complaints"
            elif "received" in label:
                key = "Received"
            else:
                continue

            for i, month in enumerate(months):
                if i + 1 >= len(cells):
                    continue

                val_text = clean_text(cells[i + 1].get_text())
                val = int(val_text) if val_text.isdigit() else 0

                scores_data.setdefault(month, {})
                if key not in scores_data[month]:
                    scores_data[month][key] = val

        break

    full_data["scores_2_0_complaints"] = {
        "Table_Name": "Details of Complaints received in SCORES 2.0",
        "Monthly_Data": scores_data
    }


    # --- ODR Complaints Summary (Inline Parsing) ---
    months = get_months_years()
    odr_complaints_data = {}

    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if not header or "Details of Complaints/Arbitration matters received in Online Dispute Resolution (ODR)" not in header.get_text():
            continue

        content = acc.find("div", class_="accordion-content")
        if not content:
            break

        tables = content.find_all("table", class_="tabular_data")
        table = None
        for t in tables:
            text = t.get_text(" ", strip=True).lower()
            if "opening complaints" in text and "received" in text:
                table = t
                break

        if not table:
            break

        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue

            label_text = clean_text(cells[0].get_text()).lower()
            if "opening" in label_text:
                key = "Opening_Complaints"
            elif "received" in label_text:
                key = "Received"
            else:
                continue

            for i, month in enumerate(months):
                if i + 1 >= len(cells):
                    continue

                val_text = clean_text(cells[i + 1].get_text())
                val = int(val_text) if val_text.isdigit() else 0

                odr_complaints_data.setdefault(month, {})
                if key not in odr_complaints_data[month]:
                    odr_complaints_data[month][key] = val
        break

    full_data["odr_complaints_summary"] = {
        "Table_Name": "ODR – Summary of Complaints received",
        "Monthly_Data": odr_complaints_data
    }

    # --- ODR Arbitration Summary (Inline Parsing) ---
    odr_arbitration_data = {}

    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if not header or "Summary of Arbitration cases" not in header.get_text():
            continue

        content = acc.find("div", class_="accordion-content")
        if not content:
            break

        tables = content.find_all("table", class_="tabular_data")
        table = None
        for t in tables:
            text = t.get_text(" ", strip=True).lower()
            if "opening complaints" in text and "received" in text:
                table = t
                break

        if not table:
            break

        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue

            label_text = clean_text(cells[0].get_text()).lower()
            if "opening" in label_text:
                key = "Opening_Cases"
            elif "received" in label_text:
                key = "Received"
            else:
                continue

            for i, month in enumerate(months):
                if i + 1 >= len(cells):
                    continue

                val_text = clean_text(cells[i + 1].get_text())
                val = int(val_text) if val_text.isdigit() else 0

                odr_arbitration_data.setdefault(month, {})
                if key not in odr_arbitration_data[month]:
                    odr_arbitration_data[month][key] = val
        break

    full_data["odr_arbitration_summary"] = {
        "Table_Name": "ODR – Summary of Arbitration cases",
        "Monthly_Data": odr_arbitration_data
    }


    # --- GRC Complaints Closed (Pre-ODR) ---
    grc_data = {
        "Table_Name": "Complaints Closed through GRC (Pre-ODR)",
        "Yearly_Data": {},
        "Note": "As decided in GRC"
    }

    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if not header or "Details of Complaints Closed through GRC" not in header.get_text():
            continue

        content = acc.find("div", class_="accordion-content")
        if not content:
            break

        inner_table = content.find("table", class_="tabular_data")
        if not inner_table:
            break

        # Find the actual data table (nested one)
        data_table = inner_table.find("table", class_="tabular_data")
        if not data_table:
            break

        # --- Extract year columns from header classes ---
        year_headers = []
        header_cells = data_table.find("thead").find_all("th")[1:]  # skip "Status"

        for th in header_cells:
            cls = " ".join(th.get("class", []))
            if "firstYear" in cls:
                year_headers.append("Year_1")
            elif "secondYear" in cls:
                year_headers.append("Year_2")
            elif "thirdYear" in cls:
                year_headers.append("Year_3")

        # --- Extract values (only first matching row) ---
        for row in data_table.find("tbody").find_all("tr"):
            label = clean_text(row.find("th").get_text()).lower()
            if "total count of complaints closed" not in label:
                continue

            cells = row.find_all("td")
            for i, year in enumerate(year_headers):
                val_text = clean_text(cells[i].get_text())
                grc_data["Yearly_Data"][year] = int(val_text) if val_text.isdigit() else 0
            break  # avoid duplicate row

        break

    full_data["grc_complaints_closed"] = grc_data


    # --- 12. Disciplinary Actions Master ---
    disciplinary_master = {
        "As_on_Date": datetime.now().strftime("%d-%b-%Y").upper(),
        "NSE_Disciplinary_Actions": {},
        "NSE_Member_Committee_Orders": {},
        "Disciplinary_Actions_By_Other_Exchanges": {},
        "SEBI_Orders": {},
        "Consent_Orders": {},
        "Disclaimer": []
    }
    
    disc_header = soup.find(lambda t: t.name in ["td", "th"] and "Disciplinary Actions" in t.get_text() and "NSE against" in t.get_text())
    if disc_header:
        date_match = re.search(r"as on (\d{1,2}-\w{3}-\d{4})", disc_header.get_text(), re.I)
        if date_match: disciplinary_master["As_on_Date"] = date_match.group(1)

    # NSE Disciplinary Actions - Monetary Penalties
    penalties_2022 = {}
    all_ths = soup.find_all(lambda t: t.name in ["td", "th"] and "Total monetary penalty levied" in t.get_text())
    for th in all_ths:
        tr = th.find_parent("tr")
        tds = tr.find_all(["td", "th"], recursive=False)
        if len(tds) > 1:
            years_in_order = ["2022-2023", "2023-2024", "2024-2025", "2025-2026"]
            for i, year in enumerate(years_in_order):
                if i+1 < len(tds):
                    val = clean_text(tds[i+1].get_text())
                    penalties_2022[year] = val if val else "NA"
                else:
                    penalties_2022[year] = "NA"
            break
    
    penalties_2021 = {
        "2021-2022": penalties_2022.get("2022-2023", "NA"),
        "2023-2024": penalties_2022.get("2023-2024", "NA"),
        "2024-2025": penalties_2022.get("2024-2025", "NA"),
        "2025-2026": penalties_2022.get("2025-2026", "NA")
    }
    
    disciplinary_master["NSE_Disciplinary_Actions"] = {
        "year_2021_2022": {"Year_Range": ["2021-2022", "2023-2024", "2024-2025", "2025-2026"], "Total_Monetary_Penalty_In_Rs": penalties_2021},
        "year_2022_2023": {"Year_Range": ["2022-2023", "2023-2024", "2024-2025", "2025-2026"], "Total_Monetary_Penalty_In_Rs": penalties_2022}
    }

    # NSE Member Committee Orders
    mc_counts_2022 = {}
    mc_details_2022 = {}
    
    all_count_cells = soup.find_all(lambda t: t.name in ["td", "th"] and "1. Orders issued(count)" in t.get_text())
    for cell in all_count_cells:
        tr = cell.find_parent("tr")
        tds = tr.find_all(["td", "th"], recursive=False)
        if len(tds) > 1:
            years_in_order = ["2022-2023", "2023-2024", "2024-2025", "2025-2026"]
            for i, year in enumerate(years_in_order):
                if i+1 < len(tds):
                    val_str = clean_text(tds[i+1].get_text())
                    num = re.sub(r"[^0-9]", "", val_str)
                    try:
                        mc_counts_2022[year] = int(num) if num else 0
                    except ValueError:
                        mc_counts_2022[year] = 0
                else:
                    mc_counts_2022[year] = 0
            break
    
    all_detail_cells = soup.find_all(lambda t: t.name in ["td", "th"] and "2. Orders issued details" in t.get_text())
    for cell in all_detail_cells:
        tr = cell.find_parent("tr")
        tds = tr.find_all(["td", "th"], recursive=False)
        if len(tds) > 1:
            years_in_order = ["2022-2023", "2023-2024", "2024-2025", "2025-2026"]
            for i, year in enumerate(years_in_order):
                if i+1 < len(tds):
                    links = tds[i+1].find_all("a")
                    if links:
                        link_list = [link.get("href", "") for link in links if link.get("href")]
                        mc_details_2022[year] = link_list if link_list else "NA"
                    else:
                        val = clean_text(tds[i+1].get_text())
                        mc_details_2022[year] = val if val else "NA"
                else:
                    mc_details_2022[year] = "NA"
            break
    
    mc_counts_2021 = {
        "2021-2022": mc_counts_2022.get("2022-2023", 0),
        "2023-2024": mc_counts_2022.get("2023-2024", 0),
        "2024-2025": mc_counts_2022.get("2024-2025", 0),
        "2025-2026": mc_counts_2022.get("2025-2026", 0)
    }
    mc_details_2021 = {
        "2021-2022": mc_details_2022.get("2022-2023", "NA"),
        "2023-2024": mc_details_2022.get("2023-2024", "NA"),
        "2024-2025": mc_details_2022.get("2024-2025", "NA"),
        "2025-2026": mc_details_2022.get("2025-2026", "NA")
    }

    disciplinary_master["NSE_Member_Committee_Orders"] = {
        "year_2021_2022": {"Year_Range": ["2021-2022", "2023-2024", "2024-2025", "2025-2026"], "Orders_Issued_Count": mc_counts_2021, "Orders_Issued_Details": mc_details_2021, "Interim_Defaulter_Expulsion_Orders": "Visit Link"},
        "year_2022_2023": {"Year_Range": ["2022-2023", "2023-2024", "2024-2025", "2025-2026"], "Orders_Issued_Count": mc_counts_2022, "Orders_Issued_Details": mc_details_2022, "Interim_Defaulter_Expulsion_Orders": "Visit Link"}
    }

    disciplinary_master["Disciplinary_Actions_By_Other_Exchanges"] = {
        "year_2021_2022": {"Year_Range": ["2021-2022", "2023-2024", "2024-2025", "2025-2026"], "Orders_Issued": "Click To View"},
        "year_2022_2023": {"Year_Range": ["2022-2023", "2023-2024", "2024-2025", "2025-2026"], "Orders_Issued": "Click To View"}
    }
    disciplinary_master["SEBI_Orders"] = {
        "year_2021_2022": {"Year_Range": ["2021-2022", "2023-2024", "2024-2025", "2025-2026"], "Orders_Issued": "NA"},
        "year_2022_2023": {"Year_Range": ["2022-2023", "2023-2024", "2024-2025", "2025-2026"], "Orders_Issued": "NA"}
    }
    disciplinary_master["Consent_Orders"] = {
        "Website": "https://www.sebi.gov.in/index.html",
        "Path": "Home » Enforcement » Orders » Settlement Order"
    }
    disciplinary_master["Disclaimer"] = [
        "The details of disciplinary actions or orders are obtained from SEBI official website. Users are advised to contact SEBI directly for queries. NSE disclaims responsibility for accuracy, completeness, or authenticity of SEBI orders."
    ]
    full_data["disciplinary_actions_master"] = disciplinary_master

    # --- 13. Associate Companies ---
    associate_companies = {"As_on_Date": "", "Table_Name": "Associate Companies", "Companies": []}
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header and "Associate Companies" in header.get_text():
            date_match = re.search(r"as on (\d{1,2}-\w{3}-\d{4})", header.get_text(), re.I)
            if date_match: associate_companies["As_on_Date"] = date_match.group(1)
            associate_companies["Companies"] = parse_acc_table("Associate Companies")
            break
    full_data["associate_companies"] = associate_companies

    # --- 14. Summary of Trading Member Information ---
    summary_tm = {"Table_Name": "Summary of Trading Member Information", "Reporting_Period": "6 Monthly", "Data_By_Period": {}}
    periods = get_reporting_periods()
    for period in periods:
        summary_tm["Data_By_Period"][period] = {}
    
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header and "Summary of trading member Information" in header.get_text():
            content = acc.find("div", class_="accordion-content")
            if content:
                # The trading summary has a nested table structure: outer table -> row[1] -> nested table
                outer_table = content.find("table", class_="tabular_data")
                if outer_table:
                    outer_rows = outer_table.find_all("tr", recursive=False)
                    # The nested table is in the second row (index 1), inside a td with colspan=2
                    if len(outer_rows) > 1:
                        nested_td = outer_rows[1].find("td", {"colspan": "2"})
                        if nested_td:
                            nested_table = nested_td.find("table", class_="tabular_data")
                            if nested_table:
                                # Use generated periods since HTML doesn't contain them (populated by JS)
                                period_cols = periods
                                
                                # Map of metric text patterns to output keys
                                metric_map = {
                                    "branches": "Number_of_branches_of_TM",
                                    "employees": "Number_of_employees_of_TM",
                                    "APs/affiliates": "Number_of_APs_affiliates_registered_with_Exchanges",
                                    "Total number of active clients": "Total_number_of_active_clients",
                                    "equity cash segment": "Clients_Equity_Cash_Segment",
                                    "derivatives": "Clients_Derivatives"
                                }
                                
                                # Parse tbody rows
                                tbody = nested_table.find("tbody")
                                if tbody:
                                    data_rows = tbody.find_all("tr", recursive=False)
                                    for row in data_rows:
                                        cells = row.find_all(["td", "th"], recursive=False)
                                        # Structure: [sr_no, empty, metric_name, val1, val2, val3, val4, val5, val6]
                                        if len(cells) >= 9:  # Need at least 9 cells (2 header + 1 metric + 6 values)
                                            metric_label = clean_text(cells[2].get_text())
                                            
                                            # Find matching key
                                            key = None
                                            for pattern, output_key in metric_map.items():
                                                if pattern.lower() in metric_label.lower():
                                                    key = output_key
                                                    break
                                            
                                            if key:
                                                # Extract 6 period values starting from cells[3]
                                                for i, period in enumerate(period_cols):
                                                    if i+3 < len(cells):
                                                        val_text = clean_text(cells[i+3].get_text())
                                                        num = re.sub(r"[^0-9]", "", val_text)
                                                        val = int(num) if num else 0
                                                        summary_tm["Data_By_Period"].setdefault(period, {})[key] = val
            break
    full_data["summary_trading_member_info"] = summary_tm

    # --- 15. Client Bank Accounts ---
    client_bank_accounts = {
        "Table_Name": "Details of Client Bank Accounts disclosed to Exchange",
        "Note": "",
        "Accounts": []
    }

    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if not header or "Details of Client Bank Accounts" not in header.get_text():
            continue

        content = acc.find("div", class_="accordion-content")
        if not content:
            break

        # -------- Extract Note --------
        note_row = content.find("b", class_="header", string=lambda t: t and "Note" in t)
        if note_row:
            span = note_row.find_next("span", class_="rowalt")
            if span:
                client_bank_accounts["Note"] = clean_text(span.get_text())

        # -------- Find INNER accounts table --------
        inner_table = content.find("table", class_="tabular_data").find("table", class_="tabular_data")
        if not inner_table:
            break

        tbody = inner_table.find("tbody")
        if not tbody:
            break

        # -------- Parse rows --------
        for tr in tbody.find_all("tr"):
            cells = tr.find_all(["th", "td"])
            if len(cells) < 5:
                continue

            account = {
                "Sr no": clean_text(cells[0].get_text()),
                "Account Name": clean_text(cells[1].get_text()),
                "Account Number": clean_text(cells[2].get_text()),
                "IFSC Code": clean_text(cells[3].get_text()),
                "Account Purpose": clean_text(cells[4].get_text())
            }

            # Safety check
            if account["Sr no"].isdigit():
                client_bank_accounts["Accounts"].append(account)

        break

    full_data["client_bank_accounts"] = client_bank_accounts


    # --- 16. Trading Member Net Worth ---
    net_worth_data = {
        "Table_Name": "Trading Member Net Worth",
        "As_on_Date": "",
        "Regulation_Reference": "Schedule VI of SEBI (Stock Brokers) Regulations, 1992",
        "Net_Worth_Rs": 0
    }
    net_worth_row = soup.find(lambda t: t.name in ["th", "td"] and "Trading member Net worth" in t.get_text())
    if net_worth_row:
        text = net_worth_row.get_text()
        date_match = re.search(r"as on (\d{1,2}-\w{3}-\d{4})", text, re.I)
        if date_match: net_worth_data["As_on_Date"] = date_match.group(1)
        
        # The value td might be a child of the th element (malformed HTML)
        td = net_worth_row.find("td")
        if not td:
            # Try as sibling
            td = net_worth_row.find_next_sibling(["td", "th"])
        if not td:
            # Try within parent tr
            parent_tr = net_worth_row.find_parent("tr")
            if parent_tr:
                tds = parent_tr.find_all(["td", "th"], recursive=False)
                if len(tds) > 1:
                    td = tds[1]
        
        if td:
            val_text = clean_text(td.get_text()).replace("Rs.", "").replace(",", "").strip()
            num_match = re.search(r"(\d+)", val_text)
            if num_match:
                net_worth_data["Net_Worth_Rs"] = int(num_match.group(1))
    full_data["trading_member_net_worth"] = net_worth_data

    return full_data


def format_data_as_text(data, member_name=""):
    """Format the parsed data as human-readable text."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"BROKER DETAILS REPORT: {member_name}")
    lines.append("=" * 80)
    lines.append("")
    
    def add_section(title, content, indent=0):
        prefix = "  " * indent
        lines.append(f"{prefix}{'=' * 60}")
        lines.append(f"{prefix}{title}")
        lines.append(f"{prefix}{'-' * 60}")
        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, (dict, list)):
                    add_section(key, value, indent + 1)
                else:
                    lines.append(f"{prefix}  {key}: {value}")
        elif isinstance(content, list):
            for i, item in enumerate(content, 1):
                if isinstance(item, dict):
                    lines.append(f"{prefix}  Item {i}:")
                    for k, v in item.items():
                        lines.append(f"{prefix}    {k}: {v}")
                else:
                    lines.append(f"{prefix}  {i}. {item}")
        else:
            lines.append(f"{prefix}  {content}")
        lines.append("")
    
    for key, value in data.items():
        if not key.startswith("meta_"):
            add_section(key, value)
    
    return "\n".join(lines)


def format_data_as_csv(data):
    """Format the parsed data as CSV rows."""
    rows = []
    rows.append(["Section", "Sub-Section", "Key", "Value"])
    
    def process_item(section, subsection, key, value):
        if isinstance(value, dict):
            for k, v in value.items():
                process_item(section, subsection, k, v)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    for k, v in item.items():
                        rows.append([section, subsection, f"{key}[{i}].{k}", str(v)])
                else:
                    rows.append([section, subsection, f"{key}[{i}]", str(item)])
        else:
            rows.append([section, subsection, key, str(value)])
    
    for key, value in data.items():
        if not key.startswith("meta_"):
            process_item(key, "", key, value)
    
    return rows
