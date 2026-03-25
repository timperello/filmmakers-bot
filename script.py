import requests
from bs4 import BeautifulSoup
import os

URL = "https://www.filmmakers.co.kr/?mid=performerCasting&search_keyword=외국인"
WEBHOOK = os.environ["WEBHOOK"]

# fichier pour stocker le dernier post
LAST_FILE = "last.txt"

res = requests.get(URL)
soup = BeautifulSoup(res.text, "html.parser")

posts = soup.select("table tbody tr")

if not posts:
    exit()

latest_post = posts[0]
title = latest_post.get_text(strip=True)

# lire ancien post
if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r", encoding="utf-8") as f:
        last_title = f.read()
else:
    last_title = ""

# comparer
if title != last_title:
    # envoyer notif
    requests.post(WEBHOOK, json={
        "content": f"🔥 New casting!\n\n{title}\n\n{URL}"
    })

    # sauvegarder
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(title)
