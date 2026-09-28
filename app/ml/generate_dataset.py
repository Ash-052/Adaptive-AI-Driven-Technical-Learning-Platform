import os
import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Constants
NUM_USERS = 100
TOPICS = [
    "basics", "arrays", "strings", "recursion", "sorting", 
    "searching", "dynamic_programming", "graphs", "trees"
]
DIFFICULTIES = [1, 2, 3]

def generate_user_data(user_id, start_time):
    # 1. CREATE STRONG USER PERSONALITY PROFILES
    base_skill = random.uniform(0.2, 0.9)
    learning_rate = random.uniform(0.001, 0.01)
    consistency = random.uniform(0.5, 1.5)
    
    num_interactions = random.randint(50, 80)
    user_interactions = []
    current_time = start_time
    
    for step in range(num_interactions):
        topic = random.choice(TOPICS)
        # Evenly distribute difficulties to ensure we see all conditions
        diff_probs = [0.33, 0.34, 0.33]
        difficulty = int(np.random.choice(DIFFICULTIES, p=diff_probs))
        
        # 2. ADD HIGH VARIANCE NOISE
        # 2. ADD HIGH VARIANCE NOISE AND LINEAR PROGRESSION
        progress = step / num_interactions  # linear progression signal
        accuracy = base_skill + 0.5 * progress + np.random.normal(0, 0.08)
        # Clamp accuracy to [0,1]
        accuracy = max(0.0, min(1.0, accuracy))

        base_time = 120 + (1 - base_skill) * 200
        time = base_time * difficulty * consistency
        time *= (1.5 - progress)
        time *= random.uniform(0.8, 1.5)
        time += np.random.normal(0, 20)

        if random.random() < 0.2:
            time *= random.uniform(1.3, 1.8)
        
        time = max(30, time)

        attempts = int((1.5 + (1 - base_skill) * 2) * difficulty * (1.3 - progress))
        attempts += random.randint(0, 1)
        attempts = max(1, attempts)
        
        # 3. MAKE DIFFICULTY IMPACT STRONG
        # 3. MAKE DIFFICULTY IMPACT STRONG
        if difficulty == 1:
            accuracy += 0.1
        elif difficulty == 3:
            accuracy -= 0.2
            time *= 1.3
            attempts += 1
            
        # 5. NON-LINEAR LEARNING REMOVED – linear progression already applied above
        # final_accuracy derived from linear accuracy signal
        accuracy = max(0.0, min(1.0, accuracy))
        final_accuracy = int(np.random.binomial(1, accuracy))
        
        # 4. ADD FAILURE CASES (CRITICAL)
        if difficulty == 3 and base_skill < 0.4 and random.random() < 0.7:
            final_accuracy = 0
            
        time_taken = int(max(10, time))
        attempts = int(attempts)
        
        # Maintain logical consistency for attempts on failure
        if final_accuracy == 0:
            attempts += random.randint(1, 2)
            
        time_jump = timedelta(minutes=random.randint(5, 1440))
        current_time += time_jump
        
        user_interactions.append({
            "user_id": f"usr_{user_id:03d}",
            "problem_id": f"prob_{topic[:3]}_{difficulty}_{random.randint(1, 100):03d}",
            "topic": topic,
            "difficulty": difficulty,
            "accuracy": final_accuracy,
            "time_taken": time_taken,
            "attempts": attempts,
            "timestamp": current_time.isoformat()
        })
        
    return user_interactions, base_skill

def generate_dataset():
    print("Starting dataset generation...")
    os.makedirs("app/data", exist_ok=True)
    
    all_data = []
    user_sequences = {}
    start_date = datetime(2023, 1, 1)
    
    base_skills = []
    
    for i in range(NUM_USERS):
        user_id = i + 1
        interactions, skill = generate_user_data(user_id, start_date)
        all_data.extend(interactions)
        user_sequences[f"usr_{user_id:03d}"] = interactions
        base_skills.append(skill)
        
    df = pd.DataFrame(all_data)
        
    df.to_csv("app/data/sequential_dataset.csv", index=False)
    with open("app/data/user_sequences.json", "w") as f:
        json.dump(user_sequences, f, indent=2)
        
    print("\n--- DATA QUALITY CHECKS ---")
    print(f"Total rows: {len(df)}")
    print(f"Unique users: {df['user_id'].nunique()}")
    print(f"Accuracy Std: {df['accuracy'].std():.3f}")
    print(f"Time Mean: {df['time_taken'].mean():.3f}")
    print(f"Time Std : {df['time_taken'].std():.3f}")
    print(f"Attempts Std: {df['attempts'].std():.3f}")
    print("\nDataset generation completed successfully!")

if __name__ == "__main__":
    generate_dataset()
