import os
import time
import chess
import pandas as pd
from gui import ChessBoardGUI

PUZZLE_DB = "data/blunder_bank.csv"

def run_puzzle_gui_session():
    if not os.path.exists(PUZZLE_DB):
        print(f"Error: {PUZZLE_DB} not found. Run mistake_parser.py first!")
        return

    df = pd.read_csv(PUZZLE_DB)
    unsolved = df[df["solved"] == False]

    if unsolved.empty:
        print("🎉 All caught up! No unsolved blunders in your database.")
        return

    print(f"\n🧩 Loaded {len(unsolved)} unsolved blunder puzzle(s). Launching Onyx GUI...")

    for idx, row in unsolved.iterrows():
        fen = row["fen_before"]
        board = chess.Board(fen)
        is_black_turn = (row["turn"].strip().lower() == "black")

        # Initialize the Tkinter Chess GUI with proper perspective
        title = f"Onyx Trainer | Puzzle #{idx + 1} | {row['turn']} to Move (-{row['cp_loss']} cp)"
        gui = ChessBoardGUI(
            board=board,
            title=title,
            flip_board=is_black_turn,
            is_analysis=False,
            white_name="White",
            black_name="Black"
        )

        print("\n" + "=" * 50)
        print(f"PUZZLE #{idx + 1} | {row['turn']} to move | Move {row['move_number']}")
        print(f"Previous Blunder Cost: -{row['cp_loss']} centipawns")
        print("Click your move directly on the GUI window.")
        print("=" * 50)

        solved = False
        attempts = row["attempts"]

        while not solved:
            gui.draw_board()
            gui.populate_history()
            gui.show()

            # Wait for user click move from the Tkinter GUI
            user_move = gui.get_mouse_move()

            # If the user closes the window or quits
            if user_move == "quit":
                print("\nSession paused. Progress saved.")
                gui.close()
                return

            # Check validity against legal chess moves
            try:
                move_obj = chess.Move.from_uci(user_move)
                if move_obj not in board.legal_moves:
                    # Check for automatic queen promotion fallback
                    move_obj = chess.Move.from_uci(user_move + "q")
                    if move_obj not in board.legal_moves:
                        print(f"⚠️ Illegal move: {user_move}")
                        continue
                    user_move += "q"
            except Exception:
                continue

            attempts += 1
            df.at[idx, "attempts"] = attempts

            # Compare against the engine solution
            if user_move == row["best_move"]:
                print(f"✅ Correct! '{user_move}' is the best move.")
                df.at[idx, "solved"] = True
                
                # Push the winning move and draw it
                board.push(move_obj)
                gui.draw_board()
                gui.populate_history()
                gui.draw_arrow(user_move[:2], user_move[2:4], color="#769656")
                gui.show()

                time.sleep(1.2)  # Brief pause to see the winning move
                solved = True
            else:
                print(f"❌ '{user_move}' is not the best move. Try again!")
                # Reset board back to the puzzle state
                board.set_fen(fen)
                gui.draw_board()

        # Save progress after each solved puzzle
        df.to_csv(PUZZLE_DB, index=False)
        gui.close()

    print("\n🏆 Congratulations! You solved all pending blunder puzzles!")

if __name__ == "__main__":
    run_puzzle_gui_session()