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

# 🔹 Extraire les 5 derniers posts
latest_posts = []

for post in posts[:5]:
    title_tag = post.select_one("h2 a")
    if not title_tag:
        continue

    title = title_tag.text.strip()
    href = title_tag["href"]

    # 🔥 extraire ID unique
    match = re.search(r'/performerCasting/(\d+)', href)
    post_id = match.group(1) if match else None

    link = "https://www.filmmakers.co.kr" + href

    if post_id:
        latest_posts.append((post_id, title, link))

# 🔹 Charger anciens IDs
if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r", encoding="utf-8") as f:
        seen_ids = set(f.read().splitlines())
else:
    seen_ids = set()

# 🔹 Détecter nouveaux posts
new_posts = []

for post_id, title, link in latest_posts:
    if post_id not in seen_ids:
        new_posts.append((post_id, title, link))

# 🔹 Envoyer notifications
if new_posts:
    print(f"{len(new_posts)} nouveaux posts 🚀")

    # ordre logique (ancien → récent)
    for post_id, title, link in reversed(new_posts):
        message = f"🎬 **New casting**\n\n{title}\n{link}"
        requests.post(WEBHOOK, json={"content": message})

else:
    print("Pas de nouveau post")

# 🔹 Sauvegarder les IDs récents
with open(LAST_FILE, "w", encoding="utf-8") as f:
    for post_id, _, _ in latest_posts:
        f.write(post_id + "\n")
