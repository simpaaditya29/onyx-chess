import os
import sys
import io
import datetime
import chess
import chess.pgn
import chess.engine
import pandas as pd
from dataclasses import dataclass, asdict

STOCKFISH_PATH = "./assets/engine/stockfish.exe"
PUZZLE_DB = "data/blunder_bank.csv"

@dataclass
class BlunderPuzzle:
    fen_before: str
    turn: str
    played_move: str
    best_move: str
    cp_loss: int
    timestamp: datetime.datetime
    complexity_depth: int = 0

def extract_blunder_puzzles(pgn_source, centipawn_threshold=150):
    """Analyzes a game and returns a list of blunder puzzles."""
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    puzzles = []

    # Detect whether pgn_source is a file path or raw PGN text
    if os.path.exists(pgn_source):
        with open(pgn_source, "r", encoding="utf-8") as f:
            game = chess.pgn.read_game(f)
    else:
        pgn_io = io.StringIO(pgn_source)
        game = chess.pgn.read_game(pgn_io)

    if game is None:
        print("Error: Could not parse any valid chess game from the input.")
        engine.quit()
        return puzzles

    board = game.board()
    prev_eval = engine.analyse(board, chess.engine.Limit(time=0.1))["score"].white().score(mate_score=10000)

    move_number = 1
    for move in game.mainline_moves():
        is_white_turn = board.turn
        fen_before = board.fen()

        # Determine engine's best move before the move was played
        best_move = engine.play(board, chess.engine.Limit(time=0.1)).move.uci()

        # Push actual played move
        board.push(move)
        
        info = engine.analyse(board, chess.engine.Limit(time=0.1))
        current_eval = info["score"].white().score(mate_score=10000)
        eval_shift = current_eval - prev_eval
        complexity_depth = info.get("depth", 0)

        # Check for significant blunders (> threshold drop)
        is_blunder = False
        cp_loss = 0
        if is_white_turn and eval_shift < -centipawn_threshold:
            is_blunder = True
            cp_loss = abs(eval_shift)
        elif not is_white_turn and eval_shift > centipawn_threshold:
            is_blunder = True
            cp_loss = abs(eval_shift)

        if is_blunder:
            puzzles.append(BlunderPuzzle(
                fen_before=fen_before,
                turn="White" if is_white_turn else "Black",
                played_move=move.uci(),
                best_move=best_move,
                cp_loss=cp_loss,
                timestamp=datetime.datetime.now(),
                complexity_depth=complexity_depth
            ))

        prev_eval = current_eval
        if not is_white_turn:
            move_number += 1

    engine.quit()
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
    
    if os.path.exists(PUZZLE_DB):
        df_existing = pd.read_csv(PUZZLE_DB)
        if "box_level" not in df_existing.columns:
            df_existing["box_level"] = 1
            df_existing["next_review_date"] = datetime.date.today().isoformat()
        if "tags" not in df_existing.columns:
            df_existing["tags"] = "Untagged"
        if "complexity_depth" not in df_existing.columns:
            df_existing["complexity_depth"] = 0
            
        df_combined = pd.concat([df_existing, df_new]).drop_duplicates(subset=["fen_before"], keep="first")
        df_combined.to_csv(PUZZLE_DB, index=False)
    else:
        df_new.to_csv(PUZZLE_DB, index=False)

if __name__ == "__main__":
    print("=" * 50)
    print(" Onyx Chess Mistake Parser")
    print("=" * 50)
    print("Choose input method:")
    print(" [1] Paste raw PGN text directly")
    print(" [2] Enter path to a .pgn file")
    
    choice = input("\nSelect (1 or 2): ").strip()
    
    pgn_data = ""
    if choice == "1":
        print("\nPaste your PGN below. When finished, press Enter, then Ctrl+Z (Windows) or Ctrl+D (Mac/Linux):")
        pgn_data = sys.stdin.read().strip()
    elif choice == "2":
        pgn_data = input("\nEnter file name/path (e.g. my_game.pgn): ").strip()
    else:
        print("Invalid choice. Exiting.")
        sys.exit()
        
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