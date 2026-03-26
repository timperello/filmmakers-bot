import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime
from deep_translator import GoogleTranslator

URL = "https://www.filmmakers.co.kr/performerCasting?search_target=title_content&search_keyword=%EC%99%B8%EA%B5%AD%EC%9D%B8&extra_vars_gender=%EB%82%A8%EC%9E%90"
WEBHOOK = os.environ["WEBHOOK"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

LAST_FILE = "last.txt"

MONTHS = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}

def format_date(raw):
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
        return f"{dt.day} {MONTHS[dt.month]} {dt.year} à {dt.strftime('%Hh%M')}"
    except:
        return raw

def translate(text):
    try:
        return GoogleTranslator(source='ko', target='en').translate(text)
    except:
        return text

# 🔹 Fetch
res = requests.get(URL, headers=HEADERS)
soup = BeautifulSoup(res.text, "html.parser")

posts = soup.select("div.p-3.cursor-pointer.group")

if not posts:
    print("Aucun post trouvé")
    exit()

all_posts = []

for post in posts:
    title_tag = post.select_one("h2 a")
    if not title_tag:
        continue

    title = title_tag.text.strip()
    translated_title = translate(title)

    href = title_tag["href"]

    match = re.search(r'/performerCasting/(\d+)', href)
    post_id = match.group(1) if match else None

    link = "https://www.filmmakers.co.kr" + href

    # 🔹 Date
    time_tag = post.select_one("div.text-xs.text-neutral-500 span")
    post_time = time_tag.text.strip() if time_tag else "Unknown"
    formatted_time = format_date(post_time)

    # 🔥 PAIEMENT CLEAN
    pay = "Non précisé"

    pay_label = post.find("span", string=lambda x: x and "출연료" in x)

    if pay_label:
        parent = pay_label.parent
        full_text = parent.get_text(strip=True)
        pay = full_text.replace("출연료", "").strip()

    if post_id:
        all_posts.append((post_id, title, translated_title, link, formatted_time, pay))

# 🔹 LAST ID
if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r", encoding="utf-8") as f:
        last_id = f.read().strip()
else:
    last_id = None

new_posts = []

if last_id:
    ids = [p[0] for p in all_posts]

    if last_id in ids:
        index = ids.index(last_id)
        new_posts = all_posts[:index]
    else:
        new_posts = all_posts
else:
    new_posts = []

# 🔹 DISCORD
if new_posts:
    requests.post(WEBHOOK, json={
        "content": f"🚀 {len(new_posts)} nouvelles offres !"
    })

    for post_id, title, translated, link, time, pay in reversed(new_posts):

        message = (
            f"\u200b\n"
            f"🎬 **New casting**\n"
            f"\u200b\n"
            f"📝 {translated}\n"
            f"\u200b\n"
            f"🇰🇷 {title}\n"
            f"\u200b\n"
            f"💰 {pay}\n"
            f"\u200b\n"
            f"🕒 {time}\n"
            f"\u200b\n"
            f"🔗 {link}"
        )

        requests.post(WEBHOOK, json={"content": message})

# 🔹 SAVE
latest_id = all_posts[0][0]

with open(LAST_FILE, "w", encoding="utf-8") as f:
    f.write(latest_id)
