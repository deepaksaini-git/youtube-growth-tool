import requests
import json
import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_trending_tags(keyword):
    url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        suggestions = json.loads(response.text)[1]
        return suggestions[:10] 
    except Exception as e:
        print(f"Error fetching {keyword}: {e}")
        return []

def send_to_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram Secrets nahi mile!")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Success: Telegram par alert bhej diya gaya hai!")
    else:
        print("Error: Telegram alert fail ho gaya:", response.text)

if __name__ == "__main__":
    target_keywords = [
        "shape matching puzzle", 
        "kids learning shapes", 
        "gta 5 funny gameplay", 
        "bgmi shorts"
    ]
    
    final_message = "🚀 *Daily YouTube SEO Trends*\n\n"
    
    for kw in target_keywords:
        tags = get_trending_tags(kw)
        if tags:
            tags_str = ", ".join(tags)
            final_message += f"🎯 *{kw.title()}*:\n`{tags_str}`\n\n"
            
    send_to_telegram(final_message)
