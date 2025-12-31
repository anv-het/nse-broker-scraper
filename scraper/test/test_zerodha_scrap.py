import requests

url = "https://enit.nseindia.com/MemDirWeb/brokerDetailPage_Beta?memID=397&h_MemType=members&memName=ANGEL%20ONE%20LIMITED"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/"
}

session = requests.Session()
response = session.get(url, headers=headers, timeout=10)

if response.status_code == 200:
    with open("response.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("HTML response saved to response.html")
else:
    print(f"Failed. Status code: {response.status_code}")
