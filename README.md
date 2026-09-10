# ♟️ Onyx Chess Engine v6.0 (Pro Edition)

Onyx Chess Engine v6.0 is a feature-rich, command-line and GUI-integrated chess application built in Python. Designed as an advanced training companion and analytics platform, it combines the analytical strength of Stockfish with custom data-driven training features, interactive Tkinter graphical interfaces, and automated game analysis.

---

## 🚀 Key Features

* **🤖 Multi-Faceted Game Modes:** 
  * Play full games against configurable Stockfish difficulty levels (Beginner to Grandmaster / Max Strength).
  * **Blindfold Mode:** Play with a hidden board and live terminal/GUI clocks to train visualization skills.
  * **Pass 'n Play & Sparring Bots:** Local multiplayer and specialized sparring drills.
* **📊 Player Statistics & Analytics Hub:** 
  * Track win rates, opening performance, and Average Centipawn Loss (ACPL) trends using `pandas` and data analytics pipelines.
  * Deep PGN parsing engine that automatically detects blunders, mistakes, and inaccuracies.
* **🧩 Advanced Training Suites:**
  * **Puzzle Dashboard:** Interactive Lichess puzzle integration categorized by themes (Endgames, Forks, Pins, Mate in 2, etc.).
  * **Mistake Decks & Blunder Tactics:** Automated review systems that pull historical mistakes for active retraining.
* **⚙️ Modern Enhancements:**
  * **Live Evaluation Bar & Pre-moves:** Tkinter-powered visual GUI overlay supporting move history, live win-probability bars, and pre-moves.
  * **Voice Announcer:** Integrated Text-to-Speech (`pyttsx3`) move narration.
  * **Smart PGN Auto-Detector:** Paste raw PGN text directly into the main menu to instantly trigger deep game evaluation.

---

## 🛠️ Tech Stack & Libraries

* **Language:** Python 3.x
* **Core Logic:** `python-chess` (Move validation, FEN parsing, board state management)
* **AI Integration:** Stockfish UCI (Universal Chess Interface) via multi-threaded Python subprocesses
* **Data & Analytics:** `pandas` (Dataset parsing for opening repertoires and Lichess tactical databases)
* **GUI & Audio:** `tkinter` (Custom chessboard rendering and HUD clocks), `pyttsx3` (Voice synthesis)

---

## ⚙️ Installation & Launch

1. Clone the repository or download the project files.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt