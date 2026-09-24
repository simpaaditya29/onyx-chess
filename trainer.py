import os
import time
import datetime
import chess
import chess.engine
import pandas as pd
import pyttsx3
from gui import ChessBoardGUI, BlindfoldHUD

PUZZLE_DB = "data/blunder_bank.csv"
STOCKFISH_PATH = "./assets/engine/stockfish.exe"

def format_speech_move(san_move):
    """Converts algebraic notation into natural spoken English for the TTS engine."""
    speech = san_move.replace('N', 'Knight ').replace('B', 'Bishop ').replace('R', 'Rook ')
    speech = speech.replace('Q', 'Queen ').replace('K', 'King ')
    speech = speech.replace('x', 'takes on ').replace('+', ' check').replace('#', ' checkmate')
    if speech == "O-O": return "Castles kingside"
    if speech == "O-O-O": return "Castles queenside"
    
    formatted_speech = ""
    for char in speech:
        if char.isdigit():
            formatted_speech += f" {char} "
        else:
            formatted_speech += char
    return formatted_speech.strip()

def run_sandbox(board, engine, gui, is_blindfold):
    """Activates a free-analysis mode with live Stockfish evaluation arrows and move tracking."""
    print("\n🔬 ANALYSIS SANDBOX ACTIVE")
    print("Explore candidate moves. Commands:")
    print(" - [Type UCI move]: Play a move (e.g., e2e4)")
    print(" - 'spar': Let Stockfish play the current turn")
    print(" - 'undo': Take back the last move")
    print(" - 'exit': Return to the puzzle queue")
    
    move_log = []

    while True:
        info = engine.analyse(board, chess.engine.Limit(time=0.1))
        score = info["score"].white().score(mate_score=10000)
        best_move = info.get("pv", [None])[0]
        
        if not is_blindfold:
            gui.update_eval(score)
            gui.clear_arrows()
            if best_move:
                gui.draw_arrow(best_move.uci()[:2], best_move.uci()[2:4], color="#3498db")
            gui.draw_board()
            gui.populate_history()
            gui.show()
            
            if move_log:
                print(f"📝 Current Variation: {' '.join(move_log)}")
                
            user_move = gui.get_mouse_move()
        else:
            if best_move:
                print(f"🤖 Engine suggests: {best_move.uci()} (Eval: {score/100:.2f})")
            if move_log:
                print(f"📝 Current Variation: {' '.join(move_log)}")
            user_move = input("\nEnter command or move: ").strip().lower()

        if user_move in ["quit", "exit", "next"]:
            if not is_blindfold:
                gui.clear_arrows()
            break
            
        if user_move == "undo":
            if move_log and len(board.move_stack) > 0:
                board.pop()
                move_log.pop()
            else:
                print("⚠️ Cannot undo further. Back at starting position.")
            continue

        if user_move == "spar":
            print("🤺 Engine takes over...")
            engine_reply = engine.play(board, chess.engine.Limit(time=0.5)).move
            if engine_reply:
                san_move = board.san(engine_reply)
                board.push(engine_reply)
                move_log.append(f"{san_move}(Eng)")
            else:
                print("🏆 Board is terminal.")
            continue
            
        try:
            move_obj = chess.Move.from_uci(user_move)
            if move_obj not in board.legal_moves:
                move_obj = chess.Move.from_uci(user_move + "q")
            if move_obj in board.legal_moves:
                san_move = board.san(move_obj)
                board.push(move_obj)
                move_log.append(san_move)
            else:
                print("⚠️ Illegal move.")
        except Exception:
            if not is_blindfold and user_move == "":
                continue
            print("⚠️ Invalid format. Use UCI (e.g., e7e5) or valid commands.")
            continue

def run_puzzle_gui_session():
    if not os.path.exists(PUZZLE_DB):
        print(f"Error: {PUZZLE_DB} not found. Run mistake_parser.py first!")
        return

    df = pd.read_csv(PUZZLE_DB)
    today = datetime.date.today().isoformat()
    
    if "next_review_date" not in df.columns:
        df["next_review_date"] = today
        
    unsolved = df[df["next_review_date"] <= today]

    if unsolved.empty:
        print("🎉 All caught up! No puzzles due for review today.")
        return

    print("\n🔍 Scanning due puzzles for tactical themes...")
    unique_themes = set()
    for tag_string in unsolved['tags'].dropna():
        if tag_string != "Untagged":
            for t in str(tag_string).split(','):
                unique_themes.add(t.strip())
            
    theme_list = sorted(list(unique_themes))
    
    if theme_list:
        print("\nAvailable Themes:")
        print("[0] All Due Puzzles (Mixed Routine)")
        for i, theme in enumerate(theme_list, 1):
            print(f"[{i}] {theme}")
            
        theme_choice = input("\nEnter choice (0 for all): ").strip()
        if theme_choice.isdigit() and int(theme_choice) > 0 and int(theme_choice) <= len(theme_list):
            selected_theme = theme_list[int(theme_choice) - 1]
            unsolved = unsolved[unsolved['tags'].str.contains(selected_theme, na=False)]
            print(f"\n🎯 Target locked: Loaded {len(unsolved)} '{selected_theme}' puzzles.")
    else:
        print("No specific tags found in due puzzles.")

    mode = input("\nSelect Training Mode:\n [1] Standard Visual Board\n [2] Blindfold Mode (Audio Enabled)\nEnter choice (1 or 2): ").strip()
    is_blindfold = (mode == "2")

    tts_engine = None
    if is_blindfold:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 160)
        print("🔊 Audio announcer initialized.")

    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    
    session_start_time = time.time()
    puzzles_completed = 0

    for idx, row in unsolved.iterrows():
        fen = row["fen_before"]
        board = chess.Board(fen)
        is_black_turn = (row["turn"].strip().lower() == "black")

        if is_blindfold:
            hud = BlindfoldHUD(title=f"Onyx Blindfold | Puzzle #{idx + 1}")
            hud.update_turn(row["turn"], 300, 300)
            print(f"\n🙈 BLINDFOLD MODE ACTIVE — Position FEN: {fen}")
            
            turn_msg = f"Turn: {row['turn']}. Type your move in UCI notation:"
            print(turn_msg)
            tts_engine.say(f"Puzzle {puzzles_completed + 1}. You are playing {row['turn']}.")
            tts_engine.runAndWait()
        else:
            gui = ChessBoardGUI(
                board=board,
                title=f"Onyx Trainer | Box {row.get('box_level', 1)} | {row['turn']} to Move",
                flip_board=is_black_turn,
                is_analysis=False
            )

        info_baseline = engine.analyse(board, chess.engine.Limit(time=0.1))
        score_baseline = info_baseline["score"].white().score(mate_score=10000)

        if not is_blindfold:
            gui.update_eval(score_baseline)

        solved = False
        attempts = row.get("attempts", 0)
        moves_solved = 0
        TARGET_MOVES = 2
        puzzle_start_time = time.time()

        while not solved:
            if not is_blindfold:
                gui.draw_board()
                gui.populate_history()
                gui.show()
                user_move = gui.get_mouse_move()
            else:
                user_move = input("\nEnter move (or 'quit'): ").strip().lower()

            if user_move == "quit":
                print("\nSession paused. Progress saved.")
                if is_blindfold: hud.close()
                else: gui.close()
                engine.quit()
                return

            if not is_blindfold and user_move == "hint":
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
                        print(f"⚠️ Illegal move: {user_move}")
                        continue
                    user_move += "q"
            except Exception:
                print("⚠️ Invalid format. Use UCI (e.g., e7e5).")
                continue

            attempts += 1
            df.at[idx, "attempts"] = attempts

            board.push(move_obj)
            info_after = engine.analyse(board, chess.engine.Limit(time=0.1))
            score_after = info_after["score"].white().score(mate_score=10000)
            board.pop()

            cp_diff = score_after - score_baseline
            if is_black_turn: cp_diff = -cp_diff

            if cp_diff >= -30:
                print(f"✅ Move {moves_solved + 1}/{TARGET_MOVES} correct! (Eval loss: {abs(cp_diff)} cp).")
                board.push(move_obj)
                moves_solved += 1

                if not is_blindfold:
                    gui.draw_board()
                    gui.populate_history()
                    gui.draw_arrow(user_move[:2], user_move[2:4], color="#769656")
                    gui.update_eval(score_after)
                    gui.show()
                    time.sleep(1.0)

                if moves_solved >= TARGET_MOVES:
                    elapsed_seconds = round(time.time() - puzzle_start_time, 1)
                    df.at[idx, "time_spent_sec"] = elapsed_seconds
                    
                    if is_blindfold:
                        tts_engine.say("Correct. Sequence complete.")
                        tts_engine.runAndWait()
                    
                    print(f"\n🌟 Sequence complete in {elapsed_seconds}s!")
                    print("Grade your performance:")
                    print(" [1] Hard (Review in 2 days)")
                    print(" [2] Good (Review in 7 days)")
                    print(" [3] Easy (Review in 14 days)")
                    
                    grade = input("Select (1-3): ").strip()
                    days_to_add = { '1': 2, '2': 7, '3': 14 }.get(grade, 7)
                    
                    current_box = df.at[idx, "box_level"] if pd.notna(df.at[idx, "box_level"]) else 1
                    new_box = current_box + 1
                    next_date = datetime.date.today() + datetime.timedelta(days=days_to_add)

                    df.at[idx, "box_level"] = new_box
                    df.at[idx, "next_review_date"] = next_date.isoformat()
                    df.at[idx, "solved"] = True
                    solved = True
                    puzzles_completed += 1
                    
                    print(f"Promoted to Box {new_box}. Next review scheduled for {next_date}.")
                    
                    ans = input("\n[Enter] Next Puzzle | [A] Analyze Position: ").strip().lower()
                    if ans == 'a':
                        run_sandbox(board, engine, gui if not is_blindfold else None, is_blindfold)

                else:
                    engine_reply = engine.play(board, chess.engine.Limit(time=0.5)).move
                    if engine_reply is None:
                        df.at[idx, "solved"] = True
                        solved = True
                        puzzles_completed += 1
                        print("🏆 Board is terminal. Puzzle solved!")
                        
                        ans = input("\n[Enter] Next Puzzle | [A] Analyze Position: ").strip().lower()
                        if ans == 'a':
                            run_sandbox(board, engine, gui if not is_blindfold else None, is_blindfold)
                    else:
                        san_move = board.san(engine_reply)
                        board.push(engine_reply)
                        reply_uci = engine_reply.uci()
                        
                        print(f"♟️ Opponent plays: {san_move} ({reply_uci}). Find the response!")
                        
                        if is_blindfold:
                            spoken_move = format_speech_move(san_move)
                            tts_engine.say(f"Opponent plays {spoken_move}")
                            tts_engine.runAndWait()
                        else:
                            gui.draw_board()
                            gui.populate_history()
                            gui.draw_arrow(reply_uci[:2], reply_uci[2:4], color="#e74c3c")
                            gui.show()

                        info_baseline = engine.analyse(board, chess.engine.Limit(time=0.1))
                        score_baseline = info_baseline["score"].white().score(mate_score=10000)
            else:
                print(f"❌ Inaccuracy. '{user_move}' loses {abs(cp_diff)} cp. Try again!")
                if is_blindfold:
                    tts_engine.say("Inaccuracy. Try again.")
                    tts_engine.runAndWait()
                
                ans = input("\n[Enter] Retry Puzzle | [A] Analyze Mistake: ").strip().lower()
                if ans == 'a':
                    board.push(move_obj)
                    run_sandbox(board, engine, gui if not is_blindfold else None, is_blindfold)
                    board.pop()
                    
                board.set_fen(fen)
                moves_solved = 0
                df.at[idx, "box_level"] = 1
                df.at[idx, "next_review_date"] = datetime.date.today().isoformat()
                if not is_blindfold:
                    gui.clear_arrows()
                    gui.draw_board()

        df.to_csv(PUZZLE_DB, index=False)
        if is_blindfold: hud.close()
        else: gui.close()

    engine.quit()
    
    total_time = round((time.time() - session_start_time) / 60, 1)
    print("\n" + "="*40)
    print(" 🏁 TRAINING SESSION COMPLETE")
    print("="*40)
    print(f" Puzzles Solved: {puzzles_completed}")
    print(f" Time Spent:     {total_time} minutes")
    print("="*40 + "\n")

if __name__ == "__main__":
    run_puzzle_gui_session()