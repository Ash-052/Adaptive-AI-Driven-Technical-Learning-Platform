import numpy as np
import torch
from app.db.supabase import supabase
from app.ml.model_loader import ModelLoader

def update_global_skill(user_id: str):
    """
    Fetches recent attempts and runs LSTM inference to update the global skill score.
    """
    try:
        # 1. Fetch last 10 attempts
        res = supabase.table('user_attempts').select('accuracy, time_taken, difficulty, attempts') \
            .eq('user_id', user_id).order('created_at', desc=True).limit(10).execute()
        
        # Handle the tuple pattern (data, count) or response object
        if isinstance(res, tuple):
            attempts = res[0][1] if len(res[0]) > 1 else []
        else:
            attempts = res.data
            
        if not attempts:
            return 0.3 # Default for new users

        # 2. Preprocess data for LSTM (padding to length 10)
        sequence = []
        for a in reversed(attempts): # Oldest first
            # Normalize: accuracy (0-1), time (capped 300s), difficulty (1-3), attempts (capped 5)
            norm_time = min(a['time_taken'] / 300.0, 1.0)
            norm_attempts = min(a['attempts'] / 5.0, 1.0)
            norm_diff = (a['difficulty'] - 1) / 2.0
            sequence.append([a['accuracy'], norm_time, norm_diff, norm_attempts])
            
        # Pad with zeros if less than 10
        while len(sequence) < 10:
            sequence.insert(0, [0, 0, 0, 0])
            
        # 3. Load Model and Run Inference
        loader = ModelLoader.get_instance()
        model = loader.lstm_model
        
        if model:
            model.eval()
            with torch.no_grad():
                input_tensor = torch.FloatTensor([sequence]) # Batch size 1
                prediction = model(input_tensor)
                new_skill = float(prediction.item())
        else:
            # Fallback to simple moving average if model not loaded
            new_skill = sum([a['accuracy'] for a in attempts]) / len(attempts)

        # 4. Update Users table
        supabase.table('users').update({"skill_score": round(new_skill, 3)}).eq('id', user_id).execute()
        
        return new_skill
        
    except Exception as e:
        print(f"Error updating global skill for user {user_id}: {e}")
        return 0.5
