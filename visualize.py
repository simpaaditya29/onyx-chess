import pandas as pd
import matplotlib.pyplot as plt
import os

PUZZLE_DB = "data/blunder_bank.csv"

def plot_blunder_trends():
    if not os.path.exists(PUZZLE_DB):
        print("No data found to visualize.")
        return

    df = pd.read_csv(PUZZLE_DB)
    
    if df.empty or len(df) < 3:
        print("Need at least 3 puzzles in the bank to generate a meaningful trend line.")
        return

    # Ensure cp_loss is positive for the graph to represent severity
    df['cp_loss'] = df['cp_loss'].abs()
    
    # Calculate a rolling average to smooth out the noise and reveal true trends
    df['rolling_avg'] = df['cp_loss'].rolling(window=3, min_periods=1).mean()

    # Configure a dark-themed analytical dashboard
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot raw data points and the smoothed trendline
    ax.plot(df.index + 1, df['cp_loss'], marker='o', linestyle='', color='#e74c3c', alpha=0.5, label='Individual Blunders')
    ax.plot(df.index + 1, df['rolling_avg'], color='#f1c40f', linewidth=2, label='3-Game Rolling Average')

    # Formatting and aesthetics
    ax.set_title('Onyx Blunder Severity Trend', fontsize=16, fontweight='bold', pad=15)
    ax.set_xlabel('Puzzle Number (Chronological)', fontsize=12)
    ax.set_ylabel('Centipawn Loss (Severity)', fontsize=12)
    ax.grid(color='#333333', linestyle='--', linewidth=0.5)
    ax.legend(frameon=False)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_blunder_trends()