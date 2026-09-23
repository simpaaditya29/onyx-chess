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
    
    # Add spacing between letters and numbers for better TTS pronunciation (e.g., "e 4")
    formatted_speech = ""
    for char in speech:
        if char.isdigit():
            formatted_speech += f" {char} "
        else:
            formatted_speech += char
    return formatted_speech.strip()

def run_puzzle_gui_session():
    if not os.path.exists(PUZZLE_DB):
        print(f"Error: {PUZZLE_DB} not found. Run mistake_parser.py first!")
        return

    df = pd.read_csv(PUZZLE_DB)
    today = datetime.date.today().isoformat()
    unsolved = df[df["next_review_date"] <= today]

    if unsolved.empty:
        print("🎉 All caught up! No puzzles due for review today.")
        return

    # NEW: Dynamic Theme Filtering
    print("\n🔍 Scanning due puzzles for tactical themes...")
    unique_themes = set()
    for tag_string in unsolved['tags'].dropna():
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

    # Initialize TTS Engine
    tts_engine = None
    if is_blindfold:
        tts_engine = pyttsx3.init()
        tts_engine.setProperty('rate', 160) # Slightly slower for clarity
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
        attempts = row["attempts"]
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
                    current_box = df.at[idx, "box_level"] if pd.notna(df.at[idx, "box_level"]) else 1
                    new_box = current_box + 1
                    days_to_add = {2: 2, 3: 5, 4: 14, 5: 30}.get(new_box, 30)
                    next_date = datetime.date.today() + datetime.timedelta(days=days_to_add)

                    df.at[idx, "box_level"] = new_box
                    df.at[idx, "next_review_date"] = next_date.isoformat()
                    df.at[idx, "solved"] = True
                    solved = True
                    puzzles_completed += 1
                    
                    if is_blindfold:
                        tts_engine.say("Correct. Sequence complete.")
                        tts_engine.runAndWait()
                        
                    print(f"🌟 Sequence complete in {elapsed_seconds}s! Promoted to Box {new_box}. Next review on {next_date}.")
                else:
                    engine_reply = engine.play(board, chess.engine.Limit(time=0.5)).move
                    if engine_reply is None:
                        df.at[idx, "solved"] = True
                        solved = True
                        puzzles_completed += 1
                        print("🏆 Board is terminal. Puzzle solved!")
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
    
    # Session Analytics Summary
    total_time = round((time.time() - session_start_time) / 60, 1)
    print("\n" + "="*40)
    print(" 🏁 TRAINING SESSION COMPLETE")
    print("="*40)
    print(f" Puzzles Solved: {puzzles_completed}")
    print(f" Time Spent:     {total_time} minutes")
    print("="*40 + "\n")

if __name__ == "__main__":
    run_puzzle_gui_session()