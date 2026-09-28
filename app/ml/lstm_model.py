import torch
import torch.nn as nn

class SkillPredictorLSTM(nn.Module):
    # 9. MODEL CAPACITY: hidden_size = 128
    # Input size: original features (5) + embedding (8) = 13
    def __init__(self, num_users, input_size=13, hidden_size=128, num_layers=2):
        super(SkillPredictorLSTM, self).__init__()
        
        # 3. ADD USER EMBEDDING
        self.user_embedding = nn.Embedding(num_users, 8)
        
        # 6. ADD SMALL DROPOUT
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, 3)

    def forward(self, x, user_id):
        batch_size, seq_len, _ = x.shape
        
        # 3. MODIFY LSTM MODEL
        user_emb = self.user_embedding(user_id)  # (B, 8)
        user_emb = user_emb.unsqueeze(1).repeat(1, seq_len, 1)  # (B, seq_len, 8)
        
        x = torch.cat([x, user_emb], dim=2)  # (B, seq_len, 13)
        
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        
        success = out[:, 0]
        time = out[:, 1]
        attempts = out[:, 2]

        time = time * 2
        attempts = attempts * 2
        
        return success, time, attempts
