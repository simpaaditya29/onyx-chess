import chess.engine

# Path to your stockfish executable
ENGINE_PATH = "assets/engine/stockfish.exe"

try:
    # Initialize the engine
    engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    
    # Set up a new board position
    board = chess.Board()
    
    # Ask Stockfish to find the best move in 0.1 seconds
    result = engine.play(board, chess.engine.Limit(time=0.1))
    
    print("--------------------------------------------------")
    print(f"✅ Success! Stockfish is alive and thinking.")
    print(f"🤖 Recommended opening move for White: {result.move}")
    print("--------------------------------------------------")
    
    engine.quit()
except Exception as e:
    print(f"❌ Error connecting to Stockfish: {e}")