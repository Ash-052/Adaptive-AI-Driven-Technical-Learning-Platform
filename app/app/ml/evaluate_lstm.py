import torch
import pandas as pd
import numpy as np
from lstm_model import SkillPredictorLSTM
import joblib
import json
from collections import defaultdict

def evaluate():
    print("Evaluating LSTM Model...")
    
    scalers = joblib.load("app/models/scalers.pkl")
    with open("app/models/user_to_index.json", "r") as f:
        user_to_index = json.load(f)
        
    num_users = len(user_to_index)
        
    df = pd.read_csv("app/data/sequential_dataset.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['user_id', 'timestamp'])
    
    df['topic_encoded'] = scalers['topic'].transform(df['topic'])
    
    df['time_taken_log'] = np.log1p(df['time_taken'])
    df['time_taken_norm'] = (df['time_taken_log'] - scalers['mean_time']) / scalers['std_time']

    df['attempts_norm'] = df['attempts'] / 3.0
    df['difficulty_norm'] = (df['difficulty'] - df['difficulty'].min()) / (df['difficulty'].max() - df['difficulty'].min())
    df['topic_encoded_norm'] = df['topic_encoded'] / df['topic_encoded'].max()
    df['diff_trend'] = df.groupby('user_id')['difficulty_norm'].rolling(3, min_periods=1).mean().reset_index(0, drop=True)
    
    model = SkillPredictorLSTM(num_users=num_users, input_size=13, hidden_size=128)
    model.load_state_dict(torch.load("app/models/lstm_model.pt"))
    model.eval()
    
    all_success_preds = []
    all_time_preds = []
    all_att_preds = []
    
    user_sequences = defaultdict(list)
    
    # PASS 1: Collect Predictions
    for user_id, group in df.groupby('user_id'):
        u_idx = user_to_index.get(str(user_id))
        if u_idx is None:
            continue
            
        features = group[['accuracy', 'time_taken_norm', 'difficulty_norm', 'topic_encoded_norm', 'diff_trend']].values
        if len(features) <= 10:
            continue
        
        for i in range(len(features) - 10):
            seq = features[i:i+10]
            seq_arr = np.array([seq])
            seq_t = torch.tensor(seq_arr, dtype=torch.float32)
            u_t = torch.tensor([u_idx], dtype=torch.long)
            
            with torch.no_grad():
                success_pred, time_pred, att_pred = model(seq_t, u_t)
                
            succ = (success_pred.item() + 1) / 2
            t = time_pred.item()
            a = att_pred.item()
            
            all_success_preds.append(succ)
            all_time_preds.append(t)
            all_att_preds.append(a)
            
            user_sequences[user_id].append({
                'succ': succ, 't': t, 'a': a
            })

    # 3. NORMALIZE TIME & ATTEMPTS
    min_t, max_t = min(all_time_preds), max(all_time_preds)
    min_a, max_a = min(all_att_preds), max(all_att_preds)
    
    user_avg_skills = {}
    all_final_skills = []
    
    # PASS 2: Calculate Skills
    for user_id, seqs in user_sequences.items():
        prev_skill = 0.5
        skill_t_history = []
        user_skill_sum = 0
        
        for row in seqs:
            succ = row['succ']
            t = row['t']
            a = row['a']
            
            norm_t = (t - min_t) / (max_t - min_t + 1e-8)
            norm_a = (a - min_a) / (max_a - min_a + 1e-8)
            
            # 4. FIX SKILL FORMULA
            perf_t = 0.3 * succ + 0.35 * (1.0 - norm_t) + 0.35 * (1.0 - norm_a)
            
            skill_t = 0.5 * prev_skill + 0.5 * perf_t
            prev_skill = skill_t
            skill_t_history.append(skill_t)
            
            last_5 = skill_t_history[-5:]
            rolling_mean = np.mean(last_5)
            
            final_skill = max(0.05, min(0.95, rolling_mean))
            all_final_skills.append(final_skill)
            user_skill_sum += final_skill
            
        user_avg_skills[user_id] = user_skill_sum / len(seqs)

    print("\n--- PREDICTION RANGES ---")
    print(f"Success Range : {min(all_success_preds):.3f} -> {max(all_success_preds):.3f}")
    print(f"Time Range    : {min_t:.3f} -> {max_t:.3f}")
    print(f"Attempts Range: {min_a:.3f} -> {max_a:.3f}")
    
    print("\n--- STANDARD DEVIATION CHECKS ---")
    print(f"Success Mean: {np.mean(all_success_preds):.3f}")
    print(f"Success Std : {np.std(all_success_preds):.3f} (Expect > 0.15)")
    print(f"Time Std    : {np.std(all_time_preds):.3f} (Expect > 0.2)")
    print(f"Attempts Std: {np.std(all_att_preds):.3f} (Expect > 0.2)")
    
    print("\n--- DERIVED SKILL RANGE ---")
    print(f"Skill Range: {min(all_final_skills):.3f} -> {max(all_final_skills):.3f}")
    
    # 5. PERCENTILE-BASED SEPARATION
    avg_skills_list = list(user_avg_skills.values())
    p30 = np.percentile(avg_skills_list, 30)
    p70 = np.percentile(avg_skills_list, 70)
    
    beginners = sum(1 for v in avg_skills_list if v <= p30)
    intermediates = sum(1 for v in avg_skills_list if p30 < v <= p70)
    advanced = sum(1 for v in avg_skills_list if v > p70)
    
    print("\n--- USER SEPARATION ---")
    print(f"Beginner (Bottom 30%): {beginners}")
    print(f"Intermediate (Middle 40%): {intermediates}")
    print(f"Advanced (Top 30%): {advanced}")
    
    print("\n--- SAMPLE USER PREDICTIONS ---")
    sample_users = list(user_avg_skills.keys())[:3]
    for uid in sample_users:
        print(f"User {uid} Avg Derived Skill: {user_avg_skills[uid]:.3f}")

if __name__ == "__main__":
    evaluate()
