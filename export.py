import chess.pgn
import pandas as pd
import os

PUZZLE_DB = "data/blunder_bank.csv"
EXPORT_PATH = "data/blunders_export.pgn"

def export_blunders():
    if not os.path.exists(PUZZLE_DB):
        print(f"No data found at {PUZZLE_DB}")
        return

    df = pd.read_csv(PUZZLE_DB)
    
    with open(EXPORT_PATH, "w") as f:
        for idx, row in df.iterrows():
            game = chess.pgn.Game()
            game.setup(row["fen_before"])
            
            # Setup headers
            game.headers["Event"] = f"Onyx Blunder Puzzle #{idx+1}"
            game.headers["White"] = "Player" if row["turn"].strip().lower() == "white" else "Stockfish"
            game.headers["Black"] = "Player" if row["turn"].strip().lower() == "black" else "Stockfish"
            
            # Add the winning move and comment
            node = game.add_variation(chess.Move.from_uci(row["best_move"]))
            node.comment = f"Original game blunder penalty: -{row['cp_loss']} cp"
            
            print(game, file=f, end="\n\n")

    print(f"✅ Successfully exported {len(df)} puzzles to {EXPORT_PATH}")

if __name__ == "__main__":
    export_blunders()