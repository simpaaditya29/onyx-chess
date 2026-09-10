import pandas as pd

print("Reading your puzzles file...")
df = pd.read_csv("puzzles.csv")

print("Finding endgame positions...")
# Look through the themes column for the word 'endgame'
endgame_df = df[df['Themes'].str.contains("endgame", case=False, na=False)]

# Save those positions into a brand new file
endgame_df.to_csv("endgames.csv", index=False)
print(f"Done! Successfully created endgames.csv with {len(endgame_df)} endgame puzzles!")