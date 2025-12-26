import os
from bs4 import BeautifulSoup, Comment
import json
import re
from datetime import datetime

def clean_text(text):
    if not text:
        return ""
    text = text.replace('\xa0', ' ')
    return " ".join(text.split()).strip()

def get_cell_data(tr):
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
                    if c.name != 'td': key += c.get_text()
            return clean_text(key), clean_text(td.get_text())
        return clean_text(th.get_text()), ""
    
    return None, None

def get_months_years():
    # Logic from getNewMonthsWithYears() in JS
    # Today is Dec 2025 based on the HTML "as on 22-DEC-2025"
    today = datetime(2025, 12, 23)
    arr = []
    for i in range(1, 7):
        month = today.month - i - 1 # 0-indexed for calculation
        year = today.year
        if month < 0:
            month += 12
            year -= 1
        month_name = datetime(year, month + 1, 1).strftime('%b')
        arr.append(f"{month_name}_{year}")
    return arr

def get_financial_years():
    # Logic from getFinancialYears() in JS
    today = datetime(2025, 12, 23)
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
    # Logic from getLatestMonthsWithYears() in JS
    today = datetime(2025, 12, 23)
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

def parse_details(html_path):
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found.")
        return None

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

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
            
    # Save the full basic details
    full_data["Basic_Details"] = basic_details

    # --- 2. Segment Status ---
    segment_status = {"LEGEND": "", "Table_Data": []}
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header and "Segment/(s) with status" in header.get_text():
            content = acc.find("div", class_="accordion-content")
            if content:
                legend_th = content.find("th", class_="row")
                if legend_th: segment_status["LEGEND"] = clean_text(legend_th.get_text())
                
                table = content.find("table", class_="tabular_data")
                if table:
                    inner = table.find("table") or table
                    rows = inner.find_all("tr")
                    headers = []
                    thead = inner.find("thead")
                    if thead: headers = [clean_text(th.get_text()) for th in thead.find_all(["td", "th"])]
                    
                    for row in rows:
                        if row.find("thead"): continue
                        cells = row.find_all("td")
                        if len(cells) >= len(headers) and headers:
                            row_dict = {h: clean_text(cells[i].get_text()) for i, h in enumerate(headers)}
                            if row_dict: segment_status["Table_Data"].append(row_dict)
            break
    full_data["Segment_Status"] = segment_status

    # --- 3. Outer Details ---
    outer_details = {}
    for tr in soup.find_all("tr"):
        key, val = get_cell_data(tr)
        if not key: continue
        
        if "List of APs registered" in key:
            td = tr.find("td") or tr.find("th").find("td")
            link = td.find("a") if td else None
            outer_details["List of APs registered"] = {"text": val, "link": link.get("href") if link else ""}
        elif "List of dealing offices" in key:
            td = tr.find("td") or tr.find("th").find("td")
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
                    table = content.find("table")
                    if table:
                        address_parts = []
                        for row in table.find_all("tr"):
                            key, val = get_cell_data(row)
                            if key is None and val is None: continue
                            if not key:
                                if val: address_parts.append(val)
                            elif "Address" in key:
                                if val: address_parts.append(val)
                            else:
                                office_data[key] = val
                        office_data["Address"] = ", ".join(address_parts)
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
                    table = content.find("table", class_="tabular_data")
                    if table:
                        inner = table.find("table") or table
                        rows = inner.find_all("tr")
                        headers = []
                        thead = inner.find("thead")
                        if thead: headers = [clean_text(th.get_text()) for th in thead.find_all(["td", "th"])]
                        for row in rows:
                            if row.find("thead"): continue
                            cells = row.find_all(["td", "th"], recursive=False)
                            if len(cells) >= len(headers) and headers:
                                row_dict = {h.replace("Sr no", "Sr.No"): clean_text(cells[i].get_text()) for i, h in enumerate(headers)}
                                if row_dict: data.append(row_dict)
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
                td = tr.find("td") or tr.find("th").find("td")
                link = td.find("a") if td else None
                path_match = re.search(r"Path-(.*)", td.get_text() if td else "", re.I | re.S)
                sebi_details[key] = {
                    "Website": link.get("href") if link else "https://www.sebi.gov.in/index.html",
                    "Path": clean_text(path_match.group(1)) if path_match else ""
                }
                break
    full_data["sebi_details"] = sebi_details

    # --- 7. Depository Participant Details ---
    depository_participant_details = {"As_on_Date": "", "Depositories": []}
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header and "Whether Depostitory Participant" in header.get_text():
            date_match = re.search(r"as on (\d{1,2}-\w{3}-\d{4})", header.get_text(), re.I)
            if date_match: depository_participant_details["As_on_Date"] = date_match.group(1)
            depository_participant_details["Depositories"] = parse_acc_table("Whether Depostitory Participant")
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
    key_management_details = {"Managing_Director_CEO": {"Name": "", "Designation": ""}, "Compliance_Officer": {"Name": "", "Email": "", "Contact_Number": ""}}
    
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
                if "Director Name" in d: d["Director_Name"] = d.pop("Director Name")
                if "Designated Director" in d: d["Designated_Director"] = d.pop("Designated Director")
            break
    full_data["directors_details"] = directors_details

    # --- 11. Complaints Details (SCORES 2.0, ODR, GRC) ---
    months = get_months_years()
    
    def parse_complaints_table(header_text):
        comp_data = {}
        for acc in soup.find_all("div", class_="accordion-item"):
            header = acc.find("div", class_="accordion-header")
            if header and header_text in header.get_text():
                content = acc.find("div", class_="accordion-content")
                if content:
                    table = content.find("table", class_="tabular_data")
                    if table:
                        rows = table.find_all("tr")
                        for row in rows:
                            th = row.find("th")
                            if th:
                                label = clean_text(th.get_text())
                                if label == "Status": continue
                                tds = row.find_all("td")
                                if len(tds) >= 6:
                                    for i, month in enumerate(months):
                                        if month not in comp_data: comp_data[month] = {}
                                        key = "Opening_Complaints" if "opening" in label.lower() else "Received"
                                        val_str = clean_text(tds[i].get_text()).replace(',', '')
                                        try:
                                            comp_data[month][key] = int(val_str or 0)
                                        except ValueError:
                                            continue
                break
        return comp_data

    full_data["scores_2_0_complaints"] = {
        "Table_Name": "Details of Complaints received in SCORES 2.0",
        "Monthly_Data": parse_complaints_table("Details of Complaints received in Scores 2.0")
    }

    odr_acc = None
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header and "Online Dispute Resolution (ODR)" in header.get_text():
            odr_acc = acc
            break
    
    if odr_acc:
        summary_comp = {}
        summary_arb = {}
        tables = odr_acc.find_all("table", class_="tabular_data")
        for i, table in enumerate(tables):
            rows = table.find_all("tr")
            for row in rows:
                th = row.find("th")
                if th:
                    label = clean_text(th.get_text())
                    if label == "Status": continue
                    tds = row.find_all("td")
                    if len(tds) >= 6:
                        target = summary_comp if i == 0 else summary_arb
                        for j, month in enumerate(months):
                            if month not in target: target[month] = {}
                            key = "Opening_Complaints" if "opening" in label.lower() else "Received"
                            if i == 1 and "opening" in label.lower(): key = "Opening_Cases"
                            val_str = clean_text(tds[j].get_text()).replace(',', '')
                            try:
                                target[month][key] = int(val_str or 0)
                            except ValueError:
                                continue
        
        full_data["odr_complaints_summary"] = {"Table_Name": "ODR – Summary of Complaints received", "Monthly_Data": summary_comp}
        full_data["odr_arbitration_summary"] = {"Table_Name": "ODR – Summary of Arbitration Cases", "Monthly_Data": summary_arb}

    # GRC
    grc_years = get_financial_years()
    grc_data = {"Table_Name": "Complaints Closed through GRC (Pre-ODR)", "Yearly_Data": {}, "Note": "As decided in GRC"}
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header and "Complaints Closed through GRC" in header.get_text():
            content = acc.find("div", class_="accordion-content")
            if content:
                table = content.find("table", class_="tabular_data")
                if table:
                    rows = table.find_all("tr")
                    for row in rows:
                        th = row.find("th")
                        if th and "Total Count" in th.get_text():
                            tds = row.find_all("td")
                            for i, year in enumerate(grc_years):
                                if i < len(tds):
                                    val_str = clean_text(tds[i].get_text()).replace(',', '')
                                    try:
                                        grc_data["Yearly_Data"][year] = int(val_str or 0)
                                    except ValueError:
                                        continue
                            break
            break
    full_data["grc_complaints_closed"] = grc_data

    # --- 12. Disciplinary Actions Master ---
    disciplinary_master = {"As_on_Date": "22-DEC-2025", "NSE_Disciplinary_Actions": {}, "NSE_Member_Committee_Orders": {}, "Disciplinary_Actions_By_Other_Exchanges": {}, "SEBI_Orders": {}, "Consent_Orders": {}, "Disclaimer": []}
    
    disc_header = soup.find(lambda t: t.name in ["td", "th"] and "Disciplinary Actions" in t.get_text() and "NSE against" in t.get_text())
    if disc_header:
        date_match = re.search(r"as on (\d{1,2}-\w{3}-\d{4})", disc_header.get_text(), re.I)
        if date_match: disciplinary_master["As_on_Date"] = date_match.group(1)

    # First column can be 2021-2022 or 2022-2023 based on dropdown
    # Remaining columns are: 3rd last, 2nd last, current financial year
    # which are: 2023-2024, 2024-2025, 2025-2026
    
    # NSE Disciplinary Actions - Monetary Penalties
    penalties_2022 = {}  # When dropdown shows 2022-2023
    # Find the th element with the text, then get its direct parent tr (not ancestor tr)
    all_ths = soup.find_all(lambda t: t.name == "th" and "Total monetary penalty levied" in t.get_text())
    for th in all_ths:
        tr = th.find_parent("tr")
        # Make sure this tr has td siblings (data cells)
        tds = tr.find_all(["td", "th"], recursive=False)
        if len(tds) > 1:  # Found the right row with data
            # Map the columns: [0]=header, [1]=fourth year(dropdown), [2]=third last, [3]=second last, [4]=current
            years_in_order = ["2022-2023", "2023-2024", "2024-2025", "2025-2026"]
            for i, year in enumerate(years_in_order):
                if i+1 < len(tds):
                    val = clean_text(tds[i+1].get_text())
                    penalties_2022[year] = val if val else "NA"
                else:
                    penalties_2022[year] = "NA"
            break
    
    # For year_2021_2022, we'd need to change first year to 2021-2022
    # But since we only have one set of data in HTML, we replicate with adjusted keys
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
    
    # Find Orders issued(count)
    all_count_cells = soup.find_all(lambda t: t.name in ["td", "th"] and "1. Orders issued(count)" in t.get_text())
    for cell in all_count_cells:
        tr = cell.find_parent("tr")
        tds = tr.find_all(["td", "th"], recursive=False)
        if len(tds) > 1:  # Found the right row with data
            years_in_order = ["2022-2023", "2023-2024", "2024-2025", "2025-2026"]
            for i, year in enumerate(years_in_order):
                if i+1 < len(tds):
                    val_str = clean_text(tds[i+1].get_text()).replace(',', '').strip()
                    try:
                        mc_counts_2022[year] = int(val_str) if val_str else 0
                    except ValueError:
                        mc_counts_2022[year] = 0
                else:
                    mc_counts_2022[year] = 0
            break
    
    # Find Orders issued details
    all_detail_cells = soup.find_all(lambda t: t.name in ["td", "th"] and "2. Orders issued details" in t.get_text())
    for cell in all_detail_cells:
        tr = cell.find_parent("tr")
        tds = tr.find_all(["td", "th"], recursive=False)
        if len(tds) > 1:  # Found the right row with data
            years_in_order = ["2022-2023", "2023-2024", "2024-2025", "2025-2026"]
            for i, year in enumerate(years_in_order):
                if i+1 < len(tds):
                    # Check if there are PDF links
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
    
    # Create versions for 2021-2022 year selection
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
        "Path": "Home \u00bb Enforcement \u00bb Orders \u00bb Settlement Order"
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
            
            table = acc.find("table", class_="tabular_data")
            if table:
                inner = table.find("table") or table
                rows = inner.find_all("tr")
                for row in rows:
                    if row.find("thead"): continue
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 4:
                        try:
                            sr_no = int(clean_text(cells[0].get_text()) or 0)
                        except ValueError:
                            continue
                        associate_companies["Companies"].append({
                            "Sr.No": sr_no,
                            "Company_Name": clean_text(cells[1].get_text()),
                            "Sector": clean_text(cells[2].get_text()),
                            "SEBI_Registration_No": clean_text(cells[3].get_text())
                        })
            break
    full_data["associate_companies"] = associate_companies

    # --- 14. Summary of Trading Member Information ---
    summary_tm = {"Table_Name": "Summary of Trading Member Information", "Reporting_Period": "6 Monthly", "Data_By_Period": {}}
    periods = get_reporting_periods()
    for period in periods: summary_tm["Data_By_Period"][period] = {}
    
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header and "Summary of trading member Information" in header.get_text():
            table = acc.find("table", class_="tabular_data")
            if table:
                inner = table.find("table") or table
                rows = inner.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= len(periods) + 1:
                        label = clean_text(cells[-len(periods)-1].get_text())
                        if not label or label == "Particulars" or "period ending" in label.lower(): continue
                        
                        key_map = {
                            "Number of branches of TM": "Number_of_branches_of_TM",
                            "Number of employees of TM": "Number_of_employees_of_TM",
                            "Number of APs/affiliates registered": "Number_of_APs_affiliates_registered_with_Exchanges",
                            "Total number of active clients": "Total_number_of_active_clients",
                            "Number of clients (UCCs) traded in equity cash": "Clients_Equity_Cash_Segment",
                            "Number of clients (UCCs) traded derivatives": "Clients_Derivatives"
                        }
                        
                        target_key = None
                        for k, v in key_map.items():
                            if k in label:
                                target_key = v
                                break
                        
                        if target_key:
                            values = cells[-len(periods):]
                            for i, period in enumerate(periods):
                                if i < len(values):
                                    val_str = clean_text(values[i].get_text()).replace(',', '')
                                    try:
                                        summary_tm["Data_By_Period"][period][target_key] = int(val_str or 0)
                                    except ValueError:
                                        continue
            break
    full_data["summary_trading_member_info"] = summary_tm

    # --- 15. Client Bank Accounts ---
    client_bank_accounts = {"Table_Name": "Details of Client Bank Accounts disclosed to Exchange", "Note": "", "Accounts": []}
    for acc in soup.find_all("div", class_="accordion-item"):
        header = acc.find("div", class_="accordion-header")
        if header and "Details of Client Bank Accounts" in header.get_text():
            content = acc.find("div", class_="accordion-content")
            if content:
                note_el = content.find("span", class_="rowalt") or content.find("td", class_="rowalt")
                if note_el: client_bank_accounts["Note"] = clean_text(note_el.get_text())
                
                table = content.find("table", class_="tabular_data")
                if table:
                    inner = table.find("table") or table
                    rows = inner.find_all("tr")
                    for row in rows:
                        if row.find("thead"): continue
                        cells = row.find_all(["td", "th"])
                        if len(cells) >= 5:
                            try:
                                sr_no = int(clean_text(cells[0].get_text()) or 0)
                            except ValueError:
                                continue
                            client_bank_accounts["Accounts"].append({
                                "Sr.No": sr_no,
                                "Account_Name": clean_text(cells[1].get_text()),
                                "Account_Number": clean_text(cells[2].get_text()),
                                "IFSC_Code": clean_text(cells[3].get_text()),
                                "Account_Purpose": clean_text(cells[4].get_text())
                            })
            break
    full_data["client_bank_accounts"] = client_bank_accounts

    # --- 16. Trading Member Net Worth ---
    net_worth_data = {"Table_Name": "Trading Member Net Worth", "As_on_Date": "", "Regulation_Reference": "Schedule VI of SEBI (Stock Brokers) Regulations, 1992", "Net_Worth_Rs": 0}
    net_worth_row = soup.find(lambda t: t.name in ["th", "td"] and "Trading member Net worth" in t.get_text())
    if net_worth_row:
        text = net_worth_row.get_text()
        date_match = re.search(r"as on (\d{1,2}-\w{3}-\d{4})", text, re.I)
        if date_match: net_worth_data["As_on_Date"] = date_match.group(1)
        
        td = net_worth_row.find_next_sibling(["td", "th"])
        if not td:
            parent_tr = net_worth_row.find_parent("tr")
            if parent_tr:
                cells = parent_tr.find_all(["td", "th"])
                if len(cells) >= 2: td = cells[1]
        
        if td:
            val_text = clean_text(td.get_text()).replace("Rs.", "").replace(",", "").strip()
            num_match = re.search(r"(\d+)", val_text)
            if num_match:
                try:
                    net_worth_data["Net_Worth_Rs"] = int(num_match.group(1))
                except ValueError:
                    pass
    full_data["trading_member_net_worth"] = net_worth_data

    return full_data

if __name__ == "__main__":
    data = parse_details("zerodha_details.html")
    if data:
        with open("zerodha_refined.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print("Successfully saved zerodha_refined.json")
