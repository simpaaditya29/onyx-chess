from flask import Flask, send_from_directory, jsonify, request
from evaluation import evaluate_position
import json
import chess

app = Flask(__name__, static_folder='web_ui')

# Load openings database into memory
try:
    with open("openings.json", "r") as f:
        REPERTOIRE_DATA = json.load(f)
except FileNotFoundError:
    REPERTOIRE_DATA = {"categories": [], "fen_lookup": {}}

@app.route('/')
def serve_index():
    return send_from_directory('web_ui', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web_ui', path)

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Returns available opening categories from openings.json"""
    return jsonify({"categories": REPERTOIRE_DATA.get("categories", [])})

@app.route('/api/interrogator/move', methods=['POST'])
def interrogator_move():
    data = request.json
    fen = data.get("fen")
    user_uci = data.get("move")
    category = data.get("category", "Catalan Opening Lines")

    fen_lookup = REPERTOIRE_DATA.get("fen_lookup", {})
    cat_entries = [e for e in fen_lookup.get(fen, []) if e.get("category") == category]
    valid_moves = [e["move"] for e in cat_entries]

    if not valid_moves:
        return jsonify({"status": "complete", "message": "Repertoire branch complete!"})

    if user_uci in valid_moves:
        board = chess.Board(fen)
        board.push(chess.Move.from_uci(user_uci))
        bot_fen = board.fen()

        bot_entries = [e for e in fen_lookup.get(bot_fen, []) if e.get("category") == category]
        bot_moves = [e["move"] for e in bot_entries]

        if bot_moves:
            bot_reply_uci = bot_moves[0]
            move_obj = chess.Move.from_uci(bot_reply_uci)
            bot_san = board.san(move_obj) # Convert to SAN (e.g. Nf3 instead of g1f3)
            board.push(move_obj)
            
            return jsonify({
                "status": "correct",
                "bot_move": bot_reply_uci,
                "bot_san": bot_san,
                "new_fen": board.fen(),
                "message": "Correct book move!"
            })
        else:
            return jsonify({"status": "complete", "message": "Line completed!"})
    else:
        return jsonify({"status": "reset", "message": "❌ Inaccuracy! Move not in repertoire. Resetting..."})


@app.route('/api/engine/move', methods=['POST'])
def engine_move():
    data = request.json
    fen = data.get("fen")
    rating = int(data.get("rating", 1200))
    
    board = chess.Board(fen)
    legal_moves = list(board.legal_moves)
    
    if not legal_moves:
        return jsonify({"status": "game_over", "message": "Game over!"})

    # Depth scaling based on selected rating
    depth = 1 if rating <= 1000 else (2 if rating <= 1500 else 3)
    
    best_move = None
    best_score = float('inf') if board.turn == chess.BLACK else float('-inf')

    for move in legal_moves:
        board.push(move)
        score = evaluate_position(board)
        board.pop()
        
        if board.turn == chess.BLACK:
            if score < best_score:
                best_score = score
                best_move = move
        else:
            if score > best_score:
                best_score = score
                best_move = move

    if not best_move:
        best_move = legal_moves[0]

    bot_san = board.san(best_move) # Convert to proper algebraic notation
    board.push(best_move)

    return jsonify({
        "status": "success",
        "bot_move": best_move.uci(),
        "bot_san": bot_san,
        "new_fen": board.fen(),
        "eval": best_score
    })

@app.route('/api/puzzles/load', methods=['GET'])
def load_puzzle():
    """
    Puzzle Dashboard Logic: Loads a random FEN from your puzzles.csv database.
    """
    # TODO: Add logic to read from your CSV file.
    # For now, we load a hardcoded tactical position.
    tactical_fen = "r1bq1rk1/pp2bppp/4p3/3pn2n/2pP4/2P1PN2/PP1NBPPP/R2Q1RK1 w - - 0 11"
    
    return jsonify({
        "status": "success",
        "fen": tactical_fen,
        "instructions": "White to move and win."
    })

if __name__ == '__main__':
    print("🚀 Starting Onyx Web Server on http://localhost:5000")
    app.run(debug=True, port=5000)