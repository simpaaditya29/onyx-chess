import os
import time
import chess
import chess.engine
import pandas as pd
from gui import ChessBoardGUI

PUZZLE_DB = "data/blunder_bank.csv"
STOCKFISH_PATH = "./assets/engine/stockfish.exe"

import datetime

def run_puzzle_gui_session():
    if not os.path.exists(PUZZLE_DB):
        print(f"Error: {PUZZLE_DB} not found. Run mistake_parser.py first!")
        return

    df = pd.read_csv(PUZZLE_DB)
    
    # NEW: Filter for puzzles that are due today or earlier
    today = datetime.date.today().isoformat()
    unsolved = df[df["next_review_date"] <= today]

    if unsolved.empty:
        print("🎉 All caught up! No puzzles due for review today.")
        return

    print(f"\n🧩 Loaded {len(unsolved)} blunder(s) due for review. Launching Onyx GUI...")

    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    for idx, row in unsolved.iterrows():
        fen = row["fen_before"]
        board = chess.Board(fen)
        is_black_turn = (row["turn"].strip().lower() == "black")

        gui = ChessBoardGUI(
            board=board,
            title=f"Onyx Trainer | Box {row.get('box_level', 1)} | {row['turn']} to Move",
            flip_board=is_black_turn,
            is_analysis=False,
            white_name="White",
            black_name="Black"
        )

        info_baseline = engine.analyse(board, chess.engine.Limit(time=0.1))
        score_baseline = info_baseline["score"].white().score(mate_score=10000)
        gui.update_eval(score_baseline) 

        solved = False
        attempts = row["attempts"]
        moves_solved = 0
        TARGET_MOVES = 2 

        while not solved:
            gui.draw_board()
            gui.populate_history()
            gui.show()

            user_move = gui.get_mouse_move()

            if user_move == "quit":
                print("\nSession paused. Progress saved.")
                gui.close()
                engine.quit()
                return
                
            # NEW: Interactive Hint System
            if user_move == "hint":
                best_start_square = row["best_move"][:2]
                print(f"💡 HINT: Look at the piece on {best_start_square}")
                gui.draw_arrow(best_start_square, best_start_square, color="#f1c40f")
                gui.show()
                continue

            try:
                move_obj = chess.Move.from_uci(user_move)
                if move_obj not in board.legal_moves:
                    move_obj = chess.Move.from_uci(user_move + "q")
                    if move_obj not in board.legal_moves:
                        continue
                    user_move += "q"
            except Exception:
                continue

            attempts += 1
            df.at[idx, "attempts"] = attempts

            board.push(move_obj)
            info_after = engine.analyse(board, chess.engine.Limit(time=0.1))
            score_after = info_after["score"].white().score(mate_score=10000)
            board.pop() 

            cp_diff = score_after - score_baseline
            if is_black_turn:
                cp_diff = -cp_diff 
            
            if cp_diff >= -30:
                print(f"✅ Move {moves_solved + 1}/{TARGET_MOVES} correct! (Eval loss: {abs(cp_diff)} cp).")
                board.push(move_obj)
                gui.draw_board()
                gui.populate_history()
                gui.draw_arrow(user_move[:2], user_move[2:4], color="#769656")
                gui.show()
                time.sleep(1.0)
                
                moves_solved += 1
                
                if moves_solved >= TARGET_MOVES:
                    # NEW: Spaced Repetition Promotion
                    current_box = df.at[idx, "box_level"] if pd.notna(df.at[idx, "box_level"]) else 1
                    new_box = current_box + 1
                    
                    days_to_add = {2: 2, 3: 5, 4: 14, 5: 30}.get(new_box, 30)
                    next_date = datetime.date.today() + datetime.timedelta(days=days_to_add)
                    
                    df.at[idx, "box_level"] = new_box
                    df.at[idx, "next_review_date"] = next_date.isoformat()
                    df.at[idx, "solved"] = True
                    solved = True
                    print(f"🌟 Sequence complete! Promoted to Box {new_box}. Next review on {next_date}.")
                else:
                    print("\n🤖 Stockfish is thinking...")
                    engine_reply = engine.play(board, chess.engine.Limit(time=0.5)).move
                    
                    if engine_reply is None:
                        df.at[idx, "solved"] = True
                        solved = True
                        print("🏆 Board is terminal. Puzzle fully solved!")
                    else:
                        board.push(engine_reply)
                        reply_uci = engine_reply.uci()
                        print(f"♟️ Opponent plays: {reply_uci}. Find the next best move!")
                        gui.draw_board()
                        gui.populate_history()
                        gui.draw_arrow(reply_uci[:2], reply_uci[2:4], color="#e74c3c")
                        gui.show()
                        
                        info_baseline = engine.analyse(board, chess.engine.Limit(time=0.1))
                        score_baseline = info_baseline["score"].white().score(mate_score=10000)
            else:
                print(f"❌ Inaccuracy. '{user_move}' loses {abs(cp_diff)} centipawns. Try again!")
                board.set_fen(fen)
                gui.clear_arrows()
                moves_solved = 0 
                
                # NEW: Reset to Box 1 on failure
                df.at[idx, "box_level"] = 1
                df.at[idx, "next_review_date"] = datetime.date.today().isoformat()
                
                info_baseline = engine.analyse(board, chess.engine.Limit(time=0.1))
                score_baseline = info_baseline["score"].white().score(mate_score=10000)

        df.to_csv(PUZZLE_DB, index=False)
        gui.close()

    engine.quit()
    print("\n🏆 Congratulations! You solved all pending blunder puzzles for today!")

if __name__ == "__main__":
    run_puzzle_gui_session()