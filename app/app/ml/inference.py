import numpy as np
import pandas as pd
import torch
import scipy.stats as stats
from app.ml.model_loader import ModelLoader

def calibrate_probs(probs, temperature=0.7):
    """Increase separation between classes using temperature sharpening."""
    probs = np.array(probs)
    probs = probs ** (1.0 / temperature)
    probs = probs / probs.sum()
    return probs

def calculate_confidence(probs):
    """Compute advanced confidence score using entropy and top-2 gap."""
    probs = np.array(probs)
    entropy = stats.entropy(probs)
    
    if entropy < 1.5:
        confidence = np.max(probs)
    else:
        confidence = np.max(probs) * 0.9
            
    sorted_probs = sorted(probs, reverse=True)
    gap = sorted_probs[0] - sorted_probs[1]
    
    if gap > 0.15:
        confidence += 0.1
            
    return min(confidence, 0.95)

def get_recommendation(user_features: dict):
    """
    Takes a dictionary of user features and returns ML-based recommendation.
    """
    loader = ModelLoader.get_instance()
    
    # 1. Prepare feature vector (ensure correct order)
    feature_dict = {fname: user_features.get(fname, 0.5) for fname in loader.feature_names}
    X = pd.DataFrame([feature_dict], columns=loader.feature_names)
    
    # 2. Topic Prediction
    probs_topic = loader.rf_topic_model.predict_proba(X)[0]
    probs_topic = calibrate_probs(probs_topic, temperature=0.7)
    topic_idx = np.argmax(probs_topic)
    topic_label = loader.rf_topic_model.classes_[topic_idx]
    
    # 3. Difficulty Prediction
    probs_diff = loader.rf_difficulty_model.predict_proba(X)[0]
    probs_diff = calibrate_probs(probs_diff, temperature=0.9)
    diff_idx = np.argmax(probs_diff)
    diff_label = int(loader.rf_difficulty_model.classes_[diff_idx])
    
    # 4. Confidence Calculations
    topic_conf = calculate_confidence(probs_topic)
    diff_conf = calculate_confidence(probs_diff)
    
    # 5. Strong User Boost (Special Heuristic)
    skill_score = feature_dict.get('skill_score', 0.0)
    if skill_score > 0.75:
        mastery_vals = {t.replace('topic_mastery_', ''): feature_dict[t] for t in loader.feature_names if 'topic_mastery_' in t}
        if mastery_vals:
            weak_topic = min(mastery_vals, key=mastery_vals.get)
            if topic_label == weak_topic:
                topic_conf += 0.15
            if mastery_vals.get(topic_label, 1.0) < 0.3:
                topic_conf += 0.10
            weak_count = sum(1 for v in mastery_vals.values() if v < 0.4)
            if weak_count <= 2:
                topic_conf += 0.05
        topic_conf = min(topic_conf, 0.95)

    return {
        "topic": topic_label,
        "difficulty": diff_label,
        "confidence": float(topic_conf)
    }

def get_lstm_skill(sequence_features, user_idx):
    """
    Calculates skill score using the LSTM model.
    """
    loader = ModelLoader.get_instance()
    if loader.lstm_model is None:
        return 0.5
        
    seq_t = torch.tensor(np.array([sequence_features]), dtype=torch.float32)
    u_t = torch.tensor([user_idx], dtype=torch.long)
    
    with torch.no_grad():
        success_pred, time_pred, att_pred = loader.lstm_model(seq_t, u_t)
        
    succ = success_pred.item()
    t_pred = time_pred.item()
    a_pred = att_pred.item()
    
    # Normalization constants (from evaluate_lstm)
    min_t, max_t = 0.3, 0.4
    min_a, max_a = 1.4, 2.1
    norm_t_pred = max(0.0, min(1.0, (t_pred - min_t) / (max_t - min_t + 1e-8)))
    norm_a_pred = max(0.0, min(1.0, (a_pred - min_a) / (max_a - min_a + 1e-8)))
    
    perf_t = 0.3 * succ + 0.35 * (1.0 - norm_t_pred) + 0.35 * (1.0 - norm_a_pred)
    return float(perf_t)
