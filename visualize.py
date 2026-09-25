import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
PUZZLE_DB = "data/blunder_bank.csv"

def plot_blunder_trends():
    if not os.path.exists(PUZZLE_DB):
        print("No data found to visualize.")
        return

    df = pd.read_csv(PUZZLE_DB)
    if df.empty or len(df) < 2:
        print("Need at least 2 records to plot trends.")
        return

    df["cp_loss"] = df["cp_loss"].abs()
    solved_df = df[df["solved"] == True].copy()

    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=False)

    df["rolling_cpl"] = df["cp_loss"].rolling(window=3, min_periods=1).mean()
    ax1.plot(df.index + 1, df["cp_loss"], marker="o", linestyle="", color="#e74c3c", alpha=0.6, label="Individual Blunders")
    ax1.plot(df.index + 1, df["rolling_cpl"], color="#f1c40f", linewidth=2, label="3-Puzzle Rolling Avg")
    ax1.set_title("Onyx Performance Metrics", fontsize=15, fontweight="bold", pad=12)
    ax1.set_ylabel("Centipawn Loss", fontsize=11)
    ax1.grid(color="#333333", linestyle="--", linewidth=0.5)
    ax1.legend(loc="upper right", frameon=False)

    if "time_spent_sec" in solved_df.columns and not solved_df["time_spent_sec"].dropna().empty:
        ax2.bar(solved_df.index + 1, solved_df["time_spent_sec"], color="#2ecc71", alpha=0.7, label="Solve Time (s)")
        avg_speed = solved_df["time_spent_sec"].mean()
        ax2.axhline(avg_speed, color="#3498db", linestyle="--", linewidth=1.5, label=f"Avg Speed ({avg_speed:.1f}s)")
        ax2.set_ylabel("Seconds Taken", fontsize=11)
        ax2.set_xlabel("Puzzle Number", fontsize=11)
        ax2.grid(color="#333333", linestyle="--", linewidth=0.5)
        ax2.legend(loc="upper right", frameon=False)
    else:
        ax2.text(0.5, 0.5, "Solve puzzles to populate speed data", horizontalalignment="center", verticalalignment="center", transform=ax2.transAxes, color="#888888")

    plt.tight_layout()
    plt.show()

def plot_spatial_heatmap():
    if not os.path.exists(PUZZLE_DB):
        print("No data found for heatmap.")
        return

    df = pd.read_csv(PUZZLE_DB)
    if df.empty:
        print("Blunder bank is empty.")
        return

    heatmap_data = np.zeros((8, 8))
    
    for idx, row in df.iterrows():
        best_move = str(row['best_move'])
        col_char, row_char = best_move[0], best_move[1]
        
        col_idx = ord(col_char) - ord('a')
        row_idx = 8 - int(row_char) 
        
        heatmap_data[row_idx, col_idx] += 1

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # Native Matplotlib implementation avoiding seaborn dependency
    ax.imshow(heatmap_data, cmap="YlOrRd", aspect="equal")
    
    ax.set_xticks(np.arange(8))
    ax.set_yticks(np.arange(8))
    ax.set_xticklabels(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
    ax.set_yticklabels(['8', '7', '6', '5', '4', '3', '2', '1'])
    
    for i in range(8):
        for j in range(8):
            val = int(heatmap_data[i, j])
            if val > 0:
                ax.text(j, i, str(val), ha="center", va="center", color="black" if val > (heatmap_data.max()/2) else "white")

    ax.set_title("Onyx Spatial Blindspots\n(Where Your Missed Tactics Originate)", fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("File", fontsize=12)
    ax.set_ylabel("Rank", fontsize=12)
    
    ax.set_xticks(np.arange(-.5, 8, 1), minor=True)
    ax.set_yticks(np.arange(-.5, 8, 1), minor=True)
    ax.grid(which="minor", color="#333333", linestyle="-", linewidth=0.5)
    ax.tick_params(which="minor", bottom=False, left=False)
    
    plt.tight_layout()
    plt.show()

def square_to_coords(square_str):
    """Converts an algebraic square (e.g., 'e4') to (row, col) matrix coordinates."""
    if not square_str or len(square_str) < 2:
        return None
    
    file_char = square_str[0].lower()
    rank_char = square_str[1]
    
    if file_char < 'a' or file_char > 'h' or rank_char < '1' or rank_char > '8':
        return None
        
    col = ord(file_char) - ord('a')
    row = 8 - int(rank_char) # 0 is 8th rank (top), 7 is 1st rank (bottom)
    return (row, col)

def generate_blunder_heatmap():
    """Generates an 8x8 spatial density heatmap of blunder destination squares."""
    puzzle_db = "data/blunder_bank.csv"
    if not os.path.exists(puzzle_db):
        print(f"Error: {puzzle_db} not found. Play some games and parse them first!")
        return

    df = pd.read_csv(puzzle_db)
    if df.empty or 'played_move' not in df.columns:
        print("Not enough data to generate a heatmap.")
        return

    print("🗺️ Mapping spatial blunder coordinates...")
    heatmap_data = np.zeros((8, 8))
    
    valid_moves = 0
    for move in df['played_move'].dropna():
        if len(str(move)) >= 4:
            dest_square = str(move)[2:4]
            coords = square_to_coords(dest_square)
            if coords:
                heatmap_data[coords[0], coords[1]] += 1
                valid_moves += 1

    if valid_moves == 0:
        print("No valid algebraic moves found to plot.")
        return

    plt.style.use('dark_background')
    plt.figure(figsize=(8, 8))
    
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
    
    sns.heatmap(heatmap_data, annot=True, fmt="g", cmap="inferno", 
                xticklabels=files, yticklabels=ranks, cbar=False, 
                linewidths=0.5, linecolor='#29292e', square=True)
    
    plt.title("Onyx Spatial Blind Spot Heatmap\n(Where Your Blunders Land)", 
              fontsize=16, fontweight='bold', pad=20, color="#00b37e")
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_blunder_trends()
    generate_blunder_heatmap()