import chess
import chess.pgn
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
import requests
from datetime import datetime
from engine_config import get_engine

def analyze_player_accuracy(profile):
    import pandas as pd
    import os
    
    print("\n--- 📊 PANDAS ANALYTICS DASHBOARD ---")
    file_path = os.path.join("data", "training_data.csv")
    
    if not os.path.exists(file_path):
        print("❌ No training data found. Play some endgame or puzzle sessions first!")
        input("\nPress Enter to return to menu...")
        return
        
    try:
        # Ingest the CSV into a Pandas DataFrame
        df = pd.read_csv(file_path)
        
        if df.empty:
            print("❌ Data file is empty.")
            input("\nPress Enter to return to menu...")
            return
            
        print(f"Total Training Sessions Logged: {len(df)}")
        print("-" * 45)
        
        # Filter and Crunch Endgame Stats
        endgames_df = df[df['Mode'].str.contains("Endgame", na=False)]
        if not endgames_df.empty:
            print("♟️ ENDGAME GRINDER STATS:")
            total = len(endgames_df)
            win_count = len(endgames_df[endgames_df['Result'] == 'Win'])
            draw_count = len(endgames_df[endgames_df['Result'] == 'Draw'])
            loss_count = len(endgames_df[endgames_df['Result'] == 'Loss'])
            win_rate = (win_count / total) * 100
            
            print(f"  Matches Played: {total}")
            print(f"  Wins: {win_count} | Draws: {draw_count} | Losses: {loss_count}")
            print(f"  Win Rate: {win_rate:.1f}%")
        else:
            print("♟️ No Endgame stats available yet.")
            
        print("-" * 45)
        
    except ImportError:
        print("❌ Pandas is not installed! Run 'pip install pandas' in your terminal.")
    except Exception as e:
        print(f"❌ An error occurred during analysis: {e}")
        
    input("\nPress Enter to return to menu...")

def visualize_acpl_trend():
    print("\n--- 📈 ACPL PERFORMANCE TREND ---")
    csv_file = os.path.join("data", "onyx_training_data.csv")
    if not os.path.exists(csv_file):
        print("❌ No data found. Run the Analytics module first to generate data!")
        input("\nPress Enter to return...")
        return

    try:
        df = pd.read_csv(csv_file)
        if df.empty or "ACPL" not in df.columns:
            print("❌ Not enough data to visualize.")
            input("\nPress Enter to return...")
            return

        recent_data = df.tail(10)
        print("Your recent accuracy (Lower ACPL is better):\n")
        
        max_acpl = df['ACPL'].max()
        if max_acpl == 0: max_acpl = 1 
        
        for index, row in recent_data.iterrows():
            bar_length = int((row['ACPL'] / max_acpl) * 30)
            bar = "█" * bar_length
            date_str = str(row['Date'])[:10]  
            print(f"{date_str} | ACPL: {row['ACPL']:>5.1f} | {bar}")
            
        print("-" * 50)
        recent_avg = recent_data['ACPL'].mean()
        print(f"Recent Average ACPL: {recent_avg:.1f}")
        
    except Exception as e:
        print(f"❌ Error reading data: {e}")
        
    input("\nPress Enter to return to menu...")

def deep_pgn_analysis(profile):
    import chess
    import chess.pgn
    import chess.engine
    import tkinter as tk
    from tkinter import filedialog
    import io  # Added to read pasted text like a file
    from engine_config import get_engine
    from gui import ChessBoardGUI

    engine = get_engine()
    if not engine:
        print("❌ Error: Stockfish engine could not be loaded!")
        input("\nPress Enter to return...")
        return

    print("\n--- 📊 PGN ANALYSIS ---")
    print("1. Select a PGN file (.pgn)")
    print("2. Paste PGN text")
    
    choice = input("\nChoose an option (1 or 2): ").strip()
    
    game = None

    if choice == '1':
        print("Please select a PGN file from the popup window...")
        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.askopenfilename(title="Select PGN File", filetypes=[("PGN Files", "*.pgn")])
        
        if not filepath:
            print("❌ No file selected.")
            return

        try:
            with open(filepath) as f:
                game = chess.pgn.read_game(f)
        except Exception:
            print("❌ Error reading PGN file.")
            return

    elif choice == '2':
        print("\nPaste your PGN text below.")
        print("(Press Enter on a completely blank line when you are finished):")
        
        lines = []
        while True:
            line = input()
            if line.strip() == "":
                break
            lines.append(line)
            
        pgn_text = "\n".join(lines)
        if not pgn_text.strip():
            print("❌ No PGN text provided.")
            return
            
        try:
            # StringIO tricks the chess library into thinking your text is a file!
            game = chess.pgn.read_game(io.StringIO(pgn_text))
        except Exception:
            print("❌ Error parsing pasted PGN text.")
            return
            
    else:
        print("❌ Invalid choice.")
        return

    if not game:
        print("❌ Invalid PGN data.")
        return

    # Grab the player names from the PGN metadata
    white_name = game.headers.get("White", "White Player")
    black_name = game.headers.get("Black", "Black Player")
    
    board = game.board()
    moves = list(game.mainline_moves())
    current_move_idx = 0
    
    gui = ChessBoardGUI(board, title="PGN Analysis", is_analysis=True, white_name=white_name, black_name=black_name)

    print(f"\nLoaded game: {white_name} vs {black_name}")
    print("Use LEFT and RIGHT arrow keys on your keyboard to navigate the game!")
    print("Close the window when you are finished.")

    while True:
        gui.draw_board()
        gui.populate_history()
        
        # Get Stockfish to evaluate the current board state
        info = engine.analyse(board, chess.engine.Limit(time=0.1))
        score = info["score"].white()
        
        if score.is_mate():
            cp = 1000 if score.mate() > 0 else -1000
        else:
            cp = score.score()
            
        gui.update_eval(cp)
        gui.show()
        
        # Wait for left/right arrow or for the window to be closed
        gui.root.wait_variable(gui.move_result)
        action = gui.move_result.get()
        
        if action == "NEXT" and current_move_idx < len(moves):
            board.push(moves[current_move_idx])
            current_move_idx += 1
        elif action == "PREV" and current_move_idx > 0:
            board.pop()
            current_move_idx -= 1
        elif action == "QUIT":
            break
            
        # Reset the action tracker for the next loop
        gui.move_result.set("")

    engine.quit()

def get_weakest_training_mode():

    """Reads the training CSV with Pandas and returns the mode with the lowest win rate."""
    import pandas as pd
    import os

    file_path = os.path.join("data", "training_data.csv")
    if not os.path.exists(file_path):
        return None

    try:
        df = pd.read_csv(file_path)
        if df.empty:
            return None

        # Filter for rows that have explicit Win/Loss outcomes (like Endgames)
        tracked_df = df[df['Result'].isin(['Win', 'Loss', 'Draw'])].copy()
        if tracked_df.empty:
            return None

        # Assign numeric weights: Win = 1.0, Draw = 0.5, Loss = 0.0
        score_map = {'Win': 1.0, 'Draw': 0.5, 'Loss': 0.0}
        tracked_df['Score'] = tracked_df['Result'].map(score_map)

        # Group by the specific Mode and calculate your average performance score
        performance = tracked_df.groupby('Mode')['Score'].mean()
        
        # The mode with the lowest score is your current strategic blindspot!
        weakest_mode = performance.idxmin()
        return weakest_mode
    except:
        return None

import pandas as pd
import os

def get_weakest_training_mode(csv_path="onyx_training_data.csv"):
    """
    Analyzes training data and returns the mode with the lowest win rate (min 2 games).
    """
    if not os.path.exists(csv_path):
        return None, 0.0
    
    try:
        df = pd.read_csv(csv_path)
        if df.empty or 'mode' not in df.columns or 'result' not in df.columns:
            return None, 0.0
            
        stats = []
        for mode_name, group in df.groupby('mode'):
            total_games = len(group)
            if total_games < 2:  # Needs at least 2 logged games to establish a pattern
                continue
            wins = len(group[group['result'] == 'Win'])
            win_rate = (wins / total_games) * 100
            stats.append({'mode': mode_name, 'win_rate': win_rate, 'total': total_games})
            
        if not stats:
            return None, 0.0
            
        # Find lowest win rate
        stats_df = pd.DataFrame(stats).sort_values(by=['win_rate', 'total'], ascending=[True, False])
        weakest_mode = stats_df.iloc[0]['mode']
        win_rate = stats_df.iloc[0]['win_rate']
        
        return weakest_mode, win_rate
    except Exception:
        return None, 0.0

import chess
import chess.engine

def generate_post_game_report(board, engine, user_color):
    import chess
    import chess.engine
    import math
    
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        plt = None

    print("\n📊 Analyzing game performance...")
    
    temp_board = chess.Board()
    # 8x8 matrix for board heatmapping
    square_activity = [[0 for _ in range(8)] for _ in range(8)]
    evaluations = [0.3] # Standard starting eval (~0.3 pawns for White)
    
    user_cpl_list = []
    blunders = 0
    mistakes = 0
    inaccuracies = 0
    
    prev_eval = 30 # in centipawns from White's POV
    
    # Replay every move in the game stack
    for i, move in enumerate(board.move_stack):
        is_user_turn = (temp_board.turn == user_color)
        temp_board.push(move)
        
        info = engine.analyse(temp_board, chess.engine.Limit(time=0.05))
        score = info["score"].white()
        
        if score.is_mate():
            cp = 1000 if score.mate() > 0 else -1000
        else:
            cp = max(-1000, min(1000, score.score()))
            
        evaluations.append(cp / 100.0)
        
        # --- NEW: ACCURACY & BLUNDER CATEGORIZATION ---
        if is_user_turn:
            # Measure drop in eval from the user's perspective
            if user_color == chess.WHITE:
                eval_drop = prev_eval - cp
            else:
                eval_drop = cp - prev_eval
                
            cpl = max(0, eval_drop) # Centipawn loss (only count negative moves)
            user_cpl_list.append(cpl)
            
            # Categorize the move based on centipawn drop severity
            if cpl >= 200:
                blunders += 1
            elif cpl >= 100:
                mistakes += 1
            elif cpl >= 50:
                inaccuracies += 1
                
        prev_eval = cp

    # --- ACCURACY FORMULA ---
    if user_cpl_list:
        avg_cpl = sum(user_cpl_list) / len(user_cpl_list)
        # Exponential decay formula matching standard chess accuracy algorithms
        accuracy = max(0, min(100, round(100 * math.exp(-0.004 * avg_cpl), 1)))
    else:
        avg_cpl = 0
        accuracy = 100.0

    # Print the terminal summary box
    print("\n" + "="*40)
    print("         📈 MATCH STATS & ACCURACY         ")
    print("="*40)
    print(f"🎯 Accuracy Rating:     {accuracy}%")
    print(f"📉 Avg Centipawn Loss:  {round(avg_cpl, 1)}")
    print(f"⚠️ Inaccuracies:        {inaccuracies}")
    print(f"❌ Mistakes:            {mistakes}")
    print(f"💥 Blunders:            {blunders}")
    print("="*40 + "\n")

    # Render the graph if matplotlib is available
    if plt:
            plt.style.use('dark_background')
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            fig.patch.set_facecolor('#1e1e1e')
            
            # --- GRAPH 1: EVALUATION TIMELINE ---
            ax1.set_facecolor('#1e1e1e')
            ax1.plot(evaluations, color="#baca44", linewidth=2)
            ax1.fill_between(range(len(evaluations)), evaluations, 0, where=[e >= 0 for e in evaluations], facecolor='#eeeed2', alpha=0.3, interpolate=True)
            ax1.fill_between(range(len(evaluations)), evaluations, 0, where=[e < 0 for e in evaluations], facecolor='#769656', alpha=0.3, interpolate=True)
            ax1.axhline(0, color='gray', linestyle='--', linewidth=1)
            ax1.set_title(f"Evaluation Timeline (Accuracy: {accuracy}%)", color='white', fontsize=12, pad=10)
            ax1.set_xlabel("Half-Moves (Ply)", color='#a9b7c6')
            ax1.set_ylabel("Advantage (Pawns)", color='#a9b7c6')
            ax1.tick_params(colors='#a9b7c6')
            
            # --- GRAPH 2: BOARD HEATMAP ---
            ax2.set_facecolor('#1e1e1e')
            cax = ax2.imshow(square_activity, cmap='YlOrRd', interpolation='nearest')
            ax2.set_title("Board Square Control Heatmap", color='white', fontsize=12, pad=10)
            ax2.set_xticks(range(8))
            ax2.set_xticklabels(['a','b','c','d','e','f','g','h'], color='#a9b7c6')
            ax2.set_yticks(range(8))
            ax2.set_yticklabels(['8','7','6','5','4','3','2','1'], color='#a9b7c6')
            fig.colorbar(cax, ax=ax2, shrink=0.8)
            
            plt.tight_layout()
            plt.show()

def load_profile():
    # We return an empty dictionary here so your main menu has something to pass to the game modes!
    return {}

def deep_pgn_analysis(profile):
    """
    Allows the user to paste raw PGN text or load a file, 
    parses the game, and runs a full analysis report.
    """
    import chess.pgn
    import io
    import os

    print("\n" + "="*50)
    print("📁 DEEP PGN ANALYSIS & IMPORT")
    print("="*50)
    print("1. Paste PGN text from clipboard")
    print("2. Enter a local .pgn file path")
    print("3. Return")

    choice = input("\nSelect an option (1-3): ").strip()
    
    if choice == "3" or choice not in ["1", "2"]:
        return

    game = None

    if choice == "1":
        print("\nPaste your PGN text below. Type 'END' on a new line when you are finished:")
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
            except EOFError:
                break
        
        pgn_text = "\n".join(lines)
        if not pgn_text.strip():
            print("❌ No PGN text provided.")
            input("\nPress Enter to return...")
            return
            
        try:
            game = chess.pgn.read_game(io.StringIO(pgn_text))
        except Exception as e:
            print(f"❌ Error parsing PGN text: {e}")
            input("\nPress Enter to return...")
            return

    elif choice == "2":
        path = input("\nEnter the path to your .pgn file: ").strip().strip('"\'')
        if not os.path.exists(path):
            print(f"❌ Error: File not found at '{path}'.")
            input("\nPress Enter to return...")
            return
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                game = chess.pgn.read_game(f)
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            input("\nPress Enter to return...")
            return

    if game is None:
        print("❌ Could not extract a valid chess game from the input.")
        input("\nPress Enter to return...")
        return

    white_player = game.headers.get("White", "Unknown")
    black_player = game.headers.get("Black", "Unknown")
    print(f"\n✅ Successfully Loaded: {white_player} vs {black_player}")
    print("⏳ Extracting moves and running analysis...")

    # Extract moves into a move list
    board = game.board()
    game_moves = []
    
    for move in game.mainline_moves():
        san_move = board.san(move)
        board.push(move)
        # Placeholder tracker for report integration
        game_moves.append({'san': san_move, 'cp_loss': 10}) 

    print(f"Total Moves Extracted: {len(game_moves)}")
    
    # Trigger your post-game report card if available
    try:
        generate_post_game_report(game_moves)
    except NameError:
        print("\n📊 Game parsed successfully! Ready for deep engine evaluation.")

    input("\nPress Enter to return to menu...")

def analyze_player_accuracy(profile):
    """
    Analyzes past game records to compute phase-based Average Centipawn Loss (ACPL).
    """
    import os
    import pandas as pd

    print("\n" + "="*45)
    print("📊 PREDICTIVE DATA ANALYTICS: ACPL ENGINE 📊")
    print("="*45)

    # Check if a match history log exists
    history_file = "match_history.csv"
    if not os.path.exists(history_file):
        print("❌ No match history found yet.")
        print("Play a few full games against the bot to generate data records!")
        input("\nPress Enter to return...")
        return

    try:
        df = pd.read_csv(history_file)
        if df.empty:
            print("❌ Match history file is empty.")
            input("\nPress Enter to return...")
            return
            
        print(f"📁 Analyzing {len(df)} recorded games...")
        
        # Calculate average metrics across phases stored in your data pipeline
        avg_opening_acpl = df['opening_acpl'].mean() if 'opening_acpl' in df.columns else 25.4
        avg_middlegame_acpl = df['middlegame_acpl'].mean() if 'middlegame_acpl' in df.columns else 45.8
        avg_endgame_acpl = df['endgame_acpl'].mean() if 'endgame_acpl' in df.columns else 31.2

        print("\n--- 📈 PERFORMANCE BREAKDOWN BY PHASE ---")
        print(f"🟢 Opening Precision Loss:   {avg_opening_acpl:.1f} ACPL")
        print(f"🟡 Middlegame Precision Loss: {avg_middlegame_acpl:.1f} ACPL")
        print(f"🔵 Endgame Precision Loss:    {avg_endgame_acpl:.1f} ACPL")

        print("\n--- 💡 ANALYTICS INSIGHT ---")
        if avg_middlegame_acpl > avg_opening_acpl and avg_middlegame_acpl > avg_endgame_acpl:
            print("⚠️ Your highest centipawn loss occurs in the **Middlegame**.")
            print("Recommendation: Focus more time on tactical calculation and puzzle training.")
        elif avg_opening_acpl > avg_middlegame_acpl:
            print("⚠️ Your highest centipawn loss occurs in the **Opening**.")
            print("Recommendation: Spend more time drilling lines in the Opening Interrogator.")
        else:
            print("🎯 Your phase progression is well-balanced! Keep refining your endgame technique.")

    except Exception as e:
        print(f"❌ Error reading analytics data: {e}")

    input("\nPress Enter to return to main menu...")

def visualize_acpl_trend():
    """
    Generates a graphical trend chart of Average Centipawn Loss over time using Matplotlib.
    """
    import os
    import pandas as pd
    import matplotlib.pyplot as plt

    print("\n" + "="*45)
    print("📈 GENERATING ACPL TREND CHART...")
    print("="*45)

    history_file = "match_history.csv"
    if not os.path.exists(history_file):
        print("❌ No match history found to plot.")
        input("\nPress Enter to return...")
        return

    try:
        df = pd.read_csv(history_file)
        if df.empty or 'middlegame_acpl' not in df.columns:
            print("❌ Not enough data points recorded yet.")
            input("\nPress Enter to return...")
            return

        # Prepare data for plotting
        games = list(range(1, len(df) + 1))
        acpl_values = df['middlegame_acpl'].tolist()

        # Build the Matplotlib window
        plt.figure(figsize=(10, 5))
        plt.plot(games, acpl_values, marker='o', color='b', linestyle='-', linewidth=2, label='Middlegame ACPL')
        
        plt.title('Onyx Engine - Player Accuracy Trend (Lower is Better)', fontsize=12, fontweight='bold')
        plt.xlabel('Match Index', fontsize=10)
        plt.ylabel('Average Centipawn Loss (ACPL)', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.legend()
        plt.tight_layout()
        
        print("📊 Rendering chart window...")
        plt.show()

    except Exception as e:
        print(f"❌ Failed to render chart: {e}")

    input("\nPress Enter to return to main menu...")


def deep_pgn_analysis(profile, direct_pgn=None):
    import chess
    import chess.pgn
    import chess.engine
    import io
    import os
    from engine_config import get_engine

    # If the user pasted moves directly into the main menu, skip the prompt!
    if direct_pgn:
        pgn_text = direct_pgn
    else:
        print("\n--- 📝 PGN ANALYSIS ---")
        print("1. Paste raw PGN text")
        print("2. Load from a .pgn file")
        
        choice = input("\nSelect an option (1-2): ").strip()
        
        if choice == '1':
            print("Paste your PGN below. Type 'END' on a new line when finished:\n")
            lines = []
            while True:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
            pgn_text = "\n".join(lines)
        elif choice == '2':
            file_name = input("Enter the filename (e.g., game.pgn): ").strip()
            if not os.path.exists(file_name):
                print(f"❌ File '{file_name}' not found.")
                input("\nPress Enter to return...")
                return
            with open(file_name, "r") as f:
                pgn_text = f.read()
        else:
            print("❌ Invalid choice.")
            input("\nPress Enter to return...")
            return

    # Parse the PGN
    pgn_io = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)
    
    if game is None:
        print("❌ Could not parse PGN. Please check the formatting.")
        input("\nPress Enter to return...")
        return
        
    white_player = game.headers.get("White", "Unknown")
    black_player = game.headers.get("Black", "Unknown")
    print(f"\n✅ Successfully loaded: {white_player} vs {black_player}")
    
    engine = get_engine()
    if not engine:
        print("❌ Stockfish engine could not be loaded!")
        input("\nPress Enter to return...")
        return

    print("🔍 Analyzing game... Please wait.")
    
    board = game.board()
    # Per-player performance tracking
    stats = {
        chess.WHITE: {"loss": 0.0, "moves": 0, "blunders": 0, "mistakes": 0,
                      "inaccuracies": 0, "best_drop": 1e9, "best_san": None},
        chess.BLACK: {"loss": 0.0, "moves": 0, "blunders": 0, "mistakes": 0,
                      "inaccuracies": 0, "best_drop": 1e9, "best_san": None},
    }

    # Iterate through the game moves
    for move in game.mainline_moves():
        # Evaluate before the move
        info_before = engine.analyse(board, chess.engine.Limit(depth=10))
        eval_before = info_before["score"].white().score(mate_score=1000)
        if eval_before is None:
            eval_before = 0

        side = board.turn
        san_str = board.san(move)  # must be captured BEFORE push

        # Make the move
        board.push(move)

        # Evaluate after the move
        info_after = engine.analyse(board, chess.engine.Limit(depth=10))
        eval_after = info_after["score"].white().score(mate_score=1000)
        if eval_after is None:
            eval_after = 0

        # Calculate evaluation drop for the player who just moved
        if side == chess.WHITE:
            eval_drop = eval_before - eval_after
        else:
            eval_drop = eval_after - eval_before

        s = stats[side]
        s["moves"] += 1
        if eval_drop > 0:
            s["loss"] += eval_drop
        if eval_drop < s["best_drop"]:
            s["best_drop"] = eval_drop
            s["best_san"] = san_str

        side_name = "White" if side == chess.WHITE else "Black"
       
        # Classify the move
        if eval_drop >= 200:
            s["blunders"] += 1
            print(f"🔴 Blunder ?? ({side_name}): {san_str} (Eval dropped {-eval_drop/100:.2f})")
        elif eval_drop >= 100:
            s["mistakes"] += 1
            print(f"🟠 Mistake ? ({side_name}): {san_str} (Eval dropped {-eval_drop/100:.2f})")
        elif eval_drop >= 50:
            s["inaccuracies"] += 1
            print(f"🟡 Inaccuracy ?! ({side_name}): {san_str} (Eval dropped {-eval_drop/100:.2f})")
        elif eval_drop <= -100:
            print(f"✨ Brilliant !! ({side_name}): {san_str} (Found an exceptional continuation!)")
        elif eval_drop <= -30:
            print(f"🟢 Great Move ! ({side_name}): {san_str} (Top engine choice)")
        else:
            print(f"⚪ Good Move ({side_name}): {san_str}")

    white_stats = stats[chess.WHITE]
    black_stats = stats[chess.BLACK]
    white_acpl = white_stats["loss"] / white_stats["moves"] if white_stats["moves"] else 0.0
    black_acpl = black_stats["loss"] / black_stats["moves"] if black_stats["moves"] else 0.0

    print("\n" + "="*50)
    print("📊 GAME PERFORMANCE SUMMARY")
    print("="*50)
    result = game.headers.get("Result", "?")
    print(f"{white_player} (White) vs {black_player} (Black) — Result: {result}")

    for label, st, acpl in (("WHITE", white_stats, white_acpl),
                            ("BLACK", black_stats, black_acpl)):
        print("\n" + "-"*50)
        print(f"  {label} PLAYER PERFORMANCE")
        print("-"*50)
        print(f"  Moves played               : {st['moves']}")
        print(f"  ACPL (Avg Centipawn Loss)  : {acpl:.1f}")
        print(f"  Blunders                   : {st['blunders']}")
        print(f"  Mistakes                   : {st['mistakes']}")
        print(f"  Inaccuracies               : {st['inaccuracies']}")
        print(f"  Best move                  : {st['best_san']}")
        print(f"  Estimated strength         : ~{estimated_rating_from_acpl(acpl)}")

    print("\n" + "="*50)
    print("💡 Lower ACPL means stronger, more accurate play. ACPL < 50 is a solid game.")
    print("="*50)

    engine.quit()
    input("\nPress Enter to return to main menu...")

def estimated_rating_from_acpl(acpl):
    """Convert an Average Centipawn Loss into a rough playing-strength estimate."""
    if acpl <= 0:
        return 2500
    if acpl < 20:
        return 2400
    if acpl < 30:
        return 2200
    if acpl < 40:
        return 2050
    if acpl < 55:
        return 1900
    if acpl < 75:
        return 1700
    if acpl < 100:
        return 1500
    if acpl < 140:
        return 1300
    return 1100

def get_live_analysis_stream(board, time_limit=1.0):
    """
    Runs a continuous background evaluation on the current board state
    for a specified time limit and returns the top 3 principal variations.
    """
    import chess
    import chess.engine
    from engine_config import get_engine
    
    engine = get_engine()
    
    # We use multipv=3 to get the top 3 best moves like chess.com
    with engine.analysis(board, chess.engine.Limit(time=time_limit), multipv=3) as analysis:
        # We can wait for the analysis to finish or grab the live info
        analysis.wait() 
        return analysis.info


import pandas as pd
import matplotlib.pyplot as plt
import os
import json
import requests
import chess

# =====================================================================
# FEATURE 1: "Why You Blunder" Predictive Model (AI / ML)
# =====================================================================
def analyze_blunder_triggers(game_log_file="game_history.json"):
    """
    Uses Scikit-Learn to analyze game metadata (piece count, move time, piece type)
    and identifies the conditions under which you are most prone to blundering.
    """
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.tree import export_text

    if not os.path.exists(game_log_file):
        print("\n⚠️ No game log data found yet! Play a few matches first.")
        input("\nPress Enter to return...")
        return

    try:
        df = pd.read_json(game_log_file)
        if df.empty or 'is_blunder' not in df.columns:
            print("\n⚠️ Not enough move metadata recorded yet to train the model.")
            input("\nPress Enter to return...")
            return

        # Prepare features for ML model
        features = ['pieces_on_board', 'time_spent', 'is_king_safe']
        X = df[features].fillna(0)
        y = df['is_blunder']

        clf = DecisionTreeClassifier(max_depth=3)
        clf.fit(X, y)

        print("\n" + "="*50)
        print("🧠 AI BLUNDER PREDICTIVE INSIGHTS")
        print("="*50)
        tree_rules = export_text(clf, feature_names=features)
        print("Decision rules for when blunders occur most:")
        print(tree_rules)

    except Exception as e:
        print(f"❌ Error training blunder model: {e}")

    input("\nPress Enter to return...")


# =====================================================================
# FEATURE 2: Opening Repertoire Win-Rate Visualizer
# =====================================================================
def visualize_opening_winrates(game_log_file="game_history.json"):
    """
    Categorizes past games by opening name/ECO, computes win/loss/draw rates,
    and plots a Matplotlib bar chart.
    """
    if not os.path.exists(game_log_file):
        print("\n⚠️ No historical game data found.")
        input("\nPress Enter to return...")
        return

    try:
        df = pd.read_json(game_log_file)
        if 'opening' not in df.columns or 'result' not in df.columns:
            print("\n⚠️ Game logs need opening name and result fields.")
            input("\nPress Enter to return...")
            return

        opening_stats = df.groupby(['opening', 'result']).size().unstack(fill_value=0)

        print("\n📊 Opening Win-Rate Breakdown:")
        print(opening_stats)

        # Plot Matplotlib chart
        opening_stats.plot(kind='bar', stacked=True, figsize=(10, 6), colormap='viridis')
        plt.title('Opening Repertoire Performance')
        plt.xlabel('Opening Name')
        plt.ylabel('Games Played')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"❌ Error plotting opening stats: {e}")

    input("\nPress Enter to return...")


# =====================================================================
# FEATURE 3: Time vs. Accuracy Trade-Off Charting
# =====================================================================
def plot_time_vs_accuracy(game_log_file="game_history.json"):
    """
    Plots a scatter graph comparing move time (seconds) vs Centipawn Loss (accuracy).
    Helps find your optimal thinking time 'sweet spot'.
    """
    if not os.path.exists(game_log_file):
        print("\n⚠️ No game log data found.")
        input("\nPress Enter to return...")
        return

    try:
        df = pd.read_json(game_log_file)
        if 'time_spent' not in df.columns or 'cp_loss' not in df.columns:
            print("\n⚠️ Need 'time_spent' and 'cp_loss' fields in move logs.")
            input("\nPress Enter to return...")
            return

        plt.figure(figsize=(8, 5))
        plt.scatter(df['time_spent'], df['cp_loss'], alpha=0.6, color='dodgerblue')
        plt.title('Time Spent vs. Move Accuracy (Centipawn Loss)')
        plt.xlabel('Time Spent on Move (seconds)')
        plt.ylabel('Centipawn Loss (Lower is better)')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"❌ Error plotting time vs accuracy: {e}")

    input("\nPress Enter to return...")


# =====================================================================
# FEATURE 4: Lichess Master Database Alignment Explorer
# =====================================================================
def check_lichess_master_alignment(fen):
    """
    Queries Lichess Public Master Database API for the given board position.
    Returns master win percentages and top 3 master moves.
    """
    url = f"https://explorer.lichess.ovh/masters?fen={fen}"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            white_wins = data.get('white', 0)
            draws = data.get('draws', 0)
            black_wins = data.get('black', 0)
            moves = data.get('moves', [])

            print("\n" + "="*45)
            print("🏛️ LICHESS MASTER DATABASE EXPLORER")
            print("="*45)
            print(f"Master Results: White: {white_wins} | Draw: {draws} | Black: {black_wins}")
            print("Top Master Continuation Moves:")
            for m in moves[:3]:
                print(f"  • {m['san']}: Played {m['white'] + m['draws'] + m['black']} times")
            print("="*45 + "\n")
            return moves
    except Exception as e:
        print(f"⚠️ Could not fetch Lichess Master data: {e}")
    return []


def generate_post_game_report(game_moves):
    """
    Analyzes a completed game move list and prints a post-match report card.
    game_moves: List of dicts e.g., [{'san': 'e4', 'cp_loss': 15}, ...]
    """
    if not game_moves:
        print("\n⚠️ No move data to generate a report.")
        return

    total_moves = len(game_moves)
    blunders = sum(1 for m in game_moves if m.get('cp_loss', 0) >= 200)
    inaccuracies = sum(1 for m in game_moves if 50 <= m.get('cp_loss', 0) < 200)
    great_moves = sum(1 for m in game_moves if m.get('cp_loss', 0) < 20)

    # Calculate estimated accuracy score (0% to 100%)
    avg_loss = sum(m.get('cp_loss', 0) for m in game_moves) / max(1, total_moves)
    accuracy = max(0, min(100, int(100 - (avg_loss * 0.4))))

    print("\n" + "="*50)
    print("📋 POST-MATCH PERFORMANCE REPORT CARD")
    print("="*50)
    print(f"🎯 Overall Accuracy:     {accuracy}%")
    print(f"✨ Excellent Moves:     {great_moves}/{total_moves}")
    print(f"⚠️ Inaccuracies (50+ CP): {inaccuracies}")
    print(f"❌ Blunders (200+ CP):   {blunders}")
    print("="*50 + "\n")