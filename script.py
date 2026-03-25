import requests
from bs4 import BeautifulSoup
import os
import re

URL = "https://www.filmmakers.co.kr/?mid=performerCasting&category=&search_target=title_content&search_keyword=%EC%99%B8%EA%B5%AD%EC%9D%B8"
WEBHOOK = os.environ["WEBHOOK"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

LAST_FILE = "last.txt"

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

    match = re.search(r'/performerCasting/(\d+)', href)
    post_id = match.group(1) if match else None

    link = "https://www.filmmakers.co.kr" + href

    if post_id:
        all_posts.append((post_id, title, link))

# 🔹 Charger last_id
if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r", encoding="utf-8") as f:
        last_id = f.read().strip()
else:
    last_id = None

print("Last ID:", last_id)

# 🔹 Trouver nouveaux posts
new_posts = []

if last_id:
    ids = [p[0] for p in all_posts]

    if last_id in ids:
        index = ids.index(last_id)
        new_posts = all_posts[:index]  # tous ceux avant = nouveaux
    else:
        print("⚠️ last_id non trouvé → fallback")
        new_posts = all_posts[:5]  # sécurité

else:
    print("First run → on ignore l'envoi")
    new_posts = []

# 🔹 Envoyer notifications
if new_posts:
    print(f"{len(new_posts)} nouveaux posts 🚀")

    for post_id, title, link in reversed(new_posts):
        message = f"🎬 **New casting**\n\n{title}\n{link}"
        requests.post(WEBHOOK, json={"content": message})

else:
    print("Pas de nouveau post")

# 🔹 Sauvegarder le plus récent
latest_id = all_posts[0][0]

with open(LAST_FILE, "w", encoding="utf-8") as f:
    f.write(latest_id)
