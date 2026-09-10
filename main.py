import sys
import random
import chess
import time
import chess.polyglot  

# Import your game and training modes
from game_modes import (
    play_full_game,
    play_pass_n_play,
    play_timed_mode,
    play_opening_interrogator, 
    play_human_sparring_bot,       # <--- Added this back!
    play_game_with_blunder_coach,
    puzzle_dashboard
)

from training_modes import (
    play_guess_the_move,
    review_mistake_deck,
    play_blunder_tactics_challenge
)

from theory_library import launch_theory_library

# Import your data analytics
from analytics import (
    load_profile,
    deep_pgn_analysis,
    analyze_player_accuracy,
    visualize_acpl_trend,
    analyze_blunder_triggers,
    visualize_opening_winrates,
    plot_time_vs_accuracy,
    check_lichess_master_alignment
)
from transposition import TranspositionTable, EXACT, LOWERBOUND, UPPERBOUND

# Instantiate global or engine-level table
tt = TranspositionTable(size_in_mb=64)

# Import your utilities and settings
from utils import load_settings, save_settings, print_startup_banner

# --- GM Quote / Chess Tip Generator ---
CHESS_QUOTES = [
    "\"When you see a good move, look for a better one.\" – Emanuel Lasker",
    "\"Tactics is knowing what to do when there is something to do.\" – Savielly Tartakower",
    "\"Play the opening like a book, the middlegame like a magician, and the endgame like a machine.\" – Rudolf Spielmann",
    "\"Always check checks, captures, and threats first!\"",
    "\"Control the center, activate your pieces, keep your king safe.\""
]

import json
import random

# Load the custom training repertoire into memory
TRAINING_REPERTOIRE = None
try:
    with open("openings.json", "r", encoding="utf-8") as f:
        TRAINING_REPERTOIRE = json.load(f)
        print(f"✅ Loaded {len(TRAINING_REPERTOIRE.get('categories', []))} training categories.")
except FileNotFoundError:
    print("⚠️ No openings.json found. Training mode disabled.")

def get_training_move(board, active_category):
    """Looks up the current board FEN in the training repertoire."""
    if not TRAINING_REPERTOIRE or not active_category:
        return None
        
    fen = board.fen()
    moves_data = TRAINING_REPERTOIRE.get("fen_lookup", {}).get(fen, [])
    
    # Filter available moves to only match the active training category
    valid_moves = [entry["move"] for entry in moves_data if entry["category"] == active_category]
    
    if valid_moves:
        # If there are multiple valid sidelines, pick one randomly to mix up the sparring
        chosen_move = random.choice(valid_moves)
        return chess.Move.from_uci(chosen_move)
        
    return None

def get_random_tip():
    return random.choice(CHESS_QUOTES)

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

# Move Ordering Heuristics
MAX_DEPTH = 64
killer_moves = [[None, None] for _ in range(MAX_DEPTH)]
history_table = {}  # Map (from_sq, to_sq) -> integer score

# Positional bonuses (Piece-Square Tables)
PAWN_PST = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_PST = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

BISHOP_PST = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

ROOK_PST = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_PST = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_MIDDLEGAME_PST = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

KING_ENDGAME_PST = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

# Map piece types to their tables
PST_MAP = {
    chess.PAWN: PAWN_PST,
    chess.KNIGHT: KNIGHT_PST,
    chess.BISHOP: BISHOP_PST,
    chess.ROOK: ROOK_PST,
    chess.QUEEN: QUEEN_PST,
    chess.KING: KING_MIDDLEGAME_PST
}

def evaluate(board):
    score = 0
    
    # 1. Determine if we are in the endgame (Phase Calculation)
    # We will define the endgame as having less than 1500 total material (excluding pawns/kings)
    total_material = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type not in [chess.PAWN, chess.KING]:
            total_material += PIECE_VALUES.get(piece.piece_type, 0)
            
    is_endgame = total_material < 1500

    # 2. Evaluate the board
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            # Base Material Value
            material_val = PIECE_VALUES.get(piece.piece_type, 0)
            
            # Positional Value 
            positional_val = 0
            
            # Handle the King's dynamic endgame shift
            if piece.piece_type == chess.KING:
                table = KING_ENDGAME_PST if is_endgame else KING_MIDDLEGAME_PST
            else:
                table = PST_MAP.get(piece.piece_type)

            if table:
                sq_index = square if piece.color == chess.WHITE else chess.square_mirror(square)
                visual_sq_index = sq_index ^ 56
                positional_val = table[visual_sq_index]
            
            # Add or subtract from total
            if piece.color == chess.WHITE:
                score += (material_val + positional_val)
            else:
                score -= (material_val + positional_val)
                
    return score

def order_moves(board, depth=0):
    """Sorts legal moves: Captures (MVV-LVA) -> Killer Moves -> History Heuristic -> Quiet Moves."""
    def move_score(move):
        # 1. Captures get top priority via MVV-LVA
        if board.is_capture(move):
            if board.is_en_passant(move):
                return 105
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                return 10000 + (PIECE_VALUES.get(victim.piece_type, 0) * 10) - PIECE_VALUES.get(attacker.piece_type, 0)
            return 10000

        # 2. Killer Moves (Quiet moves that caused cutoffs at this depth)
        if depth < MAX_DEPTH:
            if move == killer_moves[depth][0]:
                return 9000
            elif move == killer_moves[depth][1]:
                return 8000

        # 3. History Heuristic (Quiet moves with a proven track record)
        move_key = (move.from_square, move.to_square)
        return history_table.get(move_key, 0)

    return sorted(list(board.legal_moves), key=move_score, reverse=True)

def quiescence_search(board, alpha, beta, maximizing_player):
    """Evaluates quiet positions to prevent the Horizon Effect."""
    # 1. Calculate the 'Stand Pat' score (evaluating the board as-is)
    stand_pat = evaluate(board)

    # 2. Base Case Cutoffs (Pruning based on stand pat)
    if maximizing_player:
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
    else:
        if stand_pat <= alpha:
            return alpha
        beta = min(beta, stand_pat)

    # 3. Generate ONLY captures and sort them with our MVV-LVA logic
    captures = [move for move in order_moves(board, 0) if board.is_capture(move)]

    # 4. Search the capture branches
    for move in captures:
        board.push(move)
        score = quiescence_search(board, alpha, beta, not maximizing_player)
        board.pop()

        if maximizing_player:
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        else:
            beta = min(beta, score)
            if beta <= alpha:
                break

    return alpha if maximizing_player else beta


def alpha_beta(board, depth, alpha, beta, maximizing_player):
    # ------------------------------------------------------------------
    # 1. TRANSPOSITION TABLE LOOKUP
    # ------------------------------------------------------------------
    tt_score, tt_move = tt.lookup(board, depth, alpha, beta)
    if tt_score is not None:
        return tt_score, tt_move  # Instant return from memory!

    # Standard base case checks
    if board.is_game_over():
        return evaluate(board), None

    if depth == 0:
        q_score = quiescence_search(board, alpha, beta, maximizing_player)
        return q_score, None

    # ------------------------------------------------------------------
    # 2. NULL MOVE PRUNING (NMP)
    # ------------------------------------------------------------------
    # Skip turn to check if position is already winning.
    # Avoid zugzwang: Only run if not in check, depth >= 3, and pieces exist.
    R = 2  # Reduction factor
    if depth >= 1 + R and not board.is_check():
        if len(board.piece_map()) > 6:
            board.push(chess.Move.null())
            null_score, _ = alpha_beta(board, depth - 1 - R, alpha, beta, not maximizing_player)
            board.pop()

            if maximizing_player:
                if null_score >= beta:
                    return beta, None
            else:
                if null_score <= alpha:
                    return alpha, None

    original_alpha = alpha
    best_move = None

    if maximizing_player:
        max_eval = -float('inf')
        for move in order_moves(board, depth):
            board.push(move)
            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, False)
            board.pop()

            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move

            alpha = max(alpha, eval_score)
            if beta <= alpha:
                # Store Killer Move & Update History for Quiet Moves
                if not board.is_capture(move):
                    if depth < MAX_DEPTH:
                        if killer_moves[depth][0] != move:
                            killer_moves[depth][1] = killer_moves[depth][0]
                            killer_moves[depth][0] = move
                    
                    move_key = (move.from_square, move.to_square)
                    history_table[move_key] = history_table.get(move_key, 0) + (depth * depth)
                break  # Beta Cutoff

            
        # ---------------------------------------------------------
        # 2. DETERMINE FLAG & STORE IN TRANSPOSITION TABLE
        # ---------------------------------------------------------
        if max_eval <= original_alpha:
            flag = UPPERBOUND
        elif max_eval >= beta:
            flag = LOWERBOUND
        else:
            flag = EXACT

        tt.store(board, depth, max_eval, flag, best_move)
        return max_eval, best_move

    else:
        min_eval = float('inf')
        for move in order_moves(board, depth):
            board.push(move)
            eval_score, _ = alpha_beta(board, depth - 1, alpha, beta, True)
            board.pop()

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move

            beta = min(beta, eval_score)
            if beta <= alpha:
                if not board.is_capture(move):
                    # Store Killer Move & Update History for Quiet Moves
                    if depth < MAX_DEPTH:
                        if killer_moves[depth][0] != move:
                            killer_moves[depth][1] = killer_moves[depth][0]
                            killer_moves[depth][0] = move
                    
                    move_key = (move.from_square, move.to_square)
                    history_table[move_key] = history_table.get(move_key, 0) + (depth * depth)

        if min_eval <= original_alpha:
            flag = UPPERBOUND
        elif min_eval >= beta:
            flag = LOWERBOUND
        else:
            flag = EXACT

        tt.store(board, depth, min_eval, flag, best_move)
        return min_eval, best_move

def open_settings_menu():
    settings = load_settings()

    while True:
        print("\n--- ⚙️ ONYX SETTINGS ---")
        print(f"1. Board Theme: [Currently '{settings.get('theme', 'classic')}']")
        print(f"2. Audio FX: [Currently '{'ON' if settings.get('sound_enabled', True) else 'OFF'}']")
        print("3. Back to Main Menu")

        choice = input("\nSelect option (1-3): ").strip()

        if choice == '1':
            print("\nChoose Board Theme:")
            print("1. Classic (Gray/White)")
            print("2. Wood (Brown/Warm)")
            print("3. Forest Green")
            print("4. Ocean Blue")

            theme_choice = input("Select theme (1-4): ").strip()
            themes = {"1": "classic", "2": "wood", "3": "green", "4": "blue"}
            settings["theme"] = themes.get(theme_choice, "classic")
            save_settings(settings)
            print(f"✅ Board theme updated to '{settings['theme']}'!")

        elif choice == '2':
            settings["sound_enabled"] = not settings.get("sound_enabled", True)
            save_settings(settings)
            status = "enabled" if settings["sound_enabled"] else "disabled"
            print(f"🔊 Audio FX {status}!")

        elif choice == '3':
            break


# ==========================================
# 👤 THE NEW PLAYER PROFILE DASHBOARD
# ==========================================

def show_player_profile_dashboard(profile):
    """
    Central hub showing full player statistics and access to advanced training tools.
    """
    import json # Needed to save the profile to your file
    
    while True:
        print("\n" + "="*50)
        print(f"📊 {profile.get('username', 'Player').upper()}'s PLAYER STATISTICS HUB")
        print("="*50)
        print(f"Current Target Rating: {profile.get('rating', 'Unrated')}")
        print("-" * 50)
        print("1. 📈 View Win Rate Chart & Analytics (Opening Winrates)")
        print("2. ⏱️ View Time vs. Accuracy Breakdown")
        print("3. ❌ Access Mistake Deck")
        print("4. 🧠 Access Blunder Model Triggers")
        print("5. 🎯 Launch Tactics Mode")
        print("6. 📊 Deep Player Accuracy Analytics")
        print("7. 📉 Visualize ACPL Trend (Data Chart)")
        print("8. ✏️ Edit Username & Target Rating")
        print("9. 🚪 Return to Main Menu")

        choice = input("\nSelect an option (1-9): ").strip()

        if choice == "1":
            visualize_opening_winrates()
        elif choice == "2":
            plot_time_vs_accuracy()
        elif choice == "3":
            review_mistake_deck(profile)
        elif choice == "4":
            analyze_blunder_triggers()
        elif choice == "5":
            play_blunder_tactics_challenge(profile)
        elif choice == "6":
            analyze_player_accuracy(profile)
        elif choice == "7":
            visualize_acpl_trend()
        elif choice == "8":
            # --- NEW EDIT PROFILE LOGIC ---
            new_name = input("\nEnter your new username: ").strip()
            if new_name:
                profile["username"] = new_name
                
            new_rating = input("Enter your target rating (e.g., 1500): ").strip()
            if new_rating:
                profile["rating"] = new_rating
            
            # Save it to the JSON file so it remembers you next time!
            try:
                with open("onyx_profile.json", "w") as f:
                    json.dump(profile, f, indent=4)
                print("\n✅ Profile successfully updated and saved!")
            except Exception as e:
                print(f"\n❌ Could not save profile: {e}")
                
        elif choice == "9":
            break
        else:
            print("❌ Invalid option. Try again.")


def get_best_move_time_limited(board, time_limit, active_category=None):
    # 0. Check Custom Training Repertoire First (Sparring Mode)
    if active_category:
        training_move = get_training_move(board, active_category)
        if training_move:
            print(f"🎯 Training Mode: Playing mapped move {board.san(training_move)} from '{active_category}'")
            return training_move

    # 1. Check General Opening Book (Competitive Mode)
    try:
        with chess.polyglot.open_reader("OnyxBook.bin") as reader:
            entry = reader.weighted_choice(board)
            print(f"📖 Opening Book move played: {board.san(entry.move)}")
            return entry.move
    except (FileNotFoundError, IndexError):
        # File doesn't exist yet or position isn't in book -> search normally
        pass

    # 2. Iterative Deepening Search Loop
    start_time = time.time()
    best_move_overall = None

    maximizing_player = (board.turn == chess.WHITE)

    # Search up to theoretical max depth of 99
    for depth in range(1, 100):
        # Check if time limit exceeded before starting new depth
        elapsed_time = time.time() - start_time
        if elapsed_time >= time_limit:
            print(f"🛑 Time limit reached! Stopping at depth {depth-1}.")
            break

        # Run Alpha-Beta search for current depth
        score, current_best_move = alpha_beta(board, depth, -float('inf'), float('inf'), maximizing_player)

        # Save best move found at this completed depth
        if current_best_move:
            best_move_overall = current_best_move
            print(f"Depth {depth} complete | Eval: {score} | Best Move: {best_move_overall}")

        # Early exit on forced checkmate
        if score >= 19000 or score <= -19000:
            print(f"🏆 Forced mate found at depth {depth}!")
            break

    return best_move_overall


# ==========================================
# 🎮 THE CLEANED UP MAIN MENU 
# ==========================================
def main_menu():
    profile = load_profile()
    print_startup_banner()

    while True:
        print("\n" + "="*50)
        print(f"💡 {get_random_tip()}\n")
        print("♟️  ONYX CHESS ENGINE v6.0 (PRO EDITION) ♟️")
        print("="*50)
        username = profile.get("username", "Player")
        print(f"👋 Welcome back, {username}!")
        print("1. Puzzle Dashboard | 2. PGN Analysis   | 3. Play vs Bot")
        print("4. Pass 'N Play    | 5. Blindfold      | 6. Guess Move")
        print("7. Timed Mode     | 8. 🎓 Opening Coach| 9. 📚 Theory Library")
        print("10. Sparring Bot  | 11. Blunder Coach | 12. Player Dashboard")
        print("13. Settings      | 14. Lichess Explor| 15. Exit")
        
        choice = input("\nSelect path: ").strip()

        # Smart PGN Auto-Detector if raw moves are pasted into main menu
        if len(choice) > 5 and (" " in choice or "1." in choice):
            print("\n📝 Detected pasted PGN moves! Opening PGN Analysis...")
            deep_pgn_analysis(profile, direct_pgn=choice)
            continue

        try:
            if choice == '1':
                puzzle_dashboard(profile)
            elif choice == '2':
                deep_pgn_analysis(profile)
            elif choice == '3':
                play_full_game(profile, False)
            elif choice == '4':
                play_pass_n_play(profile)
            elif choice == '5':
                play_full_game(profile, True)
            elif choice == '6':
                play_guess_the_move(profile)
            elif choice == '7':
                play_timed_mode(profile)
            elif choice == '8':
                play_opening_interrogator(profile)  # <--- NOW LAUNCHES INTERROGATOR
            elif choice == '9':
                launch_theory_library(profile)
            elif choice == '10':
                print("\n--- 🎯 SPARRING MODE ---")
                if not TRAINING_REPERTOIRE or not TRAINING_REPERTOIRE.get("categories"):
                    print("⚠️ No training categories found in openings.json!")
                    print("Starting standard sparring bot...")
                    play_human_sparring_bot(profile, active_category=None)
                else:
                    categories = TRAINING_REPERTOIRE["categories"]
                    print("Available Opening Lines:")
                    for i, category in enumerate(categories):
                        print(f"[{i+1}] {category}")
                    
                    try:
                        cat_choice = int(input("\nSelect a training line by number: ")) - 1
                        if 0 <= cat_choice < len(categories):
                            active_category = categories[cat_choice]
                            print(f"\n✅ You selected: {active_category}")
                            
                            # Start the game with the selected category
                            play_human_sparring_bot(profile, active_category=active_category)
                            
                        else:
                            print("❌ Invalid selection. Returning to menu.")
                    except ValueError:
                        print("❌ Please enter a valid number. Returning to menu.")
            elif choice == '11':
                play_game_with_blunder_coach(profile)
            elif choice == '12':
                show_player_profile_dashboard(profile)
            elif choice == '13':
                open_settings_menu()
            elif choice == '14':
                fen_input = input("\nEnter FEN position (Press Enter for start board): ").strip()
                if not fen_input:
                    fen_input = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                check_lichess_master_alignment(fen_input)
            elif choice == '15':
                print("\n👋 Thanks for training! See you next time.")
                break
            else:
                print("❌ Invalid choice. Please try again.")

        except Exception as e:
            print("\n" + "!"*50)
            print(f"⚠️ APPLICATION ERROR CAUGHT: {e}")
            print("⚠️ Returning safely to the main menu...")
            print("!"*50 + "\n")

# ==========================================
# 🚀 APP EXECUTION 
# ==========================================
if __name__ == "__main__":
    main_menu()