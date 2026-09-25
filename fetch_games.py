import os
import requests
import datetime

CHESS_COM_API = "https://api.chess.com/pub/player"
HEADERS = {"User-Agent": "OnyxChessTrainer/1.0 (Educational/Analytical tool)"}

def fetch_chesscom_games(username, months_back=1):
    """
    Fetches PGNs from Chess.com for the last N months.
    Saves compiled matches into data/{username}_archive.pgn.
    """
    if not username:
        return None

    os.makedirs("data", exist_ok=True)
    today = datetime.date.today()
    all_pgn_text = ""
    total_games_found = 0

    print(f"\n📡 Connecting to Chess.com API for '{username}'...")

    for i in range(months_back):
        # Calculate year and month working backwards
        target_month = today.month - i
        target_year = today.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1

        month_str = f"{target_month:02d}"
        year_str = str(target_year)
        
        url = f"{CHESS_COM_API}/{username}/games/{year_str}/{month_str}/pgn"
        print(f" ⏳ Fetching archive: {year_str}-{month_str}...")

        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200 and res.text.strip():
                pgn_chunk = res.text
                games_count = pgn_chunk.count("[Event ")
                total_games_found += games_count
                all_pgn_text += pgn_chunk + "\n\n"
                print(f"    -> Retrieved {games_count} games.")
            elif res.status_code == 404:
                print(f"    -> No games found for {year_str}-{month_str}.")
            else:
                print(f"    -> Archive returned status: {res.status_code}")
        except Exception as e:
            print(f"    ⚠️ Network error fetching {year_str}-{month_str}: {e}")

    if not all_pgn_text.strip():
        print("❌ No game data retrieved.")
        return None

    output_path = f"data/{username}_bulk_archive.pgn"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(all_pgn_text)

    print(f"\n✅ Total games compiled: {total_games_found}")
    print(f"📁 Saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    user = input("Enter Chess.com username: ").strip()
    months = input("How many months back to fetch? (Default 6): ").strip()
    months_count = int(months) if months.isdigit() and int(months) > 0 else 6
    fetch_chesscom_games(user, months_back=months_count)