import chess
import chess.engine
import time
import random
import csv
import threading
import os
import pandas as pd


_PUZZLE_CACHE_DF = None

def _load_puzzle_database(file_path="puzzles.csv"):
    """Loads the puzzle CSV into memory once and caches it for instant access."""
    global _PUZZLE_CACHE_DF
    
    if _PUZZLE_CACHE_DF is not None:
        return _PUZZLE_CACHE_DF # Return the cached version instantly!
        
    print("⏳ Loading Lichess database for the first time... (This takes a moment)")
    try:
        # We use engine='c' for maximum parsing speed
        _PUZZLE_CACHE_DF = pd.read_csv(file_path, engine='c', low_memory=False)
        return _PUZZLE_CACHE_DF
    except Exception as e:
        print(f"❌ Failed to load puzzle data: {e}")
        return None


from gui import ChessBoardGUI
from engine_config import get_engine, get_best_move
from utils import ( 
    get_user_move, 
    log_game_data, 
    update_accuracy_stats, 
    analyze_position,
    save_profile,
    analyze_critical_moments,
    print_premium_board,
)

PUZZLE_CSV_PATH = "puzzles.csv"

# ==========================================
# 1. PLAY FULL GAME
# ==========================================

def play_full_game(profile, is_blindfold=False):
    import chess
    import chess.engine
    import chess.pgn
    import datetime
    import time
    from engine_config import get_engine
    from analytics import generate_post_game_report
    from main import get_best_move_time_limited

    engine = get_engine()
    if not engine:
        print("❌ Error: Stockfish engine could not be loaded!")
        input("\nPress Enter to return...")
        return

    print("\n--- 🤖 SELECT STOCKFISH DIFFICULTY ---")
    print("1. Beginner (800 ELO) - Makes blunders")
    print("2. Intermediate (1500 ELO) - Decent club player")
    print("3. Advanced (2000 ELO) - Very strong")
    print("4. Master (Max Strength) - Unbeatable")

    diff_choice = input("\nSelect level (1-4): ").strip()
    time_limit = 0.5

    print("\n--- ⏳ CHOOSE YOUR TIME CONTROL ---")
    print("1. Bullet (1 min)")
    print("2. Blitz (5 min)")
    print("3. Rapid (10 min)")
    print("4. Unlimited (No Timer)")

    tc_choice = input("\nSelect time control (1-4): ").strip()

    # Convert the user's choice into total seconds for our GUI clock
    time_controls = {
        "1": 60,   # 60 seconds (Bullet)
        "2": 300,  # 300 seconds (Blitz)
        "3": 600,  # 600 seconds (Rapid)
        "4": None  # No timer
    }

    # Increments
    increments = {
        "1": 0,    # Bullet: 0s increment
        "2": 2,    # Blitz: +2s increment per move
        "3": 5,    # Rapid: +5s increment per move
        "4": 0     # Unlimited: 0s
    }

    player_time = time_controls.get(tc_choice, None)
    player_increment = increments.get(tc_choice, 0)

    if player_time:
        print(f"✅ Time control set to {player_time // 60} minutes!")

        # Ask for custom increment (or keep the default)
        inc_input = input(f"Enter increment in seconds (or press Enter to keep default +{player_increment}s): ").strip()
        if inc_input.isdigit():
            player_increment = int(inc_input)
            print(f"✅ Increment manually set to {player_increment} seconds.")
    else:
        print("✅ Time control set to Unlimited!")

    try:
        if diff_choice == '1':
            engine.configure({"UCI_LimitStrength": True, "UCI_Elo": 800, "Skill Level": 2})
            time_limit = 0.1
        elif diff_choice == '2':
            engine.configure({"UCI_LimitStrength": True, "UCI_Elo": 1500, "Skill Level": 10})
            time_limit = 0.2
        elif diff_choice == '3':
            engine.configure({"UCI_LimitStrength": False, "Skill Level": 18})
            time_limit = 0.3
        else:
            engine.configure({"UCI_LimitStrength": False, "Skill Level": 20})
            time_limit = 0.5
    except Exception:
        pass

    # --- VOICE ANNOUNCER SETUP ---
    use_voice = False
    try:
        import pyttsx3
        use_voice = input("🗣️ Enable Voice Announcer? (y/n): ").strip().lower() == 'y'
    except ImportError:
        print("💡 Tip: Run 'pip install pyttsx3' to enable Voice Announcer!")

    # --- FEN SANDBOX ---
    print(f"\n--- ♟️ PLAY VS BOT {'(BLINDFOLD)' if is_blindfold else ''} ---")
    use_fen = input("♟️ Start from a custom FEN position? (y/n): ").strip().lower()

    if use_fen == 'y':
        custom_fen = input("Paste your FEN string: ").strip()
        try:
            board = chess.Board(custom_fen)
        except ValueError:
            print("❌ Invalid FEN! Starting from standard position.")
            board = chess.Board()
    else:
        board = chess.Board()

    # --- COLOR SELECTION MENU ---
    print("1. Play as White")
    print("2. Play as Black")
    color_choice = input("\nSelect your color (1-2): ").strip()
    user_color = chess.BLACK if color_choice == '2' else chess.WHITE
    is_black_pov = (user_color == chess.BLACK)

    show_eval = input("📊 Enable Live Evaluation Bar? (y/n): ").strip().lower() == 'y'
    coach_mode = input("🎓 Enable Coach Mode (Blunder Warnings)? (y/n): ").strip().lower() == 'y'

    if is_blindfold:
        from gui import BlindfoldHUD
        initial_time = player_time if player_time is not None else 300
        gui = BlindfoldHUD(title="Blindfold Mode Clock", white_time=initial_time, black_time=initial_time)
    else:
        from gui import ChessBoardGUI
        white_player = "Player" if user_color == chess.WHITE else "Stockfish"
        black_player = "Stockfish" if user_color == chess.WHITE else "Player"
        gui = ChessBoardGUI(
            board,
            title="Onyx vs Stockfish",
            flip_board=is_black_pov,
            is_analysis=show_eval,
            white_name=white_player,
            black_name=black_player,
            time_limit=player_time,
            increment=player_increment
        )

    # Persistent clock setup outside the loop!
    white_clock = player_time if player_time is not None else 300
    black_clock = player_time if player_time is not None else 300

    while not board.is_game_over():
        turn_start = time.time() # Start the stopwatch for this turn!

        if not is_blindfold:
            print("\n" + str(board) + "\n")
            
            # UPDATE LIVE EVALUATION
            if show_eval:
                info = engine.analyse(board, chess.engine.Limit(depth=10))
                score = info["score"].white()
                if score.is_mate():
                    cp = 1000 if score.mate() > 0 else -1000
                else:
                    cp = score.score()
                gui.update_eval(cp)

            gui.draw_board()
            gui.populate_history()
            gui.show()
        else:
            print("\n[Blindfold Mode Active - Board Hidden]")
            turn_str = "white" if board.turn == chess.WHITE else "black"
            gui.update_turn(turn_str, white_clock, black_clock)

        if board.turn == user_color:
            while True:
                if not is_blindfold:
                    print("Your Move: (Click piece, Backspace=Undo, H=Hint) ", end="", flush=True)
                    move_str = gui.get_mouse_move()
                else:
                    move_str = input("\nYour Move (or 'quit'): ").strip()

                if move_str.lower() == 'quit':
                    engine.quit()
                    gui.close()
                    return
                
                if move_str == "timeout":
                    break

                if move_str.lower() == 'undo':
                    if len(board.move_stack) >= 2:
                        board.pop()
                        board.pop()
                        print("\n⏪ Moves undone!")

                        if show_eval:
                            info = engine.analyse(board, chess.engine.Limit(depth=10))
                            if not is_blindfold and 'gui' in locals():
                                gui.update_eval(info["score"].white().score(mate_score=1000))
                        if not is_blindfold and 'gui' in locals():
                            gui.draw_board()
                            gui.populate_history()
                    else:
                        print("\n❌ Nothing to undo yet!")
                    continue

                if move_str.lower() == 'hint':
                    print("\n🤔 Stockfish is analyzing the position...")
                    hint_info = engine.play(board, chess.engine.Limit(time=1.0))
                    print(f"💡 Hint: The best theoretical move is {board.san(hint_info.move)}")
                    continue

                try:
                    move = board.parse_san(move_str)

                    # STRICT LEGALITY CHECK
                    if move not in board.legal_moves:
                        print("\n❌ Illegal move on the board! Please try again.")
                        continue

                    # COACH MODE LOGIC
                    if coach_mode:
                        current_info = engine.analyse(board, chess.engine.Limit(depth=10))
                        current_eval = current_info["score"].white().score(mate_score=1000)
                        if user_color == chess.BLACK:
                            current_eval *= -1

                        board.push(move)
                        next_info = engine.analyse(board, chess.engine.Limit(depth=10))
                        next_eval = next_info["score"].white().score(mate_score=1000)
                        if user_color == chess.BLACK:
                            next_eval *= -1
                        board.pop() 

                        if next_eval < (current_eval - 200):
                            print("\n⚠️ COACH ALERT: That move drops your position significantly!")
                            confirm = input("Are you sure you want to play it? (y/n): ").strip().lower()
                            if confirm != 'y':
                                print("Good catch. Try finding a better move!")
                                continue

                    board.push(move)

                    # Deduct elapsed time from the player
                    elapsed = int(time.time() - turn_start)
                    if user_color == chess.WHITE:
                        white_clock = max(0, white_clock - elapsed + player_increment)
                    else:
                        black_clock = max(0, black_clock - elapsed + player_increment)
                        
                    break

                except ValueError:
                    print("\n❌ Invalid move. Try again.")

            if move_str == "timeout":
                break
        else:
            print("\n🤖 Onyx is thinking...")

            # BACKGROUND THINKING TO KEEP CLOCK TICKING
            import threading
            import queue

            move_queue = queue.Queue()

            def bot_think():
                # Use Onyx's Iterative Deepening Search instead of Stockfish
                best_move = get_best_move_time_limited(board, time_limit)
                move_queue.put(best_move)

            think_thread = threading.Thread(target=bot_think, daemon=True)
            think_thread.start()

            while think_thread.is_alive():
                if not is_blindfold:
                    gui.root.update()
                time.sleep(0.05)

            best_move = move_queue.get()
            engine_move_text = "Resigned"

            if best_move:
                engine_move_text = board.san(best_move)
                board.push(best_move)

            # Deduct elapsed time from Stockfish
            elapsed = int(time.time() - turn_start)
            if user_color == chess.WHITE:
                black_clock = max(0, black_clock - elapsed + player_increment)
            else:
                white_clock = max(0, white_clock - elapsed + player_increment)

            print(f"Stockfish played: {engine_move_text}")

            # EXECUTE QUEUED PRE-MOVE
            if not is_blindfold:
                if hasattr(gui, 'pre_move') and gui.pre_move is not None:
                    if gui.pre_move in board.legal_moves:
                        pre_move_san = board.san(gui.pre_move)
                        board.push(gui.pre_move)
                        print(f"⚡ Pre-move executed: {pre_move_san}")
                    else:
                        print("⚠️ Pre-move was illegal in the new position and was cancelled.")
                gui.pre_move = None

            # Refresh GUI visuals immediately
            if not is_blindfold:
                gui.draw_board()
                gui.populate_history()
            else:
                turn_str = "white" if board.turn == chess.WHITE else "black"
                gui.update_turn(turn_str, white_clock, black_clock)

            # VOICE ANNOUNCER LOGIC
            if use_voice:
                spoken = engine_move_text
                spoken = spoken.replace('N', 'Knight ').replace('B', 'Bishop ')
                spoken = spoken.replace('R', 'Rook ').replace('Q', 'Queen ').replace('K', 'King ')
                spoken = spoken.replace('x', ' takes ').replace('+', ' check').replace('#', ' checkmate')

                if len(spoken) == 2 and spoken[0].isalpha() and spoken[1].isdigit():
                    spoken = f"{spoken[0]} {spoken[1]}"

                try:
                    def announce(text_to_speak):
                        local_tts = pyttsx3.init()
                        local_tts.setProperty('rate', 175)
                        local_tts.say(text_to_speak)
                        local_tts.runAndWait()

                    voice_thread = threading.Thread(target=announce, args=(spoken,), daemon=True)
                    voice_thread.start()
                except Exception:
                    pass

    # Game Over handling
    if not is_blindfold:
        print("\n" + str(board) + "\n")
        gui.draw_board()
        gui.populate_history()
        gui.show()

    print(f"\n🎯 Game Over! Result: {board.result()}")
    generate_post_game_report(board, engine, user_color)

    gui.close()

    # BLUNDER REVIEW TRIGGER
    do_review = input("\n🔄 Do you want to review and retry your blunders? (y/n): ").strip().lower()
    if do_review == 'y':
        try:
            from training_modes import review_post_game_blunders
            review_post_game_blunders(board, engine, user_color)
        except Exception:
            pass

    save_game = input("\n💾 Do you want to save this game to a PGN file? (y/n): ").strip().lower()
    if save_game == 'y':
        game = chess.pgn.Game.from_board(board)
        game.headers["White"] = "Player" if user_color == chess.WHITE else "Stockfish"
        game.headers["Black"] = "Stockfish" if user_color == chess.WHITE else "Player"
        game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")

        filename = f"saved_game_{datetime.datetime.now().strftime('%H%M%S')}.pgn"
        with open(filename, "w") as f:
            f.write(str(game))
        print(f"✅ Game saved successfully as '{filename}'!")

    input("\nPress Enter to return...")
    engine.quit()

# ==========================================
# 2. PASS 'N PLAY
# ==========================================
def play_pass_n_play(profile):
    import chess
    import chess.engine
    from gui import ChessBoardGUI
    from engine_config import get_engine

    board = chess.Board()
    print("\n--- 🤝 PASS 'N PLAY (LOCAL MULTIPLAYER) ---")

    gui = ChessBoardGUI(board, title="Onyx Local Multiplayer")
    engine = get_engine()

    while not board.is_game_over():
        gui.draw_board()
        gui.populate_history()
        gui.show()

        current_turn = "White" if board.turn == chess.WHITE else "Black"

        # Continuous Live Position Analysis (Top 3 Recommendations)
        print(f"\n⏳ Stockfish evaluating position for {current_turn}...")
        try:
            analysis = engine.analyse(board, chess.engine.Limit(time=0.8), multipv=3)
            print("📈 Top Engine Recommendations:")
            for i, info in enumerate(analysis):
                if "pv" in info and len(info["pv"]) > 0:
                    rec_move = info["pv"][0]
                    san_rec = board.san(rec_move)
                    score = info["score"].relative.score(mate_score=10000)
                    eval_str = f"+{score/100:.2f}" if score is not None and score > 0 else (f"{score/100:.2f}" if score is not None else "Mate")
                    print(f"   {i+1}. {san_rec:<6} (Eval: {eval_str})")
            print("-" * 40)
        except Exception:
            pass

        print(f"\n{current_turn}'s Move: (Click on the GUI board) ", end="", flush=True)

        move_str = gui.get_mouse_move()

        if move_str.lower() == 'quit':
            break

        try:
            # Handle both GUI mouse clicks (UCI) and manual keyboard entry (SAN)
            try:
                move = chess.Move.from_uci(move_str)
                if move not in board.legal_moves:
                    move = board.parse_san(move_str)
            except ValueError:
                move = board.parse_san(move_str)

            if move in board.legal_moves:
                board.push(move)
            else:
                print("❌ Illegal move. Try again.")
        except ValueError:
            print("❌ Invalid notation or move. Try again.")

    gui.draw_board()
    gui.populate_history()
    gui.show()
    print(f"\n🏁 Game Over! Result: {board.result()}")
    input("\nPress Enter to return...")
    gui.close()
    
# ==========================================
# 3. SURVIVAL MODE
# ==========================================
def play_survival_mode(profile):
    pass # <-- Paste your play_survival_mode code here (replace 'pass')


# ==========================================
# 4. BLITZ MODE
# ==========================================
# Import the new timer function at the top of training_modes.py:
# from utils import get_timed_user_move

def play_timed_mode(profile):
    import chess
    import time
    from utils import print_premium_board, get_timed_user_move
    from engine_config import get_engine

    engine = get_engine()
    if not engine:
        return

    # --- TIME CONTROL MENU ---
    print("\n⚡ SELECT TIME CONTROL ⚡")
    print("1. Bullet (1 min + 0)")
    print("2. Blitz (3 min + 2)")
    print("3. Blitz (5 min + 3)")
    print("4. Rapid (10 min + 5)")
    print("5. Custom")

    tc_choice = input("Select option (1-5): ").strip()

    if tc_choice == '1':
        player_clock, increment = 60.0, 0.0
    elif tc_choice == '2':
        player_clock, increment = 180.0, 2.0
    elif tc_choice == '3':
        player_clock, increment = 300.0, 3.0
    elif tc_choice == '4':
        player_clock, increment = 600.0, 5.0
    elif tc_choice == '5':
        try:
            mins = int(input("Enter starting minutes: "))
            inc = int(input("Enter increment in seconds: "))
            player_clock, increment = float(mins * 60), float(inc)
        except ValueError:
            print("Invalid input. Defaulting to 3+2.")
            player_clock, increment = 180.0, 2.0
    else:
        print("Invalid choice. Defaulting to 3+2.")
        player_clock, increment = 180.0, 2.0

    board = chess.Board()
    engine_clock = player_clock  # Engine has the same time control as the player
    print(f"\nGame starting! You have {int(player_clock//60)}:{int(player_clock%60):02d} with a {int(increment)}s increment.")

    while not board.is_game_over():
        print_premium_board(board)

        if board.turn == chess.WHITE:
            # Display current clock
            mins, secs = divmod(int(player_clock), 60)
            print(f"⏰ Time remaining: {mins}:{secs:02d}")

            # Start tracking time taken for the move
            start_time = time.time()

            # Pass the total remaining clock to the timeout function
            move_str, timed_out = get_timed_user_move(prompt="Your move: ", timeout=player_clock)

            # Deduct elapsed time
            elapsed_time = time.time() - start_time
            player_clock -= elapsed_time

            # --- ⏰ TIMEOUT FIX ---
            if timed_out or player_clock <= 0:
                print("\n⏰ FLAG FELL! You ran out of time. 0:00 remaining.")
                break

            if move_str.lower() == 'quit':
                break

            try:
                move = board.parse_san(move_str)
                if move in board.legal_moves:
                    board.push(move)
                    # Add increment ONLY if a legal move was successfully played
                    player_clock += increment
                    print(f"⏳ Move time: {elapsed_time:.1f}s | +{increment}s added!")
                else:
                    print("❌ Illegal move. Try again!")
            except ValueError:
                print("❌ Invalid notation. Try again!")

        else:
            # Engine move
            start_time = time.time()
            
            # Pass clocks directly (Human = White, Engine = Black)
            limit = chess.engine.Limit(
                white_clock=player_clock,
                black_clock=engine_clock,
                white_inc=increment,
                black_inc=increment
            )
            
            result = engine.play(board, limit)
            
            # Deduct elapsed time and add increment for engine
            elapsed_time = time.time() - start_time
            engine_clock -= elapsed_time
            engine_clock += increment
            
            engine_move_text = board.san(result.move)
            board.push(result.move)
            print(f"🤖 Stockfish played: {engine_move_text} (took {elapsed_time:.1f}s)")
            
            if engine_clock <= 0:
                print("\n⏰ ENGINE FLAG FELL! You win on time.")
                break
            
    # Check for checkmates or draws after the loop
    if board.is_game_over():
        print(f"\nGame Over! Result: {board.result()}")

    engine.quit()
    input("\nPress Enter to return...")


def play_puzzles(profile):
    import chess
    import pandas as pd
    import random
    import os
    from utils import print_premium_board

    print("\n--- 🧩 ONYX PUZZLE SUITE ---")

    # Pointing directly to the root folder where your screenshot shows it
    file_path = "puzzles.csv"
    if not os.path.exists(file_path):
        print("❌ Error: puzzles.csv not found.")
        input("Press Enter to return...")
        return

    print("⏳ Loading Lichess database... (This might take a second)")
    df = _load_puzzle_database(file_path)
    if df is None:
        input("Press Enter to return...")
        return

    # --- NEW: INFINITE LOOP STARTS HERE ---
    while True:
        try:
            puzzle = df.sample(n=1).iloc[0]

            board = chess.Board(puzzle['FEN'])
            solution = str(puzzle['Moves']).strip().split(" ")
            theme = str(puzzle.get('Themes', 'Tactics')).replace(" ", ", ")

            # --- FIX: PLAY THE OPPONENT'S INITIAL BLUNDER ---
            opp_move_str = solution[0]
            board.push(chess.Move.from_uci(opp_move_str))
            print(f"\n🚨 Opponent played: {opp_move_str}")

            # Remove it from the list so the loop correctly starts with your turn
            solution = solution[1:]
            # ------------------------------------------------

        except Exception as e:
            print(f"❌ Failed to load puzzle data: {e}")
            input("Press Enter to return...")
            return

        print(f"\n🎯 Themes: {theme}")
        print("Find the winning sequence!")

        is_black_turn = (board.turn == chess.BLACK)
        gui = ChessBoardGUI(board, title="Onyx Daily Puzzle", is_analysis=True, flip_board=is_black_turn)

        step = 0
        while step < len(solution):
            gui.draw_board()
            gui.populate_history()
            gui.root.update()
            
            if step % 2 == 0:
                print("\nYour move: (Make your move on the graphical board)")
                user_move_str = gui.get_mouse_move() # <--- This enables the mouse clicks!

                # --- NEW: GUI HINT LOGIC ---
                if user_move_str.lower() == 'hint':
                    print("\n🤔 Stockfish is calculating a hint...")
                    # Get the engine from engine_config
                    from engine_config import get_engine
                    engine = get_engine()
                    hint_info = engine.play(board, chess.engine.Limit(time=1.0))
                    print(f"💡 Hint: Try looking at {board.san(hint_info.move)}")
                    continue # Restarts the loop to let you make your move

                if user_move_str.lower() == 'quit':
                    gui.close()
                    return

                try:
                    # Lichess databases use UCI format (e.g., e2e4)
                    user_move = chess.Move.from_uci(user_move_str)
                    correct_move = chess.Move.from_uci(solution[step])

                    if user_move == correct_move:
                        print("✅ Correct!")
                        board.push(user_move)
                        step += 1
                    else:
                        print("❌ Incorrect. Try again!")
                except ValueError:
                    print("❌ Invalid format. Use UCI notation (e.g., e2e4, g1f3).")
            else:
                opponent_move = chess.Move.from_uci(solution[step])
                print(f"\n🤖 Opponent plays: {opponent_move}")
                board.push(opponent_move)
                step += 1

        print("🎉 Puzzle Solved!")
        gui.close()
        
        # --- NEW: ASK TO CONTINUE OR QUIT ---
        continue_choice = input("\nPress Enter for next puzzle (or type 'quit' to exit): ").strip().lower()
        if continue_choice == 'quit':
            return

def puzzle_dashboard(profile):
    """
    Central hub for all puzzle-related training modes.
    """
    while True:
        print("\n" + "="*45)
        print("🧩 ONYX PUZZLE DASHBOARD 🧩")
        print("="*45)
        print("1. Daily Puzzle")
        print("2. Puzzle Themes (Opening, Middlegame, Endgame)")
        print("3. Puzzle Streak (Survival - Play until you miss)")
        print("4. Puzzle Storm (Time Attack)")
        print("5. Adaptive Endgame Simulator")
        print("6. Return to Main Menu")

        choice = input("\nSelect training mode (1-6): ").strip()

        if choice == '1':
            play_puzzles(profile)
        elif choice == '2':
            print("\n--- 🎯 SELECT PUZZLE THEME ---")
            print("1. Opening Puzzles")
            print("2. Middlegame Puzzles")
            print("3. Endgame Puzzles")
            print("4. Back to Dashboard")
            theme_choice = input("Select theme (1-4): ").strip()
            
            if theme_choice == '1': play_puzzles_by_theme(profile, "opening")
            elif theme_choice == '2': play_puzzles_by_theme(profile, "middlegame")
            elif theme_choice == '3': play_puzzles_by_theme(profile, "endgame")
        elif choice == '3':
            play_puzzle_streak(profile)
        elif choice == '4':
            play_puzzle_storm(profile)
        elif choice == '5':
            play_endgame_simulator(profile) # <--- Added the new mode!
        elif choice == '6':
            break
        else:
            print("❌ Invalid choice. Try again.")    
            

def play_puzzles_by_theme(profile, theme=None):
    import chess
    import pandas as pd
    import random
    import os
    from engine_config import get_engine

    print("\n--- 🎯 THEME & ENDGAME PUZZLES ---")
    print("1. ♖ Rook Endgames       6. ⚔️ Forks")
    print("2. ♙ Pawn Endgames       7. 📌 Pins")
    print("3. ♗ Bishop Endgames     8. 🎯 Mate in 2")
    print("4. ♘ Knight Endgames     9. 🛡️ Defensive Moves")
    print("5. ♕ Queen Endgames      10. ✍️ Custom Lichess Theme")

    choice = input("\nSelect a category (1-10): ").strip()
    
    theme_map = {
        "1": "rookEndgame", "2": "pawnEndgame", "3": "bishopEndgame",
        "4": "knightEndgame", "5": "queenEndgame", "6": "fork",
        "7": "pin", "8": "mateIn2", "9": "defensiveMove"
    }

    if choice in theme_map:
        theme_input = theme_map[choice]
    elif choice == "10":
        theme_input = input("Enter exact Lichess theme (e.g., sacrifice, smotheredMate): ").strip()
    else:
        print("❌ Invalid choice. Returning to menu...")
        return
        
    if not theme_input:
        return

    file_path = "puzzles.csv"
    if not os.path.exists(file_path):
        print("❌ Error: puzzles.csv not found.")
        input("Press Enter to return...")
        return

    print("⏳ Loading Lichess database... (This might take a second)")
    df = _load_puzzle_database(file_path)
    if df is None:
        input("Press Enter to return...")
        return

    filtered_df = df[df['Themes'].str.contains(theme_input, case=False, na=False)]
    if filtered_df.empty:
        print(f"❌ No puzzles found for theme '{theme_input}'.")
        input("Press Enter to return...")
        return

    print(f"✅ Found {len(filtered_df)} puzzles for '{theme_input}'!")

    while True:
        try:
            puzzle = filtered_df.sample(n=1).iloc[0]
            board = chess.Board(puzzle['FEN'])
            solution = str(puzzle['Moves']).strip().split(" ")
            actual_themes = str(puzzle.get('Themes', 'Tactics')).replace(" ", ", ")

            opp_move_str = solution[0]
            board.push(chess.Move.from_uci(opp_move_str))
            print(f"\n🚨 Opponent played: {opp_move_str}")
            solution = solution[1:]
        except Exception as e:
            print(f"❌ Failed to load puzzle: {e}")
            input("Press Enter to return...")
            return

        print(f"\n🎯 Themes: {actual_themes}")
        print("Find the winning sequence!")

        is_black_turn = (board.turn == chess.BLACK)
        gui = ChessBoardGUI(board, title=f"Onyx Theme: {theme_input.capitalize()}", is_analysis=True, flip_board=is_black_turn)

        step = 0
        while step < len(solution):
            gui.draw_board()
            gui.populate_history()
            gui.root.update()

            if step % 2 == 0:
                print("\nYour move: (Make your move on the graphical board, press 'H' for hint)")
                user_move_str = gui.get_mouse_move()

                if user_move_str.lower() == 'quit':
                    gui.close()
                    return
                
                if user_move_str.lower() == 'hint':
                    print("\n🤔 Stockfish is calculating a hint...")
                    engine = get_engine()
                    hint_info = engine.play(board, chess.engine.Limit(time=1.0))
                    print(f"💡 Hint: Try looking at {board.san(hint_info.move)}")
                    continue

                try:
                    user_move = chess.Move.from_uci(user_move_str)
                    correct_move = chess.Move.from_uci(solution[step])

                    if user_move == correct_move:
                        print("✅ Correct!")
                        board.push(user_move)
                        step += 1
                    else:
                        print("❌ Incorrect. Try again!")
                except ValueError:
                    print("❌ Invalid format.")
            else:
                opponent_move = chess.Move.from_uci(solution[step])
                print(f"\n🤖 Opponent plays: {opponent_move}")
                board.push(opponent_move)
                step += 1

        print("🎉 Puzzle Solved!")
        gui.close()

        continue_choice = input("\nPress Enter for next puzzle (or type 'quit' to exit): ").strip().lower()
        if continue_choice == 'quit':
            return
        
def play_puzzle_streak(profile):
    import chess
    import pandas as pd
    import random
    import os
    from engine_config import get_engine

    print("\n--- 📈 PUZZLE STREAK ---")
    print("Solve as many puzzles in a row as you can! One mistake ends the streak.")
    
    file_path = "puzzles.csv"
    if not os.path.exists(file_path):
        print("❌ Error: puzzles.csv not found.")
        input("Press Enter to return...")
        return

    print("⏳ Loading Lichess database...")
    df = _load_puzzle_database(file_path)
    if df is None:
        input("Press Enter to return...")
        return

    score = 0
    
    # Streak naturally loops until you fail!
    while True:
        try:
            puzzle = df.sample(n=1).iloc[0]
            board = chess.Board(puzzle['FEN'])
            solution = str(puzzle['Moves']).strip().split(" ")
            
            # Opponent's first move
            opp_move_str = solution[0]
            board.push(chess.Move.from_uci(opp_move_str))
            solution = solution[1:]
        except Exception as e:
            print(f"❌ Error loading puzzle: {e}")
            input("Press Enter to return...")
            return

        # --- NEW: AUTO-FLIP BOARD ---
        is_black_turn = (board.turn == chess.BLACK)
        gui = ChessBoardGUI(board, title=f"Onyx Streak - Score: {score}", is_analysis=True, flip_board=is_black_turn)

        step = 0
        puzzle_failed = False
        
        while step < len(solution):
            gui.draw_board()
            gui.populate_history()
            gui.root.update()

            if step % 2 == 0:
                print(f"\nCurrent Streak: {score} | Your move (Press 'H' for hint):")
                user_move_str = gui.get_mouse_move()

                if user_move_str.lower() == 'quit':
                    gui.close()
                    return
                    
                # --- NEW: GUI HINT LOGIC ---
                if user_move_str.lower() == 'hint':
                    print("\n🤔 Stockfish is calculating a hint...")
                    engine = get_engine()
                    hint_info = engine.play(board, chess.engine.Limit(time=1.0))
                    print(f"💡 Hint: Try {board.san(hint_info.move)}")
                    continue

                try:
                    user_move = chess.Move.from_uci(user_move_str)
                    correct_move = chess.Move.from_uci(solution[step])

                    if user_move == correct_move:
                        print("✅ Correct!")
                        board.push(user_move)
                        step += 1
                    else:
                        print(f"❌ Incorrect! Streak broken at {score}!")
                        puzzle_failed = True
                        break # Breaks the inner loop, ending the puzzle
                except ValueError:
                    print("❌ Invalid format.")
            else:
                opponent_move = chess.Move.from_uci(solution[step])
                print(f"\n🤖 Opponent plays: {opponent_move}")
                board.push(opponent_move)
                step += 1
        
        gui.close()

        # If you failed, break the infinite loop and end the mode
        if puzzle_failed:
            print(f"\n💥 Game Over! Final Streak: {score}")
            input("Press Enter to return to menu...")
            return
            
        # Otherwise, increase score and loop again!
        score += 1
        print(f"\n🎉 Puzzle Solved! Streak is now {score}!")


def play_puzzle_storm(profile):
    import chess
    import pandas as pd
    import random
    import os
    import time
    from engine_config import get_engine

    print("\n--- ⚡ PUZZLE STORM ⚡ ---")
    print("Solve as many puzzles as you can in 3 minutes!")
    print("✅ +10s bonus for a 5-puzzle streak")
    print("❌ -10s penalty and skip for wrong answers")
    input("Press Enter to start the clock...")

    file_path = "puzzles.csv"
    if not os.path.exists(file_path):
        print("❌ Error: puzzles.csv not found.")
        return

    print("⏳ Loading database...")
    df = _load_puzzle_database(file_path)
    if df is None:
        return

    score = 0
    streak = 0
    start_time = time.time()
    end_time = start_time + 180.0  # 3 minutes

    while time.time() < end_time:
        try:
            puzzle = df.sample(n=1).iloc[0]
            board = chess.Board(puzzle['FEN'])
            solution = str(puzzle['Moves']).strip().split(" ")
            
            opp_move_str = solution[0]
            board.push(chess.Move.from_uci(opp_move_str))
            solution = solution[1:]
        except Exception as e:
            print(f"❌ Error loading puzzle: {e}")
            return

        is_black_turn = (board.turn == chess.BLACK)
        time_left = int(end_time - time.time())
        gui = ChessBoardGUI(board, title=f"Storm - Score: {score} | Time: {time_left}s", is_analysis=True, flip_board=is_black_turn)

        step = 0
        puzzle_failed = False
        
        while step < len(solution):
            if time.time() > end_time:
                break

            gui.draw_board()
            gui.populate_history()
            gui.root.update()

            if step % 2 == 0:
                time_left = int(end_time - time.time())
                if time_left <= 0:
                    break

                print(f"\nTime left: {time_left}s | Your move:")
                user_move_str = gui.get_mouse_move()

                if user_move_str.lower() == 'quit':
                    gui.close()
                    return
                    
                if user_move_str.lower() == 'hint':
                    print("\n🤔 Hints cost 5 seconds in Storm mode!")
                    end_time -= 5.0
                    engine = get_engine()
                    hint_info = engine.play(board, chess.engine.Limit(time=1.0))
                    print(f"💡 Hint: Try {board.san(hint_info.move)}")
                    continue

                try:
                    user_move = chess.Move.from_uci(user_move_str)
                    correct_move = chess.Move.from_uci(solution[step])

                    if user_move == correct_move:
                        print("✅ Correct!")
                        board.push(user_move)
                        step += 1
                    else:
                        print("❌ Incorrect! 10 Second Penalty!")
                        end_time -= 10.0
                        streak = 0
                        puzzle_failed = True
                        break  # Skips to the next puzzle immediately
                except ValueError:
                    print("❌ Invalid format.")
            else:
                opponent_move = chess.Move.from_uci(solution[step])
                print(f"\n🤖 Opponent plays: {opponent_move}")
                board.push(opponent_move)
                step += 1
        
        gui.close()

        # Handle time out mid-puzzle
        if time.time() > end_time:
            break
        
        if not puzzle_failed:
            score += 1
            streak += 1
            if streak > 0 and streak % 5 == 0:
                end_time += 10.0
                print(f"\n🔥 {streak} STREAK BONUS! +10 Seconds! 🔥")
                
    print(f"\n⏰ Time's up! The Storm is over.")
    print(f"🏆 Final Score: {score}")
    input("Press Enter to return to menu...")              

def play_pgn_analysis(profile):

    import chess.pgn
    import io
    
    print("\n--- 🔍 PGN GAME ANALYSIS ---")
    print("Paste your PGN text below (press Enter twice when done, or type 'quit'):")
    
    lines = []
    while True:
        line = input()
        if line.strip().lower() == 'quit':
            return
        if line == "":
            break
        lines.append(line)
        
    pgn_text = "\n".join(lines)
    if not pgn_text.strip():
        print("❌ No PGN provided.")
        input("\nPress Enter to return...")
        return
        
    try:
        pgn_io = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn_io)
        if not game:
            print("❌ Could not parse PGN. Check your formatting.")
            input("\nPress Enter to return...")
            return
    except Exception as e:
        print(f"❌ PGN Error: {e}")
        input("\nPress Enter to return...")
        return
        
    engine = get_engine()
    if not engine: return
    
    board = game.board()
    print(f"\nAnalyzing game: {game.headers.get('White', 'Player 1')} vs {game.headers.get('Black', 'Player 2')}")
    print("Running evaluation across moves...\n")
    
    move_num = 1
    prev_eval = 0.0
    
    for node in game.mainline():
        move = node.move
        board.push(move)
        
        # Analyze position every move with a fast 0.2s limit
        info = engine.analyse(board, chess.engine.Limit(time=0.2))
        score = info['score'].white().score(mate_score=10000)
        if score is not None:
            current_eval = score / 100.0
        else:
            current_eval = 0.0
            
        eval_diff = current_eval - prev_eval
        
        # If evaluation drops significantly against White/Black perspective
        if board.turn == chess.BLACK and eval_diff < -1.5:
            print(f"⚠️ Move {move_num}: White played {board.san(move)} — Significant drop ({eval_diff:+.2f} pawns)")
        elif board.turn == chess.WHITE and eval_diff > 1.5:
            print(f"⚠️ Move {move_num}: Black played {board.san(move)} — Significant drop ({eval_diff:+.2f} pawns)")
            
        prev_eval = current_eval
        move_num += 1
        
    engine.quit()
    print("\n✅ Analysis complete!")
    input("Press Enter to return to menu...")    

def manage_profile_and_settings(profile):

    print("\n--- ⚙️ ONYX SETTINGS ---")
    print(f"1. Toggle GUI Board Popup (Current: {profile.get('use_gui', False)})")
    print("2. Back to Menu")
    
    choice = input("\nSelect setting: ").strip()
    if choice == '1':
        profile['use_gui'] = not profile.get('use_gui', False)
        print(f"✅ GUI Board toggled to: {profile['use_gui']}")
        input("\nPress Enter...")    


def review_post_game_blunders(game_board, engine, user_color):
    import chess
    from gui import ChessBoardGUI
    
    print("\n🔍 Scanning your game for blunders... (This takes a few seconds)")
    blunders = []
    temp_board = chess.Board()
    
    for move in game_board.move_stack:
        is_user_turn = (temp_board.turn == user_color)
        
        if is_user_turn:
            # 1. Ask Stockfish what the best move WAS before you played
            info_before = engine.analyse(temp_board, chess.engine.Limit(depth=10))
            eval_before = info_before["score"].white().score(mate_score=10000)
            if user_color == chess.BLACK:
                eval_before *= -1
            best_move = info_before.get("pv", [None])[0]
            fen_before = temp_board.fen()
            
        temp_board.push(move)
        
        if is_user_turn:
            # 2. Evaluate the position AFTER your move
            info_after = engine.analyse(temp_board, chess.engine.Limit(depth=10))
            eval_after = info_after["score"].white().score(mate_score=10000)
            if user_color == chess.BLACK:
                eval_after *= -1
            
            # 3. If your evaluation dropped by > 150 centipawns (1.5 pawns), it is a blunder!
            if eval_before - eval_after > 150:
                blunders.append({
                    "fen": fen_before,
                    "played": move,
                    "best": best_move
                })
                
    if not blunders:
        print("\n🎉 Wow! No major blunders detected. You played a masterpiece!")
        return
        
    print(f"\n🛑 Found {len(blunders)} blunders! Launching Retry Mode...")
    
    for i, b in enumerate(blunders):
        practice_board = chess.Board(b["fen"])
        
        # Launch a specialized GUI just for this blunder
        practice_gui = ChessBoardGUI(
            practice_board,
            title=f"Retry Blunder {i+1} of {len(blunders)}",
            flip_board=(user_color == chess.BLACK),
            time_limit=None # No timer while practicing
        )
        
        print(f"\n--- Blunder {i+1}/{len(blunders)} ---")
        print(f"❌ You played: {practice_board.san(b['played'])}")
        print("🧠 What should you have played instead? (Make your move on the board)")
        
        while True:
            practice_gui.draw_board()
            practice_gui.show()
            
            move_str = practice_gui.get_mouse_move()
            
            if move_str.lower() in ['quit', 'exit']:
                practice_gui.close()
                print("\n🚪 Exiting Blunder Review.")
                return
                
            try:
                move = practice_board.parse_san(move_str)
                if move == b["best"]:
                    print("✅ Correct! That is the engine-approved Best Move.")
                    practice_board.push(move)
                    practice_gui.draw_board()
                    practice_gui.close()
                    break # Break out of the while loop to move to the next blunder
                else:
                    print("❌ Not quite! That's not the best move. Try again.")
            except ValueError:
                print("Invalid move. Try again.")    


def play_opening_interrogator(profile):
    """
    Rapid-fire opening drill using openings.json (FEN lookup).
    If you play a move not in the repertoire for the selected category, the line resets!
    """
    import chess
    import time
    import json
    from gui import ChessBoardGUI

    # 1. LOAD REPERTOIRE DATABASE
    try:
        with open("openings.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Could not find openings.json! Run build_repertoire.py first.")
        return

    categories = data.get("categories", [])
    fen_lookup = data.get("fen_lookup", {})

    if not categories:
        print("❌ No training categories found in openings.json!")
        return

    print("\n" + "="*45)
    print("🧠 DYNAMIC OPENING INTERROGATOR 🧠")
    print("="*45)

    print("\nAvailable Categories:")
    for i, cat in enumerate(categories):
        print(f"[{i+1}] {cat}")

    try:
        choice = int(input("\nSelect category to drill (0 to return): ").strip())
        if choice <= 0 or choice > len(categories):
            return
        selected_category = categories[choice - 1]
    except ValueError:
        print("❌ Invalid selection.")
        return

    print(f"\n🎯 Drilling Category: {selected_category}")
    print("Play the correct theory moves. One mistake, and the board resets!")

    board = chess.Board()
    gui = ChessBoardGUI(board, title=f"Interrogator: {selected_category}", is_analysis=True)
    
    attempts = 1
    step = 1

    while not board.is_game_over():
        gui.draw_board()
        gui.populate_history()
        gui.root.update()

        current_fen = board.fen()
        
        # Look up valid repertoire moves for the current board position and category
        cat_entries = [entry for entry in fen_lookup.get(current_fen, []) if entry.get("category") == selected_category]
        valid_uci_moves = [entry["move"] for entry in cat_entries]

        # If no theory moves remain in this branch, the line is completed
        if not valid_uci_moves:
            print(f"\n🎉 Repertoire Line Complete! You mastered this branch in {attempts} attempt(s)!")
            gui.close()
            input("\nPress Enter to continue...")
            return

        print(f"\n--- Attempt #{attempts} | Move {step} ---")
        print("Your move (Play on graphical board, type 'hint' for assistance, or 'quit'):")
        
        user_move_str = gui.get_mouse_move()
        if not user_move_str:
            continue
            
        if user_move_str.lower() == 'quit':
            gui.close()
            return

        if user_move_str.lower() == 'hint':
            hint_uci = valid_uci_moves[0]
            hint_san = board.san(chess.Move.from_uci(hint_uci))
            print(f"💡 HINT: The theory move is {hint_san} ({hint_uci})")
            continue

        clean_move = user_move_str.strip()

        # Verify if player's move is in the repertoire
        if clean_move in valid_uci_moves:
            move_obj = chess.Move.from_uci(clean_move)
            move_san = board.san(move_obj)
            board.push(move_obj)
            print(f"✅ Book move: {move_san}")
            step += 1
        else:
            print("\n❌ INACCURACY! That move is not in the repertoire line.")
            print("🔄 Resetting the board to Move 1...")
            board.reset()
            step = 1
            attempts += 1
            time.sleep(1)
            continue

        # Opponent/Bot reply move from theory
        gui.draw_board()
        gui.populate_history()
        gui.root.update()

        bot_fen = board.fen()
        bot_entries = [entry for entry in fen_lookup.get(bot_fen, []) if entry.get("category") == selected_category]
        bot_uci_moves = [entry["move"] for entry in bot_entries]

        if bot_uci_moves:
            time.sleep(0.3)
            reply_uci = bot_uci_moves[0]
            reply_move = chess.Move.from_uci(reply_uci)
            reply_san = board.san(reply_move)
            board.push(reply_move)
            print(f"🤖 Theory dictates opponent plays: {reply_san}")
            step += 1
        else:
            print(f"\n🎉 Repertoire Line Complete! Opponent has no more book moves in this branch.")
            gui.close()
            input("\nPress Enter to continue...")
            return


def play_endgame_simulator(profile):
    """
    Adaptive Endgame Simulator: Practice critical theoretical conversions.
    """
    import chess
    import chess.engine
    from gui import ChessBoardGUI
    from engine_config import get_engine

    # You can add as many FENs here as you want in the future!
    endgames = {
        "1": {"name": "King & Queen vs King", "fen": "8/8/8/8/8/8/4Q3/K6k w - - 0 1"},
        "2": {"name": "King & Rook vs King", "fen": "8/8/8/8/8/8/4R3/K6k w - - 0 1"},
        "3": {"name": "King & Two Bishops vs King", "fen": "8/8/8/8/8/8/4BB2/K6k w - - 0 1"}
    }

    print("\n" + "="*45)
    print("♟️ ADAPTIVE ENDGAME SIMULATOR ♟️")
    print("="*45)
    for key, data in endgames.items():
        print(f"{key}. {data['name']}")
    print("4. Return")

    choice = input("\nSelect endgame to drill (1-4): ").strip()

    if choice not in endgames:
        return

    drill_name = endgames[choice]["name"]
    start_fen = endgames[choice]["fen"]
    
    print(f"\n🎯 Drilling: {drill_name}")
    print("Convert the advantage! If you blunder the win into a draw, the board will reset.")
    
    # Initialize engine and GUI
    engine = get_engine()
    board = chess.Board(start_fen)
    gui = ChessBoardGUI(board, title=f"Endgame Drill: {drill_name}", is_analysis=True)
    
    attempts = 1
    
    while not board.is_game_over():
        gui.draw_board()
        gui.populate_history()
        gui.root.update()
        
        # Player is always White in these specific drills
        if board.turn == chess.WHITE:
            print(f"\n--- Attempt #{attempts} ---")
            print("Your move: (Play on the graphical board)")
            user_move_str = gui.get_mouse_move()
            
            if user_move_str.lower() == 'quit':
                break
                
            try:
                user_move = chess.Move.from_uci(user_move_str)
                if user_move in board.legal_moves:
                    board.push(user_move)
                    
                    # --- THE STRICT EVALUATOR ---
                    # Check the evaluation instantly after your move
                    info = engine.analyse(board, chess.engine.Limit(depth=10))
                    eval_score = info["score"].white().score(mate_score=1000)
                    
                    # If the score drops to 0 (draw) or goes negative (losing), you failed!
                    if eval_score <= 0:
                        print("\n❌ BLUNDER! You let the forced win slip away.")
                        print("🔄 Resetting the board to the starting position...")
                        board.set_fen(start_fen)
                        attempts += 1
                        gui.board = board # Ensure the GUI points to the fresh board
                else:
                    print("❌ Illegal move. Try again.")
            except ValueError:
                print("❌ Invalid format. Please use the mouse.")
        else:
            print("\n🤖 Stockfish is defending...")
            res = engine.play(board, chess.engine.Limit(time=0.5))
            opp_san = board.san(res.move)
            board.push(res.move)
            print(f"Opponent plays: {opp_san}")

    if board.is_game_over():
        print(f"\n🎉 Drill Complete! You successfully converted {drill_name} in {attempts} attempt(s).")
        print(f"Result: {board.result()}")
    
    gui.close()
    input("\nPress Enter to continue...") 




def manage_opening_repertoire(profile):
    """
    Manage custom opening repertoires, load PGN lines, and inspect saved variations.
    """
    import os
    import chess.pgn

    repertoire_file = "custom_repertoire.pgn"

    while True:
        print("\n" + "="*45)
        print("📁 CUSTOM OPENING REPERTOIRE MANAGER 📁")
        print("="*45)
        print("1. View Saved Repertoire Lines")
        print("2. Import Line from PGN File")
        print("3. Add New Opening Line Manually")
        print("4. Return to Main Menu")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == '1':
            print("\n--- 📖 SAVED REPERTOIRE LINES ---")
            if not os.path.exists(repertoire_file):
                print("❌ No custom repertoire file found yet.")
            else:
                try:
                    with open(repertoire_file, "r") as f:
                        count = 0
                        while True:
                            game = chess.pgn.read_game(f)
                            if game is None:
                                break
                            count += 1
                            print(f"\nLine #{count}: {game.headers.get('Event', 'Custom Line')}")
                            print(f"Moves: {game.mainline_moves()}")
                        if count == 0:
                            print("📁 The repertoire file is empty.")
                except Exception as e:
                    print(f"❌ Error reading file: {e}")
            input("\nPress Enter to continue...")

        elif choice == '2':
            print("\n--- 📥 IMPORT PGN LINE ---")
            path = input("Enter path to your PGN file (e.g., input.pgn): ").strip()
            if os.path.exists(path):
                try:
                    with open(path, "r") as src, open(repertoire_file, "a") as dst:
                        dst.write(src.read() + "\n\n")
                    print("✅ Successfully imported PGN line(s) into your repertoire!")
                except Exception as e:
                    print(f"❌ Error importing file: {e}")
            else:
                print("❌ File not found.")
            input("\nPress Enter to continue...")

        elif choice == '3':
            print("\n--- ✍️ ADD LINE MANUALLY ---")
            name = input("Enter Opening Name (e.g., Sicilian Defense): ").strip()
            moves = input("Enter moves in SAN format separated by spaces (e.g., e4 c5 Nf3 d6): ").strip()
            
            try:
                game = chess.pgn.Game()
                game.headers["Event"] = name
                node = game
                
                board = chess.Board()
                for m_str in moves.split():
                    move = board.parse_san(m_str)
                    node = node.add_variation(move)
                    board.push(move)
                
                with open(repertoire_file, "a") as f:
                    print(game, file=f, end="\n\n")
                print("✅ Successfully saved custom opening line!")
            except Exception as e:
                print(f"❌ Failed to parse moves: {e}")
            input("\nPress Enter to continue...")

        elif choice == '4':
            break
        else:
            print("❌ Invalid choice. Try again.") 

def spar_opening_position(profile):
    """
    Load a wide variety of opening lines, mainlines, and sidelines to spar against Stockfish.
    """
    import chess
    import chess.engine
    from gui import ChessBoardGUI
    from engine_config import get_engine

    # Comprehensive Opening & Sideline Database (FEN representations after key moves)
    opening_database = {
        # --- King's Pawn Openings (1. e4) ---
        "1": {"name": "Sicilian Defense: Najdorf Mainline", "fen": "r1bqk2r/1p2bppp/p1nppn2/8/3NP3/2N1B3/PPP1BPPP/R2Q1R1K w kq - 0 10"},
        "2": {"name": "Sicilian Defense: Dragon (Yugoslav Attack)", "fen": "r1bq1rk1/ppppbpbp/2np1np1/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQ - 3 9"},
        "3": {"name": "Sicilian Defense: Alapin Sideline (2. c3)", "fen": "rnbqkbnr/pp2pppp/3p4/8/3pP3/2P5/PP3PPP/RNBQKBNR w KQkq - 0 4"},
        "4": {"name": "Ruy Lopez: Closed Mainline", "fen": "r1bq1rk1/2p1bppp/p1np1n2/1p2p3/4P3/1B3N2/PPPP1PPP/RNBQR1K1 w - - 0 9"},
        "5": {"name": "Ruy Lopez: Marshall Attack Sideline", "fen": "r1bq1rk1/2p2ppp/p1p2n2/3pp3/4P3/1PN2N2/PPPP1PPP/R1BQR1K1 w - - 0 9"},
        "6": {"name": "French Defense: Winawer Variation", "fen": "r1bqk1nr/pp3ppp/2n1p3/2ppP3/3P4/2P5/P1P2PPP/R1BQKBNR w KQkq - 1 7"},
        "7": {"name": "Caro-Kann Defense: Advance Variation", "fen": "rn1qkbnr/pp2pppp/2p5/3pP3/3P2b1/8/PPP2PPP/RNBQKBNR w KQkq - 1 4"},

        # --- Queen's Pawn Openings (1. d4) ---
        "8": {"name": "Queen's Gambit Declined: Tartakower Line", "fen": "r1bq1rk1/ppp2ppp/2n1pn2/3p4/2PP4/2N2NP1/PP2PPBP/R2Q1RK1 w - - 0 8"},
        "9": {"name": "Queen's Gambit Accepted: Central Sideline", "fen": "rnbqk2r/ppp1bppp/4pn2/8/2PP4/2N5/PP3PPP/R1BQKBNR w KQkq - 1 6"},
        "10": {"name": "King's Indian Defense: Classical Mainline", "fen": "r1bq1rk1/ppp2pbp/2np1np1/4p3/2PPP3/2N1BP2/PP2N1PP/R2QKB1R w KQ - 0 8"},
        "11": {"name": "Nimzo-Indian Defense: Rubinstein Line", "fen": "r1bq1rk1/pp1p1ppp/2n1pn2/2p5/2PP4/2P1PN2/P1Q2PPP/R1B1KB1R w KQ - 1 8"},
        "12": {"name": "London System: Main Line vs 2... Nf6", "fen": "rnbqkb1r/ppp1pppp/5n2/3p4/3P1B2/5N2/PPP1PPPP/RN1QKB1R b KQkq - 3 3"},

        # --- Flank & Notion Repertoire ---
        "13": {"name": "English Opening: Symmetrical Variation", "fen": "r1bqkb1r/pp1ppppp/2n2n2/2p5/2P5/2N2N2/PP1PPPPP/R1BQKB1R w KQkq - 4 4"},
        "14": {"name": "King's Indian Attack (KIA Setup)", "fen": "rnbq1rk1/ppp1ppbp/3p1np1/8/2PPP3/2N2N2/PP2BPPP/R1BQK2R w KQ - 2 7"},
        "15": {"name": "Catalan Opening: Closed Mainline", "fen": "rnbq1rk1/pp2bppp/4pn2/2pp4/2PP4/1PN2N2/P3PPPP/R1BQKB1R w KQ - 0 7"},
        "16": {"name": "Nimzo-Indian: Custom Notion Line", "fen": "r1bq1rk1/pp1p1ppp/2n1pn2/2p5/2PP4/2P1PN2/P1Q2PPP/R1B1KB1R w KQ - 1 8"}
    }

    while True:
        print("\n" + "="*50)
        print("🎯 OPENING & SIDELINE SPARRING HUB 🎯")
        print("="*50)
        print("--- KING'S PAWN (1. e4) ---")
        for k in ["1", "2", "3", "4", "5", "6", "7"]:
            print(f"{k:>2}. {opening_database[k]['name']}")
            
        print("\n--- QUEEN'S PAWN & NOTION REPERTOIRE (1. d4) ---")
        for k in ["8", "9", "10", "11", "12", "15", "16"]:
            print(f"{k:>2}. {opening_database[k]['name']}")
            
        print("\n--- FLANK & OTHER ---")
        for k in ["13", "14"]:
            print(f"{k:>2}. {opening_database[k]['name']}")
            
        print("\n17. Return to Main Menu")

        choice = input("\nSelect opening line to spar (1-17): ").strip()

        if choice == '17' or choice not in opening_database:
            break

        opening_name = opening_database[choice]["name"]
        start_fen = opening_database[choice]["fen"]

        print(f"\n🚀 Loading Position: {opening_name}")
        print("Launching graphical board...")

        engine = get_engine()
        board = chess.Board(start_fen)
        gui = ChessBoardGUI(board, title=f"Sparring: {opening_name}", is_analysis=True)

        while not board.is_game_over():
            gui.draw_board()
            gui.populate_history()
            gui.root.update()

            if board.turn == chess.WHITE:
                print("\nYour turn (Play on the graphical board):")
                user_move_str = gui.get_mouse_move()
                
                if user_move_str.lower() == 'quit':
                    break
                    
                try:
                    user_move = chess.Move.from_uci(user_move_str)
                    if user_move in board.legal_moves:
                        board.push(user_move)
                    else:
                        print("❌ Illegal move. Try again.")
                except ValueError:
                    print("❌ Invalid format. Please use the mouse.")
            else:
                print("\n🤖 Stockfish is responding...")
                res = engine.play(board, chess.engine.Limit(time=1.0))
                bot_san = board.san(res.move)
                board.push(res.move)
                print(f"Opponent plays: {bot_san}")

        print(f"\n🏁 Sparring Session Over! Result: {board.result()}")
        gui.close()
        input("\nPress Enter to return to opening selection...")


def play_game_with_blunder_coach(profile, play_blindfold=False):
    """
    Play a full game against Stockfish equipped with a Real-Time Blunder Coach 
    that detects catastrophic centipawn drops and offers a takeback safety guard.
    """
    import chess
    import chess.engine
    from gui import ChessBoardGUI
    from engine_config import get_engine

    print("\n" + "="*50)
    print("🛡️ BLUNDER COACH MATCH MODE 🛡️")
    print("="*50)
    print("Stockfish is active. If you play a game-losing blunder,")
    print("the Blunder Coach will intercept and offer a takeback!")
    
    engine = get_engine()
    board = chess.Board()
    gui = ChessBoardGUI(board, title="Blunder Coach Protected Match", is_analysis=True)

    while not board.is_game_over():
        gui.draw_board()
        gui.populate_history()
        gui.root.update()

        if board.turn == chess.WHITE:
            print("\nYour turn (Play on board):")
            user_move_str = gui.get_mouse_move()
            
            if user_move_str.lower() == 'quit':
                break
                
            try:
                user_move = chess.Move.from_uci(user_move_str)
                if user_move in board.legal_moves:
                    # Evaluate position before move
                    info_before = engine.analyse(board, chess.engine.Limit(depth=10))
                    score_before = info_before["score"].white().score(mate_score=10000)

                    # Temporarily push move to check evaluation drop
                    board.push(user_move)
                    info_after = engine.analyse(board, chess.engine.Limit(depth=10))
                    score_after = info_after["score"].white().score(mate_score=10000)

                    if score_before is not None and score_after is not None:
                        cp_drop = score_before - score_after
                        # If drop is worse than 250 centipawns (2.5 pawns), trigger Blunder Coach
                       
# Inside play_game_with_blunder_coach...
                        if cp_drop > 250:
                            # GET THE ACTUAL BEST MOVE
                            best_move_info = engine.play(board, chess.engine.Limit(depth=10))
                            best_move_san = board.san(best_move_info.move)
                            
                            print("\n" + "!"*50)
                            print("🚨 BLUNDER COACH ALERT! Catastrophic evaluation drop detected!")
                            print(f"⚠️ You played {board.san(user_move)}, dropping {cp_drop} centipawns!")
                            print("!"*50)
                            
                            # --> NEW: Save to Mistake Deck! <--
                            from utils import save_blunder_to_deck
                            board.pop() # Temporarily pop to get the FEN BEFORE the blunder
                            save_blunder_to_deck(board.fen(), board.san(user_move), best_move_san, cp_drop)
                            board.push(user_move) # Push it back so the board state remains consistent
                            
                            choice = input("Would you like to take back this move? (y/n): ").strip().lower()
                            if choice == 'y':
                                board.pop() # Undo the blunder for real
                                print("🔄 Move retracted. Take your time and recalculate!")
                                continue
                else:
                    print("❌ Illegal move. Try again.")
            except ValueError:
                print("❌ Invalid format. Please use the mouse.")
        else:
            print("\n🤖 Stockfish is thinking...")
            res = engine.play(board, chess.engine.Limit(time=1.0))
            bot_san = board.san(res.move)
            board.push(res.move)
            print(f"Stockfish plays: {bot_san}")

    print(f"\n🏁 Protected Match Over! Result: {board.result()}")
    gui.close()
    input("\nPress Enter to return...")


def play_openings_trainer(profile):
    """
    Interactive Openings Trainer: pick a booked line from openings.json; Stockfish
    plays the booked opponent moves while you play your side's booked moves, then
    keeps playing the game normally once the line is finished.
    """
    import chess
    import chess.engine
    import json
    from gui import ChessBoardGUI
    from engine_config import get_engine

    # --- 1. LOAD THE OPENING REPERTOIRE ---
    try:
        with open("openings.json", "r", encoding="utf-8") as f:
            repertoire = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"\n❌ Could not load openings.json: {e}")
        input("\nPress Enter to return...")
        return

    families = list(repertoire.keys())
    if not families:
        print("\n❌ No opening families found in openings.json.")
        input("\nPress Enter to return...")
        return

    # --- 2. PICK AN OPENING FAMILY ---
    print("\n" + "="*50)
    print("📖 INTERACTIVE OPENINGS TRAINER 📖")
    print("="*50)
    for idx, fam in enumerate(families, 1):
        print(f"{idx}. {fam}")
    print(f"{len(families) + 1}. Return to Main Menu")

    fam_choice = input(f"\nSelect opening family (1-{len(families) + 1}): ").strip()
    if fam_choice == str(len(families) + 1):
        return
    if not fam_choice.isdigit() or int(fam_choice) > len(families):
        print("❌ Invalid choice.")
        input("\nPress Enter to return...")
        return
    family = families[int(fam_choice) - 1]

    # --- 3. PICK A LINE WITHIN THE FAMILY ---
    lines = list(repertoire[family].items())  # [(line_key, {"name", "moves"})]
    print(f"\n--- {family.upper()} LINES ---")
    for idx, (line_key, line_data) in enumerate(lines, 1):
        print(f"{idx}. {line_data.get('name', line_key)}")
    print(f"{len(lines) + 1}. Return to Main Menu")

    line_choice = input(f"\nSelect line (1-{len(lines) + 1}): ").strip()
    if line_choice == str(len(lines) + 1):
        return
    if not line_choice.isdigit() or int(line_choice) > len(lines):
        print("❌ Invalid choice.")
        input("\nPress Enter to return...")
        return

    line_data = lines[int(line_choice) - 1][1]
    opening_name = line_data.get("name", "Custom Line")
    theory_moves = line_data["moves"]
    if not theory_moves:
        print("❌ This line has no moves.")
        input("\nPress Enter to return...")
        return

    # --- 4. CHOOSE WHICH SIDE TO PLAY ---
    print("\nWhich side would you like to play?")
    print("1. White")
    print("2. Black")
    side = input("Select (1-2): ").strip()
    user_color = chess.BLACK if side == '2' else chess.WHITE

    # --- 5. STOCKFISH DIFFICULTY (for the free-play phase after the book) ---
    print("\n--- 🤖 STOCKFISH DIFFICULTY (after the booked line) ---")
    print("1. Beginner (800 ELO)")
    print("2. Intermediate (1500 ELO)")
    print("3. Advanced (2000 ELO)")
    print("4. Master (Max Strength)")
    diff_choice = input("\nSelect level (1-4): ").strip()

    engine = get_engine()
    if not engine:
        print("❌ Stockfish engine could not be loaded!")
        input("\nPress Enter to return...")
        return

    time_limit = 0.5
    try:
        if diff_choice == '1':
            engine.configure({"UCI_LimitStrength": True, "UCI_Elo": 800, "Skill Level": 2})
            time_limit = 0.15
        elif diff_choice == '2':
            engine.configure({"UCI_LimitStrength": True, "UCI_Elo": 1500, "Skill Level": 10})
            time_limit = 0.3
        elif diff_choice == '3':
            engine.configure({"UCI_LimitStrength": False, "Skill Level": 18})
            time_limit = 0.5
        else:
            engine.configure({"UCI_LimitStrength": False, "Skill Level": 20})
            time_limit = 0.6
    except Exception:
        pass

    # --- 6. SETUP BOARD + GRAPHICAL BOARD ---
    board = chess.Board()
    gui = ChessBoardGUI(
        board,
        title=f"Openings Trainer: {opening_name}",
        flip_board=(user_color == chess.BLACK),
        is_analysis=False
    )

    step = 0            # index into theory_moves (plies already played from the book)
    n_book = len(theory_moves)
    side_name = "White" if user_color == chess.WHITE else "Black"

    print(f"\n🎯 Training: {opening_name} — you play {side_name}.")
    print("Play the booked moves. H = hint, Q = quit. After the line, Stockfish continues the game.\n")

    while not board.is_game_over():
        gui.draw_board()
        gui.populate_history()
        gui.root.update()

        in_book = step < n_book

        if in_book:
            # Booked plies alternate White/Black; ply `step` belongs to White when even.
            ply_is_white = (step % 2 == 0)
            is_player_ply = (ply_is_white == (user_color == chess.WHITE))
        else:
            is_player_ply = (board.turn == user_color)

        if is_player_ply:
            # --- USER'S TURN ---
            while True:
                in_book = step < n_book  # recompute each attempt
                move_str = gui.get_mouse_move()

                if move_str.lower() == 'quit':
                    engine.quit()
                    gui.close()
                    return

                if move_str.lower() == 'hint':
                    if in_book:
                        print(f"💡 HINT: The book move is {theory_moves[step]}")
                    else:
                        print("💡 No book move left — we are in free play now.")
                    continue

                if move_str.lower() == 'undo':
                    if len(board.move_stack) >= 2:
                        board.pop()
                        board.pop()
                        if step < n_book:
                            step = max(0, step - 2)
                        print("⏪ Move undone.")
                        gui.draw_board()
                    continue

                try:
                    user_move = board.parse_san(move_str)
                except ValueError:
                    print("❌ Invalid move. Please use the mouse.")
                    continue

                if in_book:
                    try:
                        expected = board.parse_san(theory_moves[step])
                    except ValueError:
                        print("⚠️ The booked line has an invalid move — leaving the book and continuing the game.")
                        step = n_book
                        continue

                    if user_move == expected:
                        print(f"✅ Book move! ({move_str})")
                        board.push(user_move)
                        step += 1
                        break
                    else:
                        print(f"❌ That is not the booked line. Expected: {theory_moves[step]}")
                        deviate = input("Play this move anyway and leave the book? (y/n): ").strip().lower()
                        if deviate == 'y':
                            board.push(user_move)
                            step = n_book  # end the book; Stockfish continues from here
                            print("🔄 Book ended early — Stockfish continues the game.")
                            break
                        # otherwise retry the move
                else:
                    if user_move in board.legal_moves:
                        board.push(user_move)
                        break
                    else:
                        print("❌ Illegal move. Please use the mouse.")
        else:
            # --- STOCKFISH'S TURN ---
            if in_book:
                try:
                    book_move = board.parse_san(theory_moves[step])
                    book_san = board.san(book_move)  # SAN must be computed before the push
                except ValueError:
                    print("\n⚠️ The booked line has an invalid move — Stockfish continues freely from here.")
                    step = n_book
                else:
                    board.push(book_move)
                    print(f"\n🤖 Stockfish plays booked move: {book_san}")
                    step += 1
            else:
                print("\n🤖 Stockfish is thinking...")
                res = engine.play(board, chess.engine.Limit(time=time_limit))
                bot_san = board.san(res.move)  # SAN must be computed before the push
                board.push(res.move)
                print(f"Stockfish plays: {bot_san}")

    # --- GAME OVER ---
    print(f"\n🏁 Game Over! Result: {board.result()}")
    print(f"🎓 Completed the {opening_name} line ({n_book} plies of booked theory).")
    gui.close()
    engine.quit()
    input("\nPress Enter to return to menu...")


def _annotate_opening_move(board, move):
    """Return a short coaching annotation for a move (called BEFORE it is pushed)."""
    if board.is_castling(move):
        return "King safety — tuck the king away and connect the rooks."
    if board.is_capture(move):
        return "Capture — removes an enemy unit and simplifies the position."
    piece = board.piece_at(move.from_square)
    if piece is None:
        return "Move played."
    pt = piece.piece_type
    if pt == chess.PAWN:
        if move.to_square in (chess.D4, chess.E4, chess.D5, chess.E5):
            return "Pawn gains central space."
        return "Pawn move — establishing healthy structure."
    if pt == chess.KNIGHT:
        return "Develops a knight toward the center."
    if pt == chess.BISHOP:
        return "Develops the bishop to an active diagonal."
    if pt == chess.QUEEN:
        return "Queen steps out early — keep it safe from attack."
    if pt == chess.ROOK:
        return "Rook activation / centralizes the heavy piece."
    if pt == chess.KING:
        return "King safety — shelter the monarch."
    return "Good developing move."


def opening_study_and_drill(profile):
    """
    Ultimate Opening Coach — sub-option 1. Study a booked line move-by-move with
    annotations, then drill it: replay the line from memory with guided feedback.
    """
    import chess
    import json
    from gui import ChessBoardGUI

    try:
        with open("openings.json", "r", encoding="utf-8") as f:
            repertoire = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"\n❌ Could not load openings.json: {e}")
        input("\nPress Enter to return...")
        return

    families = list(repertoire.keys())
    if not families:
        print("\n❌ No opening families found in openings.json.")
        input("\nPress Enter to return...")
        return

    print("\n--- 📚 STUDY & DRILL LINES ---")
    for i, fam in enumerate(families, 1):
        print(f"{i}. {fam}")
    print(f"{len(families) + 1}. Return")
    fam_choice = input(f"\nSelect opening family (1-{len(families) + 1}): ").strip()
    if fam_choice == str(len(families) + 1):
        return
    if not fam_choice.isdigit() or int(fam_choice) > len(families):
        print("❌ Invalid choice.")
        return
    family = families[int(fam_choice) - 1]

    lines = list(repertoire[family].items())
    print(f"\n--- {family.upper()} LINES ---")
    for i, (lk, ld) in enumerate(lines, 1):
        print(f"{i}. {ld.get('name', lk)}")
    print(f"{len(lines) + 1}. Return")
    line_choice = input(f"\nSelect line (1-{len(lines) + 1}): ").strip()
    if line_choice == str(len(lines) + 1):
        return
    if not line_choice.isdigit() or int(line_choice) > len(lines):
        print("❌ Invalid choice.")
        return
    opening_name = lines[int(line_choice) - 1][1].get("name", "Custom Line")
    theory_moves = lines[int(line_choice) - 1][1]["moves"]
    if not theory_moves:
        print("❌ This line has no moves.")
        input("\nPress Enter to return...")
        return

    print("\nWhich side would you like to drill?")
    print("1. White")
    print("2. Black")
    side = input("Select (1-2): ").strip()
    user_color = chess.BLACK if side == '2' else chess.WHITE

    while True:
        print(f"\n--- 🎓 STUDY & DRILL: {opening_name} ---")
        print("1. 📖 Study the line (guided replay with annotations)")
        print("2. 🎯 Drill the line (play it from memory)")
        print("3. Return to Ultimate Opening Coach")
        choice = input("\nSelect an option (1-3): ").strip()

        if choice == '1':
            board = chess.Board()
            gui = ChessBoardGUI(board, title=f"Study: {opening_name}", is_analysis=False)
            gui.draw_board()
            gui.populate_history()
            gui.root.update()
            print(f"\n📖 STUDY MODE: {opening_name}")
            print("The line plays out move by move. Press Enter to advance.")
            for idx, san in enumerate(theory_moves):
                try:
                    mv = board.parse_san(san)
                except ValueError:
                    print(f"\n⚠️ Invalid move in line data at ply {idx + 1} — stopping.")
                    break
                san_str = board.san(mv)
                note = _annotate_opening_move(board, mv)
                board.push(mv)
                gui.draw_board()
                gui.populate_history()
                gui.root.update()
                side_name = "White" if idx % 2 == 0 else "Black"
                print(f"\n{side_name} {idx // 2 + 1}: {san_str}  —  {note}")
                input("Press Enter to continue...")
            print("\n✅ Study complete.")
            gui.close()
            input("\nPress Enter to return...")

        elif choice == '2':
            board = chess.Board()
            gui = ChessBoardGUI(board, title=f"Drill: {opening_name}", is_analysis=False)
            gui.draw_board()
            gui.populate_history()
            gui.root.update()
            step = 0
            n_book = len(theory_moves)
            attempts = 1
            completed = False
            print(f"\n🎯 DRILL MODE: {opening_name} — you play {'White' if user_color == chess.WHITE else 'Black'}.")
            print("Play each booked move. H = hint, Q = quit. A wrong move resets the line!")
            while step < n_book:
                gui.draw_board()
                gui.populate_history()
                gui.root.update()
                ply_is_white = (step % 2 == 0)
                if (ply_is_white == (user_color == chess.WHITE)):
                    move_str = gui.get_mouse_move()
                    if move_str.lower() == 'quit':
                        break
                    if move_str.lower() == 'hint':
                        print(f"💡 HINT: The book move is {theory_moves[step]}")
                        continue
                    try:
                        user_move = board.parse_san(move_str)
                    except ValueError:
                        print("❌ Invalid move. Please use the mouse.")
                        continue
                    try:
                        expected = board.parse_san(theory_moves[step])
                    except ValueError:
                        print("⚠️ Book data error at this ply — ending drill.")
                        break
                    if user_move == expected:
                        san_str = board.san(user_move)
                        note = _annotate_opening_move(board, user_move)
                        board.push(user_move)
                        step += 1
                        print(f"✅ {san_str}  —  {note}")
                    else:
                        print(f"❌ Wrong! The book move is {theory_moves[step]}. Resetting the line...")
                        board.reset()
                        step = 0
                        attempts += 1
                        gui.draw_board()
                else:
                    try:
                        opp = board.parse_san(theory_moves[step])
                        board.push(opp)
                    except ValueError:
                        print("⚠️ Book data error at this ply — ending drill.")
                        break
                    step += 1
            else:
                completed = True
            gui.close()
            if completed:
                print(f"\n🎉 Drill complete! You nailed {opening_name} in {attempts} attempt(s).")
            else:
                print("\nDrill exited early.")
            input("\nPress Enter to return...")

        elif choice == '3':
            return
        else:
            print("❌ Invalid choice.")


def spar_against_opening(profile):
    """
    Ultimate Opening Coach — sub-option 2. Pick a booked line or a sideline
    position and play against Stockfish, leading straight into a full game.
    """
    while True:
        print("\n--- 🥊 SPAR AGAINST OPENING ---")
        print("1. Booked line from your repertoire (openings.json)")
        print("2. Sideline position (FEN library)")
        print("3. Return to Ultimate Opening Coach")
        choice = input("\nSelect an option (1-3): ").strip()
        if choice == '1':
            play_openings_trainer(profile)
        elif choice == '2':
            spar_opening_position(profile)
        elif choice == '3':
            return
        else:
            print("❌ Invalid choice.")


def ultimate_opening_coach(profile):
    """
    The unified opening hub: study & drill lines, spar against booked lines and
    sidelines, quiz your repertoire, or manage it — all from one menu entry.
    """
    while True:
        print("\n" + "="*50)
        print("🎓 ULTIMATE OPENING COACH 🎓")
        print("="*50)
        print("1. 📖 Study & Drill Lines")
        print("2. 🥊 Spar Against Opening")
        print("3. 📝 Repertoire Quiz")
        print("4. 🗂️ Manage Repertoire")
        print("5. Return to Main Menu")
        choice = input("\nSelect an option (1-5): ").strip()
        if choice == '1':
            opening_study_and_drill(profile)
        elif choice == '2':
            spar_against_opening(profile)
        elif choice == '3':
            from training_modes import play_repertoire_quiz
            play_repertoire_quiz(profile)
        elif choice == '4':
            manage_opening_repertoire(profile)
        elif choice == '5':
            return
        else:
            print("❌ Invalid choice.")


def play_human_sparring_bot(profile, active_category=None):
    """
    Simulates a human-like sparring match against a customized engine depth or evaluation profile.
    """
    import chess
    from gui import ChessBoardGUI

    print("\n" + "="*50)
    print("🤖 HUMAN SPARRING BOT MODE 🤖")
    print("="*50)

    board = chess.Board()
    gui = ChessBoardGUI(board, title="Onyx Sparring Bot", is_analysis=False)

    print("\nMatch started! Make your move on the graphical board.")

    while not board.is_game_over():
        gui.draw_board()
        gui.root.update()

        user_move_str = gui.get_mouse_move()
        if user_move_str.lower() == 'quit':
            break

        try:
            # Clean the string of any hidden spaces or weird formatting
            clean_move_str = str(user_move_str).strip()
            move = chess.Move.from_uci(clean_move_str)
            
            if move in board.legal_moves:
                move_name = board.san(move)
                board.push(move)
                print(f"Your move: {move_name}")
            else:
                print("❌ Illegal move! Try again.")
                continue
        except Exception as e:
            # If it still fails, print the exact error so we know why
            print(f"❌ Could not parse '{user_move_str}': {e}")
            continue

        if board.is_game_over():
            break

    # Let Onyx calculate the best move (or pull from our training JSON)
        # Force the GUI to update visually before the engine freezes to think
        gui.draw_board()
        gui.root.update()
        
        try:
            from main import get_best_move_time_limited
            print("⏳ Engine is thinking...") 
            
            bot_move = get_best_move_time_limited(board, 1.0, active_category)
            
            if bot_move:
                bot_move_name = board.san(bot_move)
                board.push(bot_move)
                print(f"🤖 Bot plays: {bot_move_name}")
                
                # If your GUI has a history updater, it would go here later
                # gui.update_move_history()
            else:
                print("🤖 Bot returned no move! Is the FEN missing?")
                
        except Exception as e:
            print(f"⚠️ Engine Error Caught: {e}")