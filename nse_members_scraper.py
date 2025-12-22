import requests
import os
import urllib3

# Suppress only the single warning from urllib3 needed.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_nse_members():
    url = "https://enit.nseindia.com/MemDirWeb/searchMembers_Beta?step=searchTradeMembersList"
    
    # Enhanced headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }

    try:
        print(f"Sending request to: {url}")
        # Added timeout and verify=False
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Print the response content
            print("\nResponse Content (First 500 chars):")
            print(response.text[:500])
            print("...")

            # Save the data
            content_type = response.headers.get('Content-Type', '').lower()
            if 'json' in content_type:
                filename = "nse_members_data.json"
            else:
                filename = "nse_members_data.html"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            print(f"\nFull response saved to: {os.path.abspath(filename)}")
            
        else:
            print("Failed to retrieve data.")
            print(f"Response Status: {response.status_code}")
            print(f"Response Text: {response.text[:500]}")

    except requests.exceptions.Timeout:
        print("Error: The request timed out.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    fetch_nse_members()
