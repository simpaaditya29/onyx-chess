import os
import sys
import io
import datetime
import chess
import chess.pgn
import chess.engine
import chess.polyglot
import pandas as pd
from dataclasses import dataclass, asdict

STOCKFISH_PATH = "./assets/engine/stockfish.exe"
PUZZLE_DB = "data/blunder_bank.csv"
POLYGLOT_PATH = "assets/books/repertoire.bin" # Optional polyglot book for deep repertoire checking

@dataclass
class BlunderPuzzle:
    fen_before: str
    turn: str
    played_move: str
    best_move: str
    cp_loss: int
    timestamp: datetime.datetime
    complexity_depth: int = 0
    eco: str = "???"
    opening_name: str = "Unknown"
    is_opening_trap: bool = False

def extract_blunder_puzzles(pgn_source, centipawn_threshold=150):
    """Analyzes games with incremental auto-saving and CPU thermal pacing."""
    import time
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    puzzles = []

    polyglot_reader = None
    if os.path.exists(POLYGLOT_PATH):
        polyglot_reader = chess.polyglot.open_reader(POLYGLOT_PATH)

    if os.path.exists(pgn_source):
        pgn_stream = open(pgn_source, "r", encoding="utf-8")
    else:
        import io
        pgn_stream = io.StringIO(pgn_source)

    game_idx = 0
    try:
        while True:
            game = chess.pgn.read_game(pgn_stream)
            if game is None:
                break

            game_idx += 1
            print(f"♟️ Parsing Game #{game_idx} | Total Blunders Saved: {len(puzzles)}", end="\r")

            eco = game.headers.get("ECO", "???")
            opening = game.headers.get("Opening", "Unknown Opening")
            board = game.board()
            
            try:
                prev_eval = engine.analyse(board, chess.engine.Limit(time=0.05))["score"].white().score(mate_score=10000)
            except Exception:
                prev_eval = 0

            move_number = 1
            game_blunders = [] 

            for move in game.mainline_moves():
                is_white_turn = board.turn
                fen_before = board.fen()

                in_book = False
                if polyglot_reader:
                    in_book = not (polyglot_reader.get(board) is None)

                try:
                    best_move = engine.play(board, chess.engine.Limit(time=0.05)).move.uci()
                except Exception:
                    best_move = move.uci()

                board.push(move)

                try:
                    info = engine.analyse(board, chess.engine.Limit(time=0.05))
                    current_eval = info["score"].white().score(mate_score=10000)
                    complexity_depth = info.get("depth", 0)
                except Exception:
                    current_eval = prev_eval
                    complexity_depth = 0

                eval_shift = current_eval - prev_eval
                is_blunder = False
                cp_loss = 0
                
                if is_white_turn and eval_shift < -centipawn_threshold:
                    is_blunder = True
                    cp_loss = abs(eval_shift)
                elif not is_white_turn and eval_shift > centipawn_threshold:
                    is_blunder = True
                    cp_loss = abs(eval_shift)

                if is_blunder:
                    is_trap = (move_number <= 10) or in_book
                    puzzle = BlunderPuzzle(
                        fen_before=fen_before,
                        turn="White" if is_white_turn else "Black",
                        played_move=move.uci(),
                        best_move=best_move,
                        cp_loss=cp_loss,
                        timestamp=datetime.datetime.now(),
                        complexity_depth=complexity_depth,
                        eco=eco,
                        opening_name=opening,
                        is_opening_trap=is_trap
                    )
                    puzzles.append(puzzle)
                    game_blunders.append(puzzle)

                prev_eval = current_eval
                if not is_white_turn:
                    move_number += 1
                
                # Thermal pacing: give CPU 10ms idle time to prevent overheating
                time.sleep(0.01) 
            
            # --- INCREMENTAL AUTO-SAVE ---
            # Flushes data to disk immediately after each game
            if game_blunders:
                save_puzzles_to_bank(game_blunders)

    except KeyboardInterrupt:
        print("\n\n🛑 Manual stop detected! Safely exiting...")

    finally:
        if os.path.exists(pgn_source):
            pgn_stream.close()
        if polyglot_reader:
            polyglot_reader.close()
        engine.quit()

    print(f"\n✅ Finished parsing {game_idx} games.")
    return puzzles

def save_puzzles_to_bank(puzzles):
    if not puzzles:
        print("No blunders found to save.")
        return

    os.makedirs("data", exist_ok=True)
    new_data = [asdict(p) for p in puzzles]
    df_new = pd.DataFrame(new_data)
    
    df_new["solved"] = False
    df_new["attempts"] = 0
    df_new["box_level"] = 1
    df_new["next_review_date"] = datetime.date.today().isoformat()
    
    # Automated Tactical Tagging
    tags_list = []
    for idx, row in df_new.iterrows():
        board = chess.Board(row['fen_before'])
        move = chess.Move.from_uci(row['best_move'])
        
        tags = []
        
        # Inject the ECO code directly into the spaced repetition tags
        if row.get('is_opening_trap'):
            tags.append("Opening Trap")
            eco_val = str(row.get('eco', ''))
            if eco_val and eco_val != "???":
                tags.append(eco_val)
        
        if len(board.piece_map()) <= 12: 
            tags.append("Endgame")
        elif len(board.piece_map()) >= 24: 
            tags.append("Middlegame")
            
        if board.is_capture(move): 
            tags.append("Missed Capture")
            
        board.push(move)
        if board.is_checkmate(): 
            tags.append("Missed Mate")
        elif board.is_check(): 
            tags.append("Missed Check")
            
        if move.promotion: 
            tags.append("Promotion")
            
        tags_list.append(", ".join(tags) if tags else "Positional / Defensive")
    
    df_new["tags"] = tags_list
    
    if 'is_opening_trap' in df_new.columns:
        df_new = df_new.drop(columns=['is_opening_trap'])
    
    if os.path.exists(PUZZLE_DB):
        df_existing = pd.read_csv(PUZZLE_DB)
        if "box_level" not in df_existing.columns:
            df_existing["box_level"] = 1
            df_existing["next_review_date"] = datetime.date.today().isoformat()
        if "tags" not in df_existing.columns:
            df_existing["tags"] = "Untagged"
        if "complexity_depth" not in df_existing.columns:
            df_existing["complexity_depth"] = 0
        if "eco" not in df_existing.columns:
            df_existing["eco"] = "???"
        if "opening_name" not in df_existing.columns:
            df_existing["opening_name"] = "Unknown"
            
        df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=["fen_before"], keep="first")
        df_combined.to_csv(PUZZLE_DB, index=False)
    else:
        df_new.to_csv(PUZZLE_DB, index=False)

if __name__ == "__main__":
    pgn_data = ""

    # 1. Check if main.py automatically passed a file via the command line
    if len(sys.argv) > 1:
        pgn_data = sys.argv[1]
        print(f"\n🚀 Pipeline Triggered: Auto-parsing {pgn_data}...")
        
    # 2. Otherwise, show the manual menu if the user ran mistake_parser.py directly
    else:
        print("=" * 50)
        print(" Onyx Chess Mistake Parser (Polyglot Enabled)")
        print("=" * 50)
        print("Choose input method:")
        print(" [1] Paste raw PGN text directly")
        print(" [2] Enter path to a .pgn file")

        choice = input("\nSelect (1 or 2): ").strip()

        if choice == "1":
            print("\nPaste your PGN below. When finished, press Enter, then Ctrl+Z (Windows) or Ctrl+D (Unix):")
            pgn_data = sys.stdin.read().strip()
        elif choice == "2":
            pgn_data = input("\nEnter file name/path (e.g. my_game.pgn): ").strip()
        else:
            print("Invalid choice. Exiting.")
            sys.exit()

    # 3. Proceed with extracting the blunders regardless of how the file was provided
    if not pgn_data:
        print("No input provided.")
        sys.exit()

    print("\nAnalyzing game for mistakes with Stockfish...")
    puzzles = extract_blunder_puzzles(pgn_data)

    if puzzles:
        print(f"Found {len(puzzles)} blunder(s)!")
        save_puzzles_to_bank(puzzles)
        print(f"Saved successfully to {PUZZLE_DB}")
    else:
        print("No blunders found above the threshold in this game.")