# realtime_chatbot_hybrid.py
"""
Hybrid ChatBot:
- Small-talk (greetings, how are you, thanks, bye) handled locally.
- For other queries, fetch short summary from Wikipedia (first 1-2 sentences).
- If summary unavailable, provide link and friendly fallback.
- Simple in-memory cache to reduce repeated network calls.
"""

import requests
import urllib.parse
import time
import re

WIKI_SEARCH_URL = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) HybridChatBot/1.0"
}

CACHE = {}  # stores { query: {"title":..., "summary":...} }

# small-talk patterns and replies (lightweight)
SMALL_TALK = {
    "greeting": {
        "pattern": re.compile(r"\b(hi|hello|hey|hiya|hlo)\b", re.I),
        "replies": ["Hi!", "Hello 👋", "Hey! Kaise ho?"]
    },
    "howare": {
        "pattern": re.compile(r"\b(how are you|how r u|how're you|how are u|kaise ho|kya haal)\b", re.I),
        "replies": ["Main theek hoon, thank you! Aap kaise ho?", "Doing well — aap batao, kaise ho?"]
    },
    "imfine": {
        "pattern": re.compile(r"\b(i am fine|i'm fine|main theek hoon|mai theek hu|mai thik hu)\b", re.I),
        "replies": ["Achha! Khushi hui sunke 😊", "Great! Batao aur kuch puchna hai?"]
    },
    "thanks": {
        "pattern": re.compile(r"\b(thanks|thank you|thx|shukriya)\b", re.I),
        "replies": ["Aapka swagat hai!", "No problem!"]
    },
    "farewell": {
        "pattern": re.compile(r"\b(bye|goodbye|see ya|exit|quit|alvida)\b", re.I),
        "replies": ["Goodbye! 😊", "See you later!"]
    },
    "help": {
        "pattern": re.compile(r"\bhelp|commands\b", re.I),
        "replies": [
            "Aap simple questions pooch sakte hain like 'photosynthesis', 'who is albert einstein', ya normal chitchat (hello/how are you)."
        ]
    }
}


def check_small_talk(text: str):
    """Return small-talk reply if pattern matches, else None."""
    for key, info in SMALL_TALK.items():
        if info["pattern"].search(text):
            # return a random-ish reply (deterministic choice: use first or rotate)
            return info["replies"][0]
    return None


def wiki_search_first_title(query: str):
    """Return the first matching Wikipedia page title for query, or None."""
    q = query.strip()
    if not q:
        return None
    # check cache for title
    if q in CACHE and "title" in CACHE[q]:
        return CACHE[q]["title"]

    params = {
        "action": "opensearch",
        "search": q,
        "limit": 1,
        "namespace": 0,
        "format": "json"
    }
    try:
        r = requests.get(WIKI_SEARCH_URL, params=params, headers=HEADERS, timeout=8)
        r.raise_for_status()
        data = r.json()
        titles = data[1]
        if titles:
            title = titles[0]
            CACHE.setdefault(q, {})["title"] = title
            return title
    except Exception:
        return None
    return None


def wiki_get_summary(title: str):
    """Return short summary text for a given page title, or None."""
    if not title:
        return None
    # cached summary
    if title in CACHE and "summary" in CACHE[title]:
        return CACHE[title]["summary"]

    safe = urllib.parse.quote(title, safe="")
    url = WIKI_SUMMARY_URL.format(safe)
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        r.raise_for_status()
        data = r.json()
        summary = data.get("extract")
        if summary:
            CACHE.setdefault(title, {})["summary"] = summary
            return summary
    except Exception:
        return None
    return None


def short_sentences(text: str, max_sentences: int = 2):
    """Return first max_sentences sentences from text (nice truncation)."""
    # split on period, question, exclamation (keep punctuation)
    parts = re.split(r'(?<=[\.\?\!])\s+', text.strip())
    if not parts:
        return text
    sel = parts[:max_sentences]
    return " ".join(sel).strip()


def answer_query(user_input: str) -> str:
    user_input = user_input.strip()
    if not user_input:
        return "Kuch type karo, main madad karunga."

    # 1) small talk first
    st = check_small_talk(user_input)
    if st:
        return st

    # 2) search wiki
    title = wiki_search_first_title(user_input)
    if not title:
        return ("Maaf kijiye — mujhe Wikipedia par match nahi mila. "
                "Aap query thoda badal ke try kar sakte hain (e.g., 'photosynthesis' ya 'who is sachin tendulkar').")

    summary = wiki_get_summary(title)
    if summary:
        short = short_sentences(summary, max_sentences=2)
        link = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
        return f"**{title}**\n{short}\n\nAgar aur padhna ho: {link}"
    else:
        # title found but no extract available
        link = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
        return (f"Maine ek page dhoondh liya: {title} — lekin short summary fetch nahi hui.\n"
                f"Aap full article yahan dekh sakte hain: {link}")


def main():
    print("Hybrid ChatBot (small-talk + Wikipedia). Type 'bye' or 'exit' to quit.")
    while True:
        try:
            user = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Alvida! 😊")
            break
        if not user:
            continue
        if user.lower() in ("exit", "bye", "quit", "alvida"):
            print("Bot: Alvida! 😊")
            break

       # small typing hint
        start = time.time()
        reply = answer_query(user)
        elapsed = time.time() - start
        print(f"Bot: {reply}\n(lookup: {elapsed:.2f}s)")


if __name__ == "__main__":
    main()