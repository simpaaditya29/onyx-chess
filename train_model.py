import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

ML_DATASET = "data/onyx_ml_dataset.csv"

def train_blunder_classifier():
    if not os.path.exists(ML_DATASET):
        print(f"Error: {ML_DATASET} not found. Run export_ml_data.py first.")
        return

    print("📊 Loading Onyx ML Dataset...")
    df = pd.read_csv(ML_DATASET)

    if df.empty or len(df) < 10:
        print("Need at least 10 puzzles to train a meaningful model. Keep analyzing games!")
        return

    # Define the Target Variable: Severe Blunder (>300 cp loss) vs Standard Mistake
    df['is_severe'] = (df['cp_loss'] > 300).astype(int)

    # Separate features (X) and target (y)
    features = df.drop(columns=['fen_before', 'cp_loss', 'is_severe'])
    target = df['is_severe']

    # Split the dataset: 80% for training the model, 20% for testing its accuracy 
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    print("\n⚙️ Training Random Forest Classifier...")
    # Initialize the model with 100 decision trees to balance accuracy and processing time
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    # Execute predictions on the unseen 20% test data
    y_pred = rf_model.predict(X_test)

    # Terminal Output Metrics
    acc = accuracy_score(y_test, y_pred)
    print(f"\n✅ Model Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Matplotlib & Seaborn Visualization Dashboard
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Plot 1: Feature Importance Ranking (What causes the blunders?)
    importances = rf_model.feature_importances_
    sorted_idx = np.argsort(importances)
    ax1.barh(features.columns[sorted_idx], importances[sorted_idx], color='#00b37e')
    ax1.set_title("What Triggers Your Worst Blunders?", fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel("Relative Feature Importance")

    # Plot 2: Confusion Matrix (How well did the model predict the severity?)
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='g', cmap='Reds', cbar=False, ax=ax2,
                xticklabels=['Standard', 'Severe'], yticklabels=['Standard', 'Severe'])
    ax2.set_title("Prediction Confusion Matrix", fontsize=14, fontweight='bold', pad=15)
    ax2.set_ylabel('Actual Severity')
    ax2.set_xlabel('Predicted Severity')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    train_blunder_classifier()