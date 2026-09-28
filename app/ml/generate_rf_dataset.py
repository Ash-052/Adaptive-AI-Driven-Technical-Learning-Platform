import os
import json
import random
import numpy as np
import pandas as pd
import torch
from lstm_model import SkillPredictorLSTM
import joblib
from collections import defaultdict

def compute_performance(accuracy, time_taken, attempts):
    norm_time = min(time_taken / 300.0, 1.0)
    norm_att = min(attempts / 5.0, 1.0)
    return (accuracy * 0.6) + ((1.0 - norm_time) * 0.2) + ((1.0 - norm_att) * 0.2)

def generate_dataset():
    print("Generating RF Dataset...")
    df = pd.read_csv("app/data/sequential_dataset.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['user_id', 'timestamp'])
    
    scalers = joblib.load("app/models/scalers.pkl")
    with open("app/models/user_to_index.json", "r") as f:
        user_to_index = json.load(f)
        
    num_users = len(user_to_index)
    model = SkillPredictorLSTM(num_users=num_users, input_size=13, hidden_size=128)
    model.load_state_dict(torch.load("app/models/lstm_model.pt", weights_only=True))
    model.eval()
    
    df['topic_encoded'] = scalers['topic'].transform(df['topic'])
    df['time_taken_log'] = np.log1p(df['time_taken'])
    df['time_taken_norm'] = (df['time_taken_log'] - scalers['mean_time']) / scalers['std_time']
    df['attempts_norm'] = df['attempts'] / 3.0
    df['difficulty_norm'] = (df['difficulty'] - df['difficulty'].min()) / (df['difficulty'].max() - df['difficulty'].min())
    df['topic_encoded_norm'] = df['topic_encoded'] / df['topic_encoded'].max()
    df['diff_trend'] = df.groupby('user_id')['difficulty_norm'].rolling(3, min_periods=1).mean().reset_index(0, drop=True)
    
    topics_list = list(scalers['topic'].classes_)
    
    rf_data = []
    
    for user_id, group in df.groupby('user_id'):
        u_idx = user_to_index.get(str(user_id))
        if u_idx is None:
            continue
            
        features = group[['accuracy', 'time_taken_norm', 'difficulty_norm', 'topic_encoded_norm', 'diff_trend']].values
        raw_topics = group['topic'].values
        raw_acc = group['accuracy'].values
        raw_time = group['time_taken'].values
        raw_att = group['attempts'].values
        raw_diff = group['difficulty'].values
        
        topic_mastery = {t: 0.5 for t in topics_list}
        topic_perf_history = defaultdict(list)
        prev_skill = 0.5
        skill_t_history = []
        
        # Precompute performance scores for all interactions
        perf_scores = [compute_performance(raw_acc[j], raw_time[j], raw_att[j]) for j in range(len(group))]
        
        for i in range(10, len(features) - 1):
            # Compute skill score via LSTM using sequence [i-10:i]
            seq = features[i-10:i]
            seq_t = torch.tensor(np.array([seq]), dtype=torch.float32)
            u_t = torch.tensor([u_idx], dtype=torch.long)
            
            with torch.no_grad():
                success_pred, time_pred, att_pred = model(seq_t, u_t)
                
            succ = success_pred.item()
            t_pred = time_pred.item()
            a_pred = att_pred.item()
            
            # Using same scaling logic as evaluate_lstm
            min_t, max_t = 0.3, 0.4
            min_a, max_a = 1.4, 2.1
            norm_t_pred = max(0.0, min(1.0, (t_pred - min_t) / (max_t - min_t + 1e-8)))
            norm_a_pred = max(0.0, min(1.0, (a_pred - min_a) / (max_a - min_a + 1e-8)))
            
            perf_t = 0.3 * succ + 0.35 * (1.0 - norm_t_pred) + 0.35 * (1.0 - norm_a_pred)
            skill_t = 0.5 * prev_skill + 0.5 * perf_t
            prev_skill = skill_t
            skill_t_history.append(skill_t)
            rolling_skill = np.mean(skill_t_history[-5:])
            skill_score = max(0.05, min(0.95, rolling_skill))
            
            # Update history with performance at step i
            topic_perf_history[raw_topics[i]].append(perf_scores[i])
            
            # Update topic mastery (decay-based)
            topic_mastery[raw_topics[i]] = 0.7 * topic_mastery[raw_topics[i]] + 0.3 * perf_scores[i]
            
            # Recent stats (last 5)
            recent_acc_5 = np.mean(raw_acc[max(0, i-4):i+1])
            avg_time_5 = np.mean(raw_time[max(0, i-4):i+1])
            avg_att_5 = np.mean(raw_att[max(0, i-4):i+1])
            avg_perf_5 = np.mean(perf_scores[max(0, i-4):i+1])
            
            # Label generation for i+1
            # 1. next_topic (Absolute Signal: 90/10 Split)
            weakest_topic = min(topic_mastery, key=topic_mastery.get)
            
            if random.random() < 0.90:
                next_topic = weakest_topic
            else:
                next_topic = random.choice(topics_list)
                
            # 2. next_difficulty (Balanced)
            recent_acc_3 = np.mean(raw_acc[max(0, i-2):i+1])
            difficulty_score = 0.6 * skill_score + 0.4 * recent_acc_3
            next_diff = 1 if difficulty_score < 0.33 else (2 if difficulty_score < 0.66 else 3)
            
            # 3. New Advanced Features
            mastery_values = list(topic_mastery.values())
            weakest_m = min(mastery_values)
            strongest_m = max(mastery_values)
            m_gap = strongest_m - weakest_m
            
            row = {
                'skill_score': skill_score,
                'recent_accuracy_last_5': recent_acc_5,
                'performance_score_last_5': avg_perf_5,
                'weakest_mastery': weakest_m,
                'mastery_gap': m_gap,
                'next_topic': next_topic,
                'next_difficulty': next_diff
            }
            
            # Add topic mastery and one-hot weak topic features
            for t in topics_list:
                row[f'topic_mastery_{t}'] = topic_mastery[t]
                row[f'is_weak_{t}'] = 1.0 if t == weakest_topic else 0.0
                
            rf_data.append(row)
            
    rf_df = pd.DataFrame(rf_data)
    
    # 6. VERIFY SIGNAL STRENGTH (Correlation)
    print("\n--- SIGNAL STRENGTH (Correlation with next_difficulty) ---")
    diff_corr = rf_df.select_dtypes(include=[np.number]).corr()['next_difficulty'].sort_values(ascending=False)
    print(diff_corr)
    
    # Topic Correlation (using dummy encoding for correlation check)
    print("\n--- SIGNAL STRENGTH (Correlation with next_topic basics) ---")
    topic_dummies = pd.get_dummies(rf_df['next_topic'], prefix='target')
    temp_df = pd.concat([rf_df.select_dtypes(include=[np.number]), topic_dummies], axis=1)
    topic_corr = temp_df.corr()['target_basics'].sort_values(ascending=False)
    print(topic_corr.head(10))

    print(f"\nDataset generated. Shape: {rf_df.shape}")
    print("\n--- NEXT TOPIC DIST ---")
    print(rf_df['next_topic'].value_counts(normalize=True))
    print("\n--- NEXT DIFFICULTY DIST ---")
    print(rf_df['next_difficulty'].value_counts(normalize=True))
    
    os.makedirs("app/data", exist_ok=True)
    rf_df.to_csv("app/data/rf_dataset.csv", index=False)
    print("Saved to app/data/rf_dataset.csv")

if __name__ == "__main__":
    generate_dataset()
