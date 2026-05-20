import requests
from bs4 import BeautifulSoup
import json, os, re

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEEN_FILE = "seen_jobs.json"
SEARCH_URL = "https://sainsburys.jobs/jobs?location=Coventry"
KEYWORDS = ["online assistant", "home delivery", "driver"]

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
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    res = requests.get(SEARCH_URL, headers=headers, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")

    jobs = []

    # Find all "Learn more" links — each one is a job
    for link_tag in soup.find_all("a", string=re.compile("Learn more", re.I)):
        link = link_tag.get("href", "")
        if not link.startswith("http"):
            link = "https://sainsburys.jobs" + link

        # Walk backwards to find the nearest h3
        h3 = link_tag.find_previous("h3")
        title = h3.get_text(strip=True) if h3 else "Unknown"
        jobs.append((title, link))

    print(f"Found {len(jobs)} jobs total:")
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
