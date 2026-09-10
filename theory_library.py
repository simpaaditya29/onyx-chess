"""
Onyx Interactive Chess Theory Library
-------------------------------------
Curated, interactive study material split into Opening Principles, Middlegame
Tactics and Endgame Patterns. Each concept loads onto the graphical board, can
be replayed move-by-move, and (for tactics/endgames) lets the user find the
key move themselves.

Each concept in THEORY_LIBRARY:
    title       - short display name
    description - what to learn
    moves       - optional SAN sequence from the start position that sets up
                  the concept board (alternative to `fen`)
    fen         - optional direct starting position (used when `moves` absent)
    demo        - optional SAN continuation replayed by "Watch demonstration"
    key         - optional single SAN the user should try to find
"""
import chess


# ---------------------------------------------------------------------------
# THEORY CATALOG
# ---------------------------------------------------------------------------
THEORY_LIBRARY = {
    "Opening Principles": [
        {
            "title": "Control the Center",
            "description": "Central pawns and pieces command the most squares. After 1.e4 e5 "
                           "2.Nf3 Nc6 3.d4 exd4 4.Nxd4, White has a broad center to build on.",
            "moves": ["e4", "e5", "Nf3", "Nc6", "d4", "exd4", "Nxd4", "Nf6"],
            "demo": ["Nc3", "Bb4"],
        },
        {
            "title": "Develop Quickly",
            "description": "Bring your minor pieces out before attacking. Each developing move "
                           "gains time; grabbing pawns early lets the opponent catch up on "
                           "development.",
            "moves": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "O-O", "Nf6"],
            "demo": ["Re1", "O-O"],
        },
        {
            "title": "Castle Early",
            "description": "King safety comes first. Both sides castle quickly and then activate "
                           "the rooks — a king trapped in the center is a standing target.",
            "moves": ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "O-O", "Nf6", "d3", "d6", "Re1", "Bg4"],
        },
        {
            "title": "Pawns Claim Space",
            "description": "The d-pawn chain 1.d4 2.c4 puts immediate pressure on the center. "
                           "Pawn structures steer the whole middlegame plan.",
            "moves": ["d4", "d5", "c4", "e6", "Nc3", "Nf6", "Bg5", "Be7", "e3", "O-O"],
        },
    ],
    "Middlegame Tactics": [
        {
            "title": "The Knight Fork",
            "description": "A knight attacks two or more pieces at once. White plays Nxf7, "
                           "forking the queen on d8 and the rook on h8 — Black must save the "
                           "queen, so White wins the exchange.",
            "fen": "3q2kr/5pp1/8/6N1/8/8/5PPP/4R1K1 w - - 0 1",
            "key": "Nxf7",
            "demo": ["Nxf7", "Qd7", "Nxh8"],
        },
        {
            "title": "The Pin",
            "description": "A bishop on b5 pins the knight on c6 to the king — the knight cannot "
                           "move without exposing the king. Black must break the pin carefully.",
            "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5"],
            "demo": ["a6", "Ba4", "b5", "Bb3"],
        },
        {
            "title": "The Skewer",
            "description": "A skewer attacks a valuable piece that must move, exposing a weaker "
                           "one behind it. White plays Re8+, and after the king steps aside the "
                           "rook captures the queen on a8.",
            "fen": "q5k1/5p2/8/8/8/8/5PPP/4R1K1 w - - 0 1",
            "key": "Re8+",
            "demo": ["Re8+", "Kg7", "Rxa8"],
        },
        {
            "title": "Back-Rank Mate",
            "description": "A king trapped behind its own pawns can be mated on the back rank. "
                           "White swings the rook to a8 for an immediate mate.",
            "fen": "6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1",
            "key": "Ra8#",
            "demo": ["Ra8#"],
        },
        {
            "title": "Discovered Attack (Double Check)",
            "description": "Moving the knight off the diagonal uncovers the bishop's attack while "
                           "the knight itself gives check — a double check the king cannot answer "
                           "except by moving.",
            "fen": "6k1/6pp/8/3N4/2B5/8/5PPP/4K3 w - - 0 1",
            "key": "Nf6+",
            "demo": ["Nf6+", "Kh8"],
        },
    ],
    "Endgame Patterns": [
        {
            "title": "Queen Mate (K+Q vs K)",
            "description": "Use the king to shepherd the enemy king to the edge, then mate with "
                           "the queen. Here the queen mates along the eighth rank with the king's "
                           "support.",
            "fen": "6k1/8/6K1/8/8/8/8/2Q5 w - - 0 1",
            "key": "Qc8#",
            "demo": ["Qc8#"],
        },
        {
            "title": "Rook Mate (K+R vs K)",
            "description": "The rook delivers mate on the back rank while the king guards the "
                           "escape squares.",
            "fen": "6k1/8/6K1/8/8/8/8/7R w - - 0 1",
            "key": "Rh8#",
            "demo": ["Rh8#"],
        },
        {
            "title": "The Opposition (K+P vs K)",
            "description": "Kings facing across one square fight for the opposition — the side to "
                           "move can gain or lose a decisive tempo. A king must lead its pawn, "
                           "never lag behind it.",
            "fen": "8/8/8/3k4/3P4/8/8/3K4 w - - 0 1",
        },
        {
            "title": "Pawn Promotion",
            "description": "A pawn on the seventh rank is one step from a new queen. Push it to "
                           "promotion to convert a winning advantage.",
            "fen": "8/6P1/8/8/8/8/8/7K w - - 0 1",
            "key": "g8=Q",
            "demo": ["g8=Q"],
        },
    ],
}


# ---------------------------------------------------------------------------
# INTERACTIVE SESSION
# ---------------------------------------------------------------------------
def _build_board(concept):
    """Construct the concept board from `moves` (SAN from start) or `fen`."""
    if concept.get("moves"):
        b = chess.Board()
        for san in concept["moves"]:
            b.push_san(san)
        return b
    if concept.get("fen"):
        return chess.Board(concept["fen"])
    return chess.Board()


def _replay_demo(gui, board, san_list, title):
    """Push each SAN in `san_list` onto `board`, redrawing and pausing."""
    if not san_list:
        print("(No further moves to demonstrate.)")
        input("\nPress Enter to return...")
        return
    print(f"\n▶️  DEMONSTRATION: {title}")
    for san in san_list:
        try:
            mv = board.parse_san(san)
        except ValueError:
            print(f"⚠️ Demonstration move '{san}' is not legal here — skipping.")
            break
        san_str = board.san(mv)
        board.push(mv)
        gui.draw_board()
        gui.populate_history()
        gui.root.update()
        print(f"  → {san_str}")
        input("Press Enter to continue...")
    input("\nDemonstration finished. Press Enter to return...")


def _concept_session(concept):
    """Run one concept: show it on the board, replay it, or find the key move."""
    from gui import ChessBoardGUI

    board = _build_board(concept)
    gui = ChessBoardGUI(board, title=f"Theory: {concept['title']}", is_analysis=False)
    gui.draw_board()
    gui.populate_history()
    gui.root.update()

    print("\n" + "="*52)
    print(f"💡 {concept['title'].upper()}")
    print("="*52)
    print(concept.get("description", ""))

    while True:
        print("\n1. ▶️ Watch demonstration")
        if concept.get("key"):
            print("2. 🎯 Find the key move yourself")
        print("3. Return to Concept List")
        choice = input("\nSelect an option: ").strip()

        if choice == '1':
            board = _build_board(concept)
            gui.board = board
            gui.draw_board()
            gui.populate_history()
            gui.root.update()
            demo = concept.get("demo")
            _replay_demo(gui, board, demo if demo else concept.get("moves", []), concept["title"])

        elif choice == '2' and concept.get("key"):
            board = _build_board(concept)
            gui.board = board
            gui.draw_board()
            gui.populate_history()
            gui.root.update()
            print("🎯 Find the move that shows the idea. H = hint, Q = give up.")
            found = False
            while not found:
                move_str = gui.get_mouse_move()
                if move_str.lower() == 'quit':
                    break
                if move_str.lower() == 'hint':
                    print(f"💡 The key move is {concept['key']}")
                    continue
                try:
                    user_move = board.parse_san(move_str)
                except ValueError:
                    print("❌ Invalid move. Please use the mouse.")
                    continue
                try:
                    key_move = board.parse_san(concept["key"])
                except ValueError:
                    print("⚠️ Key move is not legal from this position.")
                    break
                if user_move == key_move:
                    san_str = board.san(user_move)
                    board.push(user_move)
                    gui.draw_board()
                    gui.populate_history()
                    gui.root.update()
                    print(f"✅ Correct! {san_str} is the key move.")
                    follow_up = concept.get("demo", [])
                    if follow_up and follow_up[0] == concept["key"]:
                        follow_up = follow_up[1:]  # key already played
                    if follow_up:
                        _replay_demo(gui, board, follow_up, concept["title"])
                    else:
                        input("\nPress Enter to return...")
                    found = True
                else:
                    print("❌ Not quite. (H = hint, or Q to give up.)")

        elif choice == '3':
            gui.close()
            return
        else:
            print("❌ Invalid choice.")


def launch_theory_library(profile):
    """
    Interactive Chess Theory Library: browse opening principles, middlegame
    tactics and endgame patterns on the graphical board.
    """
    sections = list(THEORY_LIBRARY.keys())

    while True:
        print("\n" + "="*50)
        print("📚 INTERACTIVE CHESS THEORY LIBRARY 📚")
        print("="*50)
        for i, section in enumerate(sections, 1):
            print(f"{i}. {section}")
        print(f"{len(sections) + 1}. Return to Main Menu")
        sec_choice = input(f"\nSelect a section (1-{len(sections) + 1}): ").strip()
        if sec_choice == str(len(sections) + 1):
            return
        if not sec_choice.isdigit() or int(sec_choice) > len(sections):
            print("❌ Invalid choice.")
            continue
        section = sections[int(sec_choice) - 1]
        concepts = THEORY_LIBRARY[section]

        while True:
            print(f"\n--- {section.upper()} ---")
            for i, c in enumerate(concepts, 1):
                print(f"{i}. {c['title']}")
            print(f"{len(concepts) + 1}. Return to Library Menu")
            c_choice = input(f"\nSelect a concept (1-{len(concepts) + 1}): ").strip()
            if c_choice == str(len(concepts) + 1):
                break
            if not c_choice.isdigit() or int(c_choice) > len(concepts):
                print("❌ Invalid choice.")
                continue
            concept = concepts[int(c_choice) - 1]
            _concept_session(concept)
