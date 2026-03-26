import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

URL = "https://www.filmmakers.co.kr/performerCasting?search_target=title_content&search_keyword=%EC%99%B8%EA%B5%AD%EC%9D%B8&extra_vars_gender=%EB%82%A8%EC%9E%90"
WEBHOOK = os.environ["WEBHOOK"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

LAST_FILE = "last.txt"

# 🔥 Mois FR
MONTHS = {
    1: "Janvier",
    2: "Février",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
    7: "Juillet",
    8: "Août",
    9: "Septembre",
    10: "Octobre",
    11: "Novembre",
    12: "Décembre"
}

# 🔹 Format date
def format_date(raw):
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
        return f"{dt.day} {MONTHS[dt.month]} {dt.year} à {dt.strftime('%Hh%M')}"
    except:
        return raw

# 🔹 Fetch page
res = requests.get(URL, headers=HEADERS)
soup = BeautifulSoup(res.text, "html.parser")

posts = soup.select("div.p-3.cursor-pointer.group")

if not posts:
    print("Aucun post trouvé")
    exit()

# 🔹 Construire liste complète
all_posts = []

for post in posts:
    title_tag = post.select_one("h2 a")
    if not title_tag:
        continue

    title = title_tag.text.strip()
    href = title_tag["href"]

    # ID unique
    match = re.search(r'/performerCasting/(\d+)', href)
    post_id = match.group(1) if match else None

    link = "https://www.filmmakers.co.kr" + href

    # 🔥 date brute
    time_tag = post.select_one("div.text-xs.text-neutral-500 span")
    post_time = time_tag.text.strip() if time_tag else "Unknown time"

    formatted_time = format_date(post_time)

    if post_id:
        all_posts.append((post_id, title, link, formatted_time))

# 🔹 Charger last_id
if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r", encoding="utf-8") as f:
        last_id = f.read().strip()
else:
    last_id = None

print("Last ID:", last_id)

# 🔹 Détecter nouveaux posts
new_posts = []

if last_id:
    ids = [p[0] for p in all_posts]

    if last_id in ids:
        index = ids.index(last_id)
        new_posts = all_posts[:index]
    else:
        print("⚠️ last_id non trouvé → fallback")
        new_posts = all_posts
else:
    print("First run → init seulement")
    new_posts = []

# 🔹 Envoyer notifications
if new_posts:
    summary_msg = f"🚀 {len(new_posts)} nouvelles offres sur Filmmakers !"
    requests.post(WEBHOOK, json={"content": summary_msg})
    print(summary_msg)

    for post_id, title, link, post_time in reversed(new_posts):

        message = (
            f"\u200b\n\n"
            f"🎬 **Nouveau casting**\n\n"
            f"📝 {title}\n\n"
            f"🕒 {post_time}\n\n"
            f"🔗 {link}\n"
        )

        requests.post(WEBHOOK, json={"content": message})

else:
    print("Pas de nouveau post")

# 🔹 Sauvegarder le plus récent
latest_id = all_posts[0][0]

with open(LAST_FILE, "w", encoding="utf-8") as f:
    f.write(latest_id)
