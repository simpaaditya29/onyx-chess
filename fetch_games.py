import requests
import datetime
import os

def fetch_chesscom_games(username, year=None, month=None):
    if not year or not month:
        now = datetime.datetime.now()
        year, month = now.year, now.month

    # Format month to be two digits (e.g., '09' for September)
    month_str = str(month).zfill(2)
    url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month_str}/pgn"
    
    headers = {
        "User-Agent": "OnyxChessTrainer/1.0 (aaditya.gusai@example.com)" # Chess.com requires a User-Agent
    }
    
    print(f"📡 Fetching games for {username} from {year}-{month_str}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        pgn_data = response.text
        if not pgn_data.strip():
            print("No games found for this month.")
            return None
            
        os.makedirs("data", exist_ok=True)
        file_path = f"data/{username}_{year}_{month_str}.pgn"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pgn_data)
            
        print(f"✅ Successfully downloaded {len(pgn_data.split('[Event '))} games to {file_path}")
        return file_path
    else:
        print(f"❌ Failed to fetch games. Status code: {response.status_code}")
        return None

if __name__ == "__main__":
    user = input("Enter Chess.com username: ").strip()
    fetch_chesscom_games(user)