import requests
from bs4 import BeautifulSoup
import os

URL = "https://www.filmmakers.co.kr/?mid=performerCasting&category=&search_target=title_content&search_keyword=%EC%99%B8%EA%B5%AD%EC%9D%B8"
WEBHOOK = os.environ["WEBHOOK"]

LAST_FILE = "last.txt"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# fetch page
res = requests.get(URL, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

posts = soup.select("div.p-3.cursor-pointer.group")

if not posts:
    print("Aucun post trouvé")
    exit()

first = posts[0]

title_tag = first.select_one("h2 a")
title = title_tag.text.strip() if title_tag else "No title"
link = "https://www.filmmakers.co.kr" + title_tag["href"]

print("Titre:", title)

# lire ancien post
if os.path.exists(LAST_FILE):
    with open(LAST_FILE, "r", encoding="utf-8") as f:
        last_title = f.read()
else:
    last_title = ""

# comparer
if title != last_title:
    print("NOUVEAU POST 🚀")

    # envoyer notif
    requests.post(WEBHOOK, json={
        "content": f"🎬 New casting!\n\n{title}\n{link}"
    })

    # sauvegarder
    with open(LAST_FILE, "w", encoding="utf-8") as f:
        f.write(title)

else:
    print("Pas de nouveau post")
