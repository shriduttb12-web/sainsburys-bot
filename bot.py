import requests
from bs4 import BeautifulSoup
import json, os

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEEN_FILE = "seen_jobs.json"
SEARCH_URL = "https://sainsburys.jobs/jobs?location=Coventry"
KEYWORDS = ["online assistant", "Online" , "Assistant"]

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def get_jobs():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.5",
    }
    res = requests.get(SEARCH_URL, headers=headers, timeout=15)
    print(f"Page status: {res.status_code}, size: {len(res.text)} chars")

    soup = BeautifulSoup(res.text, "html.parser")

    jobs = []
    # Find all links to job description pages
    for link_tag in soup.find_all("a", href=True):
        href = link_tag["href"]
        if "/jobs/description/" in href:
            full_link = href if href.startswith("http") else "https://sainsburys.jobs" + href
            h3 = link_tag.find_previous("h3")
            title = h3.get_text(strip=True) if h3 else "Unknown Role"
            jobs.append((title, full_link))

    print(f"Found {len(jobs)} jobs:")
    for t, l in jobs:
        print(f"  - {t}")

    return jobs

def is_target(title):
    return any(kw in title.lower() for kw in KEYWORDS)

seen = load_seen()
jobs = get_jobs()
new_targets = []

for title, link in jobs:
    if is_target(title) and link not in seen:
        new_targets.append((title, link))
        seen.add(link)

if new_targets:
    for title, link in new_targets:
        msg = (f"🛒 <b>New Sainsbury's Job in Coventry!</b>\n\n"
               f"<b>{title}</b>\n<a href='{link}'>Apply here</a>")
        send_telegram(msg)
        print(f"Alert sent: {title}")
else:
    print("No new matching jobs found.")

save_seen(seen)
