import numpy as np
from app.db.supabase import supabase
from app.services.topic_mastery_service import get_user_mastery
from app.ml.inference import get_recommendation, get_lstm_skill
from app.ml.model_loader import ModelLoader

def compute_performance_score(accuracy, time_taken, attempts):
    norm_time = min(time_taken / 300.0, 1.0)
    norm_att = min(attempts / 5.0, 1.0)
    return (accuracy * 0.6) + ((1.0 - norm_time) * 0.2) + ((1.0 - norm_att) * 0.2)

async def get_next_problem(user_id: str):
    """
    Orchestrates the data fetching and ML inference to recommend the next problem.
    """
    loader = ModelLoader.get_instance()
    
    # 1. Fetch Topic Mastery
    mastery = get_user_mastery(user_id)
    
    # 2. Fetch Last 5 Attempts
    try:
        response = supabase.table('user_attempts') \
            .select('accuracy, time_taken, attempts, topic, difficulty') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        attempts_data = response.data if response.data else []
    except Exception as e:
        print(f"Error fetching attempts for user {user_id}: {e}")
        attempts_data = []

    # 3. Compute Recent Stats (Last 5)
    last_5 = attempts_data[:5]
    if last_5:
        recent_acc_5 = np.mean([a['accuracy'] for a in last_5])
        avg_time_5 = np.mean([a['time_taken'] for a in last_5])
        avg_att_5 = np.mean([a['attempts'] for a in last_5])
        avg_perf_5 = np.mean([compute_performance_score(a['accuracy'], a['time_taken'], a['attempts']) for a in last_5])
    else:
        recent_acc_5, avg_time_5, avg_att_5, avg_perf_5 = 0.5, 30.0, 1.5, 0.5

    # 4. Compute LSTM Skill (Sequence of 10)
    # We need to preprocess features for LSTM exactly as in evaluate_lstm
    skill_score = 0.5 # Default
    if len(attempts_data) >= 10:
        # Note: This requires full feature preprocessing. For MVP, we can use an approximation 
        # or implement the full normalization logic here.
        # Approximation: Using a weighted moving average of performance scores
        perf_scores = [compute_performance_score(a['accuracy'], a['time_taken'], a['attempts']) for a in attempts_data]
        skill_score = np.mean(perf_scores)
    
    # 5. Build Feature Vector
    user_features = {
        'skill_score': skill_score,
        'recent_accuracy_last_5': recent_acc_5,
        'avg_time_last_5': min(avg_time_5 / 300.0, 1.0),
        'attempts_last_5': min(avg_att_5 / 5.0, 1.0),
        'performance_score_last_5': avg_perf_5
    }
    # Add topic mastery
    for topic, val in mastery.items():
        user_features[f'topic_mastery_{topic}'] = val
        
    # 6. Call ML Inference
    recommendation = get_recommendation(user_features)
    
    return recommendation
