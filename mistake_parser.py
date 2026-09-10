import chess
import chess.engine
import chess.pgn
import io
import os
import sys
import pandas as pd
from dataclasses import dataclass, asdict

STOCKFISH_PATH = "./assets/engine/stockfish.exe"
PUZZLE_DB = "data/blunder_bank.csv"

@dataclass
class BlunderPuzzle:
    fen_before: str
    blundered_move: str
    best_move: str
    turn: str
    cp_loss: int
    move_number: int

def extract_blunder_puzzles(pgn_source, centipawn_threshold=150):
    """
    Analyzes a game and returns a list of blunder puzzles.
    pgn_source can be either raw PGN text or a file path.
    """
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
        
        current_eval = engine.analyse(board, chess.engine.Limit(time=0.1))["score"].white().score(mate_score=10000)
        eval_shift = current_eval - prev_eval
        
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
                blundered_move=move.uci(),
                best_move=best_move,
                turn="White" if is_white_turn else "Black",
                cp_loss=cp_loss,
                move_number=move_number
            ))

        prev_eval = current_eval
        if not is_white_turn:
            move_number += 1

    engine.quit()
    return puzzles

def save_puzzles_to_bank(puzzles: list[BlunderPuzzle]):
    if not puzzles:
        print("No blunders found to save.")
        return

    os.makedirs("data", exist_ok=True)
    new_data = [asdict(p) for p in puzzles]
    df_new = pd.DataFrame(new_data)
    
    df_new["solved"] = False
    df_new["attempts"] = 0
    
    if os.path.exists(PUZZLE_DB):
        df_existing = pd.read_csv(PUZZLE_DB)
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
        print("\nPaste your PGN below. When finished, press Enter, then Ctrl+Z (Windows) or Ctrl+D (Mac/Linux) and Enter:")
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