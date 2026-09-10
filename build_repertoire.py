import chess.pgn
import json
import os
import glob

def build_categorized_repertoire(pgn_folder=".", output_json_path="openings.json", max_theory_moves=15):
    """
    Parses all PGN files in the directory, extracts [Event] headers,
    and builds a structured opening library for Onyx.
    """
    # Structure:
    # "categories": List of available opening lines/events
    # "fen_lookup": FEN string -> List of mapped moves with metadata
    repertoire = {
        "categories": [],
        "fen_lookup": {}
    }

    # Find all .pgn files in the current folder
    pgn_files = glob.glob(os.path.join(pgn_folder, "*.pgn"))
    
    if not pgn_files:
        print("⚠️ No .pgn files found in the directory!")
        return

    total_games_processed = 0

    for pgn_path in pgn_files:
        print(f"📖 Processing bulk file: {os.path.basename(pgn_path)}...")
        
        with open(pgn_path, 'r', encoding='utf-8', errors='ignore') as pgn_file:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break  # End of file reached
                
                total_games_processed += 1
                
                # Extract event category (default to filename if header is generic)
                event_name = game.headers.get("Event", "General Line")
                if event_name == "?" or event_name == "0":
                    event_name = os.path.splitext(os.path.basename(pgn_path))[0].replace("_", " ").title()

                if event_name not in repertoire["categories"]:
                    repertoire["categories"].append(event_name)

                board = game.board()
                
                # Determine move cap: limit theory lines to move 15, allow model games to go further
                is_model_game = "Model" in event_name or "Example" in event_name
                move_limit = 100 if is_model_game else (max_theory_moves * 2)  # In half-moves (plies)

                for move_count, move in enumerate(game.mainline_moves()):
                    if move_count >= move_limit:
                        break  # Stop theory recording at the limit so Onyx calculates afterwards

                    fen = board.fen()
                    move_uci = move.uci()

                    if fen not in repertoire["fen_lookup"]:
                        repertoire["fen_lookup"][fen] = []

                    # Store move alongside its category tag
                    move_entry = {"move": move_uci, "category": event_name}
                    
                    if move_entry not in repertoire["fen_lookup"][fen]:
                        repertoire["fen_lookup"][fen].append(move_entry)

                    board.push(move)

    # Export structured output to openings.json
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(repertoire, f, indent=4)

    print("\n" + "="*50)
    print(f"✅ Success! Processed {total_games_processed} games across {len(pgn_files)} PGN files.")
    print(f"📂 Created {len(repertoire['categories'])} distinct training categories in {output_json_path}.")
    print("="*50)

if __name__ == "__main__":
    build_categorized_repertoire()