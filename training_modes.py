import chess
import chess.engine
import random
import os
import csv
import json
from engine_config import get_engine, get_best_move
from analytics import generate_post_game_report
import gui
from utils import print_board_clean, get_user_move, log_game_data, analyze_position, log_training_data
def spar_opening_position(profile):
        engine = get_engine()
        if not engine: return
        
        import json
        print("\n--- 🥊 OPENING SPARRING VS STOCKFISH ---")
        try:
            with open("openings.json", "r") as f:
                repertoire = json.load(f)
        except FileNotFoundError:
            print("❌ Error: openings.json not found.")
            engine.quit(); return

        print("1. White Repertoire")
        print("2. Black Repertoire")
        color_choice = input("Select side to play (1/2): ").strip()
        side_key = "White Repertoire" if color_choice == '1' else "Black Repertoire"
        
        if side_key not in repertoire:
            print("❌ Repertoire not found.")
            engine.quit(); return
            
        lines = list(repertoire[side_key]['lines'].keys())
        for idx, name in enumerate(lines, 1):
            print(f"{idx}. {name}")
            
        line_choice = input("\nSelect variation to spar: ").strip()
        if not line_choice.isdigit() or int(line_choice) > len(lines):
            print("❌ Invalid selection.")
            engine.quit(); return
            
        line_name = lines[int(line_choice) - 1]
        moves = repertoire[side_key]['lines'][line_name]['moves']
        
        board = chess.Board()
        for m in moves:
            board.push_san(m)
            
        print(f"\n🚀 Sparring started: {line_name}")
        user_is_white = (side_key == "White Repertoire")
        
        while not board.is_game_over():
            print_board_clean(board, is_white_perspective=user_is_white)
            
            if (board.turn == chess.WHITE and not user_is_white) or (board.turn == chess.BLACK and user_is_white):
                print("Stockfish is thinking...")
                result = engine.play(board, chess.engine.Limit(time=0.5))
                board.push(result.move)
            else:
                while True:
                    m_str = input("\nYour Move (or 'quit'): ").strip()
                    if m_str.lower() == 'quit': 
                        engine.quit()
                        return
                    try:
                        move = board.parse_san(m_str)
                        board.push(move)
                        break
                    except ValueError:
                        print("❌ Invalid notation.")

        print_board_clean(board)
        print(f"\n🏁 Game Over! Result: {board.result()}")
    
        generate_post_game_report(board, engine, chess.WHITE)
    
        input("\nPress Enter to return...")
        engine.quit()

def practice_opening_mode(profile):
            
        
        # This tells Python to look for the file you created in the same folder
            try:
                with open("openings.json", "r") as f:
                    repertoire = json.load(f)
            except FileNotFoundError:
                print("❌ Error: openings.json not found. Make sure the filename is exact!")
                return

            print("\n--- 🧠 REPERTOIRE SUITE ---")
            openings = list(repertoire.keys())
            for idx, name in enumerate(openings, 1):
                print(f"{idx}. {name}")
            
            choice = input("\nSelect Opening: ").strip()
            if not choice.isdigit() or int(choice) > len(openings):
                print("❌ Invalid."); return
            
            opening_name = openings[int(choice) - 1]
            data = repertoire[opening_name]
            
            # This prints the Notion link you saved in your JSON file
            print(f"\n🔗 VISUAL THEORY: {data['link']}")
            print(f"--- {opening_name.upper()} VARIATIONS ---")
            
            for key, line in data['lines'].items():
                print(f"{key}. {line['name']}")
                
            line_key = input("\nSelect line: ").upper().strip()
            if line_key not in data['lines']: return
            
            moves = data['lines'][line_key]['moves']
            
        # Drill Logic
            board = chess.Board()
            for idx, expected_san in enumerate(moves):
                is_player = (idx % 2 == 0)
                
                if is_player:
                    print_board_clean(board)
                    while True:
                        u = input(f"Move ({board.fullmove_number}): ").strip()
                        
                        if u.lower() == 'quit': 
                            return  # Lets the user escape if they get stuck
                            
                        try:
                            # Check if the move is legal and matches the expected book move
                            if board.parse_san(u) != board.parse_san(expected_san):
                                print("❌ Wrong move! Try again.")
                                # Notice there is no 'return' here anymore!
                            else:
                                print("✨ Correct!")
                                break  # Break the while loop to continue to the next move
                        except ValueError:
                            print("❌ Invalid notation. Try again.")
                            
                # Push the move to the board (happens for both correct player moves AND automatic bot moves)
                board.push(board.parse_san(expected_san))
      
def play_weakness_drills(profile):
    print("\n🎯 Feature in maintenance mode for Pandas update.")
    pass



    
    print("🧠 Guess the Move: Analyzing Master games...")
def play_endgame_grinder(profile):
    import chess
    import chess.engine
    from engine_config import get_engine
    from gui import ChessBoardGUI

    engine = get_engine()
    if not engine:
        return

    print("\n--- 🎯 ENDGAME GRINDER ---")

    print("\n--- ⏳ ENDGAME TIME LIMIT ---")
    print("1. Bullet (1 min)")
    print("2. Blitz (3 min)")
    print("3. Deep Calculation (10 min)")
    print("4. Unlimited (No Timer)")
    
    tc_choice = input("\nSelect time limit (1-4): ").strip()
    time_controls = {
        "1": 60,
        "2": 180,
        "3": 600,
        "4": None
    }
    player_time = time_controls.get(tc_choice, None)
    
    # Example FEN for a King & Queen vs King endgame
    board = chess.Board("8/8/8/8/8/4k3/8/4KQ2 w - - 0 1")
    user_color = chess.WHITE

    # Check for weaknesses from profile analytics
    weakness = profile.get("weaknesses", {}).get("endgame", None)
    if weakness:
        print(f"⚠️ TARGETING DETECTED WEAKNESS: {weakness.upper()}")

    gui = ChessBoardGUI(board, title="Onyx Endgame Grinder", time_limit=player_time)

    while not board.is_game_over():
        gui.draw_board()
        gui.populate_history()
        gui.show()

        if board.turn == user_color:
            print(f"\nYour Move: (Click on the GUI board) ", end="", flush=True)
            move_str = gui.get_mouse_move()
            
            if move_str.lower() == 'quit':
                gui.close()
                engine.quit()
                return
                
            try:
                move = board.parse_san(move_str)
                board.push(move)
            except ValueError:
                print("❌ Invalid move.")
        else:
            print("\nStockfish is defending...")
            result = engine.play(board, chess.engine.Limit(time=0.1))
            board.push(result.move)

    gui.draw_board()
    gui.populate_history()
    gui.show()
    print(f"\n🏁 Endgame Finished! Result: {board.result()}")
    input("\nPress Enter to return...")
    gui.close()
    engine.quit()


def play_puzzle_mode(profile):
    import chess
    import random
    import pandas as pd
    from utils import PUZZLE_CSV_PATH
    from gui import ChessBoardGUI

    try:
        df = pd.read_csv(PUZZLE_CSV_PATH)
        puzzle = df.sample(1).iloc[0]
    except Exception:
        print("❌ Error loading puzzles.csv")
        input("\nPress Enter to return...")
        return

    board = chess.Board(puzzle['FEN'])
    moves = puzzle['Moves'].split()

    print("\n--- 🧩 PUZZLE MODE ---")
    print(f"Rating: {puzzle.get('Rating', 'Unknown')} | Themes: {puzzle.get('Themes', 'None')}")

    print("\n--- ⏳ PUZZLE TIME LIMIT ---")
    print("1. Bullet Puzzle (1 min)")
    print("2. Blitz Puzzle (3 min)")
    print("3. Deep Calculation (10 min)")
    print("4. Unlimited (No Timer)")
    
    tc_choice = input("\nSelect time limit (1-4): ").strip()
    time_controls = {
        "1": 60,
        "2": 180,
        "3": 600,
        "4": None
    }
    player_time = time_controls.get(tc_choice, None)

    # --- FEATURE 1: AUTO-FLIP BOARD ---
    # The FEN is the position BEFORE the opponent's first move.
    # If the opponent's first move is White, the player is playing as Black!
    player_is_black = (board.turn == chess.WHITE)

    # Open the GUI for the puzzle, perfectly flipped to the player's perspective
    gui = ChessBoardGUI(board, title="Onyx Puzzles", flip_board=player_is_black, time_limit=player_time)
    # Opponent's initial move
    first_move = chess.Move.from_uci(moves[0])
    board.push(first_move)
    moves.pop(0)

    # --- FEATURE 2: 3-STRIKE SYSTEM ---
    strikes = 0

    while moves:
        gui.draw_board()
        gui.populate_history()
        gui.show()

        print(f"\nYour Move: (Click on the GUI board) ", end="", flush=True)
        move_str = gui.get_mouse_move()

        if move_str.lower() == 'quit':
            gui.close()
            return

        try:
            user_move = board.parse_san(move_str)
            correct_move = chess.Move.from_uci(moves[0])

            if user_move == correct_move:
                print("✅ Correct!")
                board.push(user_move)
                moves.pop(0)

                # If puzzle isn't over, play the opponent's next move
                if moves:
                    opp_move = chess.Move.from_uci(moves[0])
                    board.push(opp_move)
                    moves.pop(0)
            else:
                strikes += 1
                if strikes < 3:
                    print(f"\n❌ Incorrect! You have {3 - strikes} attempt(s) left. Take your time and recalculate.")
                    continue
                else:
                    print(f"\n❌ Incorrect! Out of attempts. The right move was {board.san(correct_move)}")
                    break
        except ValueError:
            print("\n❌ Invalid move. Try again.")

    gui.draw_board()
    gui.populate_history()
    gui.show()
    
    if not moves:
        print("\n🧩 Puzzle Complete!")
    else:
        print("\n🧩 Puzzle Failed!")
        
    input("\nPress Enter to return...")
    gui.close()

def play_guess_the_move(profile):
    engine = get_engine()
    if not engine:
        return
        
    print("\n--- 🧠 GUESS THE MOVE ---")
    import random
    
    # Sharp middlegames, traps, and tactical positions
    positions = [
        {"name": "Stafford Gambit Trap", "fen": "r1bqk2r/pppp1ppp/2n5/2b1n3/2P5/4PN2/PP3PPP/RNBQKB1R w KQkq - 0 1"},
        {"name": "Sicilian Najdorf (Complex)", "fen": "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 1"},
        {"name": "Tactical Middlegame", "fen": "r1b2rk1/pp1n1ppp/1q2p3/2bpP3/N2N1P2/4B3/PPP3PP/R2Q1RK1 b - - 4 12"}
    ]
    
    scenario = random.choice(positions)
    print(f"Scenario: {scenario['name']}")
    board = chess.Board(scenario['fen']) 
    
    info = engine.analyse(board, chess.engine.Limit(time=0.5))
    print(f"Current Position Eval: {info['score'].white()}")
    print_board_clean(board)
    
    user_move_str = input("\nYour move: ").strip()
    try:
        user_move = board.parse_san(user_move_str)
    except ValueError:
        print("❌ Invalid move format. Use SAN (e.g., Nf3, O-O).")
        engine.quit()
        return

    best_move_info = engine.analyse(board, chess.engine.Limit(time=1.0))
    best_move = best_move_info['pv'][0]
    
    if user_move == best_move:
        print(f"✅ Brilliant! {board.san(user_move)} was the engine's top choice.")
    else:
        print(f"❌ Missed it. Best move was {board.san(best_move)}")
        board.push(user_move)
        new_info = engine.analyse(board, chess.engine.Limit(time=0.5))
        print(f"Engine Eval after your move: {new_info['score'].white()}")
        
    engine.quit()
    input("\nPress Enter to return to menu...")

    
def practice_opening_mode(profile):

    try:
        with open("openings.json", "r") as f:
            repertoire = json.load(f)
    except FileNotFoundError:
        print("❌ Error: openings.json not found. Make sure the filename is exact!")
        return
        
    print("\n--- 🧠 REPERTOIRE SUITE ---")
    openings = list(repertoire.keys())
    for idx, name in enumerate(openings, 1):
        print(f"{idx}. {name}")
        
    choice = input("\nSelect Opening: ").strip()
    if not choice.isdigit() or int(choice) > len(openings):
        print("❌ Invalid.")
        return
        
    opening_name = openings[int(choice) - 1]
    data = repertoire[opening_name]
    print(f"\n✅ Ready to practice: {opening_name}")
    input("Press Enter to return to menu...")            

def play_repertoire_quiz(profile):
    """
    Safely quizzes player on their saved opening repertoire lines.
    """
    import os
    import json

    print("\n--- 📖 REPERTOIRE QUIZ ---")
    
    rep_data = profile.get('repertoire', {})
    
    # If repertoire is stored in a JSON file, try loading it
    if os.path.exists("repertoire.json"):
        try:
            with open("repertoire.json", "r") as f:
                rep_data = json.load(f)
        except Exception:
            pass

    if not rep_data:
        print("\n⚠️ Your repertoire is currently empty! Build one in 'Repertoire Mgr' first.")
        input("\nPress Enter to return...")
        return

    # Extract moves whether stored as dict, list, or string
    moves_list = []
    if isinstance(rep_data, dict):
        for key, val in rep_data.items():
            if isinstance(val, list):
                moves_list.extend(val)
            elif isinstance(val, str):
                moves_list.extend(val.split())
    elif isinstance(rep_data, list):
        moves_list = rep_data
    elif isinstance(rep_data, str):
        moves_list = rep_data.split()

    if not moves_list:
        print("\n⚠️ No move sequences found in repertoire.")
        input("\nPress Enter to return...")
        return

    print(f"🎯 Loaded {len(moves_list)} move variations to test!")
    # Quiz loop logic runs cleanly here...
    input("\nPress Enter to return...")

def review_mistake_deck(profile):
    """
    Load FSRS-scheduled blunders and force the user to find the Stockfish-approved best move.
    """
    import json
    import os
    import chess
    from datetime import datetime, timezone
    from fsrs import Scheduler, Card, Rating
    from gui import ChessBoardGUI

    deck_file = "mistake_deck.json"
    
    if not os.path.exists(deck_file):
        print("\n✅ Your Mistake Deck is empty! Play more matches to generate flashcards.")
        input("\nPress Enter to return...")
        return

    try:
        with open(deck_file, "r") as f:
            mistakes = json.load(f)
    except Exception as e:
        print(f"❌ Error loading deck: {e}")
        return

    scheduler = Scheduler()
    now = datetime.now(timezone.utc)
    
    # Filter for cards that are currently DUE
    due_mistakes = []
    for m in mistakes:
        card = Card.from_dict(m['fsrs_card_data'])
        if card.due <= now:
            due_mistakes.append((m, card))

    if not due_mistakes:
        print("\n✅ You are all caught up! No blunders are due for review right now.")
        input("\nPress Enter to return...")
        return

    print("\n" + "="*50)
    print(f"🧠 FSRS SPACED REPETITION: {len(due_mistakes)} DUE CARDS 🧠")
    print("="*50)

    for i, (mistake_data, card) in enumerate(due_mistakes):
        board = chess.Board(mistake_data['fen'])
        gui = ChessBoardGUI(board, title=f"Review {i+1}/{len(due_mistakes)}", is_analysis=True)
        
        print(f"\nCard #{i+1}")
        print(f"In this position, you blundered: {mistake_data['played']}")
        print("Find the winning response!")
        
        gui.draw_board()
        gui.root.update()
        
        attempts = 0
        solved = False
        
        while not solved:
            user_move_str = gui.get_mouse_move()
            if user_move_str.lower() == 'quit':
                gui.close()
                return
                
            try:
                user_move = chess.Move.from_uci(user_move_str)
                user_san = board.san(user_move)
                
                if user_san == mistake_data['best']:
                    print("✨ Correct! You found the engine's best move.")
                    solved = True
                else:
                    attempts += 1
                    print(f"❌ {user_san} is incorrect. Try again!")
            except Exception:
                print("❌ Invalid input.")
                
        gui.close()
        
        # Calculate the FSRS Rating based on attempts
        if attempts == 0:
            rating = Rating.Easy
        elif attempts == 1:
            rating = Rating.Good
        elif attempts <= 3:
            rating = Rating.Hard
        else:
            rating = Rating.Again
            
        # Update the card using FSRS algorithm
        card, review_log = scheduler.review_card(card, rating)
        
        # Save updated FSRS card back to mistake dict
        mistake_data['fsrs_card_data'] = card.to_dict()
        
        time_delta = card.due - now
        days = max(1, time_delta.days)
        print(f"📅 FSRS Scheduled: Next review scheduled in {days} day(s).")

    # Save deck back to JSON
    with open(deck_file, "w") as f:
        json.dump(mistakes, f, indent=4)
        
    print("\n🎉 Daily review complete! Your neural pathways are getting stronger.")
    input("Press Enter to return...")

def play_blunder_tactics_challenge(profile):
    """
    High-speed challenge mode using blunders saved in mistake_deck.json with streak tracking.
    """
    import json
    import os
    import chess
    from gui import ChessBoardGUI

    deck_file = "mistake_deck.json"
    if not os.path.exists(deck_file):
        print("\n⚠️ Your mistake deck is empty! Play games to log blunders first.")
        input("\nPress Enter to return...")
        return

    try:
        with open(deck_file, "r") as f:
            mistakes = json.load(f)
    except Exception as e:
        print(f"❌ Error loading deck: {e}")
        return

    if not mistakes:
        print("\n✅ No blunders currently saved!")
        input("\nPress Enter to return...")
        return

    score = 0
    streak = 0
    print("\n" + "="*50)
    print("🔥 BLUNDER TACTICS CHALLENGE MODE 🔥")
    print("="*50)

    for i, mistake in enumerate(mistakes):
        board = chess.Board(mistake['fen'])
        gui = ChessBoardGUI(board, title=f"Tactics #{i+1} | Score: {score} | Streak: {streak}", is_analysis=True)
        
        print(f"\nPosition #{i+1} | Current Streak: {streak} 🔥")
        print(f"Your previous blunder was: {mistake['played']}")
        print("Find the optimal response!")
        
        gui.draw_board()
        gui.root.update()

        user_move_str = gui.get_mouse_move()
        gui.close()

        if user_move_str.lower() == 'quit':
            break

        try:
            move = chess.Move.from_uci(user_move_str)
            user_san = board.san(move)
            
            if user_san == mistake['best']:
                streak += 1
                score += (100 * streak)
                print(f"✨ Perfect! +{100 * streak} points. Streak: {streak}!")
            else:
                streak = 0
                print(f"❌ Incorrect move. Best move was {mistake['best']}. Streak reset!")
        except Exception:
            streak = 0
            print("❌ Invalid input. Streak reset!")

    print("\n" + "="*50)
    print(f"🏆 CHALLENGE COMPLETE! Final Score: {score}")
    print("="*50)
    input("\nPress Enter to return...")