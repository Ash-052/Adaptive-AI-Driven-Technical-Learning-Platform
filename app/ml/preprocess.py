import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import json

def load_and_preprocess(data_path="app/data/sequential_dataset.csv", seq_length=10, test_split=0.2):
    df = pd.read_csv(data_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by=['user_id', 'timestamp'])

    topic_le = LabelEncoder()
    df['topic_encoded'] = topic_le.fit_transform(df['topic'])
    
    # Log transform for time
    df['time_taken_log'] = np.log1p(df['time_taken'])
    mean_time = df['time_taken_log'].mean()
    std_time = df['time_taken_log'].std()
    df['time_taken_norm'] = (df['time_taken_log'] - mean_time) / std_time
    
    df['attempts_norm'] = df['attempts'] / 3.0
    
    df['difficulty_norm'] = (df['difficulty'] - df['difficulty'].min()) / (df['difficulty'].max() - df['difficulty'].min())
    df['topic_encoded_norm'] = df['topic_encoded'] / df['topic_encoded'].max()
    df['diff_trend'] = df.groupby('user_id')['difficulty_norm'].rolling(3, min_periods=1).mean().reset_index(0, drop=True)
    
    unique_users = df['user_id'].unique()
    user_to_index = {str(uid): i for i, uid in enumerate(unique_users)}
    
    os.makedirs("app/models", exist_ok=True)
    with open("app/models/user_to_index.json", "w") as f:
        json.dump(user_to_index, f)
        
    scalers = {
        "mean_time": mean_time,
        "std_time": std_time,
        "topic": topic_le
    }
    joblib.dump(scalers, "app/models/scalers.pkl")

    train_X, train_y, train_u = [], [], []
    test_X, test_y, test_u = [], [], []
    
    np.random.seed(42)
    user_ids_list = list(unique_users)
    np.random.shuffle(user_ids_list)
    split_idx = int(len(user_ids_list) * (1 - test_split))
    train_users = set(user_ids_list[:split_idx])

    for user_id, group in df.groupby('user_id'):
        group_len = len(group)
        if group_len <= seq_length:
            continue
            
        u_idx = user_to_index[str(user_id)]
            
        features = group[['accuracy', 'time_taken_norm', 'difficulty_norm', 'topic_encoded_norm', 'diff_trend']].values
        targets_acc = group['accuracy'].values
        targets_time = group['time_taken_norm'].values
        targets_att = group['attempts_norm'].values
        targets_diff = group['difficulty'].values

        for i in range(group_len - seq_length):
            seq_x = features[i:i+seq_length]

            base_acc = targets_acc[i+seq_length]
            difficulty = targets_diff[i+seq_length]
            
            success = base_acc + np.random.normal(0, 0.2)
            success -= (difficulty - 1) * 0.1
            success = max(0.0, min(1.0, success))
            success = (success - 0.5) * 2
            
            base_time = targets_time[i+seq_length]
            base_att = targets_att[i+seq_length]
            
            seq_y = [success, base_time, base_att]
            
            if user_id in train_users:
                train_X.append(seq_x)
                train_y.append(seq_y)
                train_u.append(u_idx)
            else:
                test_X.append(seq_x)
                test_y.append(seq_y)
                test_u.append(u_idx)
                
    train_X = torch.tensor(np.array(train_X), dtype=torch.float32)
    train_y = torch.tensor(np.array(train_y), dtype=torch.float32)
    train_u = torch.tensor(np.array(train_u), dtype=torch.long)
    
    test_X = torch.tensor(np.array(test_X), dtype=torch.float32)
    test_y = torch.tensor(np.array(test_y), dtype=torch.float32)
    test_u = torch.tensor(np.array(test_u), dtype=torch.long)
    
    return train_X, train_y, train_u, test_X, test_y, test_u, scalers, len(user_to_index)

if __name__ == "__main__":
    train_X, train_y, train_u, test_X, test_y, test_u, scalers, num_users = load_and_preprocess()
    print(f"Train shapes: X={train_X.shape}, y={train_y.shape}, u={train_u.shape}")
    print(f"Test shapes: X={test_X.shape}, y={test_y.shape}, u={test_u.shape}")
    print(f"Total Users: {num_users}")
