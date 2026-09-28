import os
import json
import pandas as pd
import numpy as np

def run_validation():
    print("=========================================================")
    print("DATASET VALIDATION AUDIT")
    print("=========================================================\n")

    dataset_path = "app/data/sequential_dataset.csv"
    if not os.path.exists(dataset_path):
        print(f"[FAIL] Missing dataset at {dataset_path}")
        print("\nDataset is NOT READY — fix required")
        return

    df = pd.read_csv(dataset_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    all_passed = True
    issues_found = []

    # 1. SEQUENCE ORDER CHECK
    seq_pass = True
    for user_id, group in df.groupby('user_id'):
        if not group['timestamp'].is_monotonic_increasing:
            seq_pass = False
            issues_found.append(f"SEQUENCE ORDER: {user_id} timestamps are not strictly increasing.")
            break
    
    if seq_pass:
        print("[PASS] Sequence Order")
    else:
        print("[FAIL] Sequence Order")
        all_passed = False

    # 2. USER PROGRESSION CHECK
    prog_pass = True
    overall_start_acc = []
    overall_end_acc = []
    overall_start_time = []
    overall_end_time = []

    for user_id, group in df.groupby('user_id'):
        n = len(group)
        if n < 5: continue
        split_idx = int(n * 0.2)
        if split_idx == 0: split_idx = 1
        
        start_group = group.iloc[:split_idx]
        end_group = group.iloc[-split_idx:]
        
        overall_start_acc.append(start_group['accuracy'].mean())
        overall_end_acc.append(end_group['accuracy'].mean())
        overall_start_time.append(start_group['time_taken'].mean())
        overall_end_time.append(end_group['time_taken'].mean())

    avg_start_acc = np.mean(overall_start_acc)
    avg_end_acc = np.mean(overall_end_acc)
    avg_start_time = np.mean(overall_start_time)
    avg_end_time = np.mean(overall_end_time)

    if avg_end_acc <= avg_start_acc or avg_end_time >= avg_start_time:
        prog_pass = False
        issues_found.append(f"USER PROGRESSION: No improvement trend. Acc: {avg_start_acc:.2f}->{avg_end_acc:.2f}, Time: {avg_start_time:.1f}->{avg_end_time:.1f}")
    
    if prog_pass:
        print(f"[PASS] Learning Progression (Acc: {avg_start_acc:.2f}->{avg_end_acc:.2f}, Time: {avg_start_time:.0f}s->{avg_end_time:.0f}s)")
    else:
        print("[FAIL] Learning Progression")
        all_passed = False

    # 3. TOPIC VARIANCE CHECK
    topic_var_pass = True
    for user_id, group in df.groupby('user_id'):
        topic_acc = group.groupby('topic')['accuracy'].mean()
        if len(topic_acc) > 1:
            if topic_acc.max() - topic_acc.min() < 0.1:
                topic_var_pass = False
                issues_found.append(f"TOPIC VARIANCE: {user_id} has uniform performance across topics (max-min < 0.1).")
                break
    
    if topic_var_pass:
        print("[PASS] Topic Variance")
    else:
        print("[FAIL] Topic Variance")
        all_passed = False

    # 4. DIFFICULTY IMPACT CHECK
    diff_impact_pass = True
    diff_stats = df.groupby('difficulty').agg({'accuracy': 'mean', 'time_taken': 'mean'})
    
    if (diff_stats.loc[1, 'accuracy'] <= diff_stats.loc[2, 'accuracy'] or 
        diff_stats.loc[2, 'accuracy'] <= diff_stats.loc[3, 'accuracy']):
        diff_impact_pass = False
        issues_found.append("DIFFICULTY IMPACT: Higher difficulty did not lower accuracy.")
        
    if (diff_stats.loc[1, 'time_taken'] >= diff_stats.loc[2, 'time_taken'] or 
        diff_stats.loc[2, 'time_taken'] >= diff_stats.loc[3, 'time_taken']):
        diff_impact_pass = False
        issues_found.append("DIFFICULTY IMPACT: Higher difficulty did not increase time taken.")
        
    if diff_impact_pass:
        print("[PASS] Difficulty Impact")
    else:
        print("[FAIL] Difficulty Impact")
        all_passed = False

    # 5. CLASS BALANCE CHECK
    topic_dist = df['topic'].value_counts(normalize=True)
    diff_dist = df['difficulty'].value_counts(normalize=True)
    
    if (topic_dist > 0.6).any():
        print(f"[WARN] Class Balance: Topic '{topic_dist.idxmax()}' is overrepresented ({topic_dist.max():.2%}).")
    elif (diff_dist > 0.6).any():
        print(f"[WARN] Class Balance: Difficulty '{diff_dist.idxmax()}' is overrepresented ({diff_dist.max():.2%}).")
    else:
        print("[PASS] Class Balance")

    # 6. ATTEMPTS BEHAVIOR CHECK
    attempts_pass = True
    att_stats = df.groupby('difficulty')['attempts'].mean()
    if (att_stats.loc[1] > att_stats.loc[2] and att_stats.loc[1] > att_stats.loc[3]):
        attempts_pass = False
        issues_found.append("ATTEMPTS BEHAVIOR: Easy problems had more attempts than hard problems.")
        
    if attempts_pass:
        print("[PASS] Attempts Behavior")
    else:
        print("[FAIL] Attempts Behavior")
        all_passed = False

    # 7. FEATURE RANGE CHECK
    range_pass = True
    if not df['accuracy'].isin([0, 1]).all():
        range_pass = False
        issues_found.append("FEATURE RANGE: Accuracy contains values other than 0 and 1.")
    if (df['time_taken'] <= 0).any():
        range_pass = False
        issues_found.append("FEATURE RANGE: Time taken contains zero or negative values.")
    if (df['attempts'] < 1).any():
        range_pass = False
        issues_found.append("FEATURE RANGE: Attempts contains values less than 1.")
        
    if range_pass:
        print("[PASS] Feature Range")
    else:
        print("[FAIL] Feature Range")
        all_passed = False

    # 8. DATASET SIZE CHECK
    size_pass = True
    num_rows = len(df)
    num_users = df['user_id'].nunique()
    if num_rows < 5000 or num_users < 100:
        size_pass = False
        issues_found.append(f"DATASET SIZE: Expected >=5000 rows and >=100 users, got {num_rows} rows and {num_users} users.")
        
    if size_pass:
        print(f"[PASS] Dataset Size ({num_rows} rows, {num_users} users)")
    else:
        print("[FAIL] Dataset Size")
        all_passed = False

    # SUMMARY
    print("\n---------------------------------------------------------")
    print("SUMMARY STATISTICS")
    print("---------------------------------------------------------")
    print(f"Accuracy : Mean={df['accuracy'].mean():.3f}, Std={df['accuracy'].std():.3f}")
    print(f"Time(s)  : Mean={df['time_taken'].mean():.1f}, Std={df['time_taken'].std():.1f}")
    print(f"Attempts : Mean={df['attempts'].mean():.2f}, Std={df['attempts'].std():.2f}")

    if all_passed:
        print("\nDataset is READY for LSTM training")
    else:
        print("\nDataset is NOT READY — fix required")
        print("\n--- ISSUES DETECTED ---")
        for issue in issues_found:
            print(f"- {issue}")

if __name__ == "__main__":
    run_validation()
