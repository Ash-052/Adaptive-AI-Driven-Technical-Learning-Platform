import os
import joblib
import json
import torch
import logging
from app.ml.lstm_model import SkillPredictorLSTM

logger = logging.getLogger(__name__)

class ModelLoader:
    _instance = None

    def __init__(self):
        self.lstm_model = None
        self.rf_topic_model = None
        self.rf_difficulty_model = None
        self.feature_names = None
        self.user_to_index = None
        self.scalers = None
        self.load_all()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            logger.info("Initializing ModelLoader singleton...")
            cls._instance = ModelLoader()
        return cls._instance

    def load_all(self):
        models_dir = "app/models"
        
        # Load user to index mapping
        try:
            with open(os.path.join(models_dir, "user_to_index.json"), "r") as f:
                self.user_to_index = json.load(f)
            logger.info("User mapping loaded.")
        except Exception as e:
            logger.error(f"Error loading user_to_index.json: {e}")

        # Load scalers
        try:
            self.scalers = joblib.load(os.path.join(models_dir, "scalers.pkl"))
            logger.info("Scalers loaded.")
        except Exception as e:
            logger.error(f"Error loading scalers.pkl: {e}")

        # Load LSTM
        try:
            num_users = len(self.user_to_index) if self.user_to_index else 100
            self.lstm_model = SkillPredictorLSTM(num_users=num_users, input_size=13, hidden_size=128)
            self.lstm_model.load_state_dict(torch.load(os.path.join(models_dir, "lstm_model.pt"), weights_only=True))
            self.lstm_model.eval()
            logger.info("LSTM model loaded.")
        except Exception as e:
            logger.error(f"Error loading lstm_model.pt: {e}")

        # Load RF Models
        try:
            self.rf_topic_model = joblib.load(os.path.join(models_dir, "rf_topic_model.pkl"))
            self.rf_difficulty_model = joblib.load(os.path.join(models_dir, "rf_difficulty_model.pkl"))
            logger.info("Random Forest models loaded.")
        except Exception as e:
            logger.error(f"Error loading RF models: {e}")

        # Load feature names
        try:
            with open(os.path.join(models_dir, "feature_names.json"), "r") as f:
                self.feature_names = json.load(f)
            logger.info("Feature names loaded.")
        except Exception as e:
            logger.error(f"Error loading feature_names.json: {e}")
