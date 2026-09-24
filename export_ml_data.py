import os
import pandas as pd

PUZZLE_DB = "data/blunder_bank.csv"
ML_OUTPUT = "data/onyx_ml_dataset.csv"

def generate_ml_dataset():
    if not os.path.exists(PUZZLE_DB):
        print(f"Error: {PUZZLE_DB} not found.")
        return

    df = pd.read_csv(PUZZLE_DB)
    if df.empty:
        print("No data to export.")
        return

    print("⚙️ Processing data for Machine Learning...")
    
    # Safely inject missing columns for backward compatibility with older datasets
    if 'tags' not in df.columns:
        df['tags'] = 'Untagged'
    if 'time_spent_sec' not in df.columns:
        df['time_spent_sec'] = 0.0
        
    # 1. Select relevant features
    ml_df = df[['fen_before', 'turn', 'cp_loss', 'tags', 'time_spent_sec']].copy()
    
    # 2. Clean and normalize data
    ml_df['turn'] = ml_df['turn'].apply(lambda x: 1 if str(x).strip().lower() == 'white' else 0)
    ml_df['cp_loss'] = ml_df['cp_loss'].abs()
    ml_df['time_spent_sec'] = ml_df['time_spent_sec'].fillna(0)
    
    # 3. One-Hot Encode Tactical Tags for classification
    tags_expanded = ml_df['tags'].str.get_dummies(sep=', ')
    ml_df = pd.concat([ml_df, tags_expanded], axis=1)
    ml_df = ml_df.drop('tags', axis=1)

    ml_df.to_csv(ML_OUTPUT, index=False)
    print(f"✅ ML Dataset generated successfully: {ML_OUTPUT}")
    print(f"Features ready for training: {list(ml_df.columns)}")

if __name__ == "__main__":
    generate_ml_dataset()