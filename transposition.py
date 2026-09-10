import chess
import chess.polyglot

# Evaluation Flags (To know if a score is exact, or just a bound from Alpha-Beta pruning)
EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2

class TranspositionTable:
    def __init__(self, size_in_mb=64):
        # A Python dictionary entry is roughly ~100 bytes.
        # We limit the size so the engine doesn't eat all your computer's RAM.
        self.max_entries = (size_in_mb * 1024 * 1024) // 100
        self.table = {}

    def get_hash(self, board):
        """Generates the unique 64-bit Zobrist key for the current board."""
        return chess.polyglot.zobrist_hash(board)

    def store(self, board, depth, score, flag, best_move):
        """Saves a calculated position into memory."""
        # If the table gets too full, wipe it to prevent memory crashes
        if len(self.table) >= self.max_entries:
            self.table.clear() 
            
        zobrist_key = self.get_hash(board)
        
        # We only overwrite if the new calculation searched deeper than the old one
        if zobrist_key not in self.table or self.table[zobrist_key]['depth'] <= depth:
            self.table[zobrist_key] = {
                'depth': depth,
                'score': score,
                'flag': flag,
                'best_move': best_move
            }

    def lookup(self, board, depth, alpha, beta):
        """Checks if we have already calculated this exact position."""
        zobrist_key = self.get_hash(board)
        entry = self.table.get(zobrist_key, None)
        
        if entry is not None and entry['depth'] >= depth:
            # We found a match! Check if the score is usable based on Alpha-Beta rules
            if entry['flag'] == EXACT:
                return entry['score'], entry['best_move']
            elif entry['flag'] == LOWERBOUND and entry['score'] >= beta:
                return entry['score'], entry['best_move']
            elif entry['flag'] == UPPERBOUND and entry['score'] <= alpha:
                return entry['score'], entry['best_move']
                
        return None, None