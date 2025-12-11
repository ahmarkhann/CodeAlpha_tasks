import random
import os
import sys

# --- Config ---
MIN_WORD_LEN = 4
MAX_WORD_LEN = 12
ONLINE_FETCH_COUNT = 200  # how many words to request if using API

# --- Helpers to load words from different places ---
def load_words_from_file(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            words = [w.strip().lower() for w in f if w.strip()]
        return words
    except Exception:
        return []

def load_words_local_sources():
    # 1) words.txt in current directory
    words = load_words_from_file("words.txt")
    if words:
        print("[INFO] Loaded words from words.txt")
        return words

    # 2) common system dictionary locations
    system_paths = ["/usr/share/dict/words", "/usr/dict/words"]
    for p in system_paths:
        if os.path.isfile(p):
            words = load_words_from_file(p)
            if words:
                print(f"[INFO] Loaded words from system dictionary: {p}")
                return words

    return []

def fetch_words_online():
    # Try to fetch words from an online API (random-word-api)
    # This requires internet and 'requests' package.
    try:
        import requests
    except Exception:
        return []

    # random-word-api.herokuapp.com can be used; fallback if it fails
    urls = [
        f"https://random-word-api.herokuapp.com/word?number={ONLINE_FETCH_COUNT}",
        f"https://random-word-api.vercel.app/word?number={ONLINE_FETCH_COUNT}"
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    print("[INFO] Fetched words from online API")
                    return [w.lower() for w in data if isinstance(w, str)]
        except Exception:
            continue
    return []

def sanitize_and_filter(words):
    filtered = []
    for w in words:
        w = w.strip().lower()
        # Keep only alphabetic words and within length limits
        if w.isalpha() and MIN_WORD_LEN <= len(w) <= MAX_WORD_LEN:
            filtered.append(w)
    return list(set(filtered))  # remove duplicates

# --- Prepare word list (tries multiple sources) ---
words = sanitize_and_filter(load_words_local_sources())

if not words:
    words = sanitize_and_filter(fetch_words_online())

# Emergency fallback (very small): only used if nothing else found
if not words:
    print("[WARN] No external word source found — using fallback word list.")
    words = ["python", "hangman", "computer", "program", "science", "apple"]

# --- Choose secret word ---
secret_word = random.choice(words)

# --- Reveal 1 or 2 letters as hint (based on length) ---
reveal_count = 2 if len(secret_word) >= 5 else 1
# choose distinct positions to reveal
positions = random.sample(range(len(secret_word)), k=reveal_count)
guessed_letters = [secret_word[pos] for pos in positions]
guessed_letters = list(set(guessed_letters))  # unique letters

tries = 6

print("🎮 Welcome to Hangman!")
print(f"💡 Hint: {reveal_count} letter(s) revealed to start.")
print("Guess the word:")

# --- Game loop ---
while tries > 0:
    display_word = "".join([ch if ch in guessed_letters else "_" for ch in secret_word])
    print("\nWord:", " ".join(display_word))  # spaced underscores for readability

    if display_word == secret_word:
        print("\n🎉 Congratulations! You guessed the word:", secret_word)
        break

    guess = input("Enter a letter: ").strip().lower()

    if not guess.isalpha() or len(guess) != 1:
        print("❌ Invalid input — enter a single alphabet letter.")
        continue

    if guess in guessed_letters:
        print("⚠️  You already guessed that letter.")
        continue

    if guess in secret_word:
        guessed_letters.append(guess)
        print("✔️  Correct!")
    else:
        tries -= 1
        print(f"❌  Wrong! Tries left: {tries}")

if tries == 0:
    print("\n😢 Game Over! The word was:", secret_word)