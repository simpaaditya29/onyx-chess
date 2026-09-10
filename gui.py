import tkinter as tk
import chess
from utils import load_settings
from PIL import Image, ImageTk
import os
import math
# Ensure the assets folder exists
os.makedirs("assets/pieces", exist_ok=True)

class ChessBoardGUI:
    PIECE_UNICODE = {
        'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
        'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
    }

    THEME_COLORS = {
        "classic": {"light": "#F0D9B5", "dark": "#B58863"},  # Standard wood/classic
        "wood":    {"light": "#E0C398", "dark": "#8B5A2B"},  # Warm mahogany
        "green":   {"light": "#EEEEED", "dark": "#769656"},  # Lichess/Chess.com Green
        "blue":    {"light": "#EAEAEA", "dark": "#4B7399"}   # Ocean Blue
    }

    def __init__(self, board, title="Onyx Chess", flip_board=False, is_analysis=False, white_name="White", black_name="Black", time_limit=None, increment=0):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("850x550" if is_analysis else "750x500")
        self.root.configure(bg="#1e1e1e")
        self.board = board
        self.time_limit = time_limit
        self.white_time = time_limit
        self.black_time = time_limit
        self.timer_id = None 
        self.flip_board = flip_board
        self.is_analysis = is_analysis
        self.increment = increment
        self.pre_move = None


        # --- THEME LOADING ---
        settings = load_settings()
        self.current_theme = settings.get("theme", "classic")
        theme_data = self.THEME_COLORS.get(self.current_theme, self.THEME_COLORS["classic"])
        self.light_color = theme_data["light"]
        self.dark_color = theme_data["dark"]
        self.main_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.square_size = 60

        self.load_piece_images()
        
        # --- NEW: EVAL BAR ---
        if self.is_analysis:
            self.eval_canvas = tk.Canvas(self.main_frame, width=30, height=480, highlightthickness=0, bg="#333333")
            self.eval_canvas.pack(side=tk.LEFT, padx=(0, 10))
            
        # --- BOARD & PLAYER NAMES ---
        self.board_frame = tk.Frame(self.main_frame, bg="#1e1e1e")
        self.board_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        if self.is_analysis:
            top_name = white_name if self.flip_board else black_name
            self.top_label = tk.Label(self.board_frame, text=top_name, fg="white", bg="#1e1e1e", font=("Arial", 12, "bold"))
            self.top_label.pack(anchor="w", pady=(0, 5))
            
        self.canvas = tk.Canvas(self.board_frame, width=480, height=480, highlightthickness=0, bg="#1e1e1e")
        self.canvas.pack()
        
        if self.is_analysis:
            bot_name = black_name if self.flip_board else white_name
            self.bot_label = tk.Label(self.board_frame, text=bot_name, fg="white", bg="#1e1e1e", font=("Arial", 12, "bold"))
            self.bot_label.pack(anchor="w", pady=(5, 0))


        # --- NEW: DIGITAL CLOCKS ---
        self.clock_frame = tk.Frame(self.main_frame, bg="#2d2d2d")
        self.clock_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        # Only show the clocks if a time limit was chosen (not Unlimited)
        if self.time_limit:
            self.white_clock_lbl = tk.Label(self.clock_frame, text=self.format_time(self.white_time), fg="white", bg="#333333", font=("Consolas", 16, "bold"), padx=10, pady=5)
            self.white_clock_lbl.pack(side=tk.LEFT, padx=20)
            
            self.black_clock_lbl = tk.Label(self.clock_frame, text=self.format_time(self.black_time), fg="white", bg="#333333", font=("Consolas", 16, "bold"), padx=10, pady=5)
            self.black_clock_lbl.pack(side=tk.RIGHT, padx=20)  
            self.update_timer()  # Start the countdown loop  

        # --- HISTORY PANEL ---
        self.history_frame = tk.Frame(self.main_frame, bg="#2d2d2d")
        self.history_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        title_lbl = tk.Label(self.history_frame, text="Move History", fg="white", bg="#2d2d2d", font=("Arial", 12, "bold"))
        title_lbl.pack(pady=(5, 0))

        # --- NEW: OPENING EXPLORER LABEL & DICTIONARY ---
        self.opening_lbl = tk.Label(self.history_frame, text="📖 Starting Position", fg="#baca44", bg="#2d2d2d", font=("Arial", 10, "italic"))
        self.opening_lbl.pack(pady=(0, 2))

        # --- NEW: MATERIAL BALANCE LABELS ---
        self.material_lbl = tk.Label(self.history_frame, text="Material: Even (0)", fg="white", bg="#2d2d2d", font=("Arial", 10, "bold"))
        self.material_lbl.pack(pady=(0, 5))

        self.openings = {
            "e4": "King's Pawn Game",
            "d4": "Queen's Pawn Game",
            "c4": "English Opening",
            "Nf3": "Réti Opening",
            "e4 e5": "Open Game",
            "e4 c5": "Sicilian Defense",
            "e4 e6": "French Defense",
            "e4 c6": "Caro-Kann Defense",
            "d4 d5": "Closed Game",
            "d4 Nf6": "Indian Defense",
            "e4 e5 Nf3 Nc6 Bb5": "Ruy Lopez",
            "e4 e5 Nf3 Nc6 Bc4": "Italian Game",
            "d4 d5 c4": "Queen's Gambit",
            "e4 c5 Nf3 d6 d4": "Sicilian: Open"
        }

        self.last_move_count = 0  

        self.scrollbar = tk.Scrollbar(self.history_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.move_listbox = tk.Listbox(self.history_frame, yscrollcommand=self.scrollbar.set, 
                                       bg="#1e1e1e", fg="#a9b7c6", font=("Consolas", 12), 
                                       highlightthickness=0, borderwidth=0)
        self.move_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.scrollbar.config(command=self.move_listbox.yview)
        
        # --- NEW: ON-SCREEN CONTROLS / HOTKEY GUIDE ---
        controls_frame = tk.Frame(self.history_frame, bg="#1e1e1e", bd=1, relief=tk.SOLID)
        controls_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ctrl_title = tk.Label(controls_frame, text="⌨️ Controls", fg="#a9b7c6", bg="#1e1e1e", font=("Arial", 9, "bold"))
        ctrl_title.pack(anchor="w", padx=5, pady=(2, 0))
        
        guide_text = "• [H] Get Hint\n• [T] Switch Theme\n• [C] Copy FEN\n• [Backspace] Undo"
        if self.is_analysis:
            guide_text += "\n• [← / →] Prev / Next"
            
        ctrl_lbl = tk.Label(controls_frame, text=guide_text, fg="#888888", bg="#1e1e1e", font=("Arial", 8), justify=tk.LEFT)
        ctrl_lbl.pack(anchor="w", padx=5, pady=(0, 3))
        
        self.selected_square = None
        self.move_result = tk.StringVar() 
        
        
        # --- BINDINGS ---

        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<BackSpace>", lambda e: self.move_result.set("UNDO"))
        self.root.bind("<h>", lambda e: self.move_result.set("HINT")) 
        self.root.bind("<t>", lambda e: self.move_result.set("THEME")) # NEW: Theme switcher
        self.root.bind("<c>", lambda e: self.copy_fen_to_clipboard())
        if self.is_analysis:
            self.root.bind("<Right>", lambda e: self.move_result.set("NEXT"))
            self.root.bind("<Left>", lambda e: self.move_result.set("PREV"))

        # Cleanly handles closing the window with the 'X' button
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        

        
        self.draw_board()
        self.populate_history() 

    def update_eval(self, centipawns): 
        # --- NEW: Safely exit if the window is already closed ---
        try:
            if not self.eval_canvas.winfo_exists():
                return
        except Exception:
            return
        # --------------------------------------------------------
        
        self.eval_canvas.delete("all")
        
        # Calculate visual ratio (Cap at +/- 1000 CP for display purposes)
        cp = max(-1000, min(1000, centipawns))
        white_percentage = 0.5 + (cp / 2000)
        if self.flip_board: 
            white_percentage = 1.0 - white_percentage 
            
        white_height = 480 * white_percentage
        black_height = 480 - white_height
        
        self.eval_canvas.create_rectangle(0, 0, 30, black_height, fill="#404040", outline="")
        self.eval_canvas.create_rectangle(0, black_height, 30, 480, fill="#ffffff", outline="")
        
        eval_val = abs(centipawns) / 100
        if centipawns >= 0:
            eval_str = f"+{eval_val:.1f}" if eval_val < 10 else f"+{int(eval_val)}"
        else:
            eval_str = f"-{eval_val:.1f}" if eval_val < 10 else f"-{int(eval_val)}"
            
        text_y = black_height - 15 if centipawns >= 0 else black_height + 15
        text_y = max(15, min(465, text_y))
        
        text_color = "#ffffff" if centipawns < 0 else "#000000"
        if self.flip_board: text_color = "#ffffff" if centipawns >= 0 else "#000000"
        
        self.eval_canvas.create_text(15, text_y, text=eval_str, fill=text_color, font=("Arial", 8, "bold"))

    def populate_history(self):
        self.move_listbox.delete(0, tk.END)
        temp_board = self.board.copy()
        while temp_board.move_stack:
            temp_board.pop()
            
        move_texts = []
        san_sequence = [] # Tracks moves for the Opening Explorer
        is_capture = False 
        
        for i, move in enumerate(self.board.move_stack):
            san_move = temp_board.san(move)
            san_sequence.append(san_move)
            
            # If this is the most recent move and it's a capture, flag it!
            if i == len(self.board.move_stack) - 1 and "x" in san_move:
                is_capture = True
                
            if i % 2 == 0:
                move_texts.append(f"{(i//2)+1}. {san_move}")
            else:
                move_texts[-1] += f"   {san_move}"
            temp_board.push(move)
        
        for text in move_texts:
            self.move_listbox.insert(tk.END, text)
        self.move_listbox.yview(tk.END) 
        
        # --- NEW: OPENING EXPLORER MATCHING ---
        seq_str = " ".join(san_sequence)
        matched_opening = "Starting Position" if not seq_str else "Out of Book / Variation"
        
        # Look for the longest matching sequence in our dictionary
        for key in self.openings:
            if seq_str.startswith(key):
                matched_opening = self.openings[key]
                
        self.opening_lbl.config(text=f"📖 {matched_opening}")
        
        # --- NEW: AUDIO & SOUND EFFECTS ---
        current_moves = len(self.board.move_stack)
        if current_moves > self.last_move_count: # A new move was just played!
            try:
                import winsound
                if is_capture:
                    # Plays a slightly heavier Windows chime for captures
                    winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
                else:
                    # Plays a standard light tick/chime for regular moves
                    winsound.PlaySound("SystemDefault", winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                pass
            # --- NEW: MATERIAL CALCULATION ---
        piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
        white_material = sum(len(self.board.pieces(pt, chess.WHITE)) * val for pt, val in piece_values.items())
        black_material = sum(len(self.board.pieces(pt, chess.BLACK)) * val for pt, val in piece_values.items())
        diff = white_material - black_material
        
        if diff > 0:
            mat_text = f"White is +{diff}"
        elif diff < 0:
            mat_text = f"Black is +{abs(diff)}"
        else:
            mat_text = "Material: Even (0)"
            
        self.material_lbl.config(text=f"⚖️ {mat_text}")
                
        self.last_move_count = current_moves # Update tracker for next time

    # Paste this right above your REAL draw_board function further down the page!
    def load_piece_images(self):
        self.piece_images = {}
        pieces = ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK']
        
        for piece in pieces:
            try:
                img_path = f"assets/pieces/{piece}.png"
                img = Image.open(img_path)
                img = img.resize((self.square_size, self.square_size), Image.Resampling.LANCZOS)
                self.piece_images[piece] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"⚠️ Missing graphic for {piece}: {e}")
 

    def draw_board(self):
        self.canvas.delete("all")

        # Define highlight colors
        highlight_color = "#bac223"
        last_move_light = "#f5f682"
        last_move_dark = highlight_color

        # Find out what the last move was
        last_move_squares = []
        if self.board.move_stack:
            last_move = self.board.peek()
            last_move_squares = [last_move.from_square, last_move.to_square]

        for y_index in range(8):
            for x_index in range(8):
                x1 = x_index * self.square_size
                y1 = y_index * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                if self.flip_board:
                    logical_file = 7 - x_index
                    logical_rank = y_index
                else:
                    logical_file = x_index
                    logical_rank = 7 - y_index

                square = chess.square(logical_file, logical_rank)
                is_dark_square = (logical_rank + logical_file) % 2 == 0

                # Apply square colors (selections & last moves)
                if getattr(self, 'selected_square', None) == square:
                    color = highlight_color
                elif square in last_move_squares:
                    color = last_move_dark if is_dark_square else last_move_light
                else:
                    color = self.dark_color if is_dark_square else self.light_color

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                # Draw high-res piece images
                piece = self.board.piece_at(square)
                if piece:
                    center_x = x1 + (self.square_size // 2)
                    center_y = y1 + (self.square_size // 2)

                    color_prefix = 'w' if piece.color == chess.WHITE else 'b'
                    piece_symbol = piece.symbol().upper()
                    piece_key = f"{color_prefix}{piece_symbol}"

                    if hasattr(self, 'piece_images') and piece_key in self.piece_images:
                        self.canvas.create_image(center_x, center_y, image=self.piece_images[piece_key])

            
    def on_click(self, event):
        x_index = event.x // self.square_size
        y_index = event.y // self.square_size

        if not (0 <= x_index <= 7 and 0 <= y_index <= 7):
            return

        if self.flip_board:
            logical_file = 7 - x_index
            logical_rank = y_index
        else:
            logical_file = x_index
            logical_rank = 7 - y_index

        clicked_square = chess.square(logical_file, logical_rank)
       

        if self.selected_square is None:
            piece = self.board.piece_at(clicked_square)
            # BUG FIX: Only allow selecting pieces that belong to your color!
            if piece and piece.color == self.board.turn:
                self.selected_square = clicked_square
                self.draw_board()
        else:
            move = chess.Move(self.selected_square, clicked_square)
            if move not in self.board.legal_moves:
                move = chess.Move(self.selected_square, clicked_square, promotion=chess.QUEEN)
                
            if move in self.board.legal_moves:
                self.move_result.set(move.uci())
                
            self.selected_square = None
            self.draw_board()

    def on_hint_key(self, event):
        """Sends a 'hint' command back to the game loop when H is pressed."""
        if hasattr(self, 'move_result'):
            self.move_result.set("hint")        

    def on_close(self):
        self.move_result.set("QUIT")
        self.root.destroy()

    def get_mouse_move(self):
        while True:
            self.root.wait_variable(self.move_result)
            uci_move = self.move_result.get()
            
            # Catch known system commands
            if uci_move == "QUIT": 
                return "quit"
            if uci_move == "UNDO": 
                return "undo"
            if uci_move == "HINT": 
                return "hint"
            if uci_move == "TIMEOUT":
                return "timeout"
                
            # --- NEW: THEME SWITCHER LOGIC ---
            if uci_move == "THEME":
                self.current_theme = (self.current_theme + 1) % len(self.themes)
                self.draw_board()
                self.move_result.set("")
                continue
            
            # Ignore arrow key navigation signals during active play
            if uci_move in ["PREV", "NEXT"]:
                self.move_result.set("")
                continue
                
            # Safely convert move from UCI format to SAN notation
            try:
                move_san = self.board.san(chess.Move.from_uci(uci_move))
                return move_san
            except Exception:
                # If an invalid string ever gets passed, reset and wait for a valid click
                self.move_result.set("")
                continue

    def handle_click(self, square):
            import chess

            # Determine the bot's color based on board flip perspective
            bot_color = chess.BLACK if not self.flip_board else chess.WHITE

            # --------------------------------------------------
            # 1. PRE-MOVE LOGIC (When it is Stockfish's turn)
            # --------------------------------------------------
            if self.board.turn == bot_color:
                if self.selected_square is None:
                    # Select the player's piece to pre-move
                    if self.board.color_at(square) == (not bot_color):
                        self.selected_square = square
                        self.draw_board()
                else:
                    # Store source and destination squares as a queued pre-move
                    self.pre_move = chess.Move(self.selected_square, square)
                    self.selected_square = None
                    print("⚡ Pre-move queued!")
                    self.draw_board()
                return

            # --------------------------------------------------
            # 2. NORMAL MOVE LOGIC (When it is your turn)
            # --------------------------------------------------
            if self.selected_square is None:
                # Select piece if it belongs to the active player
                if self.board.color_at(square) == self.board.turn:
                    self.selected_square = square
                    self.draw_board()
            else:
                # Attempt to form a move from selected square to clicked square
                move = chess.Move(self.selected_square, square)

                # Auto-promote pawns reaching the back rank to Queen
                piece = self.board.piece_at(self.selected_square)
                if piece and piece.piece_type == chess.PAWN:
                    if (piece.color == chess.WHITE and chess.square_rank(square) == 7) or \
                    (piece.color == chess.BLACK and chess.square_rank(square) == 0):
                        move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)

                if move in self.board.legal_moves:
                    self.selected_square = None
                    self.move_result.set(move.uci())
                elif self.board.color_at(square) == self.board.turn:
                    # Switch selection to another friendly piece
                    self.selected_square = square
                    self.draw_board()
                else:
                    # Deselect on invalid move
                    self.selected_square = None
                    self.draw_board()

                # --- FISCHER INCREMENT LOGIC ---
            if self.increment > 0:
                if self.board.turn == chess.BLACK:  # White just completed their move
                    self.white_time += self.increment
                    self.white_clock_lbl.config(text=self.format_time(self.white_time))
                else:                               # Black just completed their move
                    self.black_time += self.increment
                    self.black_clock_lbl.config(text=self.format_time(self.black_time))    

    def format_time(self, seconds):
        if seconds is None:
            return "00:00"
        
        # Calculate minutes and seconds
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"
                    

    def update_timer(self):
        """Handles countdown clock and stops immediately when time hits 0."""
        if not hasattr(self, 'white_time') or not hasattr(self, 'black_time'):
            return

        # Stop timer immediately if someone ran out of time
        if self.white_time <= 0 or self.black_time <= 0:
            if self.timer_id:
                try:
                    self.root.after_cancel(self.timer_id)
                except Exception:
                    pass
                self.timer_id = None
            return

        # Decrement active player's clock
        if hasattr(self, 'current_turn'):
            if self.current_turn == chess.WHITE:
                self.white_time = max(0, self.white_time - 1)
            else:
                self.black_time = max(0, self.black_time - 1)

            # Update labels if they exist
            if hasattr(self, 'white_clock_lbl'):
                self.white_clock_lbl.config(text=self.format_time(self.white_time))
            if hasattr(self, 'black_clock_lbl'):
                self.black_clock_lbl.config(text=self.format_time(self.black_time))

            if self.white_time <= 0:
                print("\n⏰ Black wins on time!")
            elif self.black_time <= 0:
                print("\n⏰ White wins on time!")
            else:
                # Schedule next tick only if time remains
                self.timer_id = self.root.after(1000, self.update_timer)

    def show(self):
        """Refreshes the GUI window tasks."""
        try:
            self.root.update_idletasks()
            self.root.update()
        except Exception:
            pass

    def close(self):
        """Safely stops timers and destroys the GUI window."""
        # Cancel running timer loop so it doesn't leak into terminal
        if hasattr(self, 'timer_id') and self.timer_id:
            try:
                self.root.after_cancel(self.timer_id)
            except Exception:
                pass
            self.timer_id = None

        try:
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.destroy()
        except Exception:
            pass

    def draw_arrow(self, start_square, end_square, color="green"):
        """Draws an arrow on the canvas, erases previous arrows first."""
        self.clear_arrows() 
        x1, y1 = self._get_square_center(start_square) 
        x2, y2 = self._get_square_center(end_square)
        self.canvas.create_line(x1, y1, x2, y2, arrow="last", width=6, fill=color, tags="arrow")

    def clear_arrows(self):
        """Removes all arrows from the board."""
        self.canvas.delete("arrow")

    def _get_square_center(self, square_name):
        """Helper method to get the (x, y) pixel coordinates for the center of a square."""
        file = ord(square_name[0]) - ord('a')
        rank = 8 - int(square_name[1]) 
        x = (file * self.square_size) + (self.square_size // 2)
        y = (rank * self.square_size) + (self.square_size // 2)
        return x, y

    def update_eval_bar(self, cp_score):
        """
        Updates an evaluation gauge display inside the GUI.
        cp_score: Centipawn score (e.g., +150 for +1.5, -300 for -3.0).
        """
        try:
            # Convert centipawns to evaluation string (e.g., +1.50 or -3.00)
            eval_val = cp_score / 100.0
            eval_str = f"+{eval_val:.2f}" if eval_val > 0 else f"{eval_val:.2f}"
            
            # Update title or dedicated eval label if available
            if hasattr(self, 'eval_label'):
                color = "#4CAF50" if eval_val >= 0 else "#E53935"
                self.eval_label.config(text=f"Eval: {eval_str}", fg=color)
            else:
                self.root.title(f"Onyx Chess | Eval: {eval_str}")
        except Exception:
            pass    

    def get_mouse_move(self):
        """
        Waits for the user to click two squares on the graphical board 
        and returns the resulting UCI move string (e.g. 'e2e4').
        """
        self.user_move = None
        self.selected_square = None

        # This tells the canvas to listen for Left Mouse Clicks
        self.canvas.bind("<Button-1>", self.on_square_click)

        # This loop keeps the window from freezing while waiting for your click
        while self.user_move is None:
            try:
                self.root.update_idletasks()
                self.root.update()
            except Exception:
                return "quit"

        # Once you click twice, it saves the move and returns it
        move_to_return = self.user_move
        self.user_move = None
        return move_to_return

    def on_square_click(self, event):
        """
        Calculates which square you clicked based on where your mouse is.
        """
        col = event.x // self.square_size
        row = event.y // self.square_size

        # Make sure the click is actually inside the 8x8 board
        col = max(0, min(7, col))
        row = max(0, min(7, row))

        # Convert the click into a chess square (like 'e2' or 'e4')
        file_char = chr(ord('a') + col)
        rank_num = 8 - row
        clicked_square = f"{file_char}{rank_num}"

        if self.selected_square is None:
            # Click 1: Select the piece you want to move
            self.selected_square = clicked_square
            print(f"Selected: {self.selected_square}")
        elif self.selected_square == clicked_square:
            # If you click the exact same piece again, it deselects it
            self.selected_square = None
            print("Deselected square.")
        else:
            # Click 2: Select where you want the piece to go
            self.user_move = f"{self.selected_square}{clicked_square}"
            print(f"Played move: {self.user_move}")
            self.selected_square = None    
import tkinter as tk

class BlindfoldHUD:
    """
    Minimal GUI HUD for Blindfold Mode.
    Hides the board and piece visuals while displaying active clock timers 
    and current turn indicator.
    """
    def __init__(self, title="Blindfold Mode HUD", white_time=300, black_time=300):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("420x280")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(False, False)

        self.white_time = white_time
        self.black_time = black_time

        # --- HEADER ---
        header = tk.Label(
            self.root, 
            text="🙈 BLINDFOLD CHESS HUD", 
            font=("Helvetica", 15, "bold"), 
            fg="#cdd6f4", 
            bg="#1e1e2e"
        )
        header.pack(pady=12)

        # --- TURN DISPLAY ---
        self.turn_label = tk.Label(
            self.root, 
            text="CURRENT TURN: WHITE", 
            font=("Helvetica", 11, "bold"), 
            fg="#a6e3a1", 
            bg="#1e1e2e"
        )
        self.turn_label.pack(pady=4)

        # --- CLOCK BOXES ---
        clock_frame = tk.Frame(self.root, bg="#1e1e2e")
        clock_frame.pack(pady=15)

        self.white_label = tk.Label(
            clock_frame, 
            text=f"⚪ WHITE\n{self._format_time(self.white_time)}", 
            font=("Courier", 16, "bold"), 
            fg="#11111b", 
            bg="#a6e3a1", 
            width=12, 
            height=3, 
            relief="ridge"
        )
        self.white_label.grid(row=0, column=0, padx=10)

        self.black_label = tk.Label(
            clock_frame, 
            text=f"⚫ BLACK\n{self._format_time(self.black_time)}", 
            font=("Courier", 16, "bold"), 
            fg="#cdd6f4", 
            bg="#313244", 
            width=12, 
            height=3, 
            relief="ridge"
        )
        self.black_label.grid(row=0, column=1, padx=10)

        # --- FOOTER ---
        self.status_label = tk.Label(
            self.root, 
            text="Listen to moves via Voice Announcer or Terminal", 
            font=("Helvetica", 9, "italic"), 
            fg="#bac2de", 
            bg="#1e1e2e"
        )
        self.status_label.pack(side="bottom", pady=10)

    def _format_time(self, seconds):
        mins, secs = divmod(max(0, int(seconds)), 60)
        return f"{mins:02d}:{secs:02d}"

    def update_turn(self, turn_color, w_time, b_time):
        """Updates clocks and highlights the active player."""
        self.white_time = w_time
        self.black_time = b_time

        self.white_label.config(text=f"⚪ WHITE\n{self._format_time(self.white_time)}")
        self.black_label.config(text=f"⚫ BLACK\n{self._format_time(self.black_time)}")

        if turn_color.lower() == "white":
            self.turn_label.config(text="CURRENT TURN: WHITE", fg="#a6e3a1")
            self.white_label.config(bg="#a6e3a1", fg="#11111b")
            self.black_label.config(bg="#313244", fg="#cdd6f4")
        else:
            self.turn_label.config(text="CURRENT TURN: BLACK", fg="#f38ba8")
            self.white_label.config(bg="#313244", fg="#cdd6f4")
            self.black_label.config(bg="#f38ba8", fg="#11111b")

        self.root.update()

    def close(self):
        try:
            self.root.destroy()
        except Exception:
            pass