import requests
from bs4 import BeautifulSoup
import os
import re
import json
import time
from datetime import datetime
from deep_translator import GoogleTranslator

# 🔹 URL de recherche filtrée (ajuste search_keyword / extra_vars_gender selon tes besoins)
SEARCH_URL = (
    "https://www.filmmakers.co.kr/performerCasting/"
    "?search_target=title_content"
    "&search_keyword=%EC%99%B8%EA%B5%AD%EC%9D%B8"   # 외국인
    "&extra_vars_gender=%EB%82%A8%EC%9E%90"          # 남자
)

WEBHOOK = os.environ["WEBHOOK"]
SEEN_FILE = "seen_ids.json"
MAX_SEEN = 300

HEADERS = {"User-Agent": "Mozilla/5.0"}

MONTHS = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril",
    5: "Mai", 6: "Juin", 7: "Juillet", 8: "Août",
    9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Décembre"
}

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?")


def format_date(raw):
    try:
        if len(raw) > 10:
            dt = datetime.strptime(raw, "%Y-%m-%d %H:%M")
            return f"{dt.day} {MONTHS[dt.month]} {dt.year} à {dt.strftime('%Hh%M')}"
        else:
            dt = datetime.strptime(raw, "%Y-%m-%d")
            return f"{dt.day} {MONTHS[dt.month]} {dt.year}"
    except Exception:
        return raw


def translate(text):
    try:
        return GoogleTranslator(source='ko', target='en').translate(text)
    except Exception:
        return text


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen_ids):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_ids)[-MAX_SEEN:], f)


def send_discord(content):
    try:
        r = requests.post(WEBHOOK, json={"content": content}, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"Erreur webhook: {e}")


def parse_post(post):
    title_tag = post.select_one("h2 a")
    if not title_tag:
        return None

    title = title_tag.text.strip()
    href = title_tag.get("href", "")
    match = re.search(r'/performerCasting/(\d+)', href)
    if not match:
        return None
    post_id = match.group(1)
    link = f"https://www.filmmakers.co.kr/performerCasting/{post_id}"

    # 🔹 date de création : span dont le texte matche le pattern date
    created = "Unknown"
    for span in post.find_all("span"):
        text = span.get_text(strip=True)
        if DATE_RE.fullmatch(text):
            created = text
            break

    # 🔹 catégorie : premier span "badge" hors badge-new et hors date
    category = "N/A"
    for span in post.find_all("span"):
        classes = span.get("class", [])
        text = span.get_text(strip=True)
        if "badge-new" in classes or DATE_RE.fullmatch(text):
            continue
        if text:
            category = text
            break

    # 🔹 grille d'infos structurée (제작/역할/성별/연령/출연료/마감 etc.)
    info = {}
    grid = post.select_one("div.grid")
    if grid:
        for item in grid.find_all("div", recursive=False):
            divs = item.find_all("div", recursive=False)
            if len(divs) >= 2:
                label = divs[0].get_text(strip=True)
                value = divs[1].get_text(strip=True)
                info[label] = value

    return {
        "id": post_id,
        "title": title,
        "link": link,
        "created": created,
        "category": category,
        "info": info,
    }


def build_message(post):
    translated_title = translate(post["title"])
    translated_category = translate(post["category"])
    formatted_time = format_date(post["created"])
    info = post["info"]

    lines = [
        "\u200b",
        f"🎬 **Nouveau casting posté le {formatted_time}**",
        "\u200b",
        f"📁 {translated_category} ({post['category']})",
        f"📝 {translated_title}",
        "\u200b",
        f"🇰🇷 {post['title']}",
        "\u200b",
    ]

    field_labels = {
        "제작": "🏢 Production",
        "성별": "🚻 Genre",
        "출연료": "💰 Paie",
        "마감": "⏰ Deadline",
    }

    for ko_label, display_label in field_labels.items():
        if ko_label in info:
            value = info[ko_label]
            if ko_label == "마감" and DATE_RE.fullmatch(value):
                value = format_date(value)
            lines.append(f"{display_label} : {value}")

    lines.append("\u200b")
    lines.append(f"🔗 {post['link']}")

    return "\n".join(lines)


def main():
    try:
        res = requests.get(SEARCH_URL, headers=HEADERS, timeout=10)
        print(f"Status code: {res.status_code}, taille réponse: {len(res.text)} caractères")
        res.raise_for_status()
    except requests.RequestException as e:
        print(f"Erreur fetch: {e}")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    post_divs = soup.select("div.p-3.cursor-pointer.group")

    if not post_divs:
        print("Aucun post trouvé (sélecteur cassé ou page vide) — vérifier le HTML")
        return

    seen_ids = load_seen()
    all_posts = []
    for div in post_divs:
        parsed = parse_post(div)
        if parsed:
            all_posts.append(parsed)

    if not all_posts:
        print("Aucun post parsable")
        return

    new_posts = [p for p in all_posts if p["id"] not in seen_ids]

    if not new_posts:
        save_seen(seen_ids | {p["id"] for p in all_posts})
        print("Aucune nouvelle offre")
        return

    count = len(new_posts)
    text = f"{count} nouvelle offre" if count <= 1 else f"{count} nouvelles offres"
    send_discord(f"\u200b\n🚀 {text} !")

    for post in reversed(new_posts):
        send_discord(build_message(post))
        time.sleep(0.5)  # évite le rate limit Discord

    save_seen(seen_ids | {p["id"] for p in all_posts})


if __name__ == "__main__":
    main()
