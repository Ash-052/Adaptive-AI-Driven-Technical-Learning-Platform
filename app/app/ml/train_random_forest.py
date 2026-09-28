import pandas as pd
import numpy as np
import os
import json
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

def train_rf():
    print("Loading RF dataset...")
    df = pd.read_csv("app/data/rf_dataset.csv")
    
    feature_cols = [
        'skill_score', 'recent_accuracy_last_5', 'performance_score_last_5',
        'weakest_mastery', 'mastery_gap',
        'topic_mastery_basics', 'topic_mastery_arrays', 'topic_mastery_strings',
        'topic_mastery_recursion', 'topic_mastery_sorting', 'topic_mastery_searching',
        'topic_mastery_dynamic_programming', 'topic_mastery_graphs', 'topic_mastery_trees',
        'is_weak_basics', 'is_weak_arrays', 'is_weak_strings',
        'is_weak_recursion', 'is_weak_sorting', 'is_weak_searching',
        'is_weak_dynamic_programming', 'is_weak_graphs', 'is_weak_trees'
    ]
    
    X = df[feature_cols]
    y_topic = df['next_topic']
    y_diff = df['next_difficulty']
    
    X_train, X_test, y_topic_train, y_topic_test, y_diff_train, y_diff_test = train_test_split(
        X, y_topic, y_diff, test_size=0.2, random_state=42
    )
    
    print("\nTraining Topic Model...")
    rf_topic = RandomForestClassifier(n_estimators=200, max_depth=10, class_weight="balanced", random_state=42)
    rf_topic.fit(X_train, y_topic_train)
    
    print("\nTraining Difficulty Model...")
    rf_diff = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42)
    rf_diff.fit(X_train, y_diff_train)
    
    # Evaluate Topic
    topic_preds = rf_topic.predict(X_test)
    topic_acc = accuracy_score(y_topic_test, topic_preds)
    print("\n=========================================================")
    print("TOPIC PREDICTION EVALUATION")
    print("=========================================================")
    print(f"Accuracy: {topic_acc:.4f} (Target > 0.80)")
    print("\nClassification Report:")
    print(classification_report(y_topic_test, topic_preds))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_topic_test, topic_preds))
    
    print("\nFeature Importances (Topic Model):")
    for name, imp in zip(feature_cols, rf_topic.feature_importances_):
        print(f"  {name}: {imp:.4f}")
        
    # Evaluate Difficulty
    diff_preds = rf_diff.predict(X_test)
    diff_acc = accuracy_score(y_diff_test, diff_preds)
    print("\n=========================================================")
    print("DIFFICULTY PREDICTION EVALUATION")
    print("=========================================================")
    print(f"Accuracy: {diff_acc:.4f} (Target > 0.75)")
    print("\nClassification Report:")
    print(classification_report(y_diff_test, diff_preds))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_diff_test, diff_preds))
    
    print("\nFeature Importances (Difficulty Model):")
    for name, imp in zip(feature_cols, rf_diff.feature_importances_):
        print(f"  {name}: {imp:.4f}")
        
    # Save models
    os.makedirs("app/models", exist_ok=True)
    joblib.dump(rf_topic, "app/models/rf_topic_model.pkl")
    joblib.dump(rf_diff, "app/models/rf_difficulty_model.pkl")
    
    with open("app/models/feature_names.json", "w") as f:
        json.dump(feature_cols, f, indent=2)
        
    print("\nModels saved to app/models/")

if __name__ == "__main__":
    train_rf()
