import chess

# Piece-Square Table for Knights (Encourages central positioning)
KNIGHT_PST = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]

def evaluate_position(board):
    """
    Evaluates material balance and positional placement.
    A positive score favors White; a negative score favors Black.
    """
    # Check for immediate end-game states
    if board.is_checkmate():
        return -9999 if board.turn == chess.WHITE else 9999
        
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    
    # Advanced material and PST logic will be built out here
    
    return score