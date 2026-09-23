import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

if __name__ == "__main__":
    plot_blunder_trends()
    plot_spatial_heatmap()