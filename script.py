import requests
from bs4 import BeautifulSoup
import os
import re

URL = "https://www.filmmakers.co.kr/performerCasting?search_target=title_content&search_keyword=%EC%99%B8%EA%B5%AD%EC%9D%B8&extra_vars_gender=%EB%82%A8%EC%9E%90"
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

    # ID unique
    match = re.search(r'/performerCasting/(\d+)', href)
    post_id = match.group(1) if match else None

    link = "https://www.filmmakers.co.kr" + href

    # 🔥 récupérer date/heure
    time_tag = post.select_one("div.text-xs.text-neutral-500 span")
    post_time = time_tag.text.strip() if time_tag else "Unknown time"

    if post_id:
        all_posts.append((post_id, title, link, post_time))

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
    # ✅ Message summary unique
    summary_msg = f"🚀 {len(new_posts)} nouvelles offres sur Filmmakers !"
    requests.post(WEBHOOK, json={"content": summary_msg})
    print(summary_msg)

    # ✅ Ensuite on loop pour les détails
    for post_id, title, link, post_time in reversed(new_posts):
        message = (
            f"🎬 **New casting**\n"
            f"📝 {title}\n"
            f"🕒 {post_time}\n"
            f"🔗 {link}"
        )
        requests.post(WEBHOOK, json={"content": message})

else:
    print("Pas de nouveau post")

# 🔹 Sauvegarder le plus récent
latest_id = all_posts[0][0]

with open(LAST_FILE, "w", encoding="utf-8") as f:
    f.write(latest_id)
