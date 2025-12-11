# task3_all_in_one.py
"""
Task 3 - All in One
1) Move images (jpg/jpeg/png) from source to destination
2) Extract emails from a text file and save to emails.txt
3) Scrape webpage: save <title> to web_title.txt and short summary to web_summary.txt (if available)

Save as: task3_all_in_one.py
Run: python task3_all_in_one.py
Requires: requests (for web tasks) -> pip install requests
"""

import os
import shutil
import re
import sys
from pathlib import Path

# Try import requests, give friendly message if missing
try:
    import requests
    from urllib.parse import quote as urlquote
except Exception:
    requests = None

# ----------------------- Helper utilities -----------------------
def prompt_default(prompt_text, default):
    val = input(f"{prompt_text} [{default}]: ").strip()
    return val if val else default

def ensure_dir(p):
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p

# ----------------------- Task A: Move Images -----------------------
def move_images():
    print("\n--- Move Images (jpg/jpeg/png) ---")
    src = prompt_default("Enter source folder (full path or relative)", ".")
    dst = prompt_default("Enter destination folder", "./Moved_Images")
    exts = {".jpg", ".jpeg", ".png"}
    src_p = Path(src)
    if not src_p.exists() or not src_p.is_dir():
        print("Source folder does not exist or is not a folder.")
        return
    dst_p = ensure_dir(dst)

    moved = []
    errors = []
    for name in os.listdir(src_p):
        path = src_p / name
        if path.is_file():
            _, ext = os.path.splitext(name)
            if ext.lower() in exts:
                dest_path = dst_p / name
                try:
                    # avoid overwrite by adding suffix if needed
                    if dest_path.exists():
                        base, ext2 = os.path.splitext(name)
                        i = 1
                        while True:
                            new_name = f"{base}_{i}{ext2}"
                            new_dest = dst_p / new_name
                            if not new_dest.exists():
                                dest_path = new_dest
                                break
                            i += 1
                    shutil.move(str(path), str(dest_path))
                    moved.append(dest_path.name)
                except Exception as e:
                    errors.append((name, str(e)))

    print(f"\nResult: Moved {len(moved)} file(s).")
    if moved:
        print("Files moved:")
        for f in moved:
            print(" -", f)
    if errors:
        print("Errors:")
        for fn, err in errors:
            print(" -", fn, ":", err)
    print("Done.\n")

# ----------------------- Task B: Extract Emails -----------------------
def extract_emails():
    print("\n--- Extract Emails from text file ---")
    default_in = "data.txt"
    input_path = prompt_default("Enter input text file path", default_in)
    out_path = prompt_default("Enter output file for emails", "emails.txt")
    in_p = Path(input_path)
    if not in_p.exists():
        print(f"Input file not found: {in_p}. Create it and add text containing emails, then try again.")
        return

    text = in_p.read_text(encoding="utf-8", errors="ignore")
    # regex for email addresses
    EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    found = re.findall(EMAIL_REGEX, text)
    unique = sorted(set(found), key=lambda s: s.lower())

    if not unique:
        print("No email addresses found in the file.")
        return
    out_p = Path(out_path)
    out_p.write_text("\n".join(unique), encoding="utf-8")
    print(f"Extracted {len(unique)} unique email(s) and saved to {out_p}")
    for e in unique:
        print(" -", e)
    print("Done.\n")

# ----------------------- Task C: Web Title & Short Summary -----------------------
def web_scrape_title_and_summary():
    if requests is None:
        print("Error: 'requests' library not installed. Install with: pip install requests")
        return
    print("\n--- Scrape webpage title and short summary ---")
    default_url = "https://www.example.com/"
    url = prompt_default("Enter webpage URL", default_url).strip()
    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url  # assume https if not provided

    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Task3Bot/1.0"}

    # Fetch the page
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Error fetching URL:", type(e).__name__, e)
        return

    # Extract title using regex
    m = re.search(r"<title[^>]*>(.*?)</title>", r.text, flags=re.I | re.S)
    title_text = None
    if m:
        title_text = re.sub(r"\s+", " ", m.group(1)).strip()

    # Try REST summary endpoint (Wikipedia-like) if domain is wikipedia.org
    summary_text = None
    if "wikipedia.org" in url.lower():
        # build REST summary endpoint for wikipedia
        # extract page path after /wiki/
        try:
            # attempt to take last path part as title
            page = url.rstrip("/").split("/")[-1]
            if page:
                rest_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urlquote(page)}"
                try:
                    rr = requests.get(rest_url, headers=HEADERS, timeout=8)
                    rr.raise_for_status()
                    jd = rr.json()
                    summary_text = jd.get("extract")
                except Exception:
                    summary_text = None
        except Exception:
            summary_text = None

    # Fallback: if not Wikipedia, attempt to create a short summary by taking first 1-2 sentences of visible text
    if summary_text is None and title_text:
        # crude: strip tags and take first 300 chars then sentences
        stripped = re.sub(r"<script.*?>.*?</script>", "", r.text, flags=re.I | re.S)
        stripped = re.sub(r"<[^>]+>", " ", stripped)
        stripped = re.sub(r"\s+", " ", stripped).strip()
        # get first 2 sentences
        parts = re.split(r'(?<=[\.\?\!])\s+', stripped)
        if parts:
            summary_text = " ".join(parts[:2]).strip()
            # trim to ~500 chars max
            if len(summary_text) > 500:
                summary_text = summary_text[:500].rsplit(" ", 1)[0] + "..."

    # Save outputs
    if title_text:
        Path("web_title.txt").write_text(title_text, encoding="utf-8")
        print("Saved title to web_title.txt")
        print("Title:", title_text)
    else:
        print("Title tag not found.")

    if summary_text:
        Path("web_summary.txt").write_text(summary_text, encoding="utf-8")
        print("Saved short summary to web_summary.txt")
        print("Summary (preview):", summary_text[:300] + ("..." if len(summary_text) > 300 else ""))
    else:
        print("Short summary not available.")

    print("Full page saved link:", url)
    print("Done.\n")

# ----------------------- Menu & Runner -----------------------
def print_menu():
    print("\n=== Task 3: Automation Suite ===")
    print("1) Move image files (.jpg/.jpeg/.png)")
    print("2) Extract emails from a text file")
    print("3) Scrape webpage title & short summary")
    print("4) Run all tasks sequentially (asks inputs for each)")
    print("0) Exit")

def run_all():
    # Run move images (use defaults or user inputs)
    move_images()
    extract_emails()
    # For web scrape, warn if requests missing
    if requests is None:
        print("Skipping web scraping step because 'requests' is not installed.")
    else:
        web_scrape_title_and_summary()

def main():
    while True:
        print_menu()
        choice = input("Enter choice: ").strip()
        if choice == "1":
            move_images()
        elif choice == "2":
            extract_emails()
        elif choice == "3":
            web_scrape_title_and_summary()
        elif choice == "4":
            run_all()
        elif choice == "0" or choice.lower() in ("exit", "quit"):
            print("Exiting. Bye!")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
