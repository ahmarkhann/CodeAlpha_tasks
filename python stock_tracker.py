# stock_tracker_live.py
import csv
from datetime import datetime

# Optional live fetch with yfinance (only import if user chooses live)
try:
    import yfinance as yf
except Exception:
    yf = None

# ----- Hardcoded stock prices (fallback / manual) -----
stock_prices = {
    "AAPL": 180.0,
    "TSLA": 250.0,
    "GOOGL": 130.0,
    "MSFT": 320.0,
    "AMZN": 140.0
}

def input_positive_int(prompt):
    while True:
        val = input(prompt).strip()
        try:
            n = int(val)
            if n < 0:
                print("Enter a non-negative integer.")
                continue
            return n
        except ValueError:
            print("Please enter a valid integer.")

def input_positive_float(prompt):
    while True:
        val = input(prompt).strip()
        try:
            f = float(val)
            if f < 0:
                print("Enter a non-negative number.")
                continue
            return f
        except ValueError:
            print("Please enter a valid number (e.g., 12.5).")

def format_money(x):
    return f"${x:,.2f}"

def fetch_live_price(symbol):
    """Try multiple yfinance methods to get a live-ish price.
       Returns float price or None if not available."""
    if yf is None:
        return None

    try:
        ticker = yf.Ticker(symbol)
    except Exception:
        return None

    # 1) Try fast_info last_price (works for many tickers)
    try:
        fi = getattr(ticker, "fast_info", None)
        if fi and isinstance(fi, dict):
            last = fi.get("last_price") or fi.get("last_trade_price") or fi.get("last")
            if last:
                return float(last)
    except Exception:
        pass

    # 2) Fallback: use history for period='1d' and take last close
    try:
        hist = ticker.history(period="1d", interval="1m")
        if hist is not None and not hist.empty:
            # use last available 'Close' value
            last_close = hist["Close"].iloc[-1]
            return float(last_close)
    except Exception:
        pass

    # 3) Try the simpler history(period='1d') (some environments)
    try:
        hist2 = ticker.history(period="1d")
        if hist2 is not None and not hist2.empty:
            return float(hist2["Close"].iloc[-1])
    except Exception:
        pass

    return None

def main():
    print("📈 Live-enabled Stock Portfolio Tracker")
    use_live = input("Do you want to fetch LIVE prices from Yahoo Finance? (y/n): ").strip().lower()
    if use_live == "y" and yf is None:
        print("\n⚠ yfinance is not installed. Install by running:\n   pip install yfinance\nThen re-run this script.")
        return

    print("\nAvailable (fallback) stocks:", ", ".join(stock_prices.keys()))
    print("Type 'done' when finished.\n")

    portfolio = {}  # symbol -> total quantity
    manual_price_cache = {}  # if user enters manual price for unknown ticker

    while True:
        sym = input("Enter stock symbol (or 'done'): ").strip().upper()
        if sym == "DONE":
            break
        if not sym:
            continue

        price = None
        # If user chose live, attempt to fetch live price
        if use_live == "y":
            print(f"Fetching live price for {sym} ...")
            price = fetch_live_price(sym)
            if price is not None:
                print(f"Live price for {sym}: {format_money(price)}")
            else:
                print(f"⚠ Could not fetch live price for {sym}.")
                # If we have fallback price in hardcoded dict, show it
                if sym in stock_prices:
                    print(f"Using fallback price {format_money(stock_prices[sym])} unless you enter another price.")
                # ask user if they'd like to enter manual price
                add_manual = input("Enter price manually now? (y/n): ").strip().lower()
                if add_manual == "y":
                    price = input_positive_float(f"Enter price for {sym}: ")
                    manual_price_cache[sym] = price

        else:
            # Not using live. Check hardcoded dict first
            if sym not in stock_prices:
                print(f"'{sym}' not found in price list.")
                add = input("Do you want to add this stock and its price? (y/n): ").strip().lower()
                if add == "y":
                    price = input_positive_float(f"Enter price for {sym}: ")
                    stock_prices[sym] = price
                else:
                    print("Stock skipped.")
                    continue
            else:
                price = stock_prices[sym]

        # If price still None, check manual cache or fallback dict
        if price is None:
            price = manual_price_cache.get(sym) or stock_prices.get(sym)
        if price is None:
            print("No price available—skipping this stock.")
            continue

        qty = input_positive_int(f"Enter quantity of {sym}: ")
        if qty == 0:
            print("Zero shares added — skipping.")
            continue

        # Store the price used for this symbol for summary
        # We'll keep a mapping of symbol -> (total_qty, used_price)
        if sym in portfolio:
            portfolio[sym]["qty"] += qty
        else:
            portfolio[sym] = {"qty": qty, "price": price}
        print(f"Added {qty} shares of {sym} at {format_money(price)}.\n")

    if not portfolio:
        print("\nNo stocks in portfolio — exiting.")
        return

    # Calculate values
    rows = []
    total_value = 0.0
    for s, info in portfolio.items():
        q = info["qty"]
        price_used = info["price"]
        value = q * price_used
        rows.append((s, q, price_used, value))
        total_value += value

    # Display summary
    print("\n🧾 Portfolio Summary")
    print("-" * 60)
    print(f"{'Symbol':<8}{'Qty':>6}{'Price':>16}{'Value':>18}")
    print("-" * 60)
    for s, q, price, value in rows:
        print(f"{s:<8}{q:>6}{format_money(price):>16}{format_money(value):>18}")
    print("-" * 60)
    print(f"{'Total Investment:':<34}{format_money(total_value):>18}")

    # Save option
    save = input("\nSave report? (no / txt / csv / both): ").strip().lower()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if save in ("txt", "both"):
        fname = f"portfolio_{ts}.txt"
        with open(fname, "w", encoding="utf-8") as f:
            f.write("Portfolio Summary\n")
            f.write("-" * 60 + "\n")
            f.write(f"{'Symbol':<8}{'Qty':>6}{'Price':>16}{'Value':>18}\n")
            f.write("-" * 60 + "\n")
            for s, q, price, value in rows:
                f.write(f"{s:<8}{q:>6}{format_money(price):>16}{format_money(value):>18}\n")
            f.write("-" * 60 + "\n")
            f.write(f"{'Total Investment:':<34}{format_money(total_value):>18}\n")
        print(f"Saved TXT report as: {fname}")

    if save in ("csv", "both"):
        fname = f"portfolio_{ts}.csv"
        with open(fname, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Symbol", "Quantity", "Price", "Value"])
            for s, q, price, value in rows:
                writer.writerow([s, q, f"{price:.2f}", f"{value:.2f}"])
            writer.writerow([])
            writer.writerow(["Total Investment", "", "", f"{total_value:.2f}"])
        print(f"Saved CSV report as: {fname}")

    print("\nThank you — tracker finished.")

if __name__ == "__main__":
    main()

