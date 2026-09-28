import joblib
import pandas as pd
import numpy as np
import json
import os
import scipy.stats as stats

class RFInferenceEngine:
    def __init__(self):
        self.topic_model = None
        self.diff_model = None
        self.feature_names = None
        self.load_models()

    def load_models(self):
        topic_path = "app/models/rf_topic_model.pkl"
        diff_path = "app/models/rf_difficulty_model.pkl"
        features_path = "app/models/feature_names.json"
        
        if os.path.exists(topic_path) and os.path.exists(diff_path):
            self.topic_model = joblib.load(topic_path)
            self.diff_model = joblib.load(diff_path)
            with open(features_path, "r") as f:
                self.feature_names = json.load(f)
            print(f"Models loaded successfully. Features: {len(self.feature_names)}")

    def calibrate_probs(self, probs, temperature=0.7):
        """Increase separation between classes using temperature sharpening."""
        probs = np.array(probs)
        # Temperature sharpening
        probs = probs ** (1.0 / temperature)
        probs = probs / probs.sum()
        return probs

    def calculate_confidence(self, probs):
        """Compute advanced confidence score using entropy and top-2 gap."""
        probs = np.array(probs)
        entropy = stats.entropy(probs)
        
        # Base confidence from max probability, penalized by high entropy
        if entropy < 1.5:
            confidence = np.max(probs)
        else:
            confidence = np.max(probs) * 0.9
            
        # Top-2 Gap Boost
        sorted_probs = sorted(probs, reverse=True)
        gap = sorted_probs[0] - sorted_probs[1]
        
        if gap > 0.15:
            confidence += 0.1
            
        return min(confidence, 0.95)

    def validate_and_normalize(self, user_features: dict) -> dict:
        """Ensure all inputs are in the [0, 1] range."""
        clean_features = {}
        for fname in self.feature_names:
            val = user_features.get(fname, 0.5)
            
            # Basic range check for most features (should be 0-1)
            if "avg_time" in fname and val > 1.0:
                val = min(val / 300.0, 1.0)
            elif "attempts" in fname and val > 1.0:
                val = min(val / 5.0, 1.0)
            
            clean_features[fname] = max(0.0, min(1.0, float(val)))
        return clean_features

    def predict_next(self, user_features: dict, debug=False) -> dict:
        if not self.topic_model or not self.diff_model:
            self.load_models()
            
        # 1. Normalize and Validate
        clean_features = self.validate_and_normalize(user_features)
        
        # 2. Fix Feature Alignment (Use DataFrame)
        X = pd.DataFrame([clean_features], columns=self.feature_names)
        
        # Extract topic mastery values for fallbacks/boosts
        mastery_vals = {t.replace('topic_mastery_', ''): clean_features[t] for t in self.feature_names if 'topic_mastery_' in t}
        weakest_topic = min(mastery_vals, key=mastery_vals.get) if mastery_vals else "basics"

        # --- COMPUTE ADVANCED FEATURES ---
        mastery_list = list(mastery_vals.values()) if mastery_vals else [0.5]
        clean_features['weakest_mastery'] = min(mastery_list)
        clean_features['mastery_gap'] = max(mastery_list) - min(mastery_list)
        
        # Set one-hot is_weak flags
        for t in mastery_vals.keys():
            clean_features[f'is_weak_{t}'] = 1.0 if t == weakest_topic else 0.0

        # 2. Fix Feature Alignment (Use DataFrame)
        X = pd.DataFrame([clean_features], columns=self.feature_names)

        # 3. Predict Topic
        probs_topic = self.topic_model.predict_proba(X)[0]
        probs_topic = self.calibrate_probs(probs_topic, temperature=0.7)
        
        topic_idx = np.argmax(probs_topic)
        topic_label = self.topic_model.classes_[topic_idx]
        topic_conf = self.calculate_confidence(probs_topic)
        
        # --- CONFIDENCE FALLBACK ---
        if topic_conf < 0.4:
            if debug: print(f"Low topic confidence ({topic_conf:.2f}). Falling back to weakest topic: {weakest_topic}")
            topic_label = weakest_topic
            topic_conf = 0.5 # Set a neutral confidence for fallback
        
        # --- STRONG USER CONFIDENCE BOOST ---
        skill_score = clean_features.get('skill_score', 0.0)
        if skill_score > 0.75 and topic_label == weakest_topic:
            topic_conf = min(topic_conf + 0.15, 0.95)
        
        # 4. Predict Difficulty
        probs_diff = self.diff_model.predict_proba(X)[0]
        probs_diff = self.calibrate_probs(probs_diff, temperature=0.9)
        
        diff_idx = np.argmax(probs_diff)
        diff_label = int(self.diff_model.classes_[diff_idx])
        diff_conf = self.calculate_confidence(probs_diff)

        # --- HYBRID RULE OVERRIDE ---
        if skill_score < 0.35:
            if debug and diff_label != 1: print(f"Weak user override: D{diff_label} -> D1")
            diff_label = 1
            diff_conf = 0.9 # High confidence for rule-based
        elif skill_score > 0.75:
            if debug and diff_label != 3: print(f"Strong user override: D{diff_label} -> D3")
            diff_label = 3
            diff_conf = 0.9
        
        if debug:
            print(f"Final Decision: {topic_label} (Conf: {topic_conf:.2f}), Diff: {diff_label} (Conf: {diff_conf:.2f})")
        
        return {
            "next_topic": topic_label,
            "confidence_topic": float(topic_conf),
            "next_difficulty": diff_label,
            "confidence_difficulty": float(diff_conf)
        }

engine = RFInferenceEngine()

def predict_next(user_features: dict, debug=False) -> dict:
    return engine.predict_next(user_features, debug)

if __name__ == "__main__":
    print("Running Inference Test Cases...")
    
    # 1. Weak User
    weak_user = {
        'skill_score': 0.2,
        'recent_accuracy_last_5': 0.3,
        'avg_time_last_5': 0.8,
        'attempts_last_5': 0.9,
        'performance_score_last_5': 0.25
    }
    # Fill topic mastery
    for t in ["basics", "arrays", "strings", "recursion", "sorting", "searching", "dynamic_programming", "graphs", "trees"]:
        weak_user[f"topic_mastery_{t}"] = 0.2
        
    # 2. Medium User
    medium_user = weak_user.copy()
    medium_user.update({
        'skill_score': 0.5,
        'recent_accuracy_last_5': 0.6,
        'avg_time_last_5': 0.4,
        'attempts_last_5': 0.4,
        'performance_score_last_5': 0.6
    })
    for t in ["basics", "arrays", "strings"]: medium_user[f"topic_mastery_{t}"] = 0.7
    
    # 3. Strong User
    strong_user = medium_user.copy()
    strong_user.update({
        'skill_score': 0.85,
        'recent_accuracy_last_5': 0.9,
        'avg_time_last_5': 0.1,
        'attempts_last_5': 0.2,
        'performance_score_last_5': 0.9
    })
    # For strong user, make one topic explicitly weak to trigger the boost
    for t in ["basics", "arrays", "strings", "recursion", "sorting", "searching", "dynamic_programming", "graphs", "trees"]: 
        strong_user[f"topic_mastery_{t}"] = 0.9
    strong_user["topic_mastery_trees"] = 0.1 # Weak topic

    users = [("Weak", weak_user), ("Medium", medium_user), ("Strong", strong_user)]
    
    for name, u in users:
        print(f"\n>>> Testing {name} User Profile")
        res = predict_next(u, debug=True)
        print(json.dumps(res, indent=2))
