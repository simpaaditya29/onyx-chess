import chess
import chess.pgn
import chess.engine
import io
import os
import json
import csv
import random
import time
import pandas as pd
from datetime import datetime
import requests
from engine_config import get_engine, get_best_move

class Colors:
    WHITE = '\033[97m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'
# ==========================================
# ⚙️ GLOBAL CONFIGURATION & CORE SETTINGS
# ==========================================
STOCKFISH_PATH = "stockfish"
PUZZLE_CSV_PATH = "puzzles.csv"
PROFILE_PATH = "onyx_profile.json"

def print_startup_banner():
    banner = f"""{Colors.WHITE}
 ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝ 
██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗ 
╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝
      The Ultimate Chess Training Suite{Colors.RESET}
    """
    print(banner)

def get_user_move(board):
    while True:
        move_input = input("Your Move: ").strip()
        if move_input.lower() == 'resign': return 'resign'
        if move_input.lower() == 'sol': return 'sol'
        try:
            # This handles standard algebraic notation automatically
            return board.parse_san(move_input)
        except ValueError:
            print("❌ Invalid notation. Try again (e.g., e4, Nf3): ")

def load_profile():
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, 'r') as f: return json.load(f)
        except Exception: pass
    return {"rating": 1200, "puzzles_solved": 0, "games_played": 0, "avg_accuracy": 0.0, "moves_tracked": 0, "survival_highscore": 0, "engine_time": 0.1}

def save_profile(profile):
    try:
        with open(PROFILE_PATH, 'w') as f: json.dump(profile, f, indent=4)
    except Exception as e:
        print(f"⚠️ Warning saving profile: {e}")

def update_accuracy_stats(profile, game_accuracy, moves_count):
    if moves_count <= 0: return
    current_avg = profile.get("avg_accuracy", 0.0)
    total_moves = profile.get("moves_tracked", 0)
    new_total_moves = total_moves + moves_count
    if new_total_moves > 0:
        new_avg = ((current_avg * total_moves) + (game_accuracy * moves_count)) / new_total_moves
        profile["avg_accuracy"] = round(new_avg, 2)
        profile["moves_tracked"] = new_total_moves
    save_profile(profile)

def analyze_position(engine, board, limit_time=0.1):
    if not engine: return 0
    try:
        info = engine.analyse(board, chess.engine.Limit(time=limit_time))
        score = info["score"].relative
        if score.is_mate(): return 10000 if score.mate() > 0 else -10000
        return score.score(default=0)
    except Exception: return 0

def log_game_data(profile, move_accuracies, game_result, bot_elo, fens_list):
    """Exports match data to a Pandas DataFrame and saves to CSV for ML training."""
    if not move_accuracies: return
    print("\n📦 Packaging move data into Pandas DataFrame...")
    data = {
        "Date": [datetime.now().strftime("%Y-%m-%d %H:%M")] * len(move_accuracies),
        "Bot_ELO": [bot_elo] * len(move_accuracies),
        "Move_Number": list(range(1, len(move_accuracies) + 1)),
        "Accuracy": move_accuracies,
        "Game_Result": [game_result] * len(move_accuracies),
        "Player_Rating": [profile.get("rating", 1200)] * len(move_accuracies),
        "FEN": fens_list
    }
    df = pd.DataFrame(data)
    csv_filename = "onyx_training_data.csv"
    if os.path.exists(csv_filename): df.to_csv(csv_filename, mode='a', header=False, index=False)
    else: df.to_csv(csv_filename, mode='w', header=True, index=False)
    print(f"💾 Dataset successfully exported to {csv_filename}!")

# ==========================================
# 🎨 RESTRUCTURED GRAPHICS & GRAPH VISUALS
# ==========================================
def print_board_clean(board, is_white_perspective=True, blindfold=False):
    if blindfold:
        print("\n   [ BLINDFOLD MODE ACTIVE - VISUALIZE THE BOARD ]\n")
        return
    unicode_pieces = {'R': '♜', 'N': '♞', 'B': '♝', 'Q': '♛', 'K': '♚', 'P': '♟', 'r': '♖', 'n': '♘', 'b': '♗', 'q': '♕', 'k': '♔', 'p': '♙', '.': '·'}
    board_str = board.epd()
    rows = board_str.split(' ')[0].split('/')
    print("\n    a  b  c  d  e  f  g  h" if is_white_perspective else "\n    h  g  f  e  d  c  b  a")
    print("  +-----------------------+")
    ranks = range(8) if not is_white_perspective else range(7, -1, -1)
    for r in ranks:
        row_string = ""
        current_row = rows[7 - r]
        expanded_row = "".join(['.' * int(char) if char.isdigit() else char for char in current_row])
        files = range(7, -1, -1) if not is_white_perspective else range(8)
        for f in files: row_string += f" {unicode_pieces[expanded_row[f]]} "
        print(f"{r+1} |{row_string}| {r+1}")
    print("  +-----------------------+")
    print("    a  b  c  d  e  f  g  h" if is_white_perspective else "\n    h  g  f  e  d  c  b  a\n")

def draw_ascii_graph(move_accuracies):
    if not move_accuracies: return
    print("\n📈 PERFORMANCE ACCURACY CHART")
    print("-" * 45)
    for level in range(5, 0, -1):
        threshold = level * 20
        row_str = f"{threshold:3}% | "
        for acc in move_accuracies:
            if acc >= threshold: row_str += " █ "
            elif acc >= threshold - 10: row_str += " ▄ "
            else: row_str += "   "
        print(row_str)
    print("     +" + "---" * len(move_accuracies))
    print("Move: " + "".join(f"{i+1:3}" for i in range(len(move_accuracies))))
    print("-" * 45)
    # ==========================================
# 🧩 MODULE 1-4: PUZZLES, ANALYSIS & PvP BOTS
# ==========================================




    # ==========================================
# 🏋️ MODULE 5-11: REPERTOIRES, SURVIVAL & MENUS
# ==========================================

    def spar_opening_position(profile):
        engine = get_engine()
        if not engine: return
        
        print("\n--- 🥊 OPENING SPARRING VS STOCKFISH ---")
        try:
            with open("openings.json", "r") as f:
                repertoire = json.load(f)
        except FileNotFoundError:
            print("❌ Error: openings.json not found.")
            engine.quit(); return

        print("1. White Repertoire")
        print("2. Black Repertoire")
        color_choice = input("Select side to play (1/2): ").strip()
        side_key = "White Repertoire" if color_choice == '1' else "Black Repertoire"
        
        if side_key not in repertoire:
            print("❌ Repertoire not found.")
            engine.quit(); return
            
        lines = list(repertoire[side_key]['lines'].keys())
        for idx, name in enumerate(lines, 1):
            print(f"{idx}. {name}")
            
        line_choice = input("\nSelect variation to spar: ").strip()
        if not line_choice.isdigit() or int(line_choice) > len(lines):
            print("❌ Invalid selection.")
            engine.quit(); return
            
        line_name = lines[int(line_choice) - 1]
        moves = repertoire[side_key]['lines'][line_name]['moves']
        
        # Fast-forward the board to the end of the opening line
        board = chess.Board()
        for m in moves:
            board.push_san(m)
            
        print(f"\n🚀 Sparring started: {line_name}")
        user_is_white = (side_key == "White Repertoire")
        
        # Main game loop
        while not board.is_game_over():
            print_board_clean(board, is_white_perspective=user_is_white)
            
            # Engine's turn
            if (board.turn == chess.WHITE and not user_is_white) or (board.turn == chess.BLACK and user_is_white):
                print("Stockfish is thinking...")
                result = engine.play(board, chess.engine.Limit(time=0.5))
                board.push(result.move)
            # Your turn
            else:
                while True:
                    m_str = input("\nYour Move (or 'quit'): ").strip()
                    if m_str.lower() == 'quit': 
                        engine.quit()
                        return
                    try:
                        move = board.parse_san(m_str)
                        board.push(move)
                        break
                    except ValueError:
                        print("❌ Invalid notation.")

        print_board_clean(board)
        print(f"\n🏁 Game Over! Result: {board.result()}")
        input("Press Enter to return...")
        engine.quit()


def fetch_lichess_game(username):

    """Pulls the most recent game PGN for a given Lichess user via cloud API."""
    url = f"https://lichess.org/api/games/user/{username}?max=1"
    print(f"\n📡 Pinging Lichess servers for {username}'s last match...")
    try:
        # We tell Lichess we specifically want the raw PGN format
        response = requests.get(url, headers={"Accept": "application/x-chess-pgn"})
        
        if response.status_code == 200 and response.text.strip():
            print("✅ Game downloaded successfully!")
            return response.text
        else:
            print("❌ User not found or no recent games available.")
            return None
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None
def play_guess_the_move(profile):
    print("\n--- 🧠 GUESS THE MASTER MOVE ---")
    try:
        # Looking for your specific file now!
        with open("training_archive.pgn", "r") as pgn_file:
            game = chess.pgn.read_game(pgn_file)
            if game is None:
                print("❌ No games found in training_archive.pgn.")
                input("\nPress Enter to return...")
                return
            
            board = game.board()
            print(f"Match: {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}")
            
            for move in game.mainline_moves():
                print_board_clean(board, is_white_perspective=True)
                
                while True:
                    user_input = input("Guess the next move (or 'quit'): ").strip()
                    if user_input.lower() == 'quit': 
                        return
                    
                    try:
                        user_move = board.parse_san(user_input)
                        if user_move == move:
                            print("🎯 Brilliant! That is exactly what the master played.")
                            break
                        else:
                            print(f"❌ Not quite. The master played: {board.san(move)}")
                            break
                    except ValueError:
                        print("❌ Invalid notation. Try again (e.g., Nf3).")
                
                board.push(move)
                
            print("\n🏁 Master game completed!")
            
    except FileNotFoundError:
        print("❌ Error: 'training_archive.pgn' file not found in your folder.")
        
    input("\nPress Enter to return to menu...")

def manage_profile_and_settings(profile):
    while True:
        print("\n⚙️ SETTINGS")
        print(f"Rating: {profile.get('rating', 1200)} | Engine Time: {profile.get('engine_time', 0.1)}s")
        c = input("\n1. Change Engine Time\n2. Back\n> ").strip()
        if c == '1':
            try:
                profile['engine_time'] = float(input("Enter seconds: "))
                save_profile(profile)
            except: pass
        else: break

def display_dashboard(profile):
    print("\n--- ♟️ ONYX DAILY SUMMARY ---")
    # Simple Pandas count
    try:
        df = pd.read_csv("onyx_training_data.csv")
        total_games = df['Date'].nunique()
        avg_acc = df['Accuracy'].mean()
        print(f"📈 Total Games Trained: {total_games}")
        print(f"🎯 Lifetime Accuracy: {avg_acc:.1f}%")
    except:
        print("Start your first game to generate stats!")

def analyze_critical_moments(profile, engine): # Add engine here
    print("\n🔍 COACHING: SCANNING FOR CRITICAL BLUNDERS...")
    try:
        df = pd.read_csv("onyx_training_data.csv")
    except FileNotFoundError:
        print("❌ No training data found yet.")
        return
        
    blunders = df[df['Accuracy'] < 40]
    
    if blunders.empty:
        print("✅ No major blunders found. Great accuracy!")
        return

    print(f"⚠️ Found {len(blunders)} critical moments. Let's review!")
    for index, row in blunders.iterrows():
        move_num = row['Move_Number']
        fen = row['FEN']
        best_move = get_best_move(engine, fen)
        
        # Visualize the blunder position
        board = chess.Board(fen)
        print(f"\n--- POSITION AT MOVE {move_num} ---")
        print_board_clean(board) # This prints the board visually
        
        print(f"Accuracy: {row['Accuracy']}%")
        user_attempt = input("Your try to fix the blunder: ").strip()
        
        try:
            move = board.parse_san(user_attempt)
            if move == best_move:
                print("🎯 Perfect! You found the engine's move.")
            else:
                print(f"❌ Almost. The best move was {best_move}.")
        except:
            print(f"Invalid move. The answer was {best_move}.")

def log_training_data(profile, mode, result, accuracy=None):

    """Logs training session results to a CSV file for Pandas analysis."""
    # Ensure the data folder exists
    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", "training_data.csv")
    
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write headers if the file is brand new
        if not file_exists:
            writer.writerow(["Timestamp", "Profile", "Mode", "Result", "Accuracy"])
            
        # Log the current session
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        profile_name = profile.get("name", "Player") if profile else "Player"
        
        writer.writerow([timestamp, profile_name, mode, result, accuracy])

import sys
import time

def get_timed_user_move(prompt="Your Move: ", timeout=10):

    """
    Prompts user for input with a strict countdown timer in seconds.
    Returns (move_str, timed_out_boolean).
    """
    import msvcrt
    
    print(f"{prompt}(⏱️ {timeout}s clock starting now!) ")
    start_time = time.time()
    input_chars = []
    
    while True:
        # Check if time expired
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print("\n\n⏰ TIME'S UP! You flagged under time pressure!")
            return "", True
            
        # Check if key was pressed
        if msvcrt.kbhit():
            char = msvcrt.getwche() # Read character and echo to terminal
            if char in ('\r', '\n'): # Enter key pressed
                print()
                return "".join(input_chars).strip(), False
            elif char == '\b': # Backspace
                if input_chars:
                    input_chars.pop()
                    # Visual backspace handling in terminal
                    sys.stdout.write(' \b')
                    sys.stdout.flush()
            else:
                input_chars.append(char)
                
        time.sleep(0.05) # Prevent high CPU usage loop     

def print_board_clean(board):
    """Prints ASCII board in terminal and conditionally launches GUI window."""
    # Standard terminal ASCII print
    print("\n" + str(board) + "\n")
    
    # Optional GUI board popup
    try:
        from gui import pop_gui_board
        # Opens a visual window frame alongside the terminal output
        pop_gui_board(board)
    except Exception:
        pass

def get_user_move_gui(board, prompt="Your Move: "):
    """Gets move either from mouse click on GUI or typed input in terminal."""
    try:
        from gui import ChessBoardGUI
        gui = ChessBoardGUI(board, title="Onyx Interactive Board")
        
        print(f"{prompt}(Click pieces on the GUI or type move here): ", end="", flush=True)
        
        # Keep GUI updated while waiting for click or keyboard
        move_san = gui.get_mouse_move()
        gui.close()
        return move_san
    except Exception as e:
        # Fallback to standard terminal input if GUI fails
        return input(prompt).strip()    

import json
import os

SETTINGS_PATH = "settings.json"

DEFAULT_SETTINGS = {
    "theme": "classic",  # Options: 'classic', 'wood', 'green', 'blue'
    "sound_enabled": True,
    "default_time_control": "180"  # 3 min default
}

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_SETTINGS

def save_settings(settings):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=4)    



# --- FEATURE 2: Visual ASCII Evaluation Bar ---
def render_eval_bar(eval_score: float, bar_length: int = 10) -> str:
    """
    Converts a numerical eval score (e.g. +1.5 or -2.0) into a visual bar.
    """
    # Clamp score between -5.0 and +5.0 for visual balance
    clamped_score = max(-5.0, min(5.0, eval_score))
    
    # Calculate filled percentage (0.0 to 1.0)
    percentage = (clamped_score + 5.0) / 10.0
    filled_length = int(round(bar_length * percentage))
    
    bar = "█" * filled_length + "░" * (bar_length - filled_length)
    sign = "+" if eval_score > 0 else ""
    
    return f"[{bar}] {sign}{eval_score:.1f}"


# --- FEATURE 3: Quick Session Win / Streak Tracker ---
class SessionTracker:
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.streak = 0

    def record_result(self, won: bool):
        if won:
            self.wins += 1
            self.streak += 1
        else:
            self.losses += 1
            self.streak = 0

    def display_stats(self):
        return f"🏆 Session: {self.wins}W - {self.losses}L | 🔥 Streak: {self.streak}"        


# --- (All your existing functions in utils.py stay here) ---


# --- PREMIUM BOARD ---
def print_premium_board(board):
    """
    Prints a premium chess board with coordinates, unicode pieces, 
    and a side-by-side dynamic move history panel.
    """
    # 1. Reconstruct the algebraic move history
    moves = []
    temp_board = chess.Board()
    for move in board.move_stack:
        moves.append(temp_board.san(move))
        temp_board.push(move)
        
    # Group moves into White/Black pairs (e.g., "1. e4 e5")
    move_pairs = []
    for i in range(0, len(moves), 2):
        white_move = moves[i]
        black_move = moves[i+1] if i+1 < len(moves) else ""
        move_pairs.append(f"{i//2 + 1}. {white_move:<7} {black_move}")
        
    # Grab the latest 8 rows of history so it perfectly matches the board height
    display_moves = move_pairs[-8:] if len(move_pairs) > 8 else move_pairs
    
    # Pad with empty strings if the game is less than 8 moves long
    while len(display_moves) < 8:
        display_moves.append("") 

    # 2. Map standard text characters to premium Unicode chess pieces
    unicode_pieces = {
        'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
        'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚',
        '.': '·'  # Replaces empty squares with a cleaner center dot
    }

    print("\n")
    board_str = str(board).split('\n')
    
    # 3. Print the Split-Screen Interface
    print("      BOARD                   MOVE HISTORY")
    print("  +-----------------+      -------------------")
    
    for i, row in enumerate(board_str):
        rank = 8 - i
        colored_row = " ".join([unicode_pieces.get(c, c) for c in row.split()])
        move_text = display_moves[i]
        
        print(f"{rank} | {colored_row} |      {move_text}")
        
    print("  +-----------------+")
    print("    a b c d e f g h\n")    


def save_blunder_to_deck(fen, user_move, best_move, cp_loss):
    """Saves a blundered position to the FSRS spaced-repetition deck."""
    import json
    import os
    from fsrs import Card
    
    deck_file = "mistake_deck.json"
    mistakes = []
    
    if os.path.exists(deck_file):
        try:
            with open(deck_file, "r") as f:
                mistakes = json.load(f)
        except Exception:
            pass
            
    # Avoid duplicate FENs
    for mistake in mistakes:
        if mistake['fen'] == fen:
            return
            
    # Create a new FSRS card instance
    new_card = Card()
    
    mistakes.append({
        "fen": fen,
        "played": user_move,
        "best": best_move,
        "loss": cp_loss,
        "fsrs_card_data": new_card.to_dict()  # Serialize FSRS card for JSON
    })
    
    with open(deck_file, "w") as f:
        json.dump(mistakes, f, indent=4)