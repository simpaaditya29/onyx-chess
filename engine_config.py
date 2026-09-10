import os
import chess
import chess.engine

def get_engine():
    # Points to your stockfish.exe in the new assets folder.
    # normpath() converts the '/' separators to '\' on Windows; subprocess on
    # Windows cannot resolve a relative executable path that uses forward slashes.
    STOCKFISH_PATH = os.path.normpath("assets/engine/stockfish.exe")
    try:
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        return engine
    except FileNotFoundError:
        print("❌ Error: Stockfish engine binary not found at the specified path.")
        return None

def get_best_move(engine, fen, time_limit=0.5):
    board = chess.Board(fen)
    result = engine.play(board, chess.engine.Limit(time=time_limit))
    return result.move